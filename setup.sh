#!/usr/bin/env bash
# ==============================================================================
# RecoverPay - Automated Project Setup Script
# ==============================================================================
# This script sets up the complete environment, installs dependencies,
# generates synthetic training data, and trains the ML recovery model.
#
# Usage:
#   ./setup.sh              # Standard setup (skips data/model if already present)
#   ./setup.sh --force      # Forces re-generation of data and re-training
# ==============================================================================

set -euo pipefail

# Colors for friendly output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
    FORCE=true
fi

echo -e "${BLUE}${BOLD}======================================================${NC}"
echo -e "${BLUE}${BOLD}        RecoverPay Automated Project Setup            ${NC}"
echo -e "${BLUE}${BOLD}======================================================${NC}"

# 1. Detect Python (prefer stable 3.12 or 3.11 for pre-built scientific wheel compatibility)
echo -e "\n${BLUE}[1/5] Checking Python installation...${NC}"
if command -v python3.12 &>/dev/null; then
    PYTHON_BIN="python3.12"
elif command -v python3.11 &>/dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3.10 &>/dev/null; then
    PYTHON_BIN="python3.10"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo -e "${RED}Error: Python is not installed or not in PATH.${NC}"
    exit 1
fi

PY_VERSION=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}Using $PYTHON_BIN (version $PY_VERSION)${NC}"

# 2. Virtual Environment Setup
echo -e "\n${BLUE}[2/5] Setting up virtual environment (.venv)...${NC}"
HAS_UV=false
if command -v uv &>/dev/null; then
    HAS_UV=true
    echo -e "${GREEN}Detected 'uv' package manager (fast setup mode enabled).${NC}"
fi

if [[ ! -d ".venv" ]] || [[ "$FORCE" == "true" ]]; then
    if [[ "$HAS_UV" == "true" ]]; then
        echo "Creating virtual environment with uv using $PYTHON_BIN..."
        uv venv --python "$PYTHON_BIN" .venv
    else
        echo "Creating virtual environment with $PYTHON_BIN..."
        "$PYTHON_BIN" -m venv .venv
    fi
    echo -e "${GREEN}Virtual environment created in .venv/${NC}"

else
    echo -e "${YELLOW}Virtual environment .venv already exists. Skipping recreation.${NC}"
fi

VENV_PYTHON="./.venv/bin/python"
VENV_PIP="./.venv/bin/pip"

# 3. Install Dependencies
echo -e "\n${BLUE}[3/5] Installing dependencies from requirements.txt...${NC}"
if [[ "$HAS_UV" == "true" ]]; then
    uv pip install -r requirements.txt --python "$VENV_PYTHON"
else
    "$VENV_PIP" install --upgrade pip
    "$VENV_PIP" install -r requirements.txt
fi
echo -e "${GREEN}Dependencies installed successfully.${NC}"

# Register project root in virtual environment so imports like 'import ml' work everywhere
SITE_PACKAGES=$("$VENV_PYTHON" -c "import site; print(site.getsitepackages()[0])")
echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" > "$SITE_PACKAGES/recoverpay.pth"
echo -e "\n${BLUE}[4/5] Checking training dataset...${NC}"
DATA_FILE="data/transactions.csv"
if [[ ! -f "$DATA_FILE" ]] || [[ "$FORCE" == "true" ]]; then
    echo "Generating synthetic transaction dataset (250,000 records)..."
    "$VENV_PYTHON" ml/generate_data.py
    echo -e "${GREEN}Dataset generated at $DATA_FILE${NC}"
else
    echo -e "${YELLOW}Dataset already exists ($DATA_FILE). Use --force to regenerate.${NC}"
fi

# 5. Train ML Model
echo -e "\n${BLUE}[5/5] Checking ML recovery model...${NC}"
MODEL_FILE="models/recovery_model.joblib"
COLUMNS_FILE="models/feature_columns.json"

if [[ ! -f "$MODEL_FILE" ]] || [[ ! -f "$COLUMNS_FILE" ]] || [[ "$FORCE" == "true" ]]; then
    echo "Training XGBoost recovery-probability model..."
    "$VENV_PYTHON" ml/train.py
    echo -e "${GREEN}Model trained and saved to $MODEL_FILE${NC}"
else
    echo -e "${YELLOW}Model already exists ($MODEL_FILE). Use --force to retrain.${NC}"
fi

# 6. Sanity Verification
echo -e "\n${BLUE}Verifying backend import & predictor pipeline...${NC}"
"$VENV_PYTHON" -c '
from backend.services.predictor import predict
from backend.services.optimizer import optimize
from backend.services.guardrails import apply_guardrails

sample = {
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
}
res = predict(sample)
opts = optimize(res["recovery_probability"], sample["amount"])
safe = apply_guardrails(sample, opts)
assert len(safe) > 0
print("Verification passed: model scored probability =", res["recovery_probability"])
'

echo -e "\n${GREEN}${BOLD}======================================================${NC}"
echo -e "${GREEN}${BOLD}             Setup Complete Successfully!             ${NC}"
echo -e "${GREEN}${BOLD}======================================================${NC}"
echo -e "\nTo activate the virtual environment:"
echo -e "  ${BOLD}source .venv/bin/activate${NC}"
echo -e "\nTo start the API server:"
echo -e "  ${BOLD}./run.sh${NC}  or  ${BOLD}uvicorn backend.main:app --reload${NC}"
echo -e "\nTo access documentation and swagger UI:"
echo -e "  ${BOLD}http://127.0.0.1:8000/docs${NC}\n"
