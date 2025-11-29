from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# =========================================================
# BASE CONFIG  (Pydantic v1 + v2 Compatibility)
# =========================================================
class ORMBase(BaseModel):
    class Config:
        orm_mode = True
        from_attributes = True   # pydantic v2 compatibility


# =========================================================
# USER SCHEMAS
# =========================================================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(ORMBase):
    id: int
    username: str
    email: str


# =========================================================
# HOLDING / MF SCHEMAS
# =========================================================

class HoldingCreate(BaseModel):
    broker: str
    symbol: str
    name: str
    Qty: float
    average_price: float
    Ltp: float
    prev_ltp: float
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class HoldingResponse(ORMBase):
    id: int
    broker: str
    symbol: str
    name: Optional[str]
    Qty: float
    average_price: float
    Ltp: float
    prev_ltp: float
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MFCreate(BaseModel):
    broker: str
    symbol: str
    fund: str
    Qty: float
    average_price: float
    Ltp: float
    prev_close:float
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MFResponse(ORMBase):
    id: int
    broker: str
    symbol: str
    fund: str
    Qty: float
    average_price: float
    Ltp: float
    prev_close:float
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


# =========================================================
# ACCOUNT SCHEMAS
# =========================================================

class AccountCreate(BaseModel):
    bank_name: str
    acronym: str
    account_number: str
    holder_name: Optional[str] = None
    current_balance: float = 0.0


class AccountUpdate(BaseModel):
    bank_name: Optional[str] = None
    acronym: Optional[str] = None
    holder_name: Optional[str] = None
    current_balance: Optional[float] = None


class AccountResponse(ORMBase):
    id: int
    account_number: str
    bank_name: str
    acronym: str
    holder_name: Optional[str]
    current_balance: float
    created_at: datetime
    updated_at: datetime


# =========================================================
# TRANSACTION SCHEMAS
# =========================================================

class TransactionCreate(BaseModel):
    bankName: Optional[str] = None

    account_number: Optional[str] = None
    sms_account_number: Optional[str] = None

    type: str
    amount: float

    mode: Optional[str] = None
    reference_id: Optional[str] = None

    sms_timestamp: Optional[float] = None
    sms_formatted_datetime: Optional[str] = None

    txn_datetime: Optional[datetime] = None

    sms_balance: Optional[float] = None
    description: Optional[str] = None


class TransactionResponse(ORMBase):
    id: int
    bankName: Optional[str] = None
    # stored as FULL account number
    account_id: Optional[str]
    sms_account_number: Optional[str]

    type: str
    amount: float
    mode: Optional[str]
    reference_id: Optional[str]

    sms_timestamp: Optional[float]
    sms_formatted_datetime: Optional[str]

    txn_datetime: datetime

    balance_after_txn: Optional[float]
    sms_balance: Optional[float]

    is_auto_generated: bool
    isSynced: bool
    description: Optional[str]

    created_at: datetime
