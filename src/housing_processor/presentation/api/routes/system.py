from fastapi import APIRouter, Depends
from pydantic import BaseModel

from housing_processor import __version__
from housing_processor.application.dto.actor import ActorContext
from housing_processor.config import Settings
from housing_processor.presentation.api.auth import auth_bypass_allowed
from housing_processor.presentation.api.dependencies import get_actor_context, get_settings_dep

router = APIRouter(tags=["system"])


class PublicConfigResponse(BaseModel):
    supabase_url: str | None
    supabase_anon_key: str | None
    auth_disabled: bool


@router.get("/public-config", response_model=PublicConfigResponse)
def public_config(settings: Settings = Depends(get_settings_dep)) -> PublicConfigResponse:
    """Unauthenticated bootstrap for the login UI (anon key only — never service role)."""
    anon = None
    if settings.supabase_anon_key is not None:
        anon = settings.supabase_anon_key.get_secret_value()
    return PublicConfigResponse(
        supabase_url=settings.supabase_url,
        supabase_anon_key=anon,
        auth_disabled=auth_bypass_allowed(settings),
    )


@router.get("/system/version")
def system_version(
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, str]:
    _ = actor
    return {"version": __version__}


@router.get("/system/me")
def system_me(actor: ActorContext = Depends(get_actor_context)) -> dict[str, str]:
    return {
        "actor_id": str(actor.actor_id),
        "role": actor.role,
        "request_id": actor.request_id,
    }
