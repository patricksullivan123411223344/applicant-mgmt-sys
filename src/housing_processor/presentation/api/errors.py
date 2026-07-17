from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from housing_processor.domain.shared.errors import (
    ContactMustBeGroupMemberError,
    DomainError,
    DuplicateGroupMemberError,
    InvalidStatusTransitionError,
    ResourceNotFoundError,
    VersionConflictError,
)
from housing_processor.presentation.api.contracts.common import ErrorDetail, ErrorResponse

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    ResourceNotFoundError: 404,
    VersionConflictError: 409,
    InvalidStatusTransitionError: 409,
    DuplicateGroupMemberError: 409,
    ContactMustBeGroupMemberError: 422,
}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get(
        "X-Request-Id", "unknown"
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status = _STATUS_BY_ERROR.get(type(exc), 400)
        body = ErrorResponse(
            request_id=_request_id(request),
            errors=[
                ErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    context=exc.context,
                )
            ],
        )
        return JSONResponse(status_code=status, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        _ = exc
        body = ErrorResponse(
            request_id=_request_id(request),
            errors=[
                ErrorDetail(
                    code="system.internal_error",
                    message="An unexpected error occurred.",
                )
            ],
        )
        return JSONResponse(status_code=500, content=body.model_dump())
