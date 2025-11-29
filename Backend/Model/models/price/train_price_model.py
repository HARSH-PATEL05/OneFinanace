"""
GLOBAL RETURN-BASED PRICE MODEL TRAINER
---------------------------------------
Predicts NEXT-DAY % CHANGE, not absolute price.
Much more stable and works across all stocks.

Trains:
- RandomForestRegressor
- GradientBoostingRegressor
- XGBoostRegressor (optional)
"""

from __future__ import annotations
import os
import pandas as pd
import joblib
import sys
from pathlib import Path
from typing import List, Tuple

# Path setup
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from indicators.compute_indicators import compute_all_indicators

# ML
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except:
    XGB_AVAILABLE = False

# Directories
DATA_DIR = "data/data/core_market_10yr"
MODEL_DIR = "models/price/"


# ---------------------------------------------------------
# 1. Load CSVs + Clean
# ---------------------------------------------------------
def load_all_csv() -> pd.DataFrame:
    print("\n📂 Scanning CSV files in:", DATA_DIR)

    frames = []
    count = 0

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):

            df = pd.read_csv(os.path.join(DATA_DIR, file))
            df = df.rename(str.title, axis="columns")

            if not {"Open", "High", "Low", "Close", "Volume"}.issubset(df.columns):
                continue

            # Convert OHLCV to numeric (remove commas)
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
            frames.append(df)
            count += 1

    if not frames:
        raise RuntimeError("❌ No usable CSV files found!")

    print(f"✅ TOTAL CSV FILES LOADED: {count}")
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------
# 2. Prepare dataset (Return-based)
# ---------------------------------------------------------
FEATURES = [
    "Close", "Open", "High", "Low", "Volume",
    "rsi", "macd", "macd_signal",
    "ema20", "ema50",
    "boll_up", "boll_low",
    "return"
]

def prepare_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    df = df.copy()

    # Our target: NEXT DAY % CHANGE
    df["pct_return"] = (df["Close"].shift(-1) - df["Close"]) / df["Close"]

    df = df.dropna()

    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        raise RuntimeError(f"❌ Missing indicators: {missing}")

    X = df[FEATURES]
    y = df["pct_return"]

    return X, y


# ---------------------------------------------------------
# 3. Train Models
# ---------------------------------------------------------
def train_price_global():

    df = load_all_csv()

    print("\n⚙️ Computing indicators...")
    df = compute_all_indicators(df)
    df = df.dropna()

    print("\n🧪 Preparing return-based dataset...")
    X, y = prepare_dataset(df)

    print(f"📊 Usable rows: {len(X)}")
    if len(X) < 300:
        raise RuntimeError("❌ Dataset too small!")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=True
    )

    os.makedirs(MODEL_DIR, exist_ok=True)

    # RandomForest
    print("\n🌲 Training RandomForest...")
    rf = RandomForestRegressor(n_estimators=300)
    rf.fit(X_train, y_train)
    print("RF RMSE:", (mean_squared_error(y_test, rf.predict(X_test)) ** 0.5))
    joblib.dump(rf, os.path.join(MODEL_DIR, "price_rf.pkl"))

    # GradientBoosting
    print("\n🚀 Training GradientBoosting...")
    gb = GradientBoostingRegressor()
    gb.fit(X_train, y_train)
    print("GB RMSE:", (mean_squared_error(y_test, gb.predict(X_test)) ** 0.5))
    joblib.dump(gb, os.path.join(MODEL_DIR, "price_gb.pkl"))

    # XGBoost
    if XGB_AVAILABLE:
        print("\n⚡ Training XGBoost...")
        xgb = XGBRegressor(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8
        )
        xgb.fit(X_train, y_train)
        print("XGB RMSE:", (mean_squared_error(y_test, xgb.predict(X_test)) ** 0.5))
        joblib.dump(xgb, os.path.join(MODEL_DIR, "price_xgb.pkl"))

    print("\n🎉 ALL RETURN-BASED MODELS TRAINED & SAVED SUCCESSFULLY.")


if __name__ == "__main__":
    train_price_global()
