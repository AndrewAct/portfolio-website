-- Horoscope email subscriptions: subscriber preferences plus a per-local-day delivery ledger.
-- UNIQUE(subscription_id, local_date) on horoscope_deliveries is the invariant that enforces
-- "at most one send per subscriber per local calendar day" — not application logic.

CREATE TABLE IF NOT EXISTS horoscope_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_confirmation'
        CHECK (status IN ('pending_confirmation', 'active', 'paused', 'unsubscribed')),
    birthdate DATE NOT NULL,
    gender TEXT NOT NULL DEFAULT 'neutral',
    language TEXT NOT NULL DEFAULT 'en',
    timezone TEXT NOT NULL,
    send_time_local TIME NOT NULL,
    token_version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmed_at TIMESTAMPTZ,
    unsubscribed_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_horoscope_subscriptions_email
    ON horoscope_subscriptions (lower(email));

CREATE INDEX IF NOT EXISTS ix_horoscope_subscriptions_status
    ON horoscope_subscriptions (status);

CREATE TABLE IF NOT EXISTS horoscope_deliveries (
    id BIGSERIAL PRIMARY KEY,
    subscription_id BIGINT NOT NULL REFERENCES horoscope_subscriptions (id) ON DELETE CASCADE,
    local_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'bounced', 'complained')),
    idempotency_key TEXT NOT NULL,
    resend_message_id TEXT,
    attempt_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    UNIQUE (subscription_id, local_date)
);

CREATE INDEX IF NOT EXISTS ix_horoscope_deliveries_resend_message_id
    ON horoscope_deliveries (resend_message_id);
