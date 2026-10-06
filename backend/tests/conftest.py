import os

# Test collection imports modules that construct clients at module scope. These values
# keep unit tests deterministic and ensure CI never needs production secrets.
TEST_ENV = {
    "MONGODB_USERNAME": "test-user",
    "MONGODB_PASSWORD": "test-password",
    "MONGODB_CLUSTER": "example.mongodb.net",
    "MONGODB_DATABASE": "portfolio-test",
    "OTEL_SERVICE_NAME": "portfolio-api-test",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://example.invalid",
    "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Basic test-token",
    "OTEL_RESOURCE_ATTRIBUTES": "deployment.environment=test",
    "GEMINI_API_KEY": "",
    "DATABASE_URL": "postgresql://test-user:test-password@example.invalid/test-db",
    "RESEND_API_KEY": "test-key",
    "RESEND_FROM_EMAIL": "horoscope@example.invalid",
    "RESEND_REPLY_TO_EMAIL": "",
    # Must be valid base64 (optionally "whsec_"-prefixed) — the svix library base64-decodes
    # it, same shape as a real Resend webhook signing secret.
    "RESEND_WEBHOOK_SECRET": "whsec_dGVzdC13ZWJob29rLXNlY3JldA==",
    "SUBSCRIPTION_TOKEN_SECRET": "test-token-secret",
}

os.environ.update(TEST_ENV)
