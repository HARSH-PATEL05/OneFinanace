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

# Logger setup
logger = logging.getLogger("Fetch_all_data")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
logger.propagate = False

# Broker instances
brokers = {
    "zerodha": ZerodhaBroker(),
    "angelone": AngelOneBroker(),
    "upstox": UpstoxBroker(),
    "groww": GrowwBroker()
}


def fetch_and_save_holdings_for_broker(broker):
    try:
        response = broker.fetch_holdings()

        # Parse JSON if response is string
        if isinstance(response, str):
            response = json.loads(response)

        # Normalize holdings list
        if isinstance(response, dict):
            holdings = response.get("data") or response.get("holdings") or []
            if isinstance(holdings, dict):
                holdings = holdings.get("holdings", [])
        elif isinstance(response, list):
            holdings = response
        else:
            holdings = []

        logger.info(f"{broker.broker_name}: {len(holdings)} holdings fetched")

        new_holdings_list = []

        with SessionLocal() as db:
            for h in holdings:
                # Multiple key support across brokers
                symbol = h.get("tradingsymbol") or h.get("symbol")
                name = h.get("name") or h.get("company_name") or symbol
                qty = int(h.get("quantity") or h.get("Qty") or h.get("qty") or 0)
                average_price = float(h.get("average_price") or h.get("averageprice") or 0)
                last_price = float(h.get("last_price") or h.get("ltp") or 0)
                prev_ltp = float(h.get("close") or h.get("close_price") or last_price)

                if not symbol or not name:
                    continue

                existing_holding = db.query(Holding).filter_by(
                    broker=broker.broker_name,
                    symbol=symbol
                ).first()

                if existing_holding:
                    existing_holding.Ltp = last_price
                    existing_holding.Qty = qty
                    existing_holding.average_price = average_price
                    existing_holding.additional_data = json.dumps(h)
                else:
                    new_holdings_list.append({
                        "broker": broker.broker_name,
                        "symbol": symbol,
                        "name": name,
                        "Qty": qty,
                        "average_price": average_price,
                        "Ltp": last_price,
                        "prev_ltp": prev_ltp,
                        "additional_data": h
                    })

            if new_holdings_list:
                save_holdings_to_db(new_holdings_list, db=db)
            db.commit()

        logger.info(f"Holdings fetched and saved for {broker.broker_name}")

    except Exception as e:
        logger.error(f"Error fetching/saving holdings for {broker.broker_name}: {e}\n{traceback.format_exc()}")


def fetch_and_save_mfs_for_broker(broker):
    try:
        response = broker.fetch_mfs()

        if isinstance(response, str):
            response = json.loads(response)

        # Normalize MF list
        if isinstance(response, dict):
            mfs = response.get("data", {}).get("mfs") \
                  or response.get("data", {}).get("mutualfunds") \
                  or response.get("data", [])
        elif isinstance(response, list):
            mfs = response
        else:
            mfs = []

        logger.info(f"{broker.broker_name}: {len(mfs)} MFs fetched")

        new_mfs_list = []

        with SessionLocal() as db:
            for mf in mfs:
                symbol = mf.get("tradingsymbol") or mf.get("scheme_name")
                fund = mf.get("fund") or mf.get("fund_name")
                qty = int(mf.get("quantity") or 0)
                last_price = float(mf.get("last_price") or mf.get("nav") or 0)
                average_price = float(mf.get("average_price") or mf.get("nav") or 0)

                if not symbol or not fund:
                    continue

                existing_mf = db.query(MutualFund).filter_by(
                    broker=broker.broker_name,
                    symbol=symbol
                ).first()

                if existing_mf:
                    existing_mf.Ltp = last_price
                    existing_mf.Qty = qty
                    existing_mf.average_price = average_price
                    existing_mf.additional_data = json.dumps(mf)
                else:
                    new_mfs_list.append({
                        "broker": broker.broker_name,
                        "symbol": symbol,
                        "fund": fund,
                        "Qty": qty,
                        "average_price": average_price,
                        "Ltp": last_price,
                        "additional_data": mf
                    })

            if new_mfs_list:
                save_mfs_to_db(new_mfs_list, db=db)
            db.commit()

        logger.info(f"Mutual funds saved for {broker.broker_name}")

    except Exception as e:
        logger.error(f"Error fetching/saving MFs for {broker.broker_name}: {e}\n{traceback.format_exc()}")


def fetch_all_data():
    """Fetch and save holdings and MFs for all brokers"""
    for broker_name, broker in brokers.items():
        fetch_and_save_holdings_for_broker(broker)
        fetch_and_save_mfs_for_broker(broker)
