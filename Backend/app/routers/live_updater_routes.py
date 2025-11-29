from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Holding, MutualFund
from fastapi.responses import JSONResponse

import websocket_angelone.worker as worker
from redis_client import get_redis

from datetime import datetime, timedelta
import pytz
import json
import os

router = APIRouter(prefix="/live", tags=["Live Updates"])

IST = pytz.timezone("Asia/Kolkata")
HOLIDAY_FILE = os.path.join("market_holidays.json")  # adjust if needed


# === DB Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# === STOCKS (daily snapshot from DB) ===
@router.get("/holdings")
def get_holdings(db: Session = Depends(get_db)):
    holdings = db.query(Holding.symbol, Holding.Ltp, Holding.prev_ltp).all()
    return [{"symbol": h.symbol, "Ltp": h.Ltp, "prev_ltp": h.prev_ltp} for h in holdings]


# === MUTUAL FUNDS (daily snapshot from DB) ===
@router.get("/mfs")
def get_mutual_funds(db: Session = Depends(get_db)):
    mfs = db.query(MutualFund.fund, MutualFund.Ltp, MutualFund.prev_close).all()
    return [{"fund": mf.fund, "Ltp": mf.Ltp, "prev_close": mf.prev_close} for mf in mfs]


# ------------------------------------------
# MARKET STATUS + Best Next Check Timer
# ------------------------------------------
def load_holidays():
    try:
        with open(HOLIDAY_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def get_next_market_open(now, holidays):
    next_day = now

    while True:
        next_day += timedelta(days=1)
        is_weekend = next_day.weekday() >= 5
        date_str = next_day.strftime("%Y-%m-%d")
        is_holiday = any(h.get("date") == date_str for h in holidays)

        if not is_weekend and not is_holiday:
            return next_day.replace(hour=9, minute=15, second=0, microsecond=0)


@router.get("/market-status")
def market_status():
    now = datetime.now(IST)

    open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)

    holidays = load_holidays()
    today = now.strftime("%Y-%m-%d")
    today_holiday = next((h for h in holidays if h.get("date") == today), None)

    # Weekend
    if now.weekday() >= 5:
        next_open = get_next_market_open(now, holidays)
        return JSONResponse({"open": False, "state": "Weekend",
                             "nextCheckSeconds": int((next_open - now).total_seconds())})

    # Holiday
    if today_holiday:
        next_open = get_next_market_open(now, holidays)
        return JSONResponse({"open": False, "state": f"Holiday: {today_holiday.get('name')}",
                             "nextCheckSeconds": int((next_open - now).total_seconds())})

    # Before Market
    if now < open_time:
        return JSONResponse({"open": False, "state": "Opens at 09:15 AM",
                             "nextCheckSeconds": int((open_time - now).total_seconds())})

    # During Market
    if open_time <= now <= close_time:
        #remaining = int((close_time - now).total_seconds()) -- after check
        return JSONResponse({"open": True, "state": "Market Open", "nextCheckSeconds": 60}) #nextchecksecond: remaining after test

    # After Market
    next_open = get_next_market_open(now, holidays)
    return JSONResponse({"open": False, "state": "Closed for the day",
                         "nextCheckSeconds": int((next_open - now).total_seconds())})


# ------------------------------------------
# REAL-TIME LTP SNAPSHOT
# ------------------------------------------
@router.get("/holdings-ltp")
def get_holdings_ltp():
    result = []
    r = get_redis()

    token_set = worker.holding_tokens_set
    token_to_symbol = worker.token_to_symbol_map
    cache = worker.ltp_cache

    if not token_set:
        print("❌ No tokens in holding_tokens_set")
        return []

    for token in token_set:
        symbol = token_to_symbol.get(token)
        if not symbol:
            continue

        ltp = None

        # Redis first
        if r:
            try:
                raw = r.get(f"ltp:{symbol}")
                if raw:
                    ltp = float(raw.decode("utf-8")) if isinstance(raw, bytes) else float(raw)
            except:
                pass

        # Memory-cache fallback
        if ltp is None:
            val = cache.get(symbol)
            if val is not None:
                ltp = float(val)

        result.append({"symbol": symbol, "Ltp": ltp})

    return JSONResponse(result, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })
