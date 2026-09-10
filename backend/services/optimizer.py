from __future__ import annotations

ACTIONS = {
    "payment_link": {"cost": 0.0, "success_multiplier": 0.92},
    "upi_retry": {"cost": 0.0, "success_multiplier": 0.83},
    "card_retry": {"cost": 0.0, "success_multiplier": 0.70},
    "reminder": {"cost": 2.0, "success_multiplier": 0.45},
    "discount_300": {"cost": 300.0, "success_multiplier": 1.08},
}


def optimize(base_probability: float, amount: float) -> list[dict]:
    options = []

    for action, config in ACTIONS.items():
        adjusted_probability = min(
            base_probability * config["success_multiplier"], 0.99
        )
        recovered = adjusted_probability * amount
        expected_value = recovered - config["cost"]

        options.append({
            "action": action,
            "success_probability": round(adjusted_probability, 5),
            "expected_recovery": round(recovered, 2),
            "cost": round(config["cost"], 2),
            "expected_value": round(expected_value, 2),
        })

    return sorted(options, key=lambda x: x["expected_value"], reverse=True)


def recommend(base_probability: float, amount: float) -> dict:
    return optimize(base_probability, amount)[0]
