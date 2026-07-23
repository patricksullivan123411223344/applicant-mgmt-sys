from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from housing_processor.bootstrap import AppContainer
from housing_processor.domain.shared.identifiers import ApplicantId
from housing_processor.presentation.api.contracts.common import PageMeta, PaginatedResponse
from housing_processor.presentation.api.dependencies import get_actor_context, get_app_container

router = APIRouter(
    prefix="/applicants",
    tags=["applicants"],
    dependencies=[Depends(get_actor_context)],
)


@router.get("")
def list_applicants(
    limit: int = 50,
    offset: int = 0,
    container: AppContainer = Depends(get_app_container),
) -> PaginatedResponse[dict]:
    _ = container
    return PaginatedResponse(items=[], page=PageMeta(limit=limit, offset=offset, total=0))


@router.get("/{applicant_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def get_applicant(applicant_id: UUID) -> dict[str, str]:
    return {"detail": f"Applicant {applicant_id} detail is not implemented in Phase 1 scaffold."}


@router.delete("/{applicant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_applicant(
    applicant_id: UUID,
    container: AppContainer = Depends(get_app_container),
) -> Response:
    container.delete_applicant_handler.handle(ApplicantId(applicant_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
