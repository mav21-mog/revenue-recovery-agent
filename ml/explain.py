from __future__ import annotations

import json
from pathlib import Path
import joblib
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "recovery_model.joblib"
COLUMNS_PATH = ROOT / "models" / "feature_columns.json"

print("Loading model and initializing SHAP Explainer...")
model = joblib.load(MODEL_PATH)
feature_columns = json.loads(COLUMNS_PATH.read_text())

# Initialize the explainer ONCE globally
explainer = shap.TreeExplainer(model)

def explain_row(row: pd.DataFrame, top_k: int = 5) -> list[dict]:
    """
    Returns the top-k most impactful features for a single prediction.
    """
    # Clean, one-line way to align columns and fill missing ones with 0!
    row = row.reindex(columns=feature_columns, fill_value=0)
    
    # Calculate SHAP values using the globally initialized explainer
    shap_values = explainer.shap_values(row)

    # shap_values is a matrix; get the first row for our single instance
    values = shap_values[0] 
    
    pairs = sorted(
        zip(feature_columns, values),
        key=lambda item: abs(item[1]),
        reverse=True,
    )[:top_k]

    result = []
    for feature, value in pairs:
        result.append({
            "feature": feature,
            "impact": float(value),
            "direction": "positive" if value >= 0 else "negative",
        })

    return result

if __name__ == "__main__":
    # Quick test to ensure it works
    sample_data = pd.DataFrame([{
        "transaction_amount": 1200.50,
        "customer_tenure_days": 2,
        "failed_attempts": 4,
        "payment_method_bank_transfer": 1
    }])
    
    explanations = explain_row(sample_data)
    print("\n--- SHAP Explanations ---")
    print(json.dumps(explanations, indent=2))