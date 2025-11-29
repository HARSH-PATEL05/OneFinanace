from __future__ import annotations
from typing import Dict, Any

from Model.Analysis.full_analysis import run_full_analysis
from Model.Analysis.Fundamental import get_stock_fundamentals


# ------------------------------------------------------
# 1) ML + TECHNICAL + CHART ANALYSIS
# ------------------------------------------------------
def analyze_stock(symbol: str) -> Dict[str, Any]:
    """
    Full AI/ML + technical analysis using trained models.
    Used for Stock Analyzer section.
    """
    result = run_full_analysis(symbol)

    if not isinstance(result, dict):
        return {"error": "Internal error in model output"}

    if "error" in result:
        return result

    return result


# ------------------------------------------------------
# 2) FUNDAMENTAL ANALYSIS (NSEPYTHON + YFINANCE)
# ------------------------------------------------------
def analyze_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Fetches maximum available fundamentals using:
      - NSE (live)
      - Yahoo Finance (global fundamentals)
    """
    fundamentals = get_stock_fundamentals(symbol)

    if not isinstance(fundamentals, dict):
        return {"error": "Fundamental data fetch failed"}

    return fundamentals


# ------------------------------------------------------
# MANUAL TEST
# ------------------------------------------------------
if __name__ == "__main__":
    print("=== ML / Technical / Chart Analysis ===")
    full = analyze_stock("TCS.NS")
    print(full)

    print("\n=== Fundamental Analysis ===")
    funda = analyze_fundamentals("TCS.NS")
    print(funda)
