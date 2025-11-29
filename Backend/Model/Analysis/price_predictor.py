from __future__ import annotations

from typing import Dict, Any
import sys
from pathlib import Path

# Path setup
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from Analysis.full_analysis import run_full_analysis  # folder name is 'Analysis'


def get_price_view(symbol: str) -> Dict[str, Any]:
    """
    Lightweight API: only price prediction + direction/ confidence.
    """
    full = run_full_analysis(symbol)

    if "error" in full:
        return full

    price = full.get("price_prediction", {})

    return {
        "symbol": full.get("symbol", symbol),
        "last_price": full.get("last_price"),
        "last_date": full.get("last_date"),
        "predicted_close": price.get("predicted_close"),
        "direction": price.get("direction"),
        "confidence": price.get("confidence"),
    }


if __name__ == "__main__":
    print(get_price_view("TCS.NS"))
