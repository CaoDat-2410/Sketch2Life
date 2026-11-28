"""FEAT-066 goal v4 T-12c: the encrypted support needs, offline (domain, cipher, schemas, guards).

SRS l.264 BR-20, l.499 FR-C-07, l.932, l.1922, l.2338. The cipher under test is the real
AES-256-GCM adapter (owner decision of 2026-11-23: no standard-library fake). Keys here are fixed
synthetic bytes; nothing is read from the environment. PostgreSQL behaviour is in
``tests/integration/test_support_needs_postgres.py``.
"""

from __future__ import annotations

import hashlib
import itertools
import re
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.support_needs import (
    SealedSupportNeeds,
    SupportNeedsUnavailable,
)
from sketch2life.contracts.schemas.be1_runtime import Be1SupportNeedsPutV1
from sketch2life.contracts.schemas.parent_profiles import SupportNeedsPutV1, parent_field_errors
from sketch2life.domain import support_needs as rules
from sketch2life.domain.support_needs import (
    SupportNeedsPayload,
    SupportNeedsRuleViolation,
    build_aad,
    check_revision,
    fingerprint_message,
    parse_plaintext,
    validate_payload,
)
from sketch2life.infrastructure.security.support_needs_crypto import (
    AesGcmSupportNeedsCrypto,
    StaticSupportNeedsKeyring,
    secure_nonce,
)
from sketch2life.interfaces.http.api_conventions import field_errors_from_validation

BACKEND = Path(__file__).resolve().parents[2]
SRC = BACKEND / "src" / "sketch2life"
SENTINEL = "SENTINEL-support-note-7f3a91c2"
ENC_1 = bytes(range(32))
ENC_2 = bytes(range(100, 132))
FP_1 = bytes(range(200, 232))
FP_2 = bytes(reversed(range(200, 232)))
PROFILE = "7b1c2f0e-6d6a-4c53-9a4b-0f0c0d0e0a01"
OTHER_PROFILE = "7b1c2f0e-6d6a-4c53-9a4b-0f0c0d0e0a02"


def keyring(**changes: object) -> StaticSupportNeedsKeyring:
    arguments: dict[str, object] = {
        "encryption_keys": {"enc-1": ENC_1, "enc-2": ENC_2},
        "current_key_id": "enc-1",
        "fingerprint_keys": {"fp-1": FP_1, "fp-2": FP_2},
        "current_fingerprint_key_id": "fp-1",
    }
    arguments.update(changes)
    return StaticSupportNeedsKeyring(**arguments)  # type: ignore[arg-type]


def counter_nonce() -> object:
    counter = itertools.count(1)
    return lambda: next(counter).to_bytes(rules.NONCE_BYTES, "big")


def crypto(**changes: object) -> AesGcmSupportNeedsCrypto:
    nonce = changes.pop("nonce_source", secure_nonce)
    return AesGcmSupportNeedsCrypto(keyring(**changes), nonce)  # type: ignore[arg-type]


PAYLOAD = SupportNeedsPayload(category="sensory", note=SENTINEL)


def seal(c: AesGcmSupportNeedsCrypto, **changes: object) -> SealedSupportNeeds:
    arguments: dict[str, object] = {
        "family": "parent",
        "tenant": "",
        "profile_id": PROFILE,
        "revision": 1,
        "payload": PAYLOAD,
    }
    arguments.update(changes)
    return c.seal(**arguments)  # type: ignore[arg-type]


def open_(c: AesGcmSupportNeedsCrypto, sealed: SealedSupportNeeds, **changes: object) -> object:
    arguments: dict[str, object] = {
        "family": "parent",
        "tenant": "",
        "profile_id": PROFILE,
        "revision": 1,
        "sealed": sealed,
    }
    arguments.update(changes)
    return c.open(**arguments)  # type: ignore[arg-type]


# --------------------------------------------------------------------- payload bounds
def test_the_payload_is_kept_exactly_as_sent() -> None:
    payload = validate_payload("  tactile ", "Line one\n\tline two  ")
    assert payload.category == "  tactile " and payload.note == "Line one\n\tline two  "
    assert validate_payload(None, "only a note").category is None
    assert validate_payload("only a category", None).note is None


@pytest.mark.parametrize(
    ("category", "note", "field", "code"),
    [
        (None, None, "note", "REQUIRED"),
        ("", None, "category", "EMPTY"),
        ("   ", "ok", "category", "EMPTY"),
        (None, "\n\t ", "note", "EMPTY"),
        ("x" * 81, None, "category", "TOO_LONG"),
        ("\U0001f600" * 81, None, "category", "TOO_LONG"),
        (None, "y" * 2001, "note", "TOO_LONG"),
        (None, "\U0001f600" * 2001, "note", "TOO_LONG"),
        ("bad\x00nul", None, "category", "INVALID_FORMAT"),
        ("bad\x07bell", None, "category", "INVALID_FORMAT"),
        (None, "bad\x7fdel", "note", "INVALID_FORMAT"),
        (None, "bad\x1bescape", "note", "INVALID_FORMAT"),
    ],
)
def test_bounds_and_controls_are_refused_with_a_field_and_a_code(
    category: str | None, note: str | None, field: str, code: str
) -> None:
    with pytest.raises(SupportNeedsRuleViolation) as caught:
        validate_payload(category, note)
    assert (caught.value.field, caught.value.code) == (field, code)
    assert SENTINEL not in str(caught.value)


def test_the_upper_limits_are_accepted_in_characters_and_bytes() -> None:
    validate_payload("c" * 80, "n" * 2000)
    validate_payload("\U0001f600" * 80, "\U0001f600" * 2000)  # 320 and 8000 bytes
    sealed = seal(crypto(), payload=validate_payload("\U0001f600" * 80, "\U0001f600" * 2000))
    assert len(sealed.ciphertext) <= rules.MAX_CIPHERTEXT_BYTES


def test_there_is_no_diagnosis_field_or_inference_in_the_domain() -> None:
    source = (SRC / "domain" / "support_needs.py").read_text(encoding="utf-8").lower()
    for banned in ("diagnos", "classify", "infer(", "predict"):
        cleaned = (
            source.replace("not a diagnosis", "")
            .replace("diagnosis and", "")
            .replace("domain.diagnosis_screen", "")
            .replace("looks_like_diagnosis", "")  # the BR-20 input screen refuses diagnoses
            .replace("diagnosis_like", "")
            .replace("names a diagnosis", "")
        )
        assert banned not in cleaned


@pytest.mark.parametrize("value", [0, 1, 5, rules.MAX_REVISION])
def test_revision_zero_is_an_expected_revision_only(value: int) -> None:
    assert check_revision(value, allow_zero=True) == value


@pytest.mark.parametrize("value", [-1, rules.MAX_REVISION + 1, True, 1.0, "1"])
def test_revision_overflow_negative_and_wrong_types_are_refused(value: object) -> None:
    with pytest.raises(SupportNeedsRuleViolation):
        check_revision(value, allow_zero=True)  # type: ignore[arg-type]


def test_a_stored_revision_is_never_zero() -> None:
    with pytest.raises(SupportNeedsRuleViolation):
        check_revision(0, allow_zero=False)


def test_the_canonical_plaintext_round_trips_and_a_foreign_shape_fails() -> None:
    assert parse_plaintext(PAYLOAD.plaintext()) == PAYLOAD
    assert SupportNeedsPayload(None, "é").plaintext() == '{"category":null,"note":"é"}'.encode()
    for raw in (b"not json", b"[]", b'{"category":1,"note":null}', b'{"note":"x"}', b"\xff"):
        with pytest.raises(SupportNeedsRuleViolation):
            parse_plaintext(raw)


# --------------------------------------------------------------------- request schemas
def _bodies() -> list[dict[str, object]]:
    return [
        {"expected_revision": 0, "category": f"x\x00{SENTINEL}", "note": None},
        {"expected_revision": 0, "category": None, "note": SENTINEL * 80},
        {"expected_revision": 0, "category": "  ", "note": SENTINEL},
        {"expected_revision": 0, "category": SENTINEL},
        {"expected_revision": 0, "category": None, "note": None},
        {"expected_revision": 0, "category": None, "note": SENTINEL, "extra": SENTINEL},
        {"expected_revision": "0", "category": None, "note": SENTINEL},
        {"expected_revision": -1, "category": None, "note": SENTINEL},
    ]


@pytest.mark.parametrize("model", [SupportNeedsPutV1, Be1SupportNeedsPutV1])
def test_both_request_models_refuse_bad_bodies_without_echoing_a_value(model: type) -> None:
    for body in _bodies():
        with pytest.raises(ValidationError) as caught:
            model.model_validate(body)
        errors = caught.value.errors()
        assert errors
        parent = parent_field_errors(errors)
        assert SENTINEL not in str(parent) and SENTINEL not in str(
            field_errors_from_validation(None, errors)
        )
        assert all(item["code"] for item in parent)


@pytest.mark.parametrize("model", [SupportNeedsPutV1, Be1SupportNeedsPutV1])
def test_both_request_models_need_every_key_and_keep_text_unstripped(model: type) -> None:
    ok = model.model_validate({"expected_revision": 3, "category": " a ", "note": None})
    assert ok.category == " a " and ok.note is None and ok.expected_revision == 3
    for missing in ("expected_revision", "category", "note"):
        body = {"expected_revision": 0, "category": None, "note": "n"}
        del body[missing]
        with pytest.raises(ValidationError):
            model.model_validate(body)
    schema = model.model_json_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"expected_revision", "category", "note"}


def test_the_field_error_codes_of_the_two_vocabularies() -> None:
    for model in (SupportNeedsPutV1, Be1SupportNeedsPutV1):
        with pytest.raises(ValidationError) as caught:
            model.model_validate({"expected_revision": 0, "category": "x" * 90, "note": "\x00"})
        by_field = {
            item["field"]: item["code"] for item in parent_field_errors(caught.value.errors())
        }
        assert by_field == {"category": "TOO_LONG", "note": "INVALID_FORMAT"}


# --------------------------------------------------------------------- associated data
def test_the_aad_binds_every_identity_field_and_is_length_delimited() -> None:
    base = {
        "family": "be1",
        "tenant": "org-1",
        "profile_id": "child-1",
        "revision": 4,
        "key_id": "enc-1",
        "algorithm_version": 1,
    }
    reference = build_aad(**base)  # type: ignore[arg-type]
    assert reference == build_aad(**base)  # type: ignore[arg-type]
    changes: dict[str, object] = {
        "family": "parent",
        "tenant": "org-2",
        "profile_id": "child-2",
        "revision": 5,
        "key_id": "enc-2",
        "algorithm_version": 2,
    }
    for field, value in changes.items():
        assert build_aad(**{**base, field: value}) != reference, field  # type: ignore[arg-type]
    # the length prefix keeps field boundaries: ("ab", "c") is not ("a", "bc")
    assert build_aad(**{**base, "tenant": "ab", "profile_id": "c"}) != build_aad(  # type: ignore[arg-type]
        **{**base, "tenant": "a", "profile_id": "bc"}  # type: ignore[arg-type]
    )


# --------------------------------------------------------------------- the real cipher
def test_the_cipher_round_trips_and_the_ciphertext_holds_no_plaintext() -> None:
    c = crypto()
    sealed = seal(c)
    assert sealed.algorithm_version == 1 and sealed.key_id == "enc-1"
    assert len(sealed.nonce) == 12 and len(sealed.ciphertext) >= 16
    for fragment in (SENTINEL.encode(), b"sensory", b"category", b"note"):
        assert fragment not in sealed.ciphertext
    assert open_(c, sealed) == PAYLOAD


def test_every_encryption_uses_a_fresh_nonce_and_a_fresh_ciphertext() -> None:
    c = crypto()
    first, second = seal(c), seal(c)
    assert first.nonce != second.nonce and first.ciphertext != second.ciphertext
    nonces = {seal(c).nonce for _ in range(500)}
    assert len(nonces) == 500


def test_a_counter_nonce_source_is_deterministic_and_never_repeats() -> None:
    c = crypto(nonce_source=counter_nonce())
    nonces = [seal(c).nonce for _ in range(3)]
    assert nonces == [(n).to_bytes(12, "big") for n in (1, 2, 3)]
    short = AesGcmSupportNeedsCrypto(keyring(), lambda: b"\x00" * 8)
    with pytest.raises(SupportNeedsUnavailable):
        seal(short)


def test_tampering_fails_closed_for_ciphertext_nonce_and_tag() -> None:
    c = crypto()
    sealed = seal(c)
    flipped = bytearray(sealed.ciphertext)
    flipped[0] ^= 1
    tag_flipped = bytearray(sealed.ciphertext)
    tag_flipped[-1] ^= 1
    nonce_flipped = bytearray(sealed.nonce)
    nonce_flipped[0] ^= 1
    for bad in (
        SealedSupportNeeds(bytes(flipped), sealed.nonce, sealed.key_id, 1),
        SealedSupportNeeds(bytes(tag_flipped), sealed.nonce, sealed.key_id, 1),
        SealedSupportNeeds(sealed.ciphertext, bytes(nonce_flipped), sealed.key_id, 1),
        SealedSupportNeeds(sealed.ciphertext[:-1], sealed.nonce, sealed.key_id, 1),
        SealedSupportNeeds(b"", sealed.nonce, sealed.key_id, 1),
    ):
        with pytest.raises(SupportNeedsUnavailable):
            open_(c, bad)


@pytest.mark.parametrize(
    "wrong",
    [
        {"profile_id": OTHER_PROFILE},
        {"revision": 2},
        {"family": "be1"},
        {"tenant": "org-9"},
    ],
)
def test_a_ciphertext_opens_only_for_its_own_record(wrong: dict[str, object]) -> None:
    c = crypto()
    sealed = seal(c)
    with pytest.raises(SupportNeedsUnavailable):
        open_(c, sealed, **wrong)


def test_a_relabelled_key_or_version_or_a_missing_key_fails_closed() -> None:
    c = crypto()
    sealed = seal(c)
    for bad in (
        SealedSupportNeeds(sealed.ciphertext, sealed.nonce, "enc-2", 1),  # another real key
        SealedSupportNeeds(sealed.ciphertext, sealed.nonce, "enc-9", 1),  # unknown key id
        SealedSupportNeeds(sealed.ciphertext, sealed.nonce, sealed.key_id, 2),  # unknown version
    ):
        with pytest.raises(SupportNeedsUnavailable):
            open_(c, bad)
    # a ciphertext sealed by a keyring that has rotated away its key cannot be opened
    rotated = AesGcmSupportNeedsCrypto(
        keyring(encryption_keys={"enc-2": ENC_2}, current_key_id="enc-2")
    )
    with pytest.raises(SupportNeedsUnavailable):
        open_(rotated, sealed)
    # and an older key id still opens after a rotation that keeps it
    both = AesGcmSupportNeedsCrypto(keyring(current_key_id="enc-2"))
    assert open_(both, sealed) == PAYLOAD
    assert seal(both).key_id == "enc-2"


def test_the_two_families_never_share_an_encryption_key() -> None:
    ring = keyring()
    assert ring.encryption_key("parent", "enc-1") != ring.encryption_key("be1", "enc-1")
    assert ring.encryption_key("parent", "enc-1") != ENC_1
    assert ring.fingerprint_key("parent", "fp-1") != ring.fingerprint_key("be1", "fp-1")
    assert ring.encryption_key("parent", "missing") is None
    # a Parent ciphertext does not open as a BE1 one even with every other field equal
    c = AesGcmSupportNeedsCrypto(ring)
    sealed = seal(c, family="parent", tenant="")
    with pytest.raises(SupportNeedsUnavailable):
        open_(c, sealed, family="be1", tenant="")


@pytest.mark.parametrize(
    "changes",
    [
        {"current_key_id": "missing"},
        {"current_fingerprint_key_id": "missing"},
        {"encryption_keys": {"enc-1": b"short"}},
        {"fingerprint_keys": {"fp-1": b"short"}, "current_fingerprint_key_id": "fp-1"},
        {"encryption_keys": {"enc 1": ENC_1}, "current_key_id": "enc 1"},
        {"fingerprint_keys": {"fp-1": ENC_1}},  # the MAC key may not equal an encryption key
    ],
)
def test_a_malformed_keyring_is_refused(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        keyring(**changes)


# --------------------------------------------------------------------- the receipt MAC
def _fingerprint(c: AesGcmSupportNeedsCrypto, **changes: object) -> bytes:
    arguments: dict[str, object] = {
        "family": "parent",
        "tenant": "",
        "profile_id": PROFILE,
        "principal": "actor-1",
        "expected_revision": 0,
        "payload": PAYLOAD,
    }
    arguments.update(changes)
    return c.fingerprint(**arguments)  # type: ignore[arg-type]


def test_the_fingerprint_is_a_keyed_scoped_32_byte_mac() -> None:
    c = crypto()
    reference = _fingerprint(c)
    assert len(reference) == 32 and reference == _fingerprint(c)
    variants: dict[str, object] = {
        "family": "be1",
        "tenant": "org-1",
        "profile_id": OTHER_PROFILE,
        "principal": "actor-2",
        "expected_revision": 1,
        "payload": SupportNeedsPayload("sensory", SENTINEL + "!"),
    }
    for field, value in variants.items():
        assert _fingerprint(c, **{field: value}) != reference, field
    assert _fingerprint(c, payload=SupportNeedsPayload("other", SENTINEL)) != reference
    # keyed: another key gives another value, an unkeyed digest of the message is not the MAC
    other = crypto(fingerprint_keys={"fp-1": FP_2, "fp-2": FP_1})
    assert _fingerprint(other) != reference
    message = fingerprint_message(
        family="parent",
        tenant="",
        profile_id=PROFILE,
        principal="actor-1",
        expected_revision=0,
        payload=PAYLOAD,
    )
    assert reference != hashlib.sha256(message).digest()
    assert SENTINEL.encode() not in reference


def test_a_stored_fingerprint_key_id_selects_the_old_key_after_a_rotation() -> None:
    c = crypto()
    old = _fingerprint(c)
    rotated = crypto(current_fingerprint_key_id="fp-2")
    assert rotated.fingerprint_key_id == "fp-2"
    assert _fingerprint(rotated) != old
    assert _fingerprint(rotated, key_id="fp-1") == old
    with pytest.raises(SupportNeedsUnavailable):
        _fingerprint(rotated, key_id="fp-9")


# --------------------------------------------------------------------- the dependency
def test_cryptography_is_a_declared_backend_dependency() -> None:
    project = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    declared = [
        item for item in project["project"]["dependencies"] if item.startswith("cryptography")
    ]
    assert len(declared) == 1 and re.fullmatch(r"cryptography>=\d+,<\d+", declared[0])
    lock = (BACKEND / "uv.lock").read_text(encoding="utf-8")
    entry = lock.split('name = "sketch2life-backend"', 1)[1]
    assert '{ name = "cryptography" }' in entry
    assert '{ name = "cryptography", specifier = ">=' in entry


# --------------------------------------------------------------------- the inventory guard
# No builder of a story, a rewrite, a revision, a StoryRun-lite or an activity-suggestion worker
# input, and no profile projection, may read support needs. The set below is every source module
# that mentions the feature; a new module that does (a builder that starts reading it) fails here
# and must be reviewed. The dynamic check with a stored sentinel is in the PostgreSQL tests.
_ALLOWED_MENTIONS = {
    "application/ports/support_needs.py",
    "application/services/support_needs.py",
    "contracts/schemas/be1_runtime.py",
    "contracts/schemas/parent_profiles.py",
    "contracts/schemas/support_needs.py",
    "domain/be1_profile_revisions.py",  # a docstring: interests are never a support need
    "domain/support_needs.py",
    "domain/profile_sharing.py",  # the refused-field list: support needs are never shareable
    "infrastructure/persistence/be1_models.py",
    "infrastructure/persistence/be1_profile_purge.py",  # the lifecycle purge deletes the record
    "infrastructure/persistence/parent_models.py",
    "infrastructure/persistence/support_needs_repository.py",
    "infrastructure/security/support_needs_crypto.py",
    "interfaces/http/app.py",
    "interfaces/http/error_envelope.py",
    "interfaces/http/openapi_contract.py",
    "interfaces/http/openapi_srs_v22.py",
    "interfaces/http/parent_runtime.py",
    "interfaces/http/routers/be1_registry.py",
    "interfaces/http/routers/parent_profiles.py",
    "interfaces/http/support_needs_runtime.py",
}


def test_only_the_support_needs_modules_mention_support_needs() -> None:
    pattern = re.compile(r"support[_\- ]?needs?", re.IGNORECASE)
    found = {
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    }
    assert found == _ALLOWED_MENTIONS, sorted(found ^ _ALLOWED_MENTIONS)


def test_no_worker_input_builder_module_is_in_the_allowed_set() -> None:
    builders = {
        "infrastructure/persistence/story_first_start.py",
        "infrastructure/persistence/parent_story_repository.py",
        "infrastructure/story_run_lite/repository.py",
        "application/services/parent_activity_suggestions.py",
        "infrastructure/persistence/parent_profile_repository.py",
        "infrastructure/persistence/parent_story_profile_lookup.py",
        "domain/parent_profiles.py",
    }
    assert builders.isdisjoint(_ALLOWED_MENTIONS)
    for relative in builders:
        assert (SRC / relative).is_file(), relative
