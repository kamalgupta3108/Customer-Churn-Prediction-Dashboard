"""
api/services/auth.py
----------------------
Handles two things:
1. Password hashing - never store real passwords, ever.
2. JWT tokens - the "wristband" system explained earlier.

WHY NEVER STORE REAL PASSWORDS?
If our database ever got hacked/leaked, plain-text passwords would let the
attacker log into every user's account (and often their OTHER accounts too,
since people reuse passwords). Instead, we store a "hash" - a one-way
scrambled version. You can turn a password INTO a hash, but you cannot turn
a hash BACK into the password. To check a login, we hash the entered
password again and compare the two hashes - we never need to "unscramble"
anything.
"""

import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from api.db.database import get_db
from api.db import models

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# bcrypt is the actual hashing algorithm - it's deliberately SLOW, on
# purpose, which makes it expensive for an attacker to try billions of
# password guesses against a leaked hash.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This tells FastAPI's docs page how clients should send their token:
# in a header like "Authorization: Bearer <token>". tokenUrl points to
# our login endpoint, purely for the interactive /docs page's benefit.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    """Turn a plain password into an irreversible scrambled hash."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt's password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Creates a signed JWT token ("wristband"). It contains the user's
    identity (email) and an expiry time, and is SIGNED with our SECRET_KEY
    so we can later verify it wasn't tampered with or faked by someone
    who doesn't know our secret key.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    This is a "dependency" any protected endpoint can use. FastAPI will:
    1. Extract the token from the request's Authorization header
    2. Run this function, which decodes/verifies the token
    3. Look up the matching user in the database
    4. Hand that user object to the endpoint function

    If the token is missing, expired, tampered with, or doesn't match a
    real user, this raises a 401 Unauthorized error automatically -
    the endpoint's actual code never even runs.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
