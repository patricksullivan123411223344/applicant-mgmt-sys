from uuid import UUID, uuid4

from fastapi import Header, Request

from housing_processor.application.dto.actor import ActorContext
from housing_processor.bootstrap import AppContainer, build_container
from housing_processor.config import Settings, get_settings

_DEV_ACTOR_ID = UUID("00000000-0000-4000-8000-000000000001")


def get_app_container(request: Request) -> AppContainer:
    container = getattr(request.app.state, "container", None)
    if container is None:
        container = build_container()
        request.app.state.container = container
    return container


def get_settings_dep() -> Settings:
    return get_settings()


def get_actor_context(
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> ActorContext:
    _ = idempotency_key
    request_id = x_request_id or getattr(request.state, "request_id", None) or str(uuid4())
    request.state.request_id = request_id
    # Phase 3 will replace this with authenticated staff identity.
    return ActorContext(actor_id=_DEV_ACTOR_ID, role="operations", request_id=request_id)
