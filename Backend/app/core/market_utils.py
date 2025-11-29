# market_utils.py

import requests
import json
import os
import time
from datetime import datetime, date, time as dt_time
import pytz

IST = pytz.timezone("Asia/Kolkata")

# MARKET TIME SETTINGS
MARKET_START = dt_time(9, 13)
MARKET_END   = dt_time(15, 32)

HOLIDAY_CACHE_FILE = "market_holidays.json"
HOLIDAY_REFRESH_INTERVAL = 12 * 60 * 60  # refresh every 12 hours

UPSTOX_URL = "https://api.upstox.com/v2/market/holidays"

_holidays_cache = []
_last_fetch_time = 0

def log(msg):
    print(f"[MarketUtils] {msg}")


def fetch_market_holidays(force=False):
    global _holidays_cache, _last_fetch_time

    now = time.time()
    if not force and _holidays_cache and (now - _last_fetch_time) < HOLIDAY_REFRESH_INTERVAL:
        return _holidays_cache

    try:
        resp = requests.get(UPSTOX_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])

        holidays = []
        for h in data:
            closed = h.get("closed_exchanges", [])
            holiday_type = h.get("holiday_type", "")
            date_str = h.get("date")
            name = h.get("description", "")

            # Equity full holiday
            if holiday_type == "TRADING_HOLIDAY" and "NSE" in closed and "BSE" in closed:
                holidays.append({
                    "date": date_str,
                    "name": name,
                    "day": datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
                })

        _holidays_cache = holidays
        _last_fetch_time = now

        with open(HOLIDAY_CACHE_FILE, "w") as f:
            json.dump(_holidays_cache, f, indent=4)

        log(f"Loaded {len(holidays)} filtered NSE+BSE holidays")
        return _holidays_cache

    except Exception as e:
        log(f"Holiday API failed {e}")

    if os.path.exists(HOLIDAY_CACHE_FILE):
        with open(HOLIDAY_CACHE_FILE, "r") as f:
            _holidays_cache = json.load(f)
            log(f"Loaded {len(_holidays_cache)} holidays from cache")
            return _holidays_cache

    return []


def is_weekday():
    return datetime.now(IST).weekday() < 5


def is_holiday():
    holidays = fetch_market_holidays()
    today = datetime.now(IST).date().isoformat()
    return any(h["date"] == today for h in holidays)


def is_market_time():
    now = datetime.now(IST).time()
    return MARKET_START <= now <= MARKET_END


def is_market_open():
    return  is_weekday() and not is_holiday() and is_market_time()


def next_open_status():
    if is_holiday():
        return {"open": False, "state": "Holiday today"}
    if not is_weekday():
        return {"open": False, "state": "Weekend"}
    if datetime.now(IST).time() < MARKET_START:
        return {"open": False, "state": f"Opens at {MARKET_START.strftime('%H:%M')}"}
    if datetime.now(IST).time() > MARKET_END:
        return {"open": False, "state": "Closed for the day"}
    return {"open": True, "state": "Market Running"}


