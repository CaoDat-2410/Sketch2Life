"""The request matrix of the five StoryRun input routes used to pin the Parent answers (T-4b3a).

Not a test module: ``test_teacher_run_inputs_contract.py`` runs the matrix against the current
application and compares the answers with ``golden/story_run_inputs_head.json``, which was recorded
at HEAD ``8d0fd2ed`` (the commit before T-4b3a) with this same file, BEFORE the five routes were
edited. The routes are ``POST /v1/story-runs/{id}/assets``, ``POST .../idea``,
``GET .../transcript``, ``POST .../transcript-confirmation`` and ``POST .../story-rewrites``.

The database is a fake that knows only ``Session.get(AdultIdentityModel, subject)``: every case in
the matrix is answered before a repository is touched, so the golden answers are the validation and
role answers of the routes and nothing else. A case that would reach a repository (an active Parent
or an active Teacher with a valid body and a good key) is left out: those need PostgreSQL and are
covered by the integration modules. The request id and the correlation id are masked.
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

ISSUER = "synthetic-t4b3a-issuer"
GOOD_UUID = "11111111-1111-4111-8111-111111111111"
UPLOAD_REF = "upl_22222222-2222-4222-8222-222222222222"
HASH = "a" * 64

# role -> (account_role, state, issuer) of the identity row; ``None`` has no row
IDENTITIES: dict[str, tuple[str, str, str] | None] = {
    "parent": ("parent", "active", ISSUER),
    "manager": ("school_manager", "active", ISSUER),
    "platform": ("platform_admin", "active", ISSUER),
    "teacher": ("teacher", "active", ISSUER),
    "inactive_parent": ("parent", "disabled", ISSUER),
    "inactive_teacher": ("teacher", "disabled", ISSUER),
    "other_issuer_parent": ("parent", "active", "synthetic-other-issuer"),
    "other_issuer_teacher": ("teacher", "active", "synthetic-other-issuer"),
    "stranger": None,
}
ROLES = ("anonymous", *IDENTITIES)
# the roles that pass the guard of the current application: they reach a repository
ACTIVE_ROLES = ("parent", "teacher")

RUN_IDS: dict[str, str] = {"run_ok": GOOD_UUID, "run_bad": "not-a-uuid"}
KEYS: dict[str, str | None] = {"key_ok": "key-1", "key_missing": None, "key_bad": "bad key"}
CONTENT_TYPES: dict[str, str] = {"json": "application/json", "text": "text/plain"}

COMMON_BODIES: dict[str, bytes] = {
    "empty": b"",
    "invalid_json": b"{",
    "json_array": b"[1]",
    "json_string": b'"text"',
    "empty_object": b"{}",
}

# route name -> (method, path suffix, the valid body or None, the invalid bodies)
ROUTES: dict[str, tuple[str, str, dict[str, bytes] | None]] = {
    "assets": (
        "POST",
        "assets",
        {
            "valid": json.dumps({"asset_ref": UPLOAD_REF, "expected_run_revision": 1}).encode(),
            "bad_ref": json.dumps({"asset_ref": "not-a-ref"}).encode(),
            "unknown_key": json.dumps({"asset_ref": UPLOAD_REF, "zzz": 1}).encode(),
            **COMMON_BODIES,
        },
    ),
    "idea": (
        "POST",
        "idea",
        {
            "valid": json.dumps({"expected_run_revision": 1, "text": "a small bear"}).encode(),
            "valid_audio": json.dumps(
                {"expected_run_revision": 1, "audio_ref": UPLOAD_REF}
            ).encode(),
            "both_groups": json.dumps(
                {
                    "expected_run_revision": 1,
                    "text": "x",
                    "transcript_correction": {"expected_transcript_revision": 1, "text": "y"},
                }
            ).encode(),
            "no_revision": json.dumps({"text": "x"}).encode(),
            "unknown_key": json.dumps({"expected_run_revision": 1, "text": "x", "zzz": 1}).encode(),
            **COMMON_BODIES,
        },
    ),
    "transcript": ("GET", "transcript", None),
    "transcript_confirmation": (
        "POST",
        "transcript-confirmation",
        {
            "valid": json.dumps(
                {"expected_transcript_revision": 1, "transcript_sha256": HASH, "confirmed": True}
            ).encode(),
            "not_confirmed": json.dumps(
                {"expected_transcript_revision": 1, "transcript_sha256": HASH, "confirmed": False}
            ).encode(),
            "bad_hash": json.dumps(
                {"expected_transcript_revision": 1, "transcript_sha256": "x", "confirmed": True}
            ).encode(),
            **COMMON_BODIES,
        },
    ),
    "story_rewrites": (
        "POST",
        "story-rewrites",
        {
            "valid": json.dumps(
                {"expected_story_revision": 1, "expected_story_sha256": HASH}
            ).encode(),
            "valid_hint": json.dumps(
                {"expected_story_revision": 1, "hint": "make it shorter"}
            ).encode(),
            "revision_too_high": json.dumps({"expected_story_revision": 99}).encode(),
            "control_hint": json.dumps({"expected_story_revision": 1, "hint": "a\u0007b"}).encode(),
            "unknown_key": json.dumps({"expected_story_revision": 1, "zzz": 1}).encode(),
            **COMMON_BODIES,
        },
    ),
}
_VALID_BODIES = frozenset({"valid", "valid_audio", "valid_hint"})

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


def reaches_repository(method: str, role: str, body: str, key: str, content: str) -> bool:
    """An active Parent (and, after T-4b3a, an active Teacher) with a body that validates, a good
    key and a JSON body calls a repository: that needs PostgreSQL and is not in the matrix."""

    if role not in ACTIVE_ROLES:
        return False
    if method == "GET":
        return True
    return body in _VALID_BODIES and key == "key_ok" and content == "json"


def teacher_valid_body(role: str, method: str, body: str, content: str) -> bool:
    """A Teacher whose request passes validation: the handler runs, which is a T-4b3a change
    (it was the uniform 404 before), so the golden does not pin it."""

    if role != "teacher":
        return False
    return method == "GET" or (body in _VALID_BODIES and content == "json")


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
    """Every combination that is answered before a repository is touched. With
    ``include_teacher_branch`` the Teacher cases whose handler now runs are skipped nowhere; the
    golden comparison passes ``False`` and so leaves them out."""

    results: dict[str, Any] = {}
    for route, (method, suffix, bodies) in ROUTES.items():
        body_items: dict[str, bytes | None] = (
            {"none": None} if bodies is None else dict(bodies.items())
        )
        for run_name, run_id in RUN_IDS.items():
            for role in ROLES:
                for body_name, body in body_items.items():
                    for key_name, key in KEYS.items():
                        for content_name, content_type in CONTENT_TYPES.items():
                            if method == "GET" and (key_name != "key_ok" or content_name != "json"):
                                continue  # a GET carries neither a key nor a body
                            if run_name == "run_ok" and reaches_repository(
                                method, role, body_name, key_name, content_name
                            ):
                                continue
                            if run_name == "run_bad" and role not in ("parent", "anonymous"):
                                continue
                            if (
                                role == "teacher"
                                and run_name == "run_ok"
                                and teacher_valid_body(role, method, body_name, content_name)
                                and not include_teacher_branch
                            ):
                                continue
                            headers: dict[str, str] = {}
                            if body is not None:
                                headers["Content-Type"] = content_type
                            if role != "anonymous":
                                headers["X-Test-Principal"] = role
                            if method == "POST" and key is not None:
                                headers["Idempotency-Key"] = key
                            path = f"/v1/story-runs/{run_id}/{suffix}"
                            if method == "GET":
                                response = client.get(path, headers=headers)
                            else:
                                response = client.post(path, content=body, headers=headers)
                            results[
                                f"{route}|{run_name}|{role}|{body_name}|{key_name}|{content_name}"
                            ] = {
                                "status": response.status_code,
                                "body": mask(response.content),
                                "content_type": response.headers.get("content-type"),
                            }
    return results
