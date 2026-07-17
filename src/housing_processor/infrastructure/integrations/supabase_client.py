"""Optional Supabase client built from Option 1 API credentials."""

from __future__ import annotations

from typing import TYPE_CHECKING

from housing_processor.config import Settings

if TYPE_CHECKING:
    from supabase import Client


def create_supabase_client(settings: Settings) -> Client | None:
    """Return a Supabase client when both Option 1 keys are present; else None."""
    url = (settings.supabase_url or "").strip()
    key = settings.supabase_service_role_key
    if not url or key is None:
        return None
    secret = key.get_secret_value().strip()
    if not secret:
        return None

    from supabase import create_client

    return create_client(url, secret)
