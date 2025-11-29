"""
compute_indicators.py
----------------------
Central file for generating ALL technical indicators.
Pylance-safe, warning-free, strictly typed.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from ta import momentum, trend, volatility, volume


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute advanced technical indicators for OHLCV stock data.

    Args:
        df: DataFrame containing columns:
            ['Open', 'High', 'Low', 'Close', 'Volume']

    Returns:
        DataFrame with indicators added as new columns.
    """

    df = df.copy()

    # ---------------------------
    # Safety cleaning
    # ---------------------------
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
    df["High"] = pd.to_numeric(df["High"], errors="coerce")
    df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

    df = df.dropna()

    # ---------------------------
    # 1. RSI
    # ---------------------------
    rsi = momentum.RSIIndicator(df["Close"])
    df["rsi"] = rsi.rsi()

    # ---------------------------
    # 2. MACD
    # ---------------------------
    macd_calc = trend.MACD(df["Close"])
    df["macd"] = macd_calc.macd()
    df["macd_signal"] = macd_calc.macd_signal()
    df["macd_hist"] = macd_calc.macd_diff()

    # ---------------------------
    # 3. Stochastic Oscillator
    # ---------------------------
    stoch = momentum.StochasticOscillator(df["High"], df["Low"], df["Close"])
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    # ---------------------------
    # 4. ATR (Volatility)
    # ---------------------------
    atr = volatility.AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )
    df["atr"] = atr.average_true_range()

    # ---------------------------
    # 5. ADX (Trend strength)
    # ---------------------------
    adx = trend.ADXIndicator(df["High"], df["Low"], df["Close"])
    df["adx"] = adx.adx()

    # ---------------------------
    # 6. Bollinger Bands
    # ---------------------------
    bb = volatility.BollingerBands(df["Close"])
    df["boll_up"] = bb.bollinger_hband()
    df["boll_low"] = bb.bollinger_lband()
    df["boll_mid"] = bb.bollinger_mavg()

    # ---------------------------
    # 7. VWAP
    # ---------------------------
    vwap = volume.VolumeWeightedAveragePrice(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        volume=df["Volume"]
    )
    df["vwap"] = vwap.volume_weighted_average_price()

    # ---------------------------
    # 8. Moving Averages (EMA / SMA)
    # ---------------------------
    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["ema100"] = df["Close"].ewm(span=100).mean()

    df["sma20"] = df["Close"].rolling(window=20).mean()
    df["sma50"] = df["Close"].rolling(window=50).mean()
    df["sma200"] = df["Close"].rolling(window=200).mean()

    # ---------------------------
    # 9. Returns & Volatility
    # ---------------------------
    df["return"] = df["Close"].pct_change()
    df["volatility"] = df["return"].rolling(20).std()

    df = df.dropna()

    return df
