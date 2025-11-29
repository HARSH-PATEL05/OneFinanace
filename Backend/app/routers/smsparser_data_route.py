# app/routers/smsparser_data_route.py

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.db import SessionLocal
from app import crud, schemas

router = APIRouter(tags=["smsparser"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/smsparser/receive")
async def receive_sms_data(request: Request, db: Session = Depends(get_db)):
    """
    Receive SMS data from Android parser and insert as raw transaction.

    Now also accepts **bankName** and stores into DB.
    """
    body = await request.json()

    # Build schema - TransactionCreate
    txn = schemas.TransactionCreate(
        account_number=body.get("account_number"),
        sms_account_number=body.get("account"),

        # NEW: bankName support
        bankName=body.get("bankName") or body.get("bank") or body.get("bank_name"),

        type=body.get("type"),
        amount=body.get("amount"),

        mode=body.get("mode"),
        reference_id=body.get("upiRef") or body.get("reference_id"),

        sms_timestamp=body.get("date") or body.get("sms_timestamp"),
        sms_formatted_datetime=body.get("formattedDate") or body.get("sms_formatted_datetime"),

        txn_datetime=body.get("txn_datetime"),
        sms_balance=body.get("availableBalance") or body.get("sms_balance"),

        description=body.get("messageBody") or body.get("description"),
    )

    saved = crud.insert_raw_transaction(db, txn)
    return {"status": "received", "transaction_id": saved.id}


@router.get("/smsparser/all")
def get_all_sms_data(db: Session = Depends(get_db)):
    """
    Debug endpoint: return ALL transactions (synced + unsynced).
    Now also returns bankName.
    """
    txns = db.query(crud.models.Transaction).order_by(
        crud.models.Transaction.txn_datetime.desc()
    ).all()

    result: List[Dict] = []
    for t in txns:
        result.append({
            "id": t.id,
            "account_id": t.account_id,
            "sms_account_number": t.sms_account_number,

            # ADDED
            "bankName": t.bankName,

            "type": t.type,
            "amount": t.amount,
            "mode": t.mode,
            "reference_id": t.reference_id,
            "txn_datetime": t.txn_datetime,
            "sms_timestamp": t.sms_timestamp,
            "sms_formatted_datetime": t.sms_formatted_datetime,
            "sms_balance": t.sms_balance,
            "balance_after_txn": t.balance_after_txn,
            "is_auto_generated": t.is_auto_generated,
            "isSynced": t.isSynced,
            "description": t.description,
            "created_at": t.created_at,
        })

    return {"total": len(result), "data": result}
