from fastapi import APIRouter
from typing import List
from fastapi.responses import JSONResponse
import copy

# Redis safe utils
from redis_client import (
    redis_safe_json_get,
    redis_safe_json_set,
    redis_safe_get,
)

from app.Database.database_util import (
    get_holdings_from_db,
    get_mfs_from_db,
    get_all_brokers,
)
from app.schemas import HoldingResponse, MFResponse

router = APIRouter(prefix="/brokers", tags=["Portfolio"])


def safe_float(v):
    try:
        return float(str(v))
    except:
        return 0.0


def normalize_result(rows: List[dict]):
    normalized = []
    for h in rows:
        if not isinstance(h.get("additional_data"), dict):
            h["additional_data"] = {}
        normalized.append(h)
    return normalized


def apply_redis_ltp(holdings: List[dict]):
    """
    Inject latest Redis LTP values WITHOUT modifying cached objects.
    """
    output = []
    for h in holdings:
        h2 = h.copy()                # ← important to avoid mutation
        sym = (h2.get("symbol") or "").strip().upper()

        cached = redis_safe_get(f"ltp:{sym}")
        if cached is not None:
            try:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode()
                h2["Ltp"] = safe_float(cached)
            except:
                pass

        output.append(h2)
    return output


# ---------------------------------------------------------
# HYBRID CACHE LOGIC
# ---------------------------------------------------------
# Backend:
#    Redis → 10 min TTL
# Frontend:
#    Cached forever until refresh
# ---------------------------------------------------------


@router.get("/portfolio")
async def all_portfolios():
    key = "portfolio:all"

    # -----------------------------------------
    # 1) Try Redis first
    # -----------------------------------------
    cached = redis_safe_json_get(key)
    if cached:
        fresh = {}
        for broker, info in cached.items():
            fresh[broker] = {
                "holdings": apply_redis_ltp(info["holdings"]),
                "mfs": info["mfs"]
            }
        return fresh

    # -----------------------------------------
    # 2) Redis empty → load from DB
    # -----------------------------------------
    results = {}
    brokers = get_all_brokers()

    for broker in brokers:
        holdings = get_holdings_from_db(broker)
        holdings = normalize_result(holdings)

        results[broker] = {
            "holdings": holdings,
            "mfs": get_mfs_from_db(broker),
        }

    # Save raw DB results in Redis
    redis_safe_json_set(key, results, ex=600)

    # Return with LTP
    final = {}
    for broker, info in results.items():
        final[broker] = {
            "holdings": apply_redis_ltp(info["holdings"]),
            "mfs": info["mfs"],
        }

    return final


# ------------------------------ HOLDINGS ------------------------------
@router.get("/{broker_name}/portfolio/holdings",
            response_model=List[HoldingResponse])
async def holdings(broker_name: str):
    key = f"portfolio:{broker_name}:holdings"

    cached = redis_safe_json_get(key)
    if cached:
        return apply_redis_ltp(cached)

    # DB fallback
    data = get_holdings_from_db(broker_name.lower())
    data = normalize_result(data)

    redis_safe_json_set(key, data, ex=600)
    return apply_redis_ltp(data)


# ------------------------------ MUTUAL FUNDS ------------------------------
@router.get("/{broker_name}/portfolio/mfs",
            response_model=List[MFResponse])
async def mf(broker_name: str):
    key = f"portfolio:{broker_name}:mfs"

    cached = redis_safe_json_get(key)
    if cached:
        return cached

    data = get_mfs_from_db(broker_name.lower())
    redis_safe_json_set(key, data, ex=600)
    return data
