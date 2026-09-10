from __future__ import annotations

import json
from pathlib import Path

from typing import Any

import joblib  # pyrefly: ignore [missing-import]
import pandas as pd  # pyrefly: ignore [missing-import]

from ml.features import prepare_model_frame

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "recovery_model.joblib"
COLUMNS_PATH = ROOT / "models" / "feature_columns.json"

_model: Any = None
_columns: list[str] | None = None


def load_model() -> tuple[Any, list[str]]:
    global _model, _columns
    if _model is None or _columns is None:
        if not MODEL_PATH.exists() or not COLUMNS_PATH.exists():
            raise FileNotFoundError(
                "Model files not found. Run: python ml/generate_data.py && python ml/train.py"
            )
        _model = joblib.load(MODEL_PATH)
        _columns = json.loads(COLUMNS_PATH.read_text())
    return _model, _columns


def predict(payload: dict) -> dict:
    model, columns = load_model()

    frame = pd.DataFrame([payload])
    frame = prepare_model_frame(frame)
    frame = frame.reindex(columns=columns, fill_value=0)

    probability = float(model.predict_proba(frame)[:, 1][0])
    amount = float(payload["amount"])

    return {
        "recovery_probability": round(probability, 5),
        "expected_recovery": round(probability * amount, 2),
        "model_version": "xgb-v1"
    }
