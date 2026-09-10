from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
N = 250_000

OUT = Path(__file__).resolve().parents[1] / "data" / "transactions.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(SEED)

payment_methods = np.array(["upi", "card", "netbanking", "wallet"])
devices = np.array(["mobile", "desktop", "tablet"])
categories = np.array(["fashion", "electronics", "grocery", "travel", "beauty", "home"])

customer_tenure_days = rng.integers(1, 1600, size=N)
transaction_count = rng.poisson(lam=np.clip(customer_tenure_days / 90, 1, 25)) + 1
previous_failures = rng.poisson(lam=0.8, size=N)
previous_successes = np.maximum(transaction_count - previous_failures, 0)
previous_success_rate = previous_successes / np.maximum(transaction_count, 1)

amount = np.round(
    np.exp(rng.normal(np.log(1800), 1.0, size=N)).clip(99, 100000),
    2
)

payment_method = rng.choice(
    payment_methods, size=N, p=[0.52, 0.28, 0.12, 0.08]
)
device_type = rng.choice(devices, size=N, p=[0.68, 0.27, 0.05])
merchant_category = rng.choice(categories, size=N)

hour = rng.integers(0, 24, size=N)
day_of_week = rng.integers(0, 7, size=N)

customer_ltv = np.round(
    (amount * transaction_count * rng.uniform(0.8, 1.4, size=N)).clip(500, 500000),
    2
)

failure_reason = rng.choice(
    ["bank_decline", "timeout", "insufficient_funds", "user_cancelled"],
    size=N,
    p=[0.38, 0.20, 0.17, 0.25]
)

# Synthetic but intentionally correlated recovery target.
logit = (
    -2.5
    + 2.2 * previous_success_rate
    - 0.000012 * amount
    + 0.000002 * customer_ltv
    + 0.0010 * customer_tenure_days
    - 0.28 * previous_failures
    + 0.35 * (payment_method == "upi")
    + 0.18 * (payment_method == "card")
    + 0.10 * (device_type == "mobile")
    + 0.16 * (failure_reason == "timeout")
    + 0.24 * (failure_reason == "user_cancelled")
    - 0.18 * (failure_reason == "insufficient_funds")
    + 0.10 * ((hour >= 18) & (hour <= 22))
)

prob = 1 / (1 + np.exp(-logit))
recovered = rng.binomial(1, np.clip(prob, 0.01, 0.99))

df = pd.DataFrame({
    "transaction_id": [f"TX{i:08d}" for i in range(N)],
    "customer_id": [f"C{i % 50000:06d}" for i in range(N)],
    "amount": amount,
    "payment_method": payment_method,
    "device_type": device_type,
    "merchant_category": merchant_category,
    "hour": hour,
    "day_of_week": day_of_week,
    "customer_tenure_days": customer_tenure_days,
    "transaction_count": transaction_count,
    "previous_success_rate": np.round(previous_success_rate, 5),
    "previous_failures": previous_failures,
    "customer_ltv": customer_ltv,
    "failure_reason": failure_reason,
    "recovered": recovered
})

df.to_csv(OUT, index=False)

print(f"Wrote {len(df):,} rows to {OUT}")
print(f"Recovery rate: {df['recovered'].mean():.2%}")
