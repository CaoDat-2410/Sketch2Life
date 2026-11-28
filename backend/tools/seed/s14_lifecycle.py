"""Create one synthetic export request through the manager's normal command."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.contracts.schemas.be1_runtime import DataRequestCreate
from sketch2life.infrastructure.persistence.be1_models import DataLifecycleRequestModel
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.interfaces.http.routers.be1_records import create_data_request
from tools.seed import data
from tools.seed.stage_common import StageError, StageResult, run_stage_main, seed_principal

ORGANIZATION = data.org_id("a")
ACTOR = data.manager_subject("a")
KEY = "seed:s14:lifecycle:synthetic-export"
EXPECTED = {"lifecycle_requests_s14": 1}


def _query() -> Any:
    return select(DataLifecycleRequestModel).where(
        DataLifecycleRequestModel.organization_id == ORGANIZATION,
        DataLifecycleRequestModel.requested_by == ACTOR,
        DataLifecycleRequestModel.request_type == "export",
        DataLifecycleRequestModel.target_ref == KEY,
    )


def run_s14_lifecycle(engine: Engine) -> StageResult:
    factory = create_core_session_factory(engine)
    try:
        with factory() as session:
            before_count = int(
                session.scalar(select(func.count()).select_from(_query().subquery())) or 0
            )
            if before_count > 1:
                raise StageError("S14_LIFECYCLE_DUPLICATE")
            if not before_count:
                result = create_data_request(
                    ORGANIZATION,
                    DataRequestCreate(request_type="export", target_ref=KEY),
                    seed_principal(ACTOR),
                    session,
                )
                if result.get("state") != "requested":
                    raise StageError("S14_LIFECYCLE_RESULT_UNEXPECTED")
        with factory() as session:
            after_count = int(
                session.scalar(select(func.count()).select_from(_query().subquery())) or 0
            )
        return StageResult(
            "s14_lifecycle", {"lifecycle_requests_s14": before_count},
            {"lifecycle_requests_s14": after_count}, EXPECTED,
        )
    except StageError:
        raise
    except (HTTPException, SQLAlchemyError):
        raise StageError("S14_LIFECYCLE_FAILED") from None


def main() -> int:
    return run_stage_main(run_s14_lifecycle, stage="s14_lifecycle")


if __name__ == "__main__":
    raise SystemExit(main())
