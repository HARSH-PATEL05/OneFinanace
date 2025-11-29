from typing import Dict, Any, List
from app.api.brokers.angel_broker import AngelOneBroker
from app.api.brokers.upstox_broker import UpstoxBroker
from app.api.brokers.groww_broker import GrowwBroker
from app.api.brokers.zerodha_broker import ZerodhaBroker
from app.db import SessionLocal
from app.models import Holding, MutualFund
from app.Database.database_util import save_holdings_to_db, save_mfs_to_db
import logging
import json
import traceback

# -------------------------
# Logger setup
# -------------------------
logger = logging.getLogger("Fetch_all_data")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
logger.propagate = False

# -------------------------
# Broker instances
# -------------------------
brokers: Dict[str, Any] = {
    "zerodha": ZerodhaBroker(),
    "angelone": AngelOneBroker(),
    "upstox": UpstoxBroker(),
    "groww": GrowwBroker()
}

# -------------------------
# In-memory LTP cache
# -------------------------
ltp_cache: Dict[str, float] = {}  # {symbol: latest_ltp}

# -------------------------
# Safe dict converter
# -------------------------
def ensure_dict(data: Any) -> Dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return {"raw": data}
    if isinstance(data, bytes):
        try:
            return json.loads(data.decode("utf-8"))
        except Exception:
            return {"raw": data.decode(errors="ignore")}
    return {}

# -------------------------
# Holdings fetch/save
# -------------------------
def fetch_and_save_holdings_for_broker(broker: Any) -> None:
    try:
        response = broker.fetch_holdings()
        response = ensure_dict(response)

        holdings: List[Dict[str, Any]] = response.get("data") or response.get("holdings") or []
        if isinstance(holdings, dict):
            holdings = holdings.get("holdings", [])

        logger.info(f"{broker.broker_name}: {len(holdings)} holdings fetched")
        new_holdings_list: List[Dict[str, Any]] = []

        with SessionLocal() as db:
            for h in holdings:
                h = ensure_dict(h)
                symbol = h.get("tradingsymbol") or h.get("symbol") or ""
                name = h.get("name") or h.get("company_name") or symbol
                qty = float(h.get("quantity") or h.get("Qty") or h.get("qty") or 0)
                avg_price = float(h.get("average_price") or h.get("averageprice") or 0)
                last_price = float(h.get("last_price") or h.get("ltp") or 0)

                # prev_ltp always from DB
                existing_holding = db.query(Holding).filter_by(
                    broker=broker.broker_name,
                    symbol=symbol
                ).first()
                prev_ltp = existing_holding.prev_ltp if existing_holding else last_price

                if not symbol or not name:
                    continue

                # update LTP cache
                ltp_cache[symbol] = last_price

                if existing_holding:
                    existing_holding.Ltp = last_price
                    existing_holding.Qty = qty
                    existing_holding.average_price = avg_price
                    existing_holding.additional_data = ensure_dict(h)
                else:
                    new_holdings_list.append({
                        "broker": broker.broker_name,
                        "symbol": symbol,
                        "name": name,
                        "Qty": qty,
                        "average_price": avg_price,
                        "Ltp": last_price,
                        "prev_ltp": prev_ltp,
                        "additional_data": ensure_dict(h)
                    })

            if new_holdings_list:
                save_holdings_to_db(new_holdings_list, db=db)
            db.commit()

        logger.info(f"Holdings fetched and saved for {broker.broker_name}")

    except Exception as e:
        logger.error(f"Error fetching/saving holdings for {broker.broker_name}: {e}\n{traceback.format_exc()}")

# -------------------------
# Mutual funds fetch/save
# -------------------------
def fetch_and_save_mfs_for_broker(broker: Any) -> None:
    try:
        response = broker.fetch_mfs()
        response = ensure_dict(response)

        # Unified extraction for all brokers
        mfs: List[Dict[str, Any]] = (
            response.get("mutual_funds") or
            response.get("mfs") or
            response.get("mutualfunds") or
            response.get("data") or []
        )

        logger.info(f"{broker.broker_name}: {len(mfs)} MFs fetched")
        new_mfs_list: List[Dict[str, Any]] = []

        with SessionLocal() as db:
            for mf in mfs:
                mf = ensure_dict(mf)
                symbol = mf.get("tradingsymbol") or mf.get("scheme_name") or ""
                fund = mf.get("fund") or mf.get("fund_name") or ""
                qty = float(mf.get("quantity") or 0)
                last_price = float(mf.get("last_price") or mf.get("nav") or 0)
                avg_price = float(mf.get("average_price") or mf.get("nav") or 0)

                if not symbol or not fund:
                    continue

                existing_mf = db.query(MutualFund).filter_by(
                    broker=broker.broker_name,
                    symbol=symbol
                ).first()

                if existing_mf:
                    existing_mf.Ltp = last_price
                    existing_mf.prev_close = last_price
                    existing_mf.Qty = qty
                    existing_mf.average_price = avg_price
                    existing_mf.additional_data = ensure_dict(mf)
                else:
                    new_mfs_list.append({
                        "broker": broker.broker_name,
                        "symbol": symbol,
                        "fund": fund,
                        "Qty": qty,
                        "average_price": avg_price,
                        "Ltp": last_price,
                        "prev_close":last_price,
                        "additional_data": ensure_dict(mf)
                    })

            if new_mfs_list:
                save_mfs_to_db(new_mfs_list, db=db)
            db.commit()

        logger.info(f"Mutual funds saved for {broker.broker_name}")

    except Exception as e:
        logger.error(f"Error fetching/saving MFs for {broker.broker_name}: {e}\n{traceback.format_exc()}")

# -------------------------
# Fetch all data for all brokers
# -------------------------
def fetch_all_data() -> None:
    for broker_name, broker in brokers.items():
        fetch_and_save_holdings_for_broker(broker)
        fetch_and_save_mfs_for_broker(broker)

# -------------------------
# Route to get latest LTP (can be exposed via FastAPI)
# -------------------------
def get_latest_ltp() -> Dict[str, float]:
    return dict(ltp_cache)
