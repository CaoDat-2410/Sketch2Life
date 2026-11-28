"""BE1 Manager metadata read and emergency Teacher StoryRun force-close routes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_force_close import (
    ManagerStoryRunForceClosed,
    ManagerStoryRunForceCloseFailure,
)
from sketch2life.application.services.manager_story_run_force_close import (
    ManagerStoryRunForceCloseService,
)
from sketch2life.contracts.schemas.manager_story_run_force_close import (
    ManagerActiveStoryRunConflictV1,
    ManagerForceClosedStoryRunV1,
    ManagerForceCloseStoryRunRequestV1,
)
from sketch2life.infrastructure.persistence.manager_story_run_scope import (
    SqlManagerStoryRunScope,
)
from sketch2life.infrastructure.story_teacher.manager_story_run_force_close_repository import (
    SqlManagerStoryRunForceCloseRepository,
)
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import BE1_ERROR_RESPONSES, failure

_PRIVATE_NO_STORE = {"Cache-Control": "private, no-store"}


class _PrivateNoStoreRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original_handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                response = await original_handler(request)
            except RequestValidationError:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_REQUEST"},
                    headers=_PRIVATE_NO_STORE,
                ) from None
            except HTTPException as exc:
                headers = dict(exc.headers or {})
                headers.update(_PRIVATE_NO_STORE)
                raise HTTPException(
                    status_code=exc.status_code,
                    detail=exc.detail,
                    headers=headers,
                ) from None
            response.headers.update(_PRIVATE_NO_STORE)
            return response

        return handle


router = APIRouter(
    prefix="/api/be1/v1",
    tags=["BE1 registry"],
    responses=BE1_ERROR_RESPONSES,
    route_class=_PrivateNoStoreRoute,
)


def _service(db: Session) -> ManagerStoryRunForceCloseService:
    scope = SqlManagerStoryRunScope(db)
    return ManagerStoryRunForceCloseService(
        scope=scope,
        repository=SqlManagerStoryRunForceCloseRepository(db),
    )


def _parse_key(request: Request) -> str:
    try:
        return parse_idempotency_key(request)
    except HTTPException as exc:
        headers = dict(exc.headers or {})
        headers.update(_PRIVATE_NO_STORE)
        raise HTTPException(
            status_code=400,
            detail=exc.detail,
            headers=headers,
        ) from None


def _raise_failure(
    error: ManagerStoryRunForceCloseFailure,
) -> NoReturn:
    if error.code == "STALE_REVISION" and type(error.current_version) is int:
        raise HTTPException(
            status_code=409,
            detail={"code": "STALE_REVISION", "current_version": error.current_version},
            headers=_PRIVATE_NO_STORE,
        ) from None
    raise failure(
        error.status_code,
        error.code,
        "The requested StoryRun operation could not be completed",
        headers=_PRIVATE_NO_STORE,
    ) from None


@router.get(
    "/organizations/{organization_id}/teachers/{teacher_ref}/active-story-run-conflict",
    response_model=ManagerActiveStoryRunConflictV1,
    responses={200: {"model": ManagerActiveStoryRunConflictV1}},
)
def get_manager_active_story_run_conflict(
    organization_id: str,
    teacher_ref: str,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ManagerActiveStoryRunConflictV1:
    response.headers.update(_PRIVATE_NO_STORE)
    try:
        conflict = _service(db).get_active_conflict(
            principal_subject=principal.subject,
            principal_issuer=principal.issuer,
            organization_id=organization_id,
            teacher_ref=teacher_ref,
        )
    except ManagerStoryRunForceCloseFailure as exc:
        _raise_failure(exc)
    return ManagerActiveStoryRunConflictV1(
        run_id=conflict.run_id,
        run_state=conflict.run_state,
        revision=conflict.revision,
    )


@router.post(
    "/organizations/{organization_id}/story-runs/{run_id}/force-close",
    response_model=ManagerForceClosedStoryRunV1,
    responses={200: {"model": ManagerForceClosedStoryRunV1}},
)
def force_close_manager_story_run(
    organization_id: str,
    run_id: str,
    request: Request,
    payload: ManagerForceCloseStoryRunRequestV1,
    response: Response,
    idempotency_key_header: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=1,
            max_length=128,
            description="Required; 1–128 visible ASCII characters.",
        ),
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ManagerForceClosedStoryRunV1:
    response.headers.update(_PRIVATE_NO_STORE)
    idempotency_key = _parse_key(request)

    try:
        result: ManagerStoryRunForceClosed = _service(db).force_close(
            principal_subject=principal.subject,
            principal_issuer=principal.issuer,
            organization_id=organization_id,
            run_id=run_id,
            expected_revision=payload.expected_revision,
            reason=payload.reason,
            idempotency_key=idempotency_key,
        )
    except ManagerStoryRunForceCloseFailure as exc:
        _raise_failure(exc)
    return ManagerForceClosedStoryRunV1(
        run_id=result.run_id,
        run_state="ABANDONED",
        revision=result.revision,
    )


__all__ = ["router"]
