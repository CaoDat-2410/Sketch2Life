import json
from pathlib import Path

from learning_video.library import AssetLibrary
from learning_video.resolver import CacheFirstResolver
from learning_video.schemas import LearningObjective, ResolverStatus


ROOT = Path(__file__).parents[1]
OBJECTIVE_PATH = ROOT / "fixtures/objectives/butterfly_proboscis.json"
REVIEWED_PATH = ROOT / "fixtures/reviewed_assets"


def load_objective() -> LearningObjective:
    payload = json.loads(OBJECTIVE_PATH.read_text(encoding="utf-8"))
    return LearningObjective.model_validate(payload)


def test_library_finds_reviewed_asset_by_full_objective_identity() -> None:
    library = AssetLibrary.from_directory(REVIEWED_PATH)

    asset = library.find_reviewed(load_objective())

    assert asset is not None
    assert asset.asset_id == "MV-BUTTERFLY-PROBOSCIS-v1"


def test_resolver_returns_hit_without_generation() -> None:
    resolver = CacheFirstResolver(AssetLibrary.from_directory(REVIEWED_PATH))

    result = resolver.resolve(load_objective())

    assert result.status is ResolverStatus.HIT
    assert result.generation_required is False
    assert result.asset is not None


def test_resolver_returns_miss_for_unknown_objective() -> None:
    objective = load_objective().model_copy(update={"objective_id": "unknown_concept"})
    resolver = CacheFirstResolver(AssetLibrary.from_directory(REVIEWED_PATH))

    result = resolver.resolve(objective)

    assert result.status is ResolverStatus.MISS
    assert result.generation_required is True
    assert result.reason_code == "NO_REVIEWED_ASSET"


def test_resolver_returns_miss_for_version_mismatch() -> None:
    objective = load_objective().model_copy(update={"version": "v2"})
    resolver = CacheFirstResolver(AssetLibrary.from_directory(REVIEWED_PATH))

    result = resolver.resolve(objective)

    assert result.status is ResolverStatus.MISS
    assert result.reason_code == "NO_REVIEWED_ASSET"
