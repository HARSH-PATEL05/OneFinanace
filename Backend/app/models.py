from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Integer, Float, TIMESTAMP, JSON, Boolean, Identity, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableDict


# -----------------------------------------
# Base Class (SQLAlchemy 2.0 Typed)
# -----------------------------------------
class Base(DeclarativeBase):
    pass


# -----------------------------------------
# USERS
# -----------------------------------------
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow
    )


# -----------------------------------------
# HOLDINGS
# -----------------------------------------
class Holding(Base):
    __tablename__ = "holding"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer,Identity(start=1, cycle=False), primary_key=True, index=True)
    broker: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String)

    Qty: Mapped[float] = mapped_column(Float, default=0)
    average_price: Mapped[float] = mapped_column(Float, default=0.0)
    Ltp: Mapped[float] = mapped_column(Float, default=0.0)
    prev_ltp: Mapped[float] = mapped_column(Float, default=0.0)

    # Important: MutableDict ensures SQLAlchemy tracks in-place JSON changes
    additional_data: Mapped[Optional[dict]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# -----------------------------------------
# MUTUAL FUNDS
# -----------------------------------------
class MutualFund(Base):
    __tablename__ = "mutual_fund"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer,Identity(start=1, cycle=False), primary_key=True, index=True)
    broker: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    fund: Mapped[str] = mapped_column(String)

    Qty: Mapped[float] = mapped_column(Float, default=0)
    average_price: Mapped[float] = mapped_column(Float, default=0.0)
    Ltp: Mapped[float] = mapped_column(Float, default=0.0)
    prev_close: Mapped[float] = mapped_column(Float, default=0.0)
    additional_data: Mapped[Optional[dict]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# -----------------------------------------
# ACCOUNTS
# -----------------------------------------
class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, cycle=False),
        nullable=False,
        index=True
    )

    # PK is business key
    account_number: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        unique=True,
        nullable=False,
        index=True
    )

    bank_name: Mapped[str] = mapped_column(String, nullable=False)
    acronym: Mapped[str] = mapped_column(String, nullable=False)
    holder_name: Mapped[Optional[str]] = mapped_column(String)

    current_balance: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# -----------------------------------------
# TRANSACTIONS
# -----------------------------------------
class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bankName: Mapped[str] = mapped_column(String, nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    sms_account_number: Mapped[Optional[str]] = mapped_column(String)

    type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[Optional[str]] = mapped_column(String)
    reference_id: Mapped[Optional[str]] = mapped_column(String)

    sms_timestamp: Mapped[Optional[float]] = mapped_column(Float)
    sms_formatted_datetime: Mapped[Optional[str]] = mapped_column(String)

    txn_datetime: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.utcnow
    )

    balance_after_txn: Mapped[Optional[float]] = mapped_column(Float)
    sms_balance: Mapped[Optional[float]] = mapped_column(Float)

    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    isSynced: Mapped[bool] = mapped_column(Boolean, default=False)

    description: Mapped[Optional[str]] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=text("now()"),
        default=datetime.utcnow
    )
