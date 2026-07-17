from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import Header, Request

from housing_processor.application.dto.actor import ActorContext
from housing_processor.bootstrap import AppContainer, build_container
from housing_processor.config import Settings, get_settings
from housing_processor.infrastructure.database.models.staff import StaffProfileModel
from housing_processor.presentation.api.auth import (
    AuthError,
    auth_bypass_allowed,
    forbidden,
    unauthorized,
    verify_supabase_jwt,
)

_DEV_ACTOR_ID = UUID("00000000-0000-4000-8000-000000000001")


def get_app_container(request: Request) -> AppContainer:
    container = getattr(request.app.state, "container", None)
    if container is None:
        container = build_container()
        request.app.state.container = container
    return container


def get_settings_dep() -> Settings:
    return get_settings()


def _ensure_staff_profile(
    *,
    session,
    actor_id: UUID,
    email: str,
) -> StaffProfileModel:
    profile = session.get(StaffProfileModel, actor_id)
    if profile is not None:
        return profile

    now = datetime.now(UTC)
    profile = StaffProfileModel(
        id=actor_id,
        email=email or "",
        display_name=None,
        role="operations",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def get_actor_context(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> ActorContext:
    _ = idempotency_key
    request_id = x_request_id or getattr(request.state, "request_id", None) or str(uuid4())
    request.state.request_id = request_id

    settings = get_settings()
    if auth_bypass_allowed(settings):
        return ActorContext(actor_id=_DEV_ACTOR_ID, role="operations", request_id=request_id)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized()

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise unauthorized()

    try:
        claims = verify_supabase_jwt(token, settings)
    except AuthError as exc:
        raise unauthorized(str(exc)) from exc

    actor_id = UUID(str(claims["sub"]))
    email = str(claims.get("email") or "")
    container = get_app_container(request)
    with container.uow_factory() as uow:
        assert uow.session is not None
        profile = _ensure_staff_profile(session=uow.session, actor_id=actor_id, email=email)
        if not profile.is_active:
            raise forbidden()
        role = profile.role or "operations"

    return ActorContext(actor_id=actor_id, role=role, request_id=request_id)
