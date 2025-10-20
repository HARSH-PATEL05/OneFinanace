from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, JSON

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Holding(Base):
    __tablename__ = "holding"

    id = Column(Integer, primary_key=True, index=True)
    broker = Column(String, nullable=False)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String)
    Qty = Column(Float, default=0)
    average_price = Column(Float)
    Ltp = Column(Float)
    prev_ltp = Column(Float)
    additional_data = Column(JSON)  # store full raw API data
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


class MutualFund(Base):
    __tablename__ = "mutual_fund"

    id = Column(Integer, primary_key=True, index=True)
    broker = Column(String, nullable=False)
    symbol = Column(String, nullable=False, index=True)
    fund = Column(String)
    Qty = Column(Float, default=0)
    average_price = Column(Float)
    Ltp = Column(Float)
    additional_data = Column(JSON)  # store full raw API data
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)