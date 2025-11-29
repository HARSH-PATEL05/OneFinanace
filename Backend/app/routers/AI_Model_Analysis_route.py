from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Ensure Backend root is in PYTHONPATH
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Your original ML analysis import (UNCHANGED)
from Model.inference import run_full_analysis

# New fundamentals import (ADDED)
from Model.inference import get_stock_fundamentals


router = APIRouter(prefix="/ai-analysis", tags=["AI Stock Analysis"])


class StockRequest(BaseModel):
    symbol: str


# ------------------------------------------------------------
# 1️⃣  ML + Technical + Chart Analysis (YOUR ORIGINAL LOGIC)
# ------------------------------------------------------------
@router.post("/analyze")
async def analyze_stock(req: StockRequest):
    try:
        result = run_full_analysis(req.symbol.upper())
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"status": "success", "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------
# 2️⃣  Fundamentals API (NEW LOGIC ADDED — DOES NOT MODIFY ORIGINAL)
# ------------------------------------------------------------
@router.post("/fundamentals")
async def stock_fundamentals(req: StockRequest):
    try:
        result = get_stock_fundamentals(req.symbol.upper())

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"status": "success", "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
