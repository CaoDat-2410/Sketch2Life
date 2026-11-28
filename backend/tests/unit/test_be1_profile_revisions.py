"""FEAT-066 goal v4 T-12b: the pure rules of the Teacher profile revisions (offline)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import unicodedata
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from sketch2life.contracts.schemas.be1_runtime import EditProfileRequest
from sketch2life.domain import be1_profile_revisions as rules
from sketch2life.infrastructure.persistence import be1_models
from sketch2life.infrastructure.persistence.be1_models import (
    ManagedProfileModel,
    ProfileRevisionModel,
)
from sketch2life.interfaces.http.routers import be1_registry

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20261121_bpr_0001_be1_profile_revisions.py"
)


def _migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bpr_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ----------------------------------------------------------------------------- the age band
@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (36, (1, "AGE_36_71")),
        (71, (1, "AGE_36_71")),
        (72, (1, "AGE_72_107")),
        (107, (1, "AGE_72_107")),
        (108, (1, "AGE_108_120")),
        (120, (1, "AGE_108_120")),
        (121, None),
        (155, None),
    ],
)
def test_age_band_boundaries_and_the_quarantined_legacy_age(
    age: int, expected: tuple[int, str] | None
) -> None:
    assert rules.age_band(age) == expected


def test_an_age_below_the_supported_range_is_refused() -> None:
    with pytest.raises(rules.ProfileRevisionRuleViolation) as raised:
        rules.age_band(35)
    assert raised.value.code == "AGE_OUT_OF_RANGE"


# ----------------------------------------------------------------------------- the interests
def test_interests_are_nfc_normalised_trimmed_and_keep_their_order() -> None:
    decomposed = unicodedata.normalize("NFD", "ếch")
    assert decomposed != "ếch"
    assert rules.normalize_interests(["  vẽ tranh ", decomposed, "xếp hình"]) == (
        "vẽ tranh",
        "ếch",
        "xếp hình",
    )
    assert rules.normalize_interests([]) == ()


@pytest.mark.parametrize(
    ("values", "code"),
    [
        ([f"i{n}" for n in range(21)], "TOO_MANY"),
        ([""], "EMPTY"),
        (["   "], "EMPTY"),
        (["x" * 81], "TOO_LONG"),
        (["Đ" * 80 + "Đ"], "TOO_LONG"),
        (["a\nb"], "INVALID_FORMAT"),
        (["a\tb"], "INVALID_FORMAT"),
        (["a\x7fb"], "INVALID_FORMAT"),
        (["a\x85b"], "INVALID_FORMAT"),
        (["a\u2028b"], "INVALID_FORMAT"),
        (["a\u2029b"], "INVALID_FORMAT"),
        (["a\x00b"], "INVALID_FORMAT"),
        (["vẽ", "vẽ"], "DUPLICATE"),
        (["a", " a "], "DUPLICATE"),
    ],
)
def test_interest_bounds(values: list[str], code: str) -> None:
    with pytest.raises(rules.ProfileRevisionRuleViolation) as raised:
        rules.normalize_interests(values)
    assert raised.value.code == code


def test_the_byte_bound_is_checked_apart_from_the_character_bound() -> None:
    # 80 three-byte characters are 240 bytes (allowed); the limit is 320 bytes and 80 characters,
    # so no 80-character value can reach 321 bytes with the BMP, but 80 four-byte characters
    # (320 bytes) is exactly at the limit and still allowed.
    assert rules.normalize_interests(["😀" * 80]) == ("😀" * 80,)
    assert rules.normalize_interests(["a" * 80]) == ("a" * 80,)
    assert len(rules.normalize_interests([f"i{n}" for n in range(20)])) == 20


# ----------------------------------------------------------------------------- the hash
def _hash(**overrides: Any) -> str:
    values: dict[str, Any] = {
        "child_id": "child-1",
        "revision_no": 1,
        "display_name": "Synthetic Mina",
        "age_months": 60,
        "structured_interests": ["vẽ"],
    }
    values.update(overrides)
    return rules.revision_hash(**values)


def test_the_hash_is_a_stable_sha256_of_the_canonical_json() -> None:
    expected = hashlib.sha256(
        json.dumps(
            {
                "domain": "be1.profile.revision",
                "v": 1,
                "child_id": "child-1",
                "revision_no": 1,
                "display_name": "Synthetic Mina",
                "age_months": 60,
                "age_band": {"version": 1, "code": "AGE_36_71"},
                "structured_interests": ["vẽ"],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert _hash() == expected
    assert len(expected) == 64 and expected == expected.lower()
    assert _hash() == _hash()


@pytest.mark.parametrize(
    "change",
    [
        {"child_id": "child-2"},
        {"revision_no": 2},
        {"display_name": "Synthetic Mino"},
        {"age_months": 61},
        {"age_months": 72},
        {"structured_interests": []},
        {"structured_interests": ["vẽ", "hát"]},
        {"structured_interests": ["hát", "vẽ"]},
    ],
)
def test_the_hash_binds_every_field(change: dict[str, Any]) -> None:
    assert _hash(**change) != _hash()


def test_the_canonical_bytes_hold_no_author_and_no_time() -> None:
    text = rules.canonical_revision_bytes(
        child_id="c",
        revision_no=1,
        display_name="Synthetic A",
        age_months=130,
        structured_interests=[],
    ).decode("utf-8")
    assert "authored" not in text and "created" not in text
    assert '"age_band":null' in text


def test_the_baseline_id_is_deterministic_and_per_profile() -> None:
    assert rules.baseline_revision_id("child-1") == rules.baseline_revision_id("child-1")
    assert rules.baseline_revision_id("child-1") != rules.baseline_revision_id("child-2")
    assert len(rules.baseline_revision_id("child-1")) == 36


def test_the_migration_copies_equal_the_domain_functions() -> None:
    migration = _migration()
    for child in ("child-1", "seed-ch-a-1-1", "x" * 128):
        assert migration._baseline_id(child) == rules.baseline_revision_id(child)
    for age in range(36, 156):
        assert migration._band(age) == rules.age_band(age)
        for interests in ([], ["vẽ", "hát"]):
            assert migration._hash(
                "child-1", 3, "Synthetic Mina", age, interests
            ) == rules.revision_hash(
                child_id="child-1",
                revision_no=3,
                display_name="Synthetic Mina",
                age_months=age,
                structured_interests=interests,
            )
    assert migration.LEGACY_AUTHOR == rules.LEGACY_AUTHOR


# ----------------------------------------------------------------------------- the request
def test_the_edit_request_needs_one_field_and_a_revision() -> None:
    ok = EditProfileRequest.model_validate({"expected_revision": 1, "age_months": 60})
    assert ok.model_fields_set == {"expected_revision", "age_months"}
    for body in (
        {"expected_revision": 1},
        {"age_months": 60},
        {"expected_revision": 0, "age_months": 60},
        {"expected_revision": 1, "age_months": 60, "extra": 1},
        {"expected_revision": 1, "age_months": 35},
        {"expected_revision": 1, "age_months": 121},
        {"expected_revision": 1, "display_name": "Mina"},
        {"expected_revision": 1, "display_name": "Synthetic "},
        {"expected_revision": 1, "display_name": None},
        {"expected_revision": 1, "display_name": "Synthetic a\x00b"},
        {"expected_revision": 1, "display_name": "Synthetic a\x85b"},
        {"expected_revision": 1, "display_name": "Synthetic a\u2028b"},
        {"expected_revision": 1, "age_months": None},
        {"expected_revision": 1, "structured_interests": None},
        {"expected_revision": 1, "structured_interests": ["a", "a"]},
        {"expected_revision": 1, "structured_interests": [f"i{n}" for n in range(21)]},
    ):
        with pytest.raises(ValidationError):
            EditProfileRequest.model_validate(body)


def test_the_edit_request_normalises_interests_and_clears_them_with_an_empty_list() -> None:
    parsed = EditProfileRequest.model_validate(
        {"expected_revision": 2, "structured_interests": [" vẽ "], "display_name": "Synthetic A b"}
    )
    assert parsed.structured_interests == ["vẽ"]
    cleared = EditProfileRequest.model_validate(
        {"expected_revision": 2, "structured_interests": []}
    )
    assert cleared.structured_interests == [] and "structured_interests" in cleared.model_fields_set


# ----------------------------------------------------------------------------- receipt helpers
def test_the_receipt_scope_is_hashed_only_when_it_cannot_fit() -> None:
    short = be1_registry._edit_receipt_scope("o", "c", "k")
    assert short == "PATCH /organizations/o/classes/c/profiles/k"
    long_scope = be1_registry._edit_receipt_scope("o" * 128, "c" * 128, "k" * 128)
    assert len(long_scope) <= 256 and "#" in long_scope
    assert long_scope != be1_registry._edit_receipt_scope("o" * 128, "c" * 128, "j" * 128)


def test_the_edit_fingerprint_binds_actor_scope_revision_and_patch() -> None:
    base: dict[str, Any] = {
        "key": b"k" * 32,
        "principal_ref": "p1",
        "scope": "s1",
        "expected_revision": 1,
        "patch": {"age_months": 60},
    }
    fingerprint = be1_registry._edit_fingerprint(**base)
    assert len(fingerprint) == 64 and fingerprint == be1_registry._edit_fingerprint(**base)
    for change in (
        {"key": b"j" * 32},
        {"principal_ref": "p2"},
        {"scope": "s2"},
        {"expected_revision": 2},
        {"patch": {"age_months": 61}},
        {"patch": {"age_months": 60, "structured_interests": []}},
    ):
        assert be1_registry._edit_fingerprint(**{**base, **change}) != fingerprint


# ----------------------------------------------------------------------------- the listener
def _profile(**overrides: Any) -> ManagedProfileModel:
    values: dict[str, Any] = {
        "child_id": "child-listener",
        "organization_id": "o",
        "class_id": "c",
        "display_name": "Synthetic Listener",
        "age_months": 60,
        "age_source": "SYNTHETIC_FIXTURE",
        "data_origin": "SYNTHETIC_DEV",
        "created_by": "creator-1",
    }
    values.update(overrides)
    return ManagedProfileModel(**values)


def test_a_new_profile_gets_its_baseline_revision_and_head_before_the_flush() -> None:
    session = Session()
    profile = _profile()
    session.add(profile)
    be1_models._attach_baseline_revisions(session)
    revisions = [obj for obj in session.new if isinstance(obj, ProfileRevisionModel)]
    assert len(revisions) == 1
    revision = revisions[0]
    assert profile.current_profile_revision_id == revision.profile_revision_id
    assert profile.profile_revision_no == 1 and revision.revision_no == 1
    assert revision.profile_revision_id == rules.baseline_revision_id("child-listener")
    assert (revision.display_name, revision.age_months) == ("Synthetic Listener", 60)
    assert (revision.age_band_version, revision.age_band_code) == (1, "AGE_36_71")
    assert revision.structured_interests == [] and revision.authored_by == "creator-1"
    assert revision.revision_hash == rules.revision_hash(
        child_id="child-listener",
        revision_no=1,
        display_name="Synthetic Listener",
        age_months=60,
        structured_interests=[],
    )
    be1_models._attach_baseline_revisions(session)  # a second call adds nothing
    assert len([obj for obj in session.new if isinstance(obj, ProfileRevisionModel)]) == 1


def test_a_profile_that_already_has_a_head_is_left_alone() -> None:
    session = Session()
    session.add(_profile(current_profile_revision_id="rev-x", profile_revision_no=4))
    be1_models._attach_baseline_revisions(session)
    assert not [obj for obj in session.new if isinstance(obj, ProfileRevisionModel)]


def test_a_legacy_over_age_profile_gets_a_baseline_without_a_band() -> None:
    session = Session()
    session.add(_profile(child_id="child-old", age_months=130))
    be1_models._attach_baseline_revisions(session)
    revision = next(obj for obj in session.new if isinstance(obj, ProfileRevisionModel))
    assert revision.age_band_version is None and revision.age_band_code is None
