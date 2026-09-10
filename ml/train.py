from __future__ import annotations

from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier

from ml.features import prepare_model_frame

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "transactions.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
X = prepare_model_frame(df.drop(columns=["recovered"]))
y = df["recovered"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

model = XGBClassifier(
    n_estimators=350,
    max_depth=6,
    learning_rate=0.06,
    subsample=0.85,
    colsample_bytree=0.85,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=4,
)

model.fit(X_train, y_train)

proba = model.predict_proba(X_test)[:, 1]
pred = (proba >= 0.5).astype(int)

metrics = {
    "roc_auc": float(roc_auc_score(y_test, proba)),
    "precision": float(precision_score(y_test, pred)),
    "recall": float(recall_score(y_test, pred)),
    "f1": float(f1_score(y_test, pred)),
    "rows": int(len(df)),
}

joblib.dump(model, MODEL_DIR / "recovery_model.joblib")
(MODEL_DIR / "feature_columns.json").write_text(
    json.dumps(list(X.columns), indent=2)
)
(MODEL_DIR / "metrics.json").write_text(
    json.dumps(metrics, indent=2)
)

print(json.dumps(metrics, indent=2))
print(f"Model saved to {MODEL_DIR / 'recovery_model.joblib'}")
