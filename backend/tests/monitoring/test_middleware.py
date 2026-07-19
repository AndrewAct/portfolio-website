from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from apps.monitoring.middleware import PrometheusMiddleware, normalize_endpoint


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/", "/"),
        ("/metrics", "/metrics"),
        ("/utilities", "/utilities"),
        ("/r/abc123", "/r/{short_url}"),
        ("/utilities/url_shortener/abc123", "/utilities/url_shortener/{short_url}"),
        ("/utilities/url_shortener/", "/utilities/url_shortener"),
        ("/api/medium-posts/andrew", "/api/medium-posts/{username}"),
        ("/utilities/horoscope/Aries", "/utilities/horoscope/{id}"),
        ("/api/items/123", "/api/items/{id}"),
        ("/api/items/550e8400-e29b-41d4-a716-446655440000", "/api/items/{id}"),
        ("/api/items/abc123", "/api/items/{id}"),
        ("/health", "/health"),
    ],
)
def test_normalize_endpoint(path, expected):
    assert normalize_endpoint(path) == expected


def make_request(path="/r/abc123", method="GET"):
    return SimpleNamespace(url=SimpleNamespace(path=path), method=method)


@pytest.mark.asyncio
async def test_middleware_tracks_success(monkeypatch):
    tracker = Mock()
    response = SimpleNamespace(status_code=201)
    monkeypatch.setattr("apps.monitoring.middleware.track_metrics", tracker)

    result = await PrometheusMiddleware()(make_request(), AsyncMock(return_value=response))

    assert result is response
    tracker.assert_called_once()
    assert tracker.call_args.kwargs["endpoint"] == "/r/{short_url}"
    assert tracker.call_args.kwargs["status_code"] == 201


@pytest.mark.asyncio
async def test_middleware_skips_metrics_endpoint(monkeypatch):
    tracker = Mock()
    monkeypatch.setattr("apps.monitoring.middleware.track_metrics", tracker)

    await PrometheusMiddleware()(
        make_request("/metrics"),
        AsyncMock(return_value=SimpleNamespace(status_code=200)),
    )

    tracker.assert_not_called()


@pytest.mark.asyncio
async def test_middleware_tracks_and_reraises_failure(monkeypatch):
    tracker = Mock()
    monkeypatch.setattr("apps.monitoring.middleware.track_metrics", tracker)

    with pytest.raises(RuntimeError, match="boom"):
        await PrometheusMiddleware()(
            make_request("/api/items/123", "POST"),
            AsyncMock(side_effect=RuntimeError("boom")),
        )

    assert tracker.call_args.kwargs["status_code"] == 500
    assert tracker.call_args.kwargs["endpoint"] == "/api/items/{id}"
