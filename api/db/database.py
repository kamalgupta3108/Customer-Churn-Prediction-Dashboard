"""
api/db/database.py
--------------------
This file's ONE job: set up the connection to our PostgreSQL database, and
provide a reusable way for other code to "borrow" a connection when needed.

You already know SQL commands like SELECT/INSERT run against a database.
Normally you'd open a connection (like using psql in your terminal), run
your command, then close the connection. This file automates that "open
a connection, use it, close it" cycle so we don't have to think about it
in every single endpoint.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load variables from our .env file (DATABASE_URL, SECRET_KEY, etc.)
# so we never hardcode passwords directly in our code.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# The "engine" is the actual connection pool to PostgreSQL - it manages
# opening/reusing/closing connections efficiently behind the scenes.
engine = create_engine(DATABASE_URL)

# SessionLocal is a "factory" that creates a new database session
# (a temporary workspace for running queries) whenever we need one.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is what all our table definitions (in models.py) will inherit from.
# It's how SQLAlchemy knows "these Python classes represent database tables."
Base = declarative_base()


def get_db():
    """
    This is a "dependency" - FastAPI will call this automatically for any
    endpoint that needs database access. It opens a session, hands it to
    the endpoint function (via `yield`), and guarantees the session gets
    closed afterward, even if an error happens. This pattern avoids
    connection leaks (forgetting to close a connection), which is a real
    and common bug in database code.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
