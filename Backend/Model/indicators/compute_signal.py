"""
compute_signals.py
-------------------
Converts technical indicators into human-readable trading signals.
Pylance-safe, strictly typed, used for ML features and final analysis.
"""

from __future__ import annotations
import pandas as pd
import numpy as np


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals (buy/sell/neutral, crossovers, trend, volatility).

    Args:
        df: DataFrame WITH all indicators already added
             (from compute_all_indicators.py)

    Returns:
        DataFrame with new signal columns added.
    """

    df = df.copy()

    # ============================================================
    # 1. RSI signal
    # ============================================================
    def rsi_signal(value: float) -> str:
        if value < 30:
            return "Oversold (Bullish)"
        if value > 70:
            return "Overbought (Bearish)"
        return "Neutral"

    df["rsi_signal"] = df["rsi"].apply(rsi_signal)

    # ============================================================
    # 2. MACD Crossovers
    # ============================================================
    macd = df["macd"]
    signal = df["macd_signal"]

    df["macd_crossover"] = np.where(
        macd > signal, "Bullish", "Bearish"
    )

    df["macd_strength"] = df["macd_hist"]

    # ============================================================
    # 3. Stochastic Oscillator Signals
    # ============================================================
    def stoch_signal(k: float, d: float) -> str:
        if k < 20 and d < 20:
            return "Oversold (Bullish)"
        if k > 80 and d > 80:
            return "Overbought (Bearish)"
        return "Neutral"

    df["stoch_signal"] = [
        stoch_signal(k, d) for k, d in zip(df["stoch_k"], df["stoch_d"])
    ]

    # ============================================================
    # 4. Trend Signals using EMA + ADX
    # ============================================================
    df["trend_signal"] = "Sideways"

    # Strong uptrend
    df.loc[
        (df["ema20"] > df["ema50"]) &
        (df["ema50"] > df["ema100"]) &
        (df["adx"] > 25),
        "trend_signal"
    ] = "Strong Uptrend"

    # Weak uptrend
    df.loc[
        (df["ema20"] > df["ema50"]) &
        (df["ema50"] > df["ema100"]) &
        (df["adx"] <= 25),
        "trend_signal"
    ] = "Uptrend"

    # Strong downtrend
    df.loc[
        (df["ema20"] < df["ema50"]) &
        (df["ema50"] < df["ema100"]) &
        (df["adx"] > 25),
        "trend_signal"
    ] = "Strong Downtrend"

    # Weak downtrend
    df.loc[
        (df["ema20"] < df["ema50"]) &
        (df["ema50"] < df["ema100"]) &
        (df["adx"] <= 25),
        "trend_signal"
    ] = "Downtrend"

    # ============================================================
    # 5. Volatility Signal using ATR percentile
    # ============================================================
    atr_values = df["atr"]
    atr20 = atr_values.rolling(20).mean()

    df["volatility_signal"] = np.where(
        atr_values > atr20,
        "High Volatility",
        "Normal Volatility"
    )

    # ============================================================
    # 6. Bollinger Band Signals
    # ============================================================
    close = df["Close"]
    up = df["boll_up"]
    low = df["boll_low"]

    df["bollinger_signal"] = np.where(
        close >= up, "Upper Band Rejection (Bearish)",
        np.where(
            close <= low, "Lower Band Rebound (Bullish)",
            "Within Band"
        )
    )

    # ============================================================
    # 7. Breakout Signals
    # ============================================================
    df["breakout_signal"] = "None"

    df.loc[close > up, "breakout_signal"] = "Bullish Breakout"
    df.loc[close < low, "breakout_signal"] = "Bearish Breakdown"

    # ============================================================
    # Final cleanup
    # ============================================================
    df = df.dropna()

    return df
