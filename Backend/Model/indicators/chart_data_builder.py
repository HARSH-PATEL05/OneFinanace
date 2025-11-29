from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Any, List


# -------------------------------------------------------------
# Safe UNIX timestamp converter (Pylance-clean)
# -------------------------------------------------------------
def to_unix(index: pd.Index) -> List[int]:
    """Convert pandas index to UNIX timestamps safely."""
    dt_index = pd.to_datetime(index, errors="coerce")
    return [int(ts.timestamp()) for ts in dt_index if not pd.isna(ts)]


# -------------------------------------------------------------
# Build TradingView compatible JSON
# -------------------------------------------------------------
def build_chart_data(df: pd.DataFrame) -> Dict[str, Any]:

    df = df.copy()
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.dropna()

    time: List[int] = to_unix(df.index)

    # ---------------------------------------------------------
    # Candlesticks
    # ---------------------------------------------------------
    candles: List[Dict[str, float]] = []
    for i in range(len(df)):
        candles.append({
            "time": time[i],
            "open": float(df["Open"].iloc[i]),
            "high": float(df["High"].iloc[i]),
            "low": float(df["Low"].iloc[i]),
            "close": float(df["Close"].iloc[i]),
        })

    # ---------------------------------------------------------
    # Volume
    # ---------------------------------------------------------
    volume: List[Dict[str, float]] = [
        {"time": time[i], "value": float(df["Volume"].iloc[i])}
        for i in range(len(df))
    ]

    # ---------------------------------------------------------
    # Helper for line series
    # ---------------------------------------------------------
    def make_series(col: str) -> List[Dict[str, float]]:
        if col not in df.columns:
            return []
        return [
            {"time": time[i], "value": float(v)}
            for i, v in enumerate(df[col].astype(float).tolist())
        ]

    ema20 = make_series("ema20")
    ema50 = make_series("ema50")

    bollinger = {
        "upper": make_series("boll_up"),
        "lower": make_series("boll_low"),
        "middle": make_series("boll_mid"),
    }

    rsi = make_series("rsi")

    macd = {
        "macd": make_series("macd"),
        "signal": make_series("macd_signal"),
        "hist": make_series("macd_hist"),
    }

    # ---------------------------------------------------------
    # Markers (breakouts & breakdowns)
    # ---------------------------------------------------------
    markers: List[Dict[str, Any]] = []

    closes = df["Close"].to_numpy(dtype=float)
    highs = df["High"].to_numpy(dtype=float)
    lows = df["Low"].to_numpy(dtype=float)
    ema_20 = df.get("ema20", pd.Series([None] * len(df))).to_numpy(dtype=float)

    for i in range(1, len(df)):
        # Bullish breakout
        if highs[i] > highs[i - 1] and closes[i] > ema_20[i]:
            markers.append({
                "time": time[i],
                "position": "aboveBar",
                "color": "green",
                "shape": "arrowUp",
                "text": "Bullish Breakout",
            })

        # Bearish breakdown
        if lows[i] < lows[i - 1] and closes[i] < ema_20[i]:
            markers.append({
                "time": time[i],
                "position": "belowBar",
                "color": "red",
                "shape": "arrowDown",
                "text": "Bearish Breakdown",
            })

    # ---------------------------------------------------------
    # Trendline using regression (Pylance-safe)
    # ---------------------------------------------------------
    trendline: List[Dict[str, float]] = []
    try:
        N = 50
        last_close = df["Close"].tail(N).to_numpy(dtype=float)
        xs = np.arange(len(last_close), dtype=float)

        # Fit regression (slope + intercept)
        slope, intercept = np.polyfit(xs, last_close, 1)

        for i in range(len(last_close)):
            trendline.append({
                "time": int(df.index[-N + i].timestamp()),
                "value": float(slope * i + intercept),
            })
    except Exception:
        trendline = []

    # ---------------------------------------------------------
    # Final JSON
    # ---------------------------------------------------------
    return {
        "candles": candles,
        "volume": volume,
        "ema20": ema20,
        "ema50": ema50,
        "bollinger": bollinger,
        "rsi": rsi,
        "macd": macd,
        "markers": markers,
        "trendline": trendline,
    }
