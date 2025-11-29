from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Optional

# ✅ Use the safe redis helpers (NO redis_client)
from redis_client import (
    get_redis,
    redis_safe_get,
    redis_safe_set,
    redis_safe_json_get,
    redis_safe_json_set
)

from . import models
from . import schemas


# ------------------------------------------------------
# Small helper
# ------------------------------------------------------
def safe_float(v) -> float:
    try:
        return float(str(v))
    except Exception:
        return 0.0


# ------------------------------------------------------
# Reset IDs
# ------------------------------------------------------
def reset_ids(db: Session, table_model, table_name: str):
    rows = db.query(table_model).order_by(table_model.id).all()
    next_id = 1

    for r in rows:
        try:
            r.id = next_id
        except Exception:
            pass
        next_id += 1

    db.commit()

    seq_name = f"public.{table_name}_id_seq"
    try:
        db.execute(text(f"ALTER SEQUENCE {seq_name} RESTART WITH {next_id}"))
        db.commit()
    except Exception:
        db.rollback()


# =========================
# USER CRUD
# =========================
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        username=user.username,
        email=user.email,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session):
    return db.query(models.User).all()


# =========================
# ACCOUNT CRUD
# =========================
def create_account(db: Session, acc: schemas.AccountCreate):
    """
    Account uses bank_name (snake_case).
    Transaction uses bankName (camelCase).
    """
    new_acc = models.Account(
        account_number=acc.account_number,
        bank_name=acc.bank_name,
        acronym=acc.acronym,
        holder_name=acc.holder_name,
        current_balance=acc.current_balance,
    )

    db.add(new_acc)
    db.commit()
    db.refresh(new_acc)

    # Save balance in Redis safely
    redis_safe_set(f"balance:{new_acc.account_number}", new_acc.current_balance)

    # Reset IDs
    try:
        reset_ids(db, models.Account, "accounts")
    except Exception:
        db.rollback()

    return new_acc


def get_account_by_number(db: Session, account_number: str):
    return db.query(models.Account).filter(models.Account.account_number == account_number).first()


def get_account_by_id(db: Session, account_id: int):
    return db.query(models.Account).filter(models.Account.id == account_id).first()


def list_accounts(db: Session):
    return db.query(models.Account).order_by(models.Account.id).all()


def update_account(db: Session, account: models.Account, data: dict):
    for k, v in data.items():
        if v is not None:
            setattr(account, k, v)

    account.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(account)

    # Update Redis
    redis_safe_set(f"balance:{account.account_number}", account.current_balance)

    return account


def delete_account(db: Session, account: models.Account):
    full_acc_no = account.account_number

    # Delete all transactions of this account
    try:
        db.query(models.Transaction).filter(
            models.Transaction.account_id == full_acc_no
        ).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()

    # Delete the account
    try:
        db.delete(account)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Delete Redis key
    try:
        r = get_redis()
        if r:
            r.delete(f"balance:{full_acc_no}")
    except Exception:
        pass

    # Reset both tables
    try:
        reset_ids(db, models.Account, "accounts")
    except Exception:
        db.rollback()

    try:
        reset_ids(db, models.Transaction, "transactions")
    except Exception:
        db.rollback()


# =========================
# INSERT RAW TRANSACTION
# =========================
def insert_raw_transaction(db: Session, txn: schemas.TransactionCreate):
    sms_digits = (txn.sms_account_number or txn.account_number or "").strip()
    matched_account_number: Optional[str] = None

    # Exact match
    if txn.account_number:
        acc = get_account_by_number(db, txn.account_number)
        if acc:
            matched_account_number = acc.account_number

    # EndsWith match
    if matched_account_number is None and sms_digits:
        for acc in list_accounts(db):
            if acc.account_number.strip().endswith(sms_digits):
                matched_account_number = acc.account_number
                break

    # Determine datetime
    if txn.txn_datetime:
        chosen_dt = txn.txn_datetime
    elif txn.sms_timestamp:
        try:
            chosen_dt = datetime.fromtimestamp(float(txn.sms_timestamp) / 1000.0)
        except Exception:
            chosen_dt = datetime.utcnow()
    else:
        chosen_dt = datetime.utcnow()

    # -------------------------------------------
    # NOT YOUR ACCOUNT
    # -------------------------------------------
    if matched_account_number is None:
        new_txn = models.Transaction(
            account_id=None,
            bankName=txn.bankName,
            sms_account_number=sms_digits or None,

            sms_timestamp=safe_float(txn.sms_timestamp),
            sms_formatted_datetime=txn.sms_formatted_datetime,

            type=txn.type.lower(),
            amount=safe_float(txn.amount),
            mode=txn.mode,
            reference_id=txn.reference_id,

            description="NOT YOUR ACCOUNT",
            txn_datetime=chosen_dt,

            balance_after_txn=None,
            sms_balance=txn.sms_balance,
            is_auto_generated=False,
            isSynced=True
        )

        db.add(new_txn)
        db.commit()
        db.refresh(new_txn)

        try:
            reset_ids(db, models.Transaction, "transactions")
        except Exception:
            db.rollback()

        return new_txn

    # -------------------------------------------
    # MATCHED ACCOUNT
    # -------------------------------------------
    new_txn = models.Transaction(
        account_id=matched_account_number,
        bankName=txn.bankName,
        sms_account_number=sms_digits or None,

        sms_timestamp=safe_float(txn.sms_timestamp),
        sms_formatted_datetime=txn.sms_formatted_datetime,

        type=txn.type.lower(),
        amount=safe_float(txn.amount),
        mode=txn.mode,
        reference_id=txn.reference_id,

        description=txn.description,
        txn_datetime=chosen_dt,

        sms_balance=txn.sms_balance,
        isSynced=False
    )

    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)

    try:
        reset_ids(db, models.Transaction, "transactions")
    except Exception:
        db.rollback()

    return new_txn


# =========================
# SYNC ENGINE
# =========================
def process_single_transaction(db: Session, txn: models.Transaction):
    if txn.account_id is None:
        raise ValueError("Cannot sync NOT-YOUR-ACCOUNT transaction.")

    acc = get_account_by_number(db, txn.account_id)
    if acc is None:
        raise ValueError("Account not found")

    created_txns = []

    # ==========================================
    # 1️⃣ Find previous transaction by timestamp
    # ==========================================
    prev_txn = (
        db.query(models.Transaction)
        .filter(models.Transaction.account_id == acc.account_number)
        .filter(models.Transaction.sms_timestamp < txn.sms_timestamp)
        .order_by(models.Transaction.sms_timestamp.desc())
        .first()
    )

    prev_balance = 0.0
    if prev_txn and prev_txn.balance_after_txn is not None:
        prev_balance = safe_float(prev_txn.balance_after_txn)
    else:
        # fallback to account balance
        prev_balance = safe_float(redis_safe_get(f"balance:{acc.account_number}") or acc.current_balance)

    amount = safe_float(txn.amount)
    expected_balance = prev_balance - amount if txn.type == "debit" else prev_balance + amount

    # ==========================================
    # 2️⃣ Mismatch handling if SMS has balance
    # ==========================================
    if txn.sms_balance is not None:
        sms_bal = safe_float(txn.sms_balance)

        if abs(expected_balance - sms_bal) > 0.01:
            diff = expected_balance - sms_bal
            missing_type = "debit" if diff > 0 else "credit"
            base_ts = txn.sms_timestamp if txn.sms_timestamp is not None else txn.txn_datetime.timestamp()
            auto_timestamp = base_ts - 1

            auto_txn = models.Transaction(
                account_id=acc.account_number,
                bankName=acc.bank_name,
                sms_account_number=None,
                type=missing_type,
                amount=abs(diff),
                mode="auto",
                reference_id=None,
                description="Auto-generated missing transaction",
                txn_datetime=datetime.utcnow(),
                sms_timestamp=auto_timestamp,  # ensure order
                balance_after_txn=sms_bal,
                sms_balance=None,
                is_auto_generated=True,
                isSynced=True
            )

            db.add(auto_txn)
            db.commit()
            db.refresh(auto_txn)
            created_txns.append(auto_txn)

        final_balance = sms_bal
    else:
        final_balance = expected_balance

    # ==========================================
    # 3️⃣ Update current txn
    # ==========================================
    txn.balance_after_txn = final_balance
    txn.isSynced = True
    db.commit()
    db.refresh(txn)

    # ==========================================
    # 4️⃣ Recalculate all future transactions
    # ==========================================
    future_txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.account_id == acc.account_number)
        .filter(models.Transaction.sms_timestamp > txn.sms_timestamp)
        .order_by(models.Transaction.sms_timestamp.asc())
        .all()
    )

    running_balance = final_balance
    for ft in future_txns:
        amt = safe_float(ft.amount)
        running_balance = running_balance - amt if ft.type == "debit" else running_balance + amt
        ft.balance_after_txn = running_balance
        db.add(ft)

    # Update account final balance
    acc.current_balance = running_balance
    acc.updated_at = datetime.utcnow()

    db.commit()

    # ==========================================
    # 5️⃣ Update redis
    # ==========================================
    redis_safe_set(f"balance:{acc.account_number}", running_balance)

    created_txns.append(txn)
    return created_txns



def process_all_unsynced_transactions(db: Session):
    unsynced = db.query(models.Transaction).filter(models.Transaction.isSynced == False).all()
    processed = []

    for txn in unsynced:
        processed.extend(process_single_transaction(db, txn))

    try:
        reset_ids(db, models.Transaction, "transactions")
    except Exception:
        db.rollback()

    return processed


# =========================
# FETCH TRANSACTIONS
# =========================
def get_transactions(db: Session, account_number: Optional[str] = None):
    q = db.query(models.Transaction).filter(models.Transaction.isSynced == True)

    if account_number:
        q = q.filter(models.Transaction.account_id == account_number)

    return q.order_by(models.Transaction.txn_datetime.desc()).all()


# =========================
# DELETE TRANSACTIONS
# =========================
def delete_all_transactions(db: Session):
    db.query(models.Transaction).delete(synchronize_session=False)
    db.commit()


def delete_transactions_for_account(db: Session, account_number: str):
    db.query(models.Transaction).filter(
        models.Transaction.account_id == account_number
    ).delete(synchronize_session=False)

    db.commit()
