from pydantic import BaseModel
from typing import Optional, Dict

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True


class HoldingCreate(BaseModel):
    broker: str
    symbol: str
    name: str
    Qty: float
    average_price: float
    Ltp: float
    prev_ltp:float
    additional_data: Optional[Dict] = None

class HoldingResponse(BaseModel):
    id: int
    broker: str
    symbol: str
    name: str
    Qty: float
    average_price: float
    Ltp: float
    prev_ltp:float
    additional_data: Optional[Dict] = None

    class Config:
        orm_mode = True



class MFCreate(BaseModel):
    broker: str
    symbol: str
    fund: str
    Qty: float
    average_price: float
    Ltp: float
    additional_data: Optional[Dict] = None

class MFResponse(BaseModel):
    id: int
    broker: str
    symbol: str
    fund: str
    Qty: float
    average_price: float
    Ltp: float
    additional_data: Optional[Dict] = None

    class Config:
        orm_mode = True