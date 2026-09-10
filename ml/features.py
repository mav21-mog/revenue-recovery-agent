from __future__ import annotations

import pandas as pd

CATEGORICAL = [
    "payment_method",
    "device_type",
    "merchant_category",
    "failure_reason",
]

ID_COLUMNS = [
    "transaction_id",
    "customer_id",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    # IDs are identifiers, not predictive features.
    data = data.drop(columns=ID_COLUMNS, errors="ignore")

    data["amount_to_ltv"] = data["amount"] / data["customer_ltv"].clip(lower=1)
    data["is_peak_hour"] = data["hour"].between(18, 22).astype(int)
    data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)
    data["customer_is_returning"] = (data["transaction_count"] > 1).astype(int)

    return data


def prepare_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    data = build_features(df)
    return pd.get_dummies(
        data,
        columns=CATEGORICAL,
        drop_first=False,
        dtype=float,
    )
