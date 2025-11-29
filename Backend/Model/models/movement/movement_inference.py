import numpy as np
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

class MovementModelInference:
    """
    Loads and runs 3-model ensemble for UP/DOWN movement prediction:
    - RandomForestClassifier
    - GradientBoostingClassifier
    - XGBoostClassifier (optional)

    Expects a **1-row DataFrame of FEATURES** as input.
    """

    def __init__(self, model_dir: str = "Model/models/movement"):
        self.model_dir = Path(model_dir)

        # Required models
        self.rf_path = self.model_dir / "movement_rf.pkl"
        self.gb_path = self.model_dir / "movement_gb.pkl"

        # Optional model (only if installed)
        self.xgb_path = self.model_dir / "movement_xgb.pkl"

        self.rf_model = self._must_load(self.rf_path)
        self.gb_model = self._must_load(self.gb_path)
        self.xgb_model = self._optional_load(self.xgb_path)

    # ----------------------------------------------------
    # SAFE LOADERS
    # ----------------------------------------------------

    def _must_load(self, path: Path):
        """Strict loader — used for required models."""
        if not path.exists():
            raise FileNotFoundError(f"Model file missing: {path}")
        return joblib.load(path)

    def _optional_load(self, path: Path):
        """
        Optional loader for XGB.
        Returns None safely if file missing.
        """
        if path.exists():
            return joblib.load(path)
        return None

    # ----------------------------------------------------
    # PREDICTION (FEATURE-BASED)
    # ----------------------------------------------------

    def predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        Takes a **1-row feature DataFrame** and returns ensemble UP/DOWN prediction.

        features must contain the same columns as used in training:
        ["Close", "Open", "High", "Low", "Volume",
         "rsi", "macd", "macd_signal",
         "ema20", "ema50",
         "boll_up", "boll_low",
         "return"]
        """

        if features is None or features.empty:
            return {"error": "Invalid feature row"}

        # Ensure 2D shape for sklearn
        row = features.to_numpy().reshape(1, -1)

        # Required models
        rf_pred = int(self.rf_model.predict(row)[0])
        gb_pred = int(self.gb_model.predict(row)[0])

        predictions = {
            "RF": rf_pred,
            "GB": gb_pred,
        }

        preds = [rf_pred, gb_pred]

        # XGB only if available
        if self.xgb_model is not None:
            xgb_pred = int(self.xgb_model.predict(row)[0])
            predictions["XGB"] = xgb_pred
            preds.append(xgb_pred)

        # Voting
        up_votes = preds.count(1)
        total_models = len(preds)

        final_move = 1 if up_votes > (total_models / 2) else 0
        confidence = round(
            (max(up_votes, total_models - up_votes) / total_models) * 100, 2
        )

        return {
            "movement_prediction": "UP" if final_move == 1 else "DOWN",
            "movement_confidence": confidence,
            "votes": predictions,
        }


if __name__ == "__main__":
    # Simple shape test
    sample_row = pd.DataFrame([{
        "Close": 100,
        "Open": 99,
        "High": 102,
        "Low": 98,
        "Volume": 2_000_000,
        "rsi": 45,
        "macd": -0.2,
        "macd_signal": -0.1,
        "ema20": 98,
        "ema50": 95,
        "boll_up": 110,
        "boll_low": 90,
        "return": 0.01,
    }])

    model = MovementModelInference()
    print(model.predict(sample_row))
