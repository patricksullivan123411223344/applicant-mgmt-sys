"""Unit tests for Supabase JWT auth helpers."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from pydantic import SecretStr

from housing_processor.config import Settings
from housing_processor.presentation.api import auth as auth_module
from housing_processor.presentation.api.auth import (
    AuthError,
    auth_bypass_allowed,
    verify_supabase_jwt,
)


def _settings(**kwargs) -> Settings:
    base = {
        "environment": "local",
        "database_url": SecretStr("sqlite:///./data/test.db"),
        "auth_disabled": False,
        "supabase_url": "https://example.supabase.co",
        "supabase_jwt_secret": SecretStr("test-jwt-secret-value-32chars!!!"),
    }
    base.update(kwargs)
    return Settings(**base)


def test_auth_bypass_only_for_local_sqlite() -> None:
    assert auth_bypass_allowed(
        _settings(auth_disabled=True, environment="local", database_url=SecretStr("sqlite:///./x.db"))
    )
    assert not auth_bypass_allowed(
        _settings(
            auth_disabled=True,
            environment="production",
            database_url=SecretStr("sqlite:///./x.db"),
        )
    )
    assert not auth_bypass_allowed(
        _settings(
            auth_disabled=True,
            environment="local",
            database_url=SecretStr("postgresql+psycopg://u:p@h/db"),
        )
    )
    assert not auth_bypass_allowed(_settings(auth_disabled=False))


def test_verify_supabase_jwt_accepts_valid_hs256_token() -> None:
    user_id = str(uuid4())
    token = jwt.encode(
        {"sub": user_id, "role": "authenticated", "exp": 4102444800},
        "test-jwt-secret-value-32chars!!!",
        algorithm="HS256",
    )
    claims = verify_supabase_jwt(token, _settings())
    assert claims["sub"] == user_id


def test_verify_supabase_jwt_rejects_bad_hs256_signature() -> None:
    token = jwt.encode(
        {"sub": str(uuid4()), "role": "authenticated", "exp": 4102444800},
        "wrong-secret-also-long-enough!!!",
        algorithm="HS256",
    )
    with pytest.raises(AuthError):
        verify_supabase_jwt(token, _settings())


def test_verify_supabase_jwt_accepts_es256_via_jwks() -> None:
    user_id = str(uuid4())
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    token = jwt.encode(
        {"sub": user_id, "role": "authenticated", "email": "a@b.co", "exp": 4102444800},
        private_key,
        algorithm="ES256",
        headers={"kid": "test-kid"},
    )

    mock_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_client.get_signing_key_from_jwt.return_value = mock_signing_key

    with patch.object(auth_module, "_jwks_client_for_url", return_value=mock_client):
        claims = verify_supabase_jwt(token, _settings())

    assert claims["sub"] == user_id
    mock_client.get_signing_key_from_jwt.assert_called_once_with(token)


def test_verify_supabase_jwt_es256_requires_supabase_url() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(
        {"sub": str(uuid4()), "role": "authenticated", "exp": 4102444800},
        private_key,
        algorithm="ES256",
        headers={"kid": "test-kid"},
    )
    with pytest.raises(AuthError, match="SUPABASE_URL"):
        verify_supabase_jwt(token, _settings(supabase_url=None))
