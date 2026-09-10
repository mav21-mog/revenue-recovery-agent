#!/usr/bin/env python3
"""Quick script to test the RecoverPay API prediction endpoint."""

import json
import urllib.request
import urllib.error

URL = "http://127.0.0.1:8000/predict/recovery"

SAMPLE_PAYLOAD = {
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

def main():
    print(f"Sending test request to {URL}...")
    req_data = json.dumps(SAMPLE_PAYLOAD).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("\nResponse received successfully (HTTP 200):")
            print(json.dumps(data, indent=2))
    except urllib.error.URLError as e:
        print(f"\nFailed to connect: {e}")
        print("Make sure the server is running with: ./run.sh")

if __name__ == "__main__":
    main()
