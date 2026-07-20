import json

import httpx
import pytest

from apps.integrations.resend import ResendEmailSender, ResendSendError


def make_sender(handler) -> ResendEmailSender:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url="https://api.resend.com", transport=transport)
    return ResendEmailSender(client=client)


@pytest.mark.asyncio
async def test_send_returns_message_id_and_sets_idempotency_header():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        return httpx.Response(200, json={"id": "resend-msg-1"})

    sender = make_sender(handler)

    message_id = await sender.send(
        to="user@example.com",
        subject="Hi",
        html="<p>hi</p>",
        text="hi",
        idempotency_key="horoscope:1:2026-07-19",
    )

    assert message_id == "resend-msg-1"
    assert captured["headers"]["idempotency-key"] == "horoscope:1:2026-07-19"


@pytest.mark.asyncio
async def test_send_raises_on_http_error_status():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "invalid recipient"})

    sender = make_sender(handler)

    with pytest.raises(ResendSendError):
        await sender.send(
            to="bad@example.com", subject="s", html="h", text="t", idempotency_key="k"
        )


@pytest.mark.asyncio
async def test_send_raises_on_transport_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    sender = make_sender(handler)

    with pytest.raises(ResendSendError):
        await sender.send(
            to="user@example.com", subject="s", html="h", text="t", idempotency_key="k"
        )


@pytest.mark.asyncio
async def test_send_raises_when_response_has_no_message_id():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    sender = make_sender(handler)

    with pytest.raises(ResendSendError, match="did not contain a message id"):
        await sender.send(
            to="user@example.com", subject="s", html="h", text="t", idempotency_key="k"
        )


@pytest.mark.asyncio
async def test_close_closes_underlying_client():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "x"})

    sender = make_sender(handler)

    await sender.close()

    assert sender._client.is_closed


def test_constructor_builds_default_client_when_none_given():
    sender = ResendEmailSender()

    assert sender._client.headers["authorization"] == "Bearer test-key"
    assert sender.reply_to == ""  # not set in TEST_ENV, defaults to blank


@pytest.mark.asyncio
async def test_send_includes_reply_to_header_when_configured():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "resend-msg-1"})

    sender = make_sender(handler)
    sender.reply_to = "andrewisgrinding@gmail.com"

    await sender.send(to="user@example.com", subject="s", html="h", text="t", idempotency_key="k")

    assert captured["body"]["reply_to"] == "andrewisgrinding@gmail.com"


@pytest.mark.asyncio
async def test_send_omits_reply_to_when_not_configured():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "resend-msg-1"})

    sender = make_sender(handler)
    sender.reply_to = ""

    await sender.send(to="user@example.com", subject="s", html="h", text="t", idempotency_key="k")

    assert "reply_to" not in captured["body"]
