"""
Pylance-clean support & resistance generator.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Any


# -----------------------------------------------------------
# 1. PIVOT POINTS
# -----------------------------------------------------------
def compute_pivot_levels(df: pd.DataFrame) -> Dict[str, float]:
    last = df.iloc[-1]

    high = float(last["High"])
    low = float(last["Low"])
    close = float(last["Close"])

    pivot = (high + low + close) / 3

    return {
        "pivot": round(pivot, 2),
        "s1": round(2 * pivot - high, 2),
        "s2": round(pivot - (high - low), 2),
        "s3": round(low - 2 * (high - pivot), 2),
        "r1": round(2 * pivot - low, 2),
        "r2": round(pivot + (high - low), 2),
        "r3": round(high + 2 * (pivot - low), 2),
    }


# -----------------------------------------------------------
# 2. SWING HIGH/LOW
# -----------------------------------------------------------
def get_swing_levels(df: pd.DataFrame, window: int = 3) -> Dict[str, List[float]]:
    highs = df["High"].to_numpy(dtype=float)
    lows = df["Low"].to_numpy(dtype=float)

    supports: List[float] = []
    resistances: List[float] = []

    length = len(df)

    for i in range(window, length - window):
        if highs[i] == max(highs[i - window : i + window + 1]):
            resistances.append(float(highs[i]))

        if lows[i] == min(lows[i - window : i + window + 1]):
            supports.append(float(lows[i]))

    supports = sorted(list({float(x) for x in supports}))[-5:]
    resistances = sorted(list({float(x) for x in resistances}))[:5]

    return {
        "supports": supports,
        "resistances": resistances,
    }


# -----------------------------------------------------------
# 3. MULTI-TIMEFRAME LEVELS
# -----------------------------------------------------------
def compute_multi_tf_levels(
    df: pd.DataFrame,
    daily_levels: Dict[str, List[float]]
) -> Dict[str, List[float]]:
    df = df.copy()

    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")

    # Weekly compression
    df["week"] = df.index.to_period("W").astype(str)

    weekly = df.groupby("week").agg({"High": "max", "Low": "min"})

    weekly_supports = [float(x) for x in weekly["Low"].tail(10).to_list()]
    weekly_resistances = [float(x) for x in weekly["High"].tail(10).to_list()]

    # Volume cluster price zones
    close_prices = df["Close"].to_numpy(dtype=float)

    cluster_levels: List[float] = []
    if len(close_prices) > 50:
        min_p = float(np.min(close_prices))
        max_p = float(np.max(close_prices))
        bins = np.linspace(min_p, max_p, 20)

        hist, edges = np.histogram(close_prices, bins=bins)
        top_idx = np.argsort(hist)[-5:]

        cluster_levels = [float(edges[i]) for i in top_idx]

    # Merge levels safely
    merged_supports: List[float] = (
        list(daily_levels["supports"]) +
        weekly_supports +
        cluster_levels
    )

    merged_resistances: List[float] = (
        list(daily_levels["resistances"]) +
        weekly_resistances +
        cluster_levels
    )

    # Deduplicate & sort
    supports = sorted({float(x) for x in merged_supports})[-8:]
    resistances = sorted({float(x) for x in merged_resistances})[:8]

    return {
        "supports": supports,
        "resistances": resistances,
    }


# -----------------------------------------------------------
# MASTER WRAPPER
# -----------------------------------------------------------
def compute_all_levels(df: pd.DataFrame) -> Dict[str, Any]:
    pivot_levels = compute_pivot_levels(df)
    swing_levels = get_swing_levels(df, window=3)
    multi_tf = compute_multi_tf_levels(df, swing_levels)

    return {
        "pivot_levels": pivot_levels,
        "swing_levels": swing_levels,
        "multi_tf_levels": multi_tf,
    }
