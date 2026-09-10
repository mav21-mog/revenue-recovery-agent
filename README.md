# RecoverPay

ML-powered autonomous revenue recovery for payment failures.

## Current milestone

- Synthetic transaction generator
- PostgreSQL schema
- Feature engineering
- XGBoost recovery-probability model
- SHAP-based explanations
- FastAPI prediction endpoint
- Action optimizer
- Basic guardrail engine

## Project structure

```text
recoverpay/
├── backend/
│   ├── main.py
│   └── services/
│       ├── predictor.py
│       └── optimizer.py
├── ml/
│   ├── generate_data.py
│   ├── features.py
│   ├── train.py
│   └── explain.py
├── database/
│   └── schema.sql
├── data/
├── models/
├── requirements.txt
└── .gitignore
```

## Quick Start (Automated Setup)

Run the automated setup script to configure the virtual environment, install dependencies (supports both `uv` and standard `pip`), generate synthetic training data, and train the XGBoost model:

```bash
./setup.sh
```

To force-regenerate synthetic data and retrain the model from scratch:
```bash
./setup.sh --force
```

Start the API development server:
```bash
./run.sh
```
Or directly via:
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

Interactive API documentation (Swagger UI) is available at:
```text
http://127.0.0.1:8000/docs
```

## Manual Setup

If you prefer setting up step-by-step manually:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1. Generate synthetic data (250,000 transactions)
python ml/generate_data.py

# 2. Train model and generate artifacts
python ml/train.py

# 3. Start API server
uvicorn backend.main:app --reload
```


Prediction:

```bash
curl -X POST http://127.0.0.1:8000/predict/recovery \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 12500,
    "payment_method": "upi",
    "previous_success_rate": 0.92,
    "previous_failures": 1,
    "customer_ltv": 85000,
    "customer_tenure_days": 420,
    "transaction_count": 9,
    "hour": 20,
    "day_of_week": 4,
    "device_type": "mobile",
    "merchant_category": "fashion",
    "failure_reason": "bank_decline"
  }'
```

The initial release uses synthetic data. Replace the generator with anonymized Razorpay/Test Mode data when available.
