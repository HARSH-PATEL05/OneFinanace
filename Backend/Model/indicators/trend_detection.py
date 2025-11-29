import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.linear_model import LinearRegression


class TrendDetector:
    """
    Detects stock trend direction and strength based on
    EMAs, slope, and regression analysis.
    """

    @staticmethod
    def _safe_ema(value: float) -> float:
        return float(value) if not pd.isna(value) else 0.0

    @staticmethod
    def compute_trend(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Determine short, medium and long-term trends.

        Returns:
            A dictionary containing overall trend direction and trend strength.
        """

        if df.empty:
            return {"trend": "UNKNOWN", "strength": 0.0}

        df = df.copy()

        # Ensure indicators exist
        if "ema20" not in df.columns or "ema50" not in df.columns:
            return {"trend": "UNKNOWN", "strength": 0.0}

        ema20 = TrendDetector._safe_ema(df["ema20"].iloc[-1])
        ema50 = TrendDetector._safe_ema(df["ema50"].iloc[-1])

        # --- SHORT TERM TREND USING EMA20 vs EMA50 ---
        if ema20 > ema50:
            short = "UP"
        elif ema20 < ema50:
            short = "DOWN"
        else:
            short = "SIDEWAYS"

        # --- MEDIUM TERM: PRICE SLOPE (last 30 days) ---
        slope = 0.0
        try:
            last_n = df["Close"].tail(30).values.astype(float)
            x_vals = np.arange(len(last_n)).reshape(-1, 1)

            model = LinearRegression()
            model.fit(x_vals, last_n)
            slope = float(model.coef_[0])
        except Exception:
            slope = 0.0

        if slope > 0.05:
            medium = "UP"
        elif slope < -0.05:
            medium = "DOWN"
        else:
            medium = "SIDEWAYS"

        # --- LONG TERM TREND USING 90-DAY REGRESSION ---
        long = "SIDEWAYS"
        try:
            last_90 = df["Close"].tail(90).values.astype(float)
            x_vals = np.arange(len(last_90)).reshape(-1, 1)

            model = LinearRegression()
            model.fit(x_vals, last_90)
            long_slope = float(model.coef_[0])

            if long_slope > 0.03:
                long = "UP"
            elif long_slope < -0.03:
                long = "DOWN"
        except Exception:
            long = "SIDEWAYS"

        # --- FINAL TREND DECISION ---
        combined = [short, medium, long]

        if combined.count("UP") >= 2:
            final = "Strong Uptrend"
        elif combined.count("DOWN") >= 2:
            final = "Strong Downtrend"
        else:
            final = "Sideways / Consolidation"

        # --- TREND STRENGTH SCORE ---
        score = (
            (1 if short == "UP" else -1 if short == "DOWN" else 0) +
            (1 if medium == "UP" else -1 if medium == "DOWN" else 0) +
            (1 if long == "UP" else -1 if long == "DOWN" else 0)
        ) * 33.33  # Normalize to 100 scale

        strength = float(max(min(score, 100), -100))

        return {
            "short_term": short,
            "medium_term": medium,
            "long_term": long,
            "trend": final,
            "trend_strength": round(strength, 2)
        }


if __name__ == "__main__":
    # Simple test
    sample_df = pd.DataFrame({
        "Close": np.linspace(100, 150, 100),
        "ema20": np.linspace(105, 155, 100),
        "ema50": np.linspace(100, 150, 100),
    })

    td = TrendDetector()
    print(td.compute_trend(sample_df))
