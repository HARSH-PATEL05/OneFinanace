from __future__ import annotations

from typing import Dict, Any
import sys
from pathlib import Path

# Path setup
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Analysis.full_analysis import run_full_analysis  # folder name is 'Analysis'


def get_movement_view(symbol: str) -> Dict[str, Any]:
    """
    Lightweight API: only UP/DOWN + confidence + trend.
    """
    full = run_full_analysis(symbol)

    if "error" in full:
        return full

    movement = full.get("movement", {})
    trend = full.get("trend", {})

    return {
        "symbol": full.get("symbol", symbol),
        "last_price": full.get("last_price"),
        "last_date": full.get("last_date"),
        "movement_prediction": movement.get("movement_prediction"),
        "movement_confidence": movement.get("movement_confidence"),
        "trend": trend.get("trend"),
        "trend_strength": trend.get("trend_strength"),
    }


if __name__ == "__main__":
    print(get_movement_view("TCS.NS"))
