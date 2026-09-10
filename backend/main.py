from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException  # pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware  # pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field  # pyrefly: ignore [missing-import]

from backend.services.predictor import load_model, predict
from backend.services.optimizer import optimize
from backend.services.guardrails import apply_guardrails


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm ML model into memory on server boot to avoid cold-start latency
    try:
        load_model()
    except Exception as exc:
        print(f"Warning: Could not pre-load model at startup: {exc}")
    yield


app = FastAPI(
    title="RecoverPay API",
    description="ML-powered autonomous revenue recovery for payment failures",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend and cross-origin fetch requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PaymentMethod = Literal["upi", "card", "netbanking", "wallet"]
DeviceType = Literal["mobile", "desktop", "tablet"]
MerchantCategory = Literal["fashion", "electronics", "grocery", "travel", "beauty", "home"]
FailureReason = Literal["bank_decline", "timeout", "insufficient_funds", "user_cancelled"]


class PredictionRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount in INR")
    payment_method: PaymentMethod = Field(..., description="Payment method: upi, card, netbanking, or wallet")
    previous_success_rate: float = Field(..., ge=0.0, le=1.0, description="Past success rate (0.0 to 1.0)")
    previous_failures: int = Field(..., ge=0, description="Number of past failed attempts")
    customer_ltv: float = Field(..., ge=0.0, description="Customer Lifetime Value")
    customer_tenure_days: int = Field(..., ge=0, description="Customer tenure in days")
    transaction_count: int = Field(..., ge=0, description="Total transaction count")
    hour: int = Field(..., ge=0, le=23, description="Hour of the day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Mon, 6=Sun)")
    device_type: DeviceType = Field(..., description="Device type: mobile, desktop, or tablet")
    merchant_category: MerchantCategory = Field(..., description="Category: fashion, electronics, grocery, travel, beauty, home")
    failure_reason: FailureReason = Field(..., description="Failure reason: bank_decline, timeout, insufficient_funds, user_cancelled")
    transaction_id: str | None = Field(default=None, description="Optional transaction ID")
    customer_id: str | None = Field(default=None, description="Optional customer ID")

    model_config = {
        "json_schema_extra": {
            "example": {
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
                "failure_reason": "bank_decline",
            }
        }
    }


class ActionItem(BaseModel):
    action: str = Field(..., description="Recovery action identifier")
    success_probability: float = Field(..., description="Estimated recovery probability for this action")
    expected_recovery: float = Field(..., description="Gross expected recovery amount")
    cost: float = Field(..., description="Execution cost of this action")
    expected_value: float = Field(..., description="Net expected value (recovery minus cost)")


class PredictionResponse(BaseModel):
    recovery_probability: float = Field(..., description="Base model recovery probability (0.0 to 1.0)")
    expected_recovery: float = Field(..., description="Base expected recovery value in INR")
    model_version: str = Field(..., description="Model version tag")
    recommended_action: ActionItem = Field(..., description="Top recommended recovery action after guardrails")
    candidate_actions: list[ActionItem] = Field(..., description="All safe candidate actions ranked by expected value")
    rejected_actions_count: int = Field(..., description="Number of actions filtered out by guardrails")


@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "RecoverPay API",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "predict_recovery": "/predict/recovery [POST]",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict/recovery", response_model=PredictionResponse)
def predict_recovery(request: PredictionRequest):
    try:
        request_dict = request.model_dump()

        # 1. Get the raw ML prediction
        result = predict(request_dict)

        # 2. Get all mathematically optimal actions
        raw_actions = optimize(
            result["recovery_probability"],
            request.amount,
        )

        # 3. Apply business guardrails to filter out risky actions
        safe_actions = apply_guardrails(request_dict, raw_actions)

        # 4. Return the typed response
        return {
            **result,
            "recommended_action": safe_actions[0],
            "candidate_actions": safe_actions,
            "rejected_actions_count": len(raw_actions) - len(safe_actions),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(exc)}") from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)