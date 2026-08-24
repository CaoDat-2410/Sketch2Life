"""Infrastructure health endpoint only."""

from typing import Literal, TypedDict

from fastapi import APIRouter


class HealthResponse(TypedDict):
    status: Literal["ok"]
    service: str


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return {"status": "ok", "service": "sketch2life-api"}
