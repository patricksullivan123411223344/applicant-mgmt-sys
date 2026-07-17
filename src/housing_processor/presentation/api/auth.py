"""Supabase JWT verification for staff API authentication."""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from housing_processor.config import Settings

_ASYMMETRIC_ALGS = frozenset({"ES256", "RS256", "EdDSA"})
_DECODE_OPTIONS: dict[str, Any] = {
    "require": ["exp", "sub"],
    "verify_aud": False,
}


class AuthError(Exception):
    """Raised when a bearer token cannot be accepted."""


def auth_bypass_allowed(settings: Settings) -> bool:
    """Local SQLite only: allow AUTH_DISABLED for offline smoke tests."""
    if not settings.auth_disabled:
        return False
    if settings.environment != "local":
        return False
    url = settings.database_url.get_secret_value().lower()
    return url.startswith("sqlite:")


@lru_cache(maxsize=8)
def _jwks_client_for_url(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


def _jwks_url(settings: Settings) -> str:
    base = (settings.supabase_url or "").rstrip("/")
    if not base:
        raise AuthError("SUPABASE_URL is required to verify asymmetric access tokens.")
    return f"{base}/auth/v1/.well-known/jwks.json"


def _validate_claims(claims: dict[str, Any]) -> dict[str, Any]:
    sub = claims.get("sub")
    if not sub:
        raise AuthError("Token missing subject.")
    try:
        UUID(str(sub))
    except ValueError as exc:
        raise AuthError("Token subject is not a valid user id.") from exc

    role = claims.get("role")
    if role not in (None, "authenticated", "service_role"):
        raise AuthError("Token role is not allowed.")

    return claims


def _decode_hs256(token: str, settings: Settings) -> dict[str, Any]:
    secret = settings.supabase_jwt_secret
    if secret is None:
        raise AuthError("SUPABASE_JWT_SECRET is not configured for HS256 tokens.")
    try:
        return jwt.decode(
            token,
            secret.get_secret_value(),
            algorithms=["HS256"],
            options=_DECODE_OPTIONS,
        )
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid or expired access token.") from exc


def _decode_asymmetric(token: str, settings: Settings, algorithms: list[str]) -> dict[str, Any]:
    try:
        client = _jwks_client_for_url(_jwks_url(settings))
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=algorithms,
            options=_DECODE_OPTIONS,
        )
    except AuthError:
        raise
    except jwt.PyJWTError as exc:
        raise AuthError("JWKS verification failed: invalid or expired access token.") from exc
    except Exception as exc:  # network / JWKS fetch errors
        raise AuthError(f"JWKS verification failed: {exc}") from exc


def verify_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    """Verify a Supabase user access token (ES256/RS256 via JWKS, or legacy HS256)."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise AuthError("Malformed access token.") from exc

    alg = str(header.get("alg") or "")
    if alg in _ASYMMETRIC_ALGS:
        claims = _decode_asymmetric(token, settings, algorithms=[alg])
    elif alg == "HS256" or not alg:
        claims = _decode_hs256(token, settings)
    else:
        # Unknown alg: try JWKS first (future-proof), then HS256.
        try:
            claims = _decode_asymmetric(token, settings, algorithms=["ES256", "RS256", "EdDSA"])
        except AuthError:
            claims = _decode_hs256(token, settings)

    return _validate_claims(claims)


def unauthorized(detail: str = "Authentication required.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden(detail: str = "Staff account is inactive.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
