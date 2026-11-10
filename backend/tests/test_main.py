from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import main


def test_healthcheck_reports_process_liveness():
    assert main.healthcheck() == {"status": "ok"}


def test_app_uses_fastapi_native_telemetry_with_low_volume_defaults():
    assert main.app._telemetry["operation_spans"] is False
    assert main.app._telemetry["logs"] is False
    assert main.app._telemetry["exclude"]({"path": "/health"}) is True


@pytest.mark.asyncio
async def test_lifespan_starts_and_stops_resources(monkeypatch):
    metrics = SimpleNamespace(install=Mock())
    horoscope_service = SimpleNamespace(close=AsyncMock())
    subscription_service = SimpleNamespace(close=AsyncMock())
    init_db = AsyncMock()
    close_db = AsyncMock()
    init_postgres_db = AsyncMock()
    close_postgres_db = AsyncMock()
    monkeypatch.setattr(main, "system_metrics", metrics)
    monkeypatch.setattr(main, "get_horoscope_service", Mock(return_value=horoscope_service))
    monkeypatch.setattr(main, "get_subscription_service", Mock(return_value=subscription_service))
    monkeypatch.setattr(main, "init_db", init_db)
    monkeypatch.setattr(main, "close_db", close_db)
    monkeypatch.setattr(main, "init_postgres_db", init_postgres_db)
    monkeypatch.setattr(main, "close_postgres_db", close_postgres_db)

    async with main.lifespan(main.app):
        init_db.assert_awaited_once()
        init_postgres_db.assert_awaited_once()
        metrics.install.assert_called_once()

    horoscope_service.close.assert_awaited_once()
    subscription_service.close.assert_awaited_once()
    close_db.assert_awaited_once()
    close_postgres_db.assert_awaited_once()
