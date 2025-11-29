"""
Price Prediction Inference (Return-Based)
-----------------------------------------
Uses trained models that predict NEXT-DAY % RETURN.

Final Price = last_close * (1 + predicted_return)
"""

from __future__ import annotations
import joblib
import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Dict, Any, List

# Path Setup
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from indicators.compute_indicators import compute_all_indicators


class PricePredictor:

    def __init__(self, model_dir: str = "Model/models/price"):

        self.model_dir = Path(model_dir)

        self.rf_model = self._safe_load("price_rf.pkl")
        self.gb_model = self._safe_load("price_gb.pkl")
        self.xgb_model = self._safe_load("price_xgb.pkl")

        # Must match training
        self.FEATURES = [
            "Close", "Open", "High", "Low", "Volume",
            "rsi", "macd", "macd_signal",
            "ema20", "ema50",
            "boll_up", "boll_low",
            "return",
        ]

    def _safe_load(self, name: str):
        path = self.model_dir / name
        return joblib.load(path) if path.exists() else None

    # --------------------------------------------------------
    # Main Prediction Function
    # --------------------------------------------------------
    def predict(self, symbol: str) -> Dict[str, Any]:

        # 1️⃣ Fetch OHLCV (NO auto adjust)
        df = yf.download(
            symbol,
            period="1y",
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if df is None or df.empty:
            return {"error": f"Could not fetch data for {symbol}"}

        df = df.copy()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

        try:
            df = df[["Open", "High", "Low", "Close", "Volume"]]
        except:
            return {"error": "OHLCV columns missing from Yahoo Finance"}

        df = df.dropna()
        if df.empty:
            return {"error": "No valid OHLCV data"}

        # 2️⃣ Compute indicators
        df = compute_all_indicators(df)
        df = df.dropna()

        if df.empty:
            return {"error": "No rows after indicator computation"}

        # 3️⃣ Latest feature row
        try:
            latest = df[self.FEATURES].tail(1).astype(float)
        except Exception as e:
            return {"error": f"Feature mismatch: {e}"}

        preds: List[float] = []

        # 4️⃣ Predict % return
        if self.rf_model:
            preds.append(float(self.rf_model.predict(latest)[0]))

        if self.gb_model:
            preds.append(float(self.gb_model.predict(latest)[0]))

        if self.xgb_model:
            preds.append(float(self.xgb_model.predict(latest)[0]))

        if not preds:
            return {"error": "No models available"}

        predicted_return = float(np.mean(preds))
        std_dev = float(np.std(preds))

        # 5️⃣ Convert % return → price
        last_close = float(df["Close"].iloc[-1])
        predicted_close = round(last_close * (1 + predicted_return), 2)

        direction = "UP" if predicted_close > last_close else "DOWN"
        confidence = round(max(0, 100 - std_dev * 200), 2)

        return {
            "symbol": symbol,
            "last_close": last_close,
            "predicted_return": round(predicted_return * 100, 3),  # %
            "predicted_close": predicted_close,
            "direction": direction,
            "confidence": confidence,
            "raw_model_returns": preds,
            "models_used": len(preds)
        }


if __name__ == "__main__":
    model = PricePredictor()
    print(model.predict("BEL.NS"))
