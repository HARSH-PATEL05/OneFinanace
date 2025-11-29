from app.db import SessionLocal
from app.models import Holding, MutualFund
from sqlalchemy import text
import json
import logging
import sys
import traceback
from typing import Any


# ---------------------------------------------------------
# Logger setup
# ---------------------------------------------------------
logger = logging.getLogger("database_util")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
logger.propagate = False


# ---------------------------------------------------------
# JSON helper (safe for SQLAlchemy JSON column)
# ---------------------------------------------------------
def safe_json(val: Any) -> dict:
    """
    Make sure additional_data is always a dict.
    SQLAlchemy JSON = dict, not string.
    """
    if val is None:
        return {}

    if isinstance(val, dict):
        return val

    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {"raw": val}

    return {}


# ---------------------------------------------------------
# Save holdings
# ---------------------------------------------------------
def save_holdings_to_db(holdings_list, db=None):
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    added, updated = 0, 0
    try:
        for h in holdings_list:
            try:
                existing = db.query(Holding).filter_by(
                    broker=h["broker"],
                    symbol=h["symbol"]
                ).first()

                qty = int(h.get("Qty", 0))
                average_price = float(h.get("average_price", 0))
                Ltp = float(h.get("Ltp", 0))
                prev_ltp = float(h.get("prev_ltp", 0))
                extra = safe_json(h.get("additional_data"))

                if existing:
                    existing.name = h["name"]
                    existing.Qty = qty
                    existing.average_price = average_price
                    existing.Ltp = Ltp
                    existing.prev_ltp = prev_ltp
                    existing.additional_data = extra
                    updated += 1
                else:
                    holding = Holding(
                        broker=h["broker"],
                        symbol=h["symbol"],
                        name=h["name"],
                        Qty=qty,
                        average_price=average_price,
                        Ltp=Ltp,
                        prev_ltp=prev_ltp,
                        additional_data=extra
                    )
                    db.add(holding)
                    added += 1
            except Exception as inner_e:
                logger.error(f"Error saving holding {h.get('symbol')}: {inner_e}\n{traceback.format_exc()}")

        if own_session:
            db.commit()

        logger.info(f"Holdings saved: {added} added, {updated} updated")

    except Exception as e:
        if own_session:
            db.rollback()
        logger.error(f"Error saving holdings: {e}\n{traceback.format_exc()}")
    finally:
        if own_session:
            db.close()


# ---------------------------------------------------------
# Save mutual funds
# ---------------------------------------------------------
def save_mfs_to_db(mfs_list, db=None):
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    added, updated = 0, 0
    try:
        for mf in mfs_list:
            try:
                existing = db.query(MutualFund).filter_by(
                    broker=mf["broker"],
                    symbol=mf["symbol"]
                ).first()

                qty = float(mf.get("Qty", 0))
                average_price = float(mf.get("average_price", 0))
                Ltp = float(mf.get("Ltp", 0))
                extra = safe_json(mf.get("additional_data"))

                if existing:
                    existing.fund = mf["fund"]
                    existing.Qty = qty
                    existing.average_price = average_price
                    existing.Ltp = Ltp
                    existing.prev_close = Ltp
                    existing.additional_data = extra
                    updated += 1
                else:
                    mutual_fund = MutualFund(
                        broker=mf["broker"],
                        symbol=mf["symbol"],
                        fund=mf["fund"],
                        Qty=qty,
                        average_price=average_price,
                        Ltp=Ltp,
                        prev_close=Ltp,
                        additional_data=extra
                    )
                    db.add(mutual_fund)
                    added += 1
            except Exception as inner_e:
                logger.error(f"Error saving MF {mf.get('symbol')}: {inner_e}\n{traceback.format_exc()}")

        if own_session:
            db.commit()

        logger.info(f"Mutual funds saved: {added} added, {updated} updated")

    except Exception as e:
        if own_session:
            db.rollback()
        logger.error(f"Error saving mutual funds: {e}\n{traceback.format_exc()}")
    finally:
        if own_session:
            db.close()


# ---------------------------------------------------------
# Distinct brokers
# ---------------------------------------------------------
def get_all_brokers():
    db = SessionLocal()
    try:
        query = text("""
            SELECT DISTINCT broker FROM holding
            UNION
            SELECT DISTINCT broker FROM mutual_fund;
        """)
        rows = db.execute(query).fetchall()
        return [row[0] for row in rows]
    finally:
        db.close()


# ---------------------------------------------------------
# Get holdings
# ---------------------------------------------------------
def get_holdings_from_db(broker_name: str):
    db = SessionLocal()
    try:
        holdings = db.query(Holding).filter(Holding.broker == broker_name).all()
        result = []
        for h in holdings:
            result.append({
                "id": h.id,
                "broker": h.broker,
                "symbol": h.symbol,
                "name": h.name,
                "Qty": h.Qty,
                "average_price": h.average_price,
                "Ltp": h.Ltp,
                "prev_ltp": h.prev_ltp,
                "additional_data": safe_json(h.additional_data)
            })
        return result
    finally:
        db.close()


# ---------------------------------------------------------
# Get Mutual Funds
# ---------------------------------------------------------
def get_mfs_from_db(broker_name: str):
    db = SessionLocal()
    try:
        mfs = db.query(MutualFund).filter(MutualFund.broker == broker_name).all()
        result = []
        for mf in mfs:
            result.append({
                "id": mf.id,
                "broker": mf.broker,
                "symbol": mf.symbol,
                "fund": mf.fund,
                "Qty": mf.Qty,
                "prev_close":mf.prev_close,
                "average_price": mf.average_price,
                "Ltp": mf.Ltp,
                "additional_data": safe_json(mf.additional_data)
            })
        return result
    finally:
        db.close()
