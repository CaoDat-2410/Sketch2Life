"""Seed one original synthetic SVG using the normal teacher catalog command."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.application.services.svg_catalog import SvgCatalogApplicationService
from sketch2life.contracts.schemas.svg_engine import SvgCatalogAssetCreateRequestV1
from sketch2life.infrastructure.catalog.svg_assets import SqlSvgCatalogRepository, SqlSvgSanitizer
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.persistence.svg_catalog_tables import SVG_CATALOG_ASSETS
from sketch2life.infrastructure.storage.s3_compatible import Boto3S3CompatibleObjectStorage
from sketch2life.interfaces.http.routers.svg_catalog import create_organization_asset
from tools.seed import data
from tools.seed.stage_common import StageError, StageResult, run_stage_main, seed_principal

SOURCE = "https://seed.example.test/s14/khu-vuon.svg"
EXPECTED = {"svg_catalog_assets_s14": 1}
PAYLOAD = SvgCatalogAssetCreateRequestV1(
    title_vi="Bông hoa trong vườn",
    topic_key="khu-vuon",
    alt_text_vi="Bông hoa có thân, lá và cánh hoa đơn giản.",
    source_uri=SOURCE,
    license_id="synthetic-demo-original",
    license_uri="https://seed.example.test/s14/synthetic-demo-original",
    source_svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<path d="M50 90 L50 45 M50 70 L30 60 M50 75 L70 60" stroke="#438552" '
    'stroke-width="4" fill="none"/><circle cx="50" cy="35" r="18" fill="#f4aa55"/></svg>',
)


def local_storage() -> Boto3S3CompatibleObjectStorage:
    endpoint = os.environ.get("SKETCH2LIFE_S3_ENDPOINT", "")
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError:
        raise StageError("S14_SVG_STORAGE_NOT_LOCAL") from None
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or port in {5432, 5433, 8000, 55439}
        or parsed.username is not None
        or parsed.password is not None
        or not os.environ.get("SKETCH2LIFE_S3_ACCESS_KEY")
        or not os.environ.get("SKETCH2LIFE_S3_SECRET_KEY")
    ):
        raise StageError("S14_SVG_STORAGE_NOT_LOCAL")
    return Boto3S3CompatibleObjectStorage(
        endpoint_url=endpoint,
        bucket=os.environ.get("SKETCH2LIFE_S3_BUCKET", "sketch2life-private"),
        region_name=os.environ.get("SKETCH2LIFE_S3_REGION", "us-east-1"),
        access_key=os.environ["SKETCH2LIFE_S3_ACCESS_KEY"],
        secret_key=os.environ["SKETCH2LIFE_S3_SECRET_KEY"],
    )


def run_s14_svg(engine: Engine) -> StageResult:
    factory = create_core_session_factory(engine)
    query = select(func.count()).select_from(SVG_CATALOG_ASSETS).where(
        SVG_CATALOG_ASSETS.c.source_uri == SOURCE,
        SVG_CATALOG_ASSETS.c.organization_id == data.org_id("a"),
    )
    try:
        with factory() as session:
            before = int(session.scalar(query) or 0)
            if before > 1:
                raise StageError("S14_SVG_DUPLICATE")
            if not before:
                service = SvgCatalogApplicationService(
                    catalog=SqlSvgCatalogRepository(session, local_storage()),
                    sanitizer=SqlSvgSanitizer(),
                )
                create_organization_asset(
                    data.org_id("a"), PAYLOAD, seed_principal(data.ORG_A_TEACHERS[0]),
                    session, service,
                )
        with factory() as session:
            after = int(session.scalar(query) or 0)
        return StageResult("s14_svg", {"svg_catalog_assets_s14": before},
                           {"svg_catalog_assets_s14": after}, EXPECTED)
    except StageError:
        raise
    except (HTTPException, SQLAlchemyError):
        raise StageError("S14_SVG_FAILED") from None


def main() -> int:
    return run_stage_main(run_s14_svg, stage="s14_svg")


if __name__ == "__main__":
    raise SystemExit(main())
