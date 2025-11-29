"""
Clean UP/DOWN movement model trainer
Uses:
- RandomForest
- GradientBoosting
- XGBoost (optional)

🔥 No threshold
🔥 Uses all real price movements
🔥 Balanced dataset (UP = DOWN)
🔥 Works perfectly with curated high-quality stocks
"""

from __future__ import annotations
import os
import pandas as pd
import joblib
from typing import List, Tuple
import sys
from pathlib import Path

# Path setup
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


# Use existing indicator generator
from indicators.compute_indicators import compute_all_indicators

# ML Imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Optional XGBoost
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False

# Directories
DATA_DIR = "data/data/core_market_10yr"
MODEL_DIR = "models/movement/"


# ---------------------------------------------------------
# 1. Load ALL CSVs from selected sector folder
# ---------------------------------------------------------
def load_all_csv() -> pd.DataFrame:
    print("\n📂 Scanning CSV files in:", DATA_DIR)

    frames: List[pd.DataFrame] = []
    count = 0

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(DATA_DIR, file))
            df = df.rename(str.title, axis="columns")  # Make columns consistent

            if {"Open", "High", "Low", "Close", "Volume"}.issubset(df.columns):
                frames.append(df)
                count += 1
                

    if not frames:
        raise RuntimeError("❌ No CSV files found!")

    print(f"\n✅ TOTAL CSV FILES LOADED: {count}")
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------
# 2. Prepare dataset (No threshold)
# ---------------------------------------------------------
def prepare_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    df = df.copy()

    df["future_close"] = df["Close"].shift(-1)
    df["movement"] = (df["future_close"] > df["Close"]).astype(int)

    df = df.dropna()

    up_df = df[df["movement"] == 1]
    down_df = df[df["movement"] == 0]

    print("\n📊 Before balancing:")
    print("UP   =", len(up_df))
    print("DOWN =", len(down_df))

    # Balance dataset
    min_count = min(len(up_df), len(down_df))
    up_df = up_df.sample(min_count, random_state=42)
    down_df = down_df.sample(min_count, random_state=42)

    df_balanced = pd.concat([up_df, down_df]).sample(frac=1, random_state=42)

    print("\n📊 After balancing:")
    print("UP   =", len(up_df))
    print("DOWN =", len(down_df))
    print("TOTAL =", len(df_balanced))

    FEATURES = [
        "Close", "Open", "High", "Low", "Volume",
        "rsi", "macd", "macd_signal",
        "ema20", "ema50",
        "boll_up", "boll_low",
        "return",
    ]

    return df_balanced[FEATURES], df_balanced["movement"]


# ---------------------------------------------------------
# 3. Train models
# ---------------------------------------------------------
def train_movement_global() -> None:
    df = load_all_csv()

    print("\n⚙️ Computing indicators...")
    df = compute_all_indicators(df)
    df = df.dropna()

    print("\n🧪 Preparing dataset...")
    X, y = prepare_dataset(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=True
    )

    os.makedirs(MODEL_DIR, exist_ok=True)

    # -------------------------
    # Random Forest
    # -------------------------
    print("\n🌲 Training RandomForest...")
    rf = RandomForestClassifier(n_estimators=300)
    rf.fit(X_train, y_train)
    print("RF Accuracy:", accuracy_score(y_test, rf.predict(X_test)))
    joblib.dump(rf, os.path.join(MODEL_DIR, "movement_rf.pkl"))

    # -------------------------
    # Gradient Boosting
    # -------------------------
    print("\n🚀 Training GradientBoosting...")
    gb = GradientBoostingClassifier()
    gb.fit(X_train, y_train)
    print("GB Accuracy:", accuracy_score(y_test, gb.predict(X_test)))
    joblib.dump(gb, os.path.join(MODEL_DIR, "movement_gb.pkl"))

    # -------------------------
    # XGBoost
    # -------------------------
    if XGB_AVAILABLE:
        print("\n⚡ Training XGBoost...")
        xgb = XGBClassifier(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=6,
        )
        xgb.fit(X_train, y_train)
        print("XGB Accuracy:", accuracy_score(y_test, xgb.predict(X_test)))
        joblib.dump(xgb, os.path.join(MODEL_DIR, "movement_xgb.pkl"))

    print("\n✔ ALL MODELS TRAINED & SAVED.")


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    train_movement_global()
