import logging
from urllib.parse import parse_qs, unquote_plus, urlsplit

from apps.config import Settings, get_settings
from apps.core.logger import setup_logging


def make_settings(**overrides):
    values = {
        "mongodb_username": "user@example.com",
        "mongodb_password": "p@ss:/?#[]!",
        "mongodb_cluster": "cluster.example.net",
        "mongodb_database": "portfolio",
        "grafana_api_key": "key",
        "grafana_instance_id": "instance",
        "grafana_otlp_endpoint": "https://otlp.example.net",
    }
    values.update(overrides)
    return Settings(**values)


def test_mongodb_url_encodes_credentials_and_options():
    settings = make_settings()

    parsed = urlsplit(settings.mongodb_url)
    options = parse_qs(parsed.query)

    assert unquote_plus(parsed.username) == settings.mongodb_username
    assert unquote_plus(parsed.password) == settings.mongodb_password
    assert settings.mongodb_url.count("?") == 1
    assert options["appName"] == ["Cluster0"]
    assert options["retryWrites"] == ["true"]
    assert options["tls"] == ["true"]


def test_gemini_defaults_target_stable_low_latency_model():
    settings = make_settings()

    assert settings.gemini_model == "gemini-3.1-flash-lite"
    assert settings.gemini_timeout_seconds == 15


def test_get_settings_is_cached():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()


def test_setup_logging_adds_handler_when_root_has_none(monkeypatch):
    root_logger = logging.getLogger()
    monkeypatch.setattr(root_logger, "handlers", [])

    result = setup_logging("portfolio")

    assert result is logging.getLogger("portfolio")
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    assert result.level == logging.INFO


def test_setup_logging_reuses_existing_root_handler(monkeypatch):
    root_logger = logging.getLogger()
    existing_handler = logging.NullHandler()
    monkeypatch.setattr(root_logger, "handlers", [existing_handler])

    setup_logging()

    assert root_logger.handlers == [existing_handler]
