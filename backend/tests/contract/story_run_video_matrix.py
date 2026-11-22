"""The request matrix of the five StoryRun video routes used to pin the Parent answers (T-4b3b).

Not a test module: ``test_teacher_run_video_contract.py`` runs the matrix against the current
application and compares the answers with ``golden/story_run_video_head.json``, which was recorded
at HEAD ``29949961`` (the T-4b3a commit) with this same file, BEFORE the five routes were edited.
The routes are ``POST /v1/story-runs/{id}/video-generations``, ``POST .../video-unsuitable``,
``POST .../complete``, ``POST .../playback-token`` and ``GET .../playback``.

The database is a fake that knows only ``Session.get(AdultIdentityModel, subject)`` (and the
context manager protocol the stream route uses for its own short session): every case in the matrix
is answered before a repository is touched, so the golden answers are the validation, key, token and
role answers of the routes and nothing else. A case that would reach a repository (an active Parent
or an active Teacher with a valid body, a good key and, for the stream, a valid token) is left out:
those need PostgreSQL and are covered by the integration modules. The request id and the
correlation id are masked.
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
from sketch2life.infrastructure.story_video.playback_tokens import PlaybackTokenCodec

ISSUER = "synthetic-t4b3b-issuer"
GOOD_UUID = "11111111-1111-4111-8111-111111111111"
GENERATION_UUID = "33333333-3333-4333-8333-333333333333"
HASH = "a" * 64
_NOW = 1_900_000_000.0

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

# route name -> (method, path suffix, the bodies; None = no body)
ROUTES: dict[str, tuple[str, str, dict[str, bytes] | None]] = {
    "video_generations": (
        "POST",
        "video-generations",
        {
            "valid": json.dumps({"expected_revision": 1, "story_sha256": HASH}).encode(),
            "valid_regen": json.dumps(
                {"expected_revision": 2, "story_sha256": HASH, "quality_reason_code": "QUALITY_LOW"}
            ).encode(),
            "bad_hash": json.dumps({"expected_revision": 1, "story_sha256": "x"}).encode(),
            "bad_reason": json.dumps(
                {"expected_revision": 1, "story_sha256": HASH, "quality_reason_code": "NOPE"}
            ).encode(),
            "revision_zero": json.dumps({"expected_revision": 0, "story_sha256": HASH}).encode(),
            "unknown_key": json.dumps(
                {"expected_revision": 1, "story_sha256": HASH, "zzz": 1}
            ).encode(),
            **COMMON_BODIES,
        },
    ),
    "video_unsuitable": (
        "POST",
        "video-unsuitable",
        {
            "valid": json.dumps(
                {
                    "expected_revision": 3,
                    "generation_id": GENERATION_UUID,
                    "reason_code": "QUALITY_LOW",
                }
            ).encode(),
            "bad_reason": json.dumps(
                {"expected_revision": 3, "generation_id": GENERATION_UUID, "reason_code": "NOPE"}
            ).encode(),
            "bad_generation": json.dumps(
                {"expected_revision": 3, "generation_id": "x", "reason_code": "QUALITY_LOW"}
            ).encode(),
            "no_generation": json.dumps(
                {"expected_revision": 3, "reason_code": "QUALITY_LOW"}
            ).encode(),
            "unknown_key": json.dumps(
                {
                    "expected_revision": 3,
                    "generation_id": GENERATION_UUID,
                    "reason_code": "QUALITY_LOW",
                    "zzz": 1,
                }
            ).encode(),
            **COMMON_BODIES,
        },
    ),
    "complete": (
        "POST",
        "complete",
        {
            "valid": json.dumps({"expected_revision": 3}).encode(),
            "revision_zero": json.dumps({"expected_revision": 0}).encode(),
            "revision_text": json.dumps({"expected_revision": "3"}).encode(),
            "unknown_key": json.dumps({"expected_revision": 3, "zzz": 1}).encode(),
            **COMMON_BODIES,
        },
    ),
    "playback_token": ("POST", "playback-token", None),
    "playback": ("GET", "playback", None),
}
_VALID_BODIES = frozenset({"valid", "valid_regen"})

_MASK = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def make_codec() -> PlaybackTokenCodec:
    return PlaybackTokenCodec(
        active_key_id="k1",
        keys={"k1": b"synthetic-t4b3b-secret-0123456789abcdef"},
        clock=lambda: _NOW,
    )


def valid_token() -> str:
    token, _expires = make_codec().issue(
        run_id=GOOD_UUID, generation_id=GENERATION_UUID, actor_digest="b" * 32
    )
    return token


class _Session:
    """The calls the matrix needs: the identity row of the subject and the context manager."""

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

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def __getattr__(self, name: str) -> Any:  # a repository call means the matrix left its lane
        raise AssertionError(f"the matrix reached the database: {name}")


def reaches_repository(
    route: str, role: str, body: str, key: str, content: str, token: str
) -> bool:
    """An active Parent (and, after T-4b3b, an active Teacher) whose request passes validation, the
    key rule and, for the stream, the token check calls a repository: that needs PostgreSQL and is
    not in the matrix."""

    if role not in ACTIVE_ROLES:
        return False
    if route == "playback":
        return token == "token_valid"
    if route == "playback_token":
        return True
    return body in _VALID_BODIES and key == "key_ok" and content == "json"


def teacher_branch(route: str, role: str, body: str, content: str, token: str) -> bool:
    """A Teacher request that passes validation: the handler runs, which is a T-4b3b change (it was
    the uniform 404 before), so the golden does not pin it."""

    if role != "teacher":
        return False
    if route == "playback":
        return token == "token_valid"
    if route == "playback_token":
        return True
    return body in _VALID_BODIES and content == "json"


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
            session_factory=_Session,
        )

    application.state.story_playback_tokens = make_codec()
    application.dependency_overrides[runtime_module.get_verified_adult] = principal
    application.dependency_overrides[runtime_module.get_db] = session
    application.dependency_overrides[runtime_module.get_runtime] = runtime


def mask(value: bytes) -> str:
    return _MASK.sub("<uuid>", value.decode("utf-8", errors="replace"))


def _tokens_for(route: str) -> dict[str, str | None]:
    if route != "playback":
        return {"token_none": None}
    return {"token_none": None, "token_garbage": "not-a-token", "token_valid": valid_token()}


def run_matrix(client: TestClient, *, include_teacher_branch: bool) -> dict[str, Any]:
    """Every combination that is answered before a repository is touched. With
    ``include_teacher_branch`` the Teacher cases whose handler now runs are included; the golden
    comparison passes ``False`` and so leaves them out."""

    results: dict[str, Any] = {}
    for route, (method, suffix, bodies) in ROUTES.items():
        body_items: dict[str, bytes | None] = (
            {"none": None} if bodies is None else dict(bodies.items())
        )
        bodyless = bodies is None
        tokens = _tokens_for(route)
        for run_name, run_id in RUN_IDS.items():
            for role in ROLES:
                for body_name, body in body_items.items():
                    for key_name, key in KEYS.items():
                        for content_name, content_type in CONTENT_TYPES.items():
                            if bodyless and (key_name != "key_ok" or content_name != "json"):
                                continue  # no body and no key on this route
                            for token_name, token in tokens.items():
                                if run_name == "run_ok" and reaches_repository(
                                    route, role, body_name, key_name, content_name, token_name
                                ):
                                    continue
                                if run_name == "run_bad" and role not in ("parent", "anonymous"):
                                    continue
                                if (
                                    run_name == "run_ok"
                                    and not include_teacher_branch
                                    and teacher_branch(
                                        route, role, body_name, content_name, token_name
                                    )
                                ):
                                    continue
                                headers: dict[str, str] = {}
                                if body is not None:
                                    headers["Content-Type"] = content_type
                                if role != "anonymous":
                                    headers["X-Test-Principal"] = role
                                if method == "POST" and key is not None:
                                    headers["Idempotency-Key"] = key
                                if token is not None:
                                    headers["X-Playback-Token"] = token
                                path = f"/v1/story-runs/{run_id}/{suffix}"
                                if method == "GET":
                                    response = client.get(path, headers=headers)
                                else:
                                    response = client.post(path, content=body, headers=headers)
                                results[
                                    f"{route}|{run_name}|{role}|{body_name}|{key_name}"
                                    f"|{content_name}|{token_name}"
                                ] = {
                                    "status": response.status_code,
                                    "body": mask(response.content),
                                    "content_type": response.headers.get("content-type"),
                                }
    return results
