import base64
import json

import pytest

from apps.services.horoscope_subscriptions import tokens


def test_sign_and_verify_round_trip():
    token = tokens.sign_token(subscription_id=42, purpose="confirm", token_version=1)

    payload = tokens.verify_token(token, expected_purpose="confirm")

    assert payload == tokens.TokenPayload(subscription_id=42, purpose="confirm", token_version=1)


def test_verify_rejects_purpose_mismatch():
    token = tokens.sign_token(subscription_id=1, purpose="unsubscribe", token_version=1)

    with pytest.raises(tokens.TokenError):
        tokens.verify_token(token, expected_purpose="preferences")


def test_verify_rejects_tampered_signature():
    token = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1)
    payload_part, signature_part = token.split(".", 1)
    tampered = f"{payload_part}.{signature_part[:-2]}zz"

    with pytest.raises(tokens.TokenError):
        tokens.verify_token(tampered, expected_purpose="confirm")


def test_verify_rejects_expired_token():
    token = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1, ttl_seconds=-1)

    with pytest.raises(tokens.TokenError, match="expired"):
        tokens.verify_token(token, expected_purpose="confirm")


def test_verify_accepts_non_expiring_token_without_ttl():
    token = tokens.sign_token(subscription_id=1, purpose="unsubscribe", token_version=3)

    payload = tokens.verify_token(token, expected_purpose="unsubscribe")

    assert payload.token_version == 3


@pytest.mark.parametrize("garbage", ["not-a-token", "only.one.part.too.many", ""])
def test_verify_rejects_malformed_tokens(garbage):
    with pytest.raises(tokens.TokenError):
        tokens.verify_token(garbage, expected_purpose="confirm")


def test_verify_rejects_payload_missing_required_fields():
    payload_bytes = json.dumps({"purpose": "confirm"}).encode("utf-8")
    signature = tokens._sign(payload_bytes)
    bad_token = f"{tokens._b64encode(payload_bytes)}.{tokens._b64encode(signature)}"

    with pytest.raises(tokens.TokenError, match="Malformed"):
        tokens.verify_token(bad_token, expected_purpose="confirm")


def test_b64_helpers_round_trip_without_padding_artifacts():
    for length in range(0, 8):
        data = bytes(range(length))
        assert tokens._b64decode(tokens._b64encode(data)) == data


def test_verify_rejects_invalid_base64_payload():
    with pytest.raises(tokens.TokenError):
        tokens.verify_token("not-valid-base64!!.also-not-valid!!", expected_purpose="confirm")


def test_signature_differs_across_secrets_conceptually():
    # sanity check that two different payloads never collide under the same secret
    token_a = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1)
    token_b = tokens.sign_token(subscription_id=2, purpose="confirm", token_version=1)
    assert token_a != token_b
    sig_a = base64.urlsafe_b64decode(token_a.split(".")[1] + "==")
    sig_b = base64.urlsafe_b64decode(token_b.split(".")[1] + "==")
    assert sig_a != sig_b
