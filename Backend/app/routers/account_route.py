from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Use runtime-safe getter, NOT redis_client variable
from redis_client import get_redis

from app.db import SessionLocal
from app import crud, schemas

router = APIRouter(tags=["accounts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Safe float
# -----------------------------
def safe_float(v):
    try:
        return float(str(v))
    except Exception:
        return 0.0


# -----------------------------
# Create account
# -----------------------------
@router.post("/accounts", response_model=schemas.AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(acc: schemas.AccountCreate, db: Session = Depends(get_db)):
    existing = crud.get_account_by_number(db, acc.account_number)
    if existing:
        raise HTTPException(400, "Account already exists")

    created = crud.create_account(db, acc)
    return created


# -----------------------------
# Get all accounts (Redis enhanced)
# -----------------------------
@router.get("/accounts", response_model=List[schemas.AccountResponse])
def get_all_accounts(db: Session = Depends(get_db)):
    accounts = crud.list_accounts(db)

    r = get_redis()
    for acc in accounts:
        if not r:
            continue
        try:
            raw = r.get(f"balance:{acc.account_number}")
            if raw is not None:
                raw_str = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                acc.current_balance = safe_float(raw_str)
        except Exception:
            pass

    return accounts


# -----------------------------
# Single account
# -----------------------------
@router.get("/accounts/{account_number}", response_model=schemas.AccountResponse)
def get_single_account(account_number: str, db: Session = Depends(get_db)):
    account = crud.get_account_by_number(db, account_number)
    if not account:
        raise HTTPException(404, "Account not found")

    r = get_redis()
    if r:
        try:
            raw = r.get(f"balance:{account_number}")
            if raw is not None:
                raw_str = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                account.current_balance = safe_float(raw_str)
        except Exception:
            pass

    return account


# -----------------------------
# Update account
# -----------------------------
@router.put("/accounts/{account_number}", response_model=schemas.AccountResponse)
def update_account(account_number: str, acc_data: schemas.AccountUpdate, db: Session = Depends(get_db)):
    account = crud.get_account_by_number(db, account_number)
    if not account:
        raise HTTPException(404, "Account not found")

    updated = crud.update_account(db, account, acc_data.dict())
    return updated


# -----------------------------
# Delete account
# -----------------------------
@router.delete("/accounts/{account_number}", status_code=200)
def delete_account(account_number: str, db: Session = Depends(get_db)):
    account = crud.get_account_by_number(db, account_number)
    if not account:
        raise HTTPException(404, "Account not found")

    crud.delete_account(db, account)
    return {"message": "Account and related transactions deleted"}


# -----------------------------
# All transactions
# -----------------------------
@router.get("/transactions/all", response_model=List[schemas.TransactionResponse])
def get_all_transactions(db: Session = Depends(get_db)):
    return crud.get_transactions(db)


# -----------------------------
# Transactions for one account
# -----------------------------
@router.get("/transactions/{account_number}", response_model=List[schemas.TransactionResponse])
def get_transactions_for_account(account_number: str, db: Session = Depends(get_db)):
    account = crud.get_account_by_number(db, account_number)
    if not account:
        raise HTTPException(404, "Account not found")

    return crud.get_transactions(db, account_number=account_number)


# -----------------------------
# Delete all transactions
# -----------------------------
@router.delete("/transactions", status_code=200)
def delete_all_transactions(db: Session = Depends(get_db)):
    crud.delete_all_transactions(db)
    return {"message": "All transactions deleted successfully"}


# -----------------------------
# Delete all transactions for account
# -----------------------------
@router.delete("/transactions/{account_id}", status_code=200)
def delete_transactions_for_account(account_id: str, db: Session = Depends(get_db)):
    account = crud.get_account_by_number(db, account_id)
    if not account:
        raise HTTPException(404, "Account not found")

    crud.delete_transactions_for_account(db, account_id)
    return {"message": f"All transactions for account {account_id} deleted"}
