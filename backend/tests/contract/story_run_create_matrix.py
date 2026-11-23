"""The request matrix of ``POST /v1/story-runs`` used to pin the Parent answers (FEAT-066 T-4b2).

Not a test module: ``test_teacher_story_run_create_contract.py`` runs the matrix against the current
application and compares the Parent-side answers with ``golden/story_run_create_head.json``, which
was recorded at HEAD ``82c59bdb`` (the commit before T-4b2) with this same file. The database is a
fake that knows only ``Session.get(AdultIdentityModel, subject)``: every case in the matrix is
answered before a repository is touched, so the golden answers are the validation and role
answers of the route and nothing else. The request id and the correlation id are masked.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal

ISSUER = "synthetic-t4b2-issuer"
GOOD_UUID = "11111111-1111-4111-8111-111111111111"
SELECTION_ID = "22222222-2222-4222-8222-222222222222"
HASH = "a" * 64

# role -> (account_role, state, issuer) of the identity row; ``None`` has no row
IDENTITIES: dict[str, tuple[str, str, str] | None] = {
    "parent": ("parent", "active", ISSUER),
    "manager": ("school_manager", "active", ISSUER),
    "platform": ("platform_admin", "active", ISSUER),
    "teacher": ("teacher", "active", ISSUER),
    "inactive_teacher": ("teacher", "disabled", ISSUER),
    "other_issuer_teacher": ("teacher", "active", "synthetic-other-issuer"),
    "stranger": None,
}
ROLES = ("anonymous", *IDENTITIES)

TEACHER_BODY: dict[str, Any] = {
    "profile_ref": {"kind": "MANAGED_PROFILE", "id": "synthetic-child"},
    "occurrence_id": "occurrence-1",
    "plan": {"revision_no": 1, "plan_hash": HASH},
    "activity_id": "activity-1",
    "selection_id": SELECTION_ID,
    "selection_sha256": HASH,
}

BODIES: dict[str, bytes] = {
    "parent_valid": json.dumps({"parent_profile_id": GOOD_UUID}).encode(),
    "parent_missing": b"{}",
    "parent_unknown_key": json.dumps({"parent_profile_id": GOOD_UUID, "zzz": 1}).encode(),
    "parent_bad_uuid": json.dumps({"parent_profile_id": "not-a-uuid"}).encode(),
    "parent_bad_lesson_version": json.dumps(
        {"parent_profile_id": GOOD_UUID, "lesson_version": {"lesson_id": "x"}}
    ).encode(),
    "empty": b"",
    "invalid_json": b"{",
    "json_array": b"[1]",
    "json_string": b'"text"',
    "teacher_full": json.dumps(TEACHER_BODY).encode(),
    "teacher_partial": json.dumps({"profile_ref": TEACHER_BODY["profile_ref"]}).encode(),
    "teacher_plus_parent": json.dumps(
        {"parent_profile_id": GOOD_UUID, "occurrence_id": "occurrence-1"}
    ).encode(),
    "multi_child": json.dumps(
        {**TEACHER_BODY, "profile_ref": [TEACHER_BODY["profile_ref"]]}
    ).encode(),
    "multi_child_key": json.dumps({"profile_refs": ["a", "b"], "occurrence_id": "o"}).encode(),
}
KEYS: dict[str, str | None] = {"key_ok": "key-1", "key_missing": None, "key_bad": "bad key"}
CONTENT_TYPES: dict[str, str] = {"json": "application/json", "text": "text/plain"}

_MASK = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class _Session:
    """The one call the matrix needs: the identity row of the subject."""

    def get(self, _model: object, subject: str) -> Any:
        row = IDENTITIES.get(subject)
        if row is None:
            return None
        role, state, issuer = row
        return SimpleNamespace(
            subject=subject,
            account_role=role,
            state=state,
            issuer=issuer,
            account_id=f"account-{subject}",
        )

    def __getattr__(self, name: str) -> Any:  # a repository call means the matrix left its lane
        raise AssertionError(f"the matrix reached the database: {name}")


def needs_database(role: str, body: str, key: str) -> bool:
    """The Parent with a valid Parent body and a good key creates a run: that needs PostgreSQL."""

    return role == "parent" and body == "parent_valid" and key == "key_ok"


def install_overrides(application: Any, runtime_module: Any) -> None:
    async def principal(request: Request) -> VerifiedPrincipal:
        subject = request.headers.get("X-Test-Principal")
        if subject is None:
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
        return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())

    def session() -> Iterator[_Session]:
        yield _Session()

    def runtime() -> SimpleNamespace:
        return SimpleNamespace(
            settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True),
            session_factory=None,
        )

    application.dependency_overrides[runtime_module.get_verified_adult] = principal
    application.dependency_overrides[runtime_module.get_db] = session
    application.dependency_overrides[runtime_module.get_runtime] = runtime


def mask(value: bytes) -> str:
    return _MASK.sub("<uuid>", value.decode("utf-8", errors="replace"))


def run_matrix(client: TestClient, *, include_teacher_branch: bool) -> dict[str, Any]:
    """Every combination; the Teacher branch (an active Teacher with a Teacher-shaped body) answers
    from the Teacher endpoint and is excluded from the golden comparison."""

    results: dict[str, Any] = {}
    for role in ROLES:
        for body_name, body in BODIES.items():
            for key_name, key in KEYS.items():
                for content_name, content_type in CONTENT_TYPES.items():
                    if needs_database(role, body_name, key_name):
                        continue
                    teacher_branch = (
                        role == "teacher"
                        and content_name == "json"
                        and body_name.startswith(("teacher", "multi_child"))
                    )
                    if teacher_branch and not include_teacher_branch:
                        continue
                    headers = {"Content-Type": content_type}
                    if role != "anonymous":
                        headers["X-Test-Principal"] = role
                    if key is not None:
                        headers["Idempotency-Key"] = key
                    response = client.post("/v1/story-runs", content=body, headers=headers)
                    results[f"{role}|{body_name}|{key_name}|{content_name}"] = {
                        "status": response.status_code,
                        "body": mask(response.content),
                        "content_type": response.headers.get("content-type"),
                    }
    return results
