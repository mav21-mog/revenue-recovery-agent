CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(32),
    created_at TIMESTAMP NOT NULL,
    total_spend NUMERIC(14,2) NOT NULL DEFAULT 0,
    transaction_count INTEGER NOT NULL DEFAULT 0,
    successful_transactions INTEGER NOT NULL DEFAULT 0,
    failed_transactions INTEGER NOT NULL DEFAULT 0,
    preferred_payment_method VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL REFERENCES customers(customer_id),
    order_id VARCHAR(64) NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    payment_method VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    failure_reason VARCHAR(64),
    created_at TIMESTAMP NOT NULL,
    device_type VARCHAR(32),
    merchant_category VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS recovery_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) REFERENCES transactions(transaction_id),
    recovery_probability NUMERIC(6,5) NOT NULL,
    expected_recovery NUMERIC(14,2) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recovery_actions (
    action_id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) REFERENCES transactions(transaction_id),
    action_type VARCHAR(64) NOT NULL,
    predicted_success_probability NUMERIC(6,5),
    expected_value NUMERIC(14,2),
    actual_result BOOLEAN,
    recovered_amount NUMERIC(14,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merchant_guardrails (
    merchant_id VARCHAR(64) PRIMARY KEY,
    max_auto_amount NUMERIC(14,2) NOT NULL DEFAULT 10000,
    max_discount NUMERIC(14,2) NOT NULL DEFAULT 500,
    max_attempts INTEGER NOT NULL DEFAULT 2,
    require_approval_above NUMERIC(14,2) NOT NULL DEFAULT 10000
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
