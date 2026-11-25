from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from sketch2life.infrastructure import local_bootstrap

_BACKEND = Path(__file__).resolve().parents[2]


def _script() -> ScriptDirectory:
    config = Config(str(_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND / "alembic"))
    return ScriptDirectory.from_config(config)


def test_bootstrap_revisions_skip_the_legacy_parent_line_and_keep_the_live_heads() -> None:
    revisions = local_bootstrap.bootstrap_revisions(_script())
    assert "20261123_parent_topic_rotation" in revisions
    assert "20261123_rv_0001" in revisions
    assert "20261123_vnpay_cancel" in revisions
    for legacy in (
        "20261110_parent_profiles",
        "20261110_parent_lesson_pin",
        "20261113_parent_consent_policy",
        "20261122_parent_activity_selection",
    ):
        assert legacy not in revisions


def test_identity_upsert_sql_only_touches_the_given_subject() -> None:
    sql, params = local_bootstrap.identity_upsert("uid123", "https://securetoken.google.com/p")
    assert "ON CONFLICT (subject)" in sql
    assert params["subject"] == "uid123" and params["issuer"].endswith("/p")
    assert "uid123" not in sql
