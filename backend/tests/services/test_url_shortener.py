from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from apps.services.url_shortener import database, router
from apps.services.url_shortener.models import URLMapping
from apps.services.url_shortener.schemas import DeleteURLRequest, URLBase, URLResponse
from apps.services.url_shortener.service import URLShortenerService


def make_collection():
    return SimpleNamespace(
        find_one=AsyncMock(),
        insert_one=AsyncMock(),
        delete_one=AsyncMock(),
        create_indexes=AsyncMock(),
    )


def test_generate_short_url_uses_requested_length():
    result = URLShortenerService(collection=make_collection()).generate_short_url(12)

    assert len(result) == 12
    assert result.isalnum()


@pytest.mark.asyncio
async def test_create_short_url_returns_existing_mapping():
    created_at = datetime(2026, 7, 18)
    collection = make_collection()
    collection.find_one.return_value = {
        "original_url": "https://example.com",
        "short_url": "andrewcee.io/r/existing",
        "created_at": created_at,
    }
    service = URLShortenerService(collection=collection)

    result = await service.create_short_url("https://example.com")

    assert result == URLResponse(
        original_url="https://example.com",
        shortened_url="andrewcee.io/r/existing",
        created_at=created_at,
    )
    collection.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_short_url_adds_scheme_and_retries_collision(monkeypatch):
    collection = make_collection()
    collection.find_one.side_effect = [None, {"short_url": "duplicate"}, None]
    service = URLShortenerService(domain="sho.rt", collection=collection)
    monkeypatch.setattr(service, "generate_short_url", Mock(side_effect=["duplicate", "unique"]))

    result = await service.create_short_url("example.com")

    assert result.original_url == "https://example.com"
    assert result.shortened_url == "sho.rt/r/unique"
    inserted = collection.insert_one.await_args.args[0]
    assert inserted["original_url"] == "https://example.com"
    assert inserted["short_url"] == "sho.rt/r/unique"


@pytest.mark.asyncio
async def test_create_short_url_rejects_invalid_url(monkeypatch):
    service = URLShortenerService(collection=make_collection())
    monkeypatch.setattr("apps.services.url_shortener.service.validators.url", lambda _url: False)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_short_url("not a url")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_original_url_normalizes_code():
    collection = make_collection()
    collection.find_one.return_value = {"original_url": "https://example.com"}
    service = URLShortenerService(collection=collection)

    result = await service.get_original_url('https://andrewcee.io/r/"abc123"')

    assert result == "https://example.com"
    collection.find_one.assert_awaited_once_with({"short_url": "andrewcee.io/r/abc123"})


@pytest.mark.asyncio
async def test_get_original_url_raises_when_missing():
    collection = make_collection()
    collection.find_one.return_value = None
    service = URLShortenerService(collection=collection)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_original_url("missing")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize(("deleted_count", "expected_error"), [(1, False), (0, True)])
async def test_delete_url(deleted_count, expected_error):
    collection = make_collection()
    collection.delete_one.return_value = SimpleNamespace(deleted_count=deleted_count)
    service = URLShortenerService(collection=collection)

    if expected_error:
        with pytest.raises(HTTPException, match="URL not found"):
            await service.delete_url("missing")
    else:
        assert await service.delete_url("existing") is True


def test_url_mapping_generates_object_id_and_uses_database_alias():
    mapping = URLMapping(short_url="sho.rt/r/abc", original_url="https://example.com")
    assert isinstance(mapping.id, ObjectId)
    assert mapping.model_dump(by_alias=True)["_id"] == mapping.id


@pytest.mark.asyncio
async def test_database_lifecycle(monkeypatch):
    collection = SimpleNamespace(create_indexes=AsyncMock())
    client = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(database, "url_collection", collection)
    monkeypatch.setattr(database, "client", client)

    await database.init_db()
    await database.close_db()

    indexes = collection.create_indexes.await_args.args[0]
    assert len(indexes) == 2
    client.close.assert_awaited_once()


def test_get_collection_returns_configured_collection(monkeypatch):
    collection = object()
    monkeypatch.setattr(database, "url_collection", collection)

    assert database.get_collection() is collection


@pytest.mark.asyncio
async def test_router_happy_paths(monkeypatch):
    created_at = datetime(2026, 7, 18)
    service = SimpleNamespace(
        create_short_url=AsyncMock(
            return_value=URLResponse(
                original_url="https://example.com",
                shortened_url="andrewcee.io/r/abc123",
                created_at=created_at,
            )
        ),
        get_original_url=AsyncMock(return_value="example.com"),
        delete_url=AsyncMock(return_value=True),
    )
    monkeypatch.setattr(router, "url_shortener_service", service)

    created = await router.create_short_url(URLBase(url="https://example.com"))
    retrieved = await router.get_original_url("abc123")
    deleted = await router.delete_url(DeleteURLRequest(url="abc123"))
    redirected = await router.redirect_to_original_url("abc123")
    info = await router.get_service_info()

    assert created.shortened_url.endswith("abc123")
    assert retrieved == {"original_url": "example.com"}
    assert deleted == {"message": "URL mapping deleted successfully"}
    assert redirected.status_code == 302
    assert redirected.headers["location"] == "https://example.com"
    assert info["service"] == "URL Shortener"


@pytest.mark.asyncio
async def test_redirect_preserves_existing_scheme(monkeypatch):
    service = SimpleNamespace(get_original_url=AsyncMock(return_value="http://example.com"))
    monkeypatch.setattr(router, "url_shortener_service", service)

    response = await router.redirect_to_original_url("abc123")

    assert response.headers["location"] == "http://example.com"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("handler", "argument", "status_code"),
    [
        (router.redirect_to_original_url, "missing", 404),
        (router.create_short_url, URLBase(url="https://example.com"), 500),
        (router.get_original_url, "missing", 404),
        (router.delete_url, DeleteURLRequest(url="missing"), 404),
    ],
)
async def test_router_translates_service_failures(monkeypatch, handler, argument, status_code):
    service = SimpleNamespace(
        create_short_url=AsyncMock(side_effect=RuntimeError("database unavailable")),
        get_original_url=AsyncMock(side_effect=RuntimeError("database unavailable")),
        delete_url=AsyncMock(side_effect=RuntimeError("database unavailable")),
    )
    monkeypatch.setattr(router, "url_shortener_service", service)

    with pytest.raises(HTTPException) as exc_info:
        await handler(argument)

    assert exc_info.value.status_code == status_code
