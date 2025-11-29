from __future__ import annotations

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Any, List
import sys
from pathlib import Path

# Path setup
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# --- MODEL IMPORTS ---
from models.movement.movement_inference import MovementModelInference
from models.price.price_inference import PricePredictor

# --- INDICATORS ---
from indicators.compute_indicators import compute_all_indicators
from indicators.support_resistance import compute_all_levels
from indicators.chart_data_builder import build_chart_data
from indicators.trend_detection import TrendDetector


# MUST MATCH MOVEMENT TRAINING
FEATURES = [
    "Close", "Open", "High", "Low", "Volume",
    "rsi", "macd", "macd_signal",
    "ema20", "ema50",
    "boll_up", "boll_low",
    "return",
]


# ------------------------------
# TECHNICAL SNAPSHOT (for LLM)
# ------------------------------
def _technical_snapshot(df: pd.DataFrame) -> Dict[str, Any]:

    last = df.iloc[-1]

    rsi_val = float(last["rsi"])
    macd_val = float(last["macd"])
    sig_val = float(last["macd_signal"])
    close = float(last["Close"])

    # RSI Interpretation
    if rsi_val >= 70:
        rsi_signal = "Overbought – possible pullback"
    elif rsi_val <= 30:
        rsi_signal = "Oversold – possible bounce"
    else:
        rsi_signal = "Neutral"

    # MACD Interpretation
    if macd_val > sig_val:
        macd_signal = "Bullish (MACD > Signal)"
    else:
        macd_signal = "Bearish (MACD < Signal)"

    # Bollinger Interpretation
    if close >= last["boll_up"]:
        band_sig = "At/above upper Bollinger (stretched up)"
    elif close <= last["boll_low"]:
        band_sig = "At/below lower Bollinger (stretched down)"
    else:
        band_sig = "Inside normal volatility zone"

    return {
        "close": close,
        "rsi": round(rsi_val, 2),
        "rsi_signal": rsi_signal,
        "macd": round(macd_val, 3),
        "macd_signal": macd_signal,
        "ema20": round(float(last["ema20"]), 2),
        "ema50": round(float(last["ema50"]), 2),
        "boll_up": round(float(last["boll_up"]), 2),
        "boll_low": round(float(last["boll_low"]), 2),
        "band_signal": band_sig,
    }


# ------------------------------
# MAIN PIPELINE
# ------------------------------
def run_full_analysis(symbol: str) -> Dict[str, Any]:

    # ------------------------------
    # 1️⃣ Fetch Market Data
    # ------------------------------
    df = yf.download(
        symbol,
        period="1y",
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    if df is None or df.empty:
        return {"error": f"No price data for {symbol}"}

    df = df.copy()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    try:
        df = df[["Open", "High", "Low", "Close", "Volume"]]
    except:
        return {"error": "Missing OHLCV columns"}

    df = df.dropna()
    if df.empty:
        return {"error": "Not enough OHLCV rows"}

    # ------------------------------
    # 2️⃣ Compute Indicators
    # ------------------------------
    df = compute_all_indicators(df)
    df = df.dropna()
    if df.empty:
        return {"error": "Not enough indicator rows"}

    last_close = float(df["Close"].iloc[-1])
    last_date = str(df.index[-1].date())

    # ------------------------------
    # 3️⃣ Trend / Levels / Charts
    # ------------------------------
    levels = compute_all_levels(df)
    trend_info = TrendDetector.compute_trend(df)
    chart_data = build_chart_data(df)

    # ------------------------------
    # 4️⃣ Movement Prediction
    # ------------------------------
    movement_features = df[FEATURES].tail(1)
    mov_model = MovementModelInference("Model/models/movement")
    movement_result = mov_model.predict(movement_features)

    # ------------------------------
    # 5️⃣ Price Prediction
    # ------------------------------
    price_model = PricePredictor("Model/models/price")
    price_result = price_model.predict(symbol)

    # ------------------------------
    # 6️⃣ Technical Snapshot
    # ------------------------------
    tech = _technical_snapshot(df)

    # ------------------------------
    # 7️⃣ Summary
    # ------------------------------
    mv_pred = movement_result.get("movement_prediction", "N/A")
    mv_conf = movement_result.get("movement_confidence", 0)

    pred_close = price_result.get("predicted_close", last_close)
    direction = price_result.get("direction", "?")
    price_conf = price_result.get("confidence", 0)

    summary = (
        f"{symbol} analysis for {last_date}:\n"
        f"- Last close: {round(last_close, 2)}\n"
        f"- Movement model: **{mv_pred}** ({mv_conf:.1f}% confidence)\n"
        f"- Price model: predicts **{round(pred_close, 2)}** ({direction}), "
        f"confidence {price_conf:.1f}%\n"
        f"- Trend: {trend_info.get('trend')} "
        f"(Short: {trend_info.get('short_term')}, "
        f"Medium: {trend_info.get('medium_term')}, "
        f"Long: {trend_info.get('long_term')})\n"
        f"- RSI: {tech['rsi']} ({tech['rsi_signal']})\n"
        f"- MACD: {tech['macd_signal']}\n"
        f"- Bollinger: {tech['band_signal']}\n"
        "\nThis is technical/ML-only analysis. Not financial advice."
    )

    # ------------------------------
    # 8️⃣ Final JSON
    # ------------------------------
    return {
        "symbol": symbol,
        "last_price": last_close,
        "last_date": last_date,
        "movement": movement_result,
        "price_prediction": price_result,
        "technical": tech,
        "trend": trend_info,
        "levels": levels,
        "charts": chart_data,      # <-- HIGH-VALUE front-end chart JSON
        "summary": summary,        # <-- Send this to LLM for human-style answer
    }


if __name__ == "__main__":
    output = run_full_analysis("TCS.NS")
    print(output["summary"])
