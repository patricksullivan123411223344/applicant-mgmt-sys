"""External integration adapters (Supabase, email, CRM)."""

from housing_processor.infrastructure.integrations.supabase_client import create_supabase_client

__all__ = ["create_supabase_client"]
