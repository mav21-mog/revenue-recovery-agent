# backend/services/guardrails.py
from typing import Any

def apply_guardrails(request_data: dict[str, Any], candidate_actions: list[dict]) -> list[dict]:
    """
    Filters out unsafe or un-business-friendly actions based on strict rules.
    """
    filtered_actions = []
    
    # Extract key context for rule evaluation
    failure_reason = request_data.get("failure_reason")
    customer_ltv = request_data.get("customer_ltv", 0)
    previous_failures = request_data.get("previous_failures", 0)

    for action_item in candidate_actions:
        action_name = action_item["action"]
        is_safe = True

        # Rule 1: No automatic retries if the bank said "insufficient_funds"
        if failure_reason == "insufficient_funds" and action_name in ["upi_retry", "card_retry"]:
            is_safe = False

        # Rule 2: Never give a discount if the customer's LTV is below 5,000
        if "discount" in action_name and customer_ltv < 5000:
            is_safe = False

        # Rule 3: If it has already failed 3 or more times, only allow passive reminders
        if previous_failures >= 3 and action_name not in ["reminder", "payment_link"]:
            is_safe = False
            
        # Rule 4: Do not offer discounts for small amounts (e.g., less than 500)
        if "discount" in action_name and request_data.get("amount", 0) < 500:
            is_safe = False

        if is_safe:
            filtered_actions.append(action_item)
            
    # Fallback: If guardrails removed everything, default to a safe, zero-cost action
    if not filtered_actions:
        return [{
            "action": "reminder",
            "success_probability": 0.1,
            "expected_recovery": 0,
            "cost": 0,
            "expected_value": 0
        }]

    return filtered_actions