from uuid import UUID

from fastapi import APIRouter, Depends, status

from housing_processor.bootstrap import AppContainer
from housing_processor.presentation.api.contracts.common import PageMeta, PaginatedResponse
from housing_processor.presentation.api.contracts.reviews import ResolveReviewRequest
from housing_processor.presentation.api.dependencies import get_actor_context, get_app_container

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    dependencies=[Depends(get_actor_context)],
)


@router.get("")
def list_reviews(
    limit: int = 50,
    offset: int = 0,
    container: AppContainer = Depends(get_app_container),
) -> PaginatedResponse[dict]:
    _ = container
    return PaginatedResponse(items=[], page=PageMeta(limit=limit, offset=offset, total=0))


@router.get("/{review_item_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def get_review(review_item_id: UUID) -> dict[str, str]:
    return {"detail": f"Review {review_item_id} is not implemented in Phase 1 scaffold."}


@router.post("/{review_item_id}/resolve", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def resolve_review(review_item_id: UUID, body: ResolveReviewRequest) -> dict[str, str]:
    _ = review_item_id, body
    return {"detail": "Review resolution is not implemented in Phase 1 scaffold."}


@router.post("/{review_item_id}/dismiss", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def dismiss_review(review_item_id: UUID) -> dict[str, str]:
    return {"detail": f"Dismiss review {review_item_id} is not implemented in Phase 1 scaffold."}
