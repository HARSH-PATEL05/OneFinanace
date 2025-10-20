from fastapi import APIRouter
from typing import List
from fastapi.responses import JSONResponse

from app.Database.database_util import get_holdings_from_db, get_mfs_from_db,get_all_brokers
from app.schemas import HoldingResponse, MFResponse

router = APIRouter(prefix="/brokers", tags=["Portfolio"])


@router.get("/portfolio")
def all_portfolios():
    results = {}
    brokers=get_all_brokers()
    for broker_name in brokers:
        results[broker_name] = {
            "holdings": get_holdings_from_db(broker_name),
            "mfs": get_mfs_from_db(broker_name)
        }
    return results


@router.get("/{broker_name}/portfolio/holdings", response_model=List[HoldingResponse])
def holdings(broker_name: str):
    try:
        holdings = get_holdings_from_db(broker_name.lower())
        return holdings
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/{broker_name}/portfolio/mfs", response_model=List[MFResponse])
def mf(broker_name: str):
    try:
        mfs = get_mfs_from_db(broker_name.lower())
        return mfs
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
