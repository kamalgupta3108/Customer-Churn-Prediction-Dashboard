"""
api/db/models.py
------------------
This file defines our database TABLES, but written as Python classes
instead of SQL. Each class = one table. Each attribute = one column.

For example, this SQL:
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR UNIQUE NOT NULL,
        hashed_password VARCHAR NOT NULL
    );

...becomes this Python class below. SQLAlchemy converts our Python class
into that exact SQL when we tell it to create the tables.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # We NEVER store the actual password - only a "hashed" (scrambled,
    # irreversible) version. Explained more in auth.py.
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # This creates a Python-side link: user.predictions gives you all
    # PredictionRecord rows belonging to this user, without writing a
    # manual SQL JOIN yourself.
    predictions = relationship("PredictionRecord", back_populates="owner")


class PredictionBatch(Base):
    """
    Represents one CSV upload containing many customers. We track its
    progress here so the client can poll "how's my big upload going?"
    instead of the API being frozen/blocked until it's fully done.
    """
    __tablename__ = "prediction_batches"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(String, default="processing")  # processing | completed | failed
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    records = relationship("PredictionRecord", back_populates="batch")


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("prediction_batches.id"), nullable=True)

    # We store the key input details so history is meaningful to look back on
    contract = Column(String)
    tenure = Column(Integer)
    monthly_charges = Column(Float)

    # The actual prediction result
    churn_probability = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    from_cache = Column(String, default="no")  # "yes"/"no" - useful for demoing caching later

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="predictions")
    batch = relationship("PredictionBatch", back_populates="records")
