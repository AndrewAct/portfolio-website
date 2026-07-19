import os

# Test collection imports modules that construct clients at module scope. These values
# keep unit tests deterministic and ensure CI never needs production secrets.
TEST_ENV = {
    "MONGODB_USERNAME": "test-user",
    "MONGODB_PASSWORD": "test-password",
    "MONGODB_CLUSTER": "example.mongodb.net",
    "MONGODB_DATABASE": "portfolio-test",
    "GRAFANA_API_KEY": "test-key",
    "GRAFANA_INSTANCE_ID": "test-instance",
    "GRAFANA_OTLP_ENDPOINT": "https://example.invalid",
    "GEMINI_API_KEY": "",
}

os.environ.update(TEST_ENV)
