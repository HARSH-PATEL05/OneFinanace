import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ✅ safer path handling
try:
    df = pd.read_csv("stocks_dataset.csv")
except Exception as e:
    print("CSV Load Error:", e)
    df = pd.DataFrame()


class FilterRequest(BaseModel):
    indicator: str
    condition: str
    value: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None


@router.post("/filter")
def filter_stocks(req: FilterRequest):

    print("Incoming request:", req)  # 🔥 DEBUG

    if df.empty:
        raise HTTPException(status_code=500, detail="Dataset not loaded")

    data = df.copy()

    if req.indicator not in data.columns:
        raise HTTPException(status_code=400, detail="Invalid indicator")

    try:
        if req.condition == "<":
            if req.value is None:
                raise HTTPException(status_code=400, detail="Value required")
            data = data[data[req.indicator] < req.value]

        elif req.condition == ">":
            if req.value is None:
                raise HTTPException(status_code=400, detail="Value required")
            data = data[data[req.indicator] > req.value]

        elif req.condition == "between":
            if req.min is None or req.max is None:
                raise HTTPException(status_code=400, detail="Min and Max required")
            data = data[
                (data[req.indicator] >= req.min) &
                (data[req.indicator] <= req.max)
            ]

        else:
            raise HTTPException(status_code=400, detail="Invalid condition")

    except Exception as e:
        print("Filter Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

    return data.to_dict(orient="records")