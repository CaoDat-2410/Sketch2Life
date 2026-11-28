"""Translate transport-neutral profile-sharing failures at the HTTP boundary."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NoReturn

from fastapi import HTTPException

from sketch2life.domain.profile_sharing import (
    ProfileShareConflict,
    ProfileShareError,
    ProfileShareInvalidRequest,
    ProfileShareNotFound,
    ProfileShareStaleRevision,
    ProfileShareUnavailable,
)


def _raise_profile_share_http_error(error: ProfileShareError) -> NoReturn:
    if isinstance(error, ProfileShareNotFound):
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"}) from error
    if isinstance(error, ProfileShareInvalidRequest):
        detail: dict[str, object] = {"code": error.code}
        if error.field_errors:
            detail["field_errors"] = error.field_errors
        raise HTTPException(status_code=400, detail=detail) from error
    if isinstance(error, ProfileShareStaleRevision):
        current_version = error.current_version
        raise HTTPException(
            status_code=409,
            detail={"code": error.code, "current_version": current_version},
            headers={"ETag": f'"{current_version}"'},
        ) from error
    if isinstance(error, ProfileShareConflict):
        raise HTTPException(status_code=409, detail={"code": error.code}) from error
    if isinstance(error, ProfileShareUnavailable):
        raise HTTPException(status_code=503, detail={"code": error.code}) from error
    raise error


def call_profile_share_service[T](function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    try:
        return function(*args, **kwargs)
    except ProfileShareError as error:
        _raise_profile_share_http_error(error)


__all__ = ["call_profile_share_service"]
