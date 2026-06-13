from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import settings
from app.services.auth_service import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_correct_password_verifies() -> None:
    hashed = hash_password("qwerty123")
    assert verify_password("qwerty123", hashed) is True


def test_wrong_password_does_not_verify() -> None:
    hashed = hash_password("qwerty123")
    assert verify_password("wrong", hashed) is False


def test_two_hashes_of_same_password_differ() -> None:
    assert hash_password("qwerty123") != hash_password("qwerty123")


# ---------------------------------------------------------------------------
# Token creation and decoding
# ---------------------------------------------------------------------------


def test_access_token_decodes_correct_user_id() -> None:
    token = create_access_token("user-abc")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc"


def test_refresh_token_decodes_correct_user_id() -> None:
    token = create_refresh_token("user-abc")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc"


def test_access_token_contains_exp_and_iat() -> None:
    token = create_access_token("user-abc")
    payload = decode_token(token)
    assert "exp" in payload
    assert "iat" in payload


def test_access_and_refresh_tokens_differ() -> None:
    access = create_access_token("user-abc")
    refresh = create_refresh_token("user-abc")
    assert access != refresh


def test_expired_token_raises() -> None:
    expired_payload = {
        "sub": "user-abc",
        "exp": datetime.now(UTC) - timedelta(seconds=1),
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(expired_payload, settings.JWT_SECRET, algorithm=ALGORITHM)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_tampered_token_raises() -> None:
    token = create_access_token("user-abc")
    tampered = token[:-3] + "123"
    with pytest.raises(jwt.PyJWTError):
        decode_token(tampered)


def test_wrong_secret_raises() -> None:
    payload = {
        "sub": "user-abc",
        "exp": datetime.now(UTC) + timedelta(minutes=15),
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, "wrong-secret", algorithm=ALGORITHM)
    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(token)


def test_garbage_string_raises() -> None:
    with pytest.raises(jwt.PyJWTError):
        decode_token("not.a.valid.token")


def test_empty_string_raises() -> None:
    with pytest.raises(jwt.PyJWTError):
        decode_token("")
