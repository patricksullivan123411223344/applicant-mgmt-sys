from pydantic import BaseModel, Field


class PageMeta(BaseModel):
    limit: int
    offset: int
    total: int


class PaginatedResponse[T](BaseModel):
    items: list[T]
    page: PageMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    context: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    request_id: str
    errors: list[ErrorDetail]
