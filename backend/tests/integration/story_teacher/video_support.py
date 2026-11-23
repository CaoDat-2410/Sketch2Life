"""Shared fixtures and helpers of the T-4b3b PostgreSQL modules (Teacher video routes, sweepers).

Not a test module. It builds on ``inputs_support`` (the T-4b2 and T-4b3a fixtures: a synthetic
organization, classes, Teachers, one confirmed child per run, in-memory object storage, the
deterministic analyzer, transcriber and story generator) and adds the video
side: the local/test admission adapter pair behind a scope recorder (so a test can see the scope
the ports were given), a confirmed script, the video request and the two decisions, the playback
token and the stream, and the fixture video runner.

The FIRST Teacher story starts by itself at the last of the subject and context confirmations
(V4-A OPEN-A D1): ``to_confirmed_script`` confirms the generated first story through the real
``script-confirmation`` route. The adapters are the accept-all local pair of T-1a (no quota,
billing or capacity logic); nothing calls a provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest
from inputs_support import (  # type: ignore[import-not-found]
    Env,
    api,  # noqa: F401 - the T-4b2 fixture, re-exported
    env,  # noqa: F401 - fixture
    new_run,
    receipt_rows,
    rewrite,
    run_revision,
    run_row,
    story_rows,
    to_script_review,
    who_headers,
    wire,
)
from sqlalchemy import select

from sketch2life.application.ports.story_video import StoryVideoAdapters
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.fixture_runner import FixtureVideoRunner
from sketch2life.infrastructure.story_video.local_adapters import (
    VideoAdmissionScript,
    build_local_video_adapters,
)

__all__ = [
    "RUNS",
    "VG",
    "VGS",
    "Env",
    "ScopeRecorder",
    "VEnv",
    "accepted_generation",
    "api",
    "cancel",
    "complete",
    "confirm_script",
    "env",
    "generations",
    "mark_unsuitable",
    "new_run",
    "playback_token",
    "receipt_rows",
    "regenerate_cycle",
    "request_video",
    "rewrite",
    "run_revision",
    "run_row",
    "runner",
    "scenes_of",
    "stream",
    "story_rows",
    "to_confirmed_script",
    "to_ready",
    "to_script_review",
    "v",
    "who_headers",
    "wire",
]

RUNS = story_tables.story_runs
VG = story_tables.video_generations
VGS = story_tables.video_generation_scenes
STORAGE_WORDS = ("bucket", "object_key", "presigned", "s3mock", "parent/", "output.mp4")


class ScopeRecorder:
    """Delegates to a local port and records the ``scope`` of every call it receives."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.scopes: list[Any] = []

    @property
    def calls(self) -> Any:
        return self._inner.calls

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._inner, name)
        if not callable(target):
            return target

        def call(**kwargs: Any) -> Any:
            if "scope" in kwargs:
                self.scopes.append(kwargs["scope"])
            return target(**kwargs)

        return call


@dataclass
class VEnv:
    e: Env
    script: VideoAdmissionScript
    reservation: ScopeRecorder
    quota: ScopeRecorder
    adapters: StoryVideoAdapters

    def use_adapters(self, adapters: StoryVideoAdapters | None) -> None:
        self.e.api.app.state.story_video_ports = adapters


@pytest.fixture
def v(env: Env) -> VEnv:  # noqa: F811 - the re-exported inputs fixture
    script = VideoAdmissionScript()
    inner = build_local_video_adapters(env="test", script=script)
    reservation, quota = ScopeRecorder(inner.reservation), ScopeRecorder(inner.quota)
    adapters = StoryVideoAdapters(reservation=reservation, quota=quota)
    env.api.app.state.story_video_ports = adapters
    return VEnv(env, script, reservation, quota, adapters)


# ----------------------------------------------------------------------------- the script
def confirm_script(
    e: Env, who: str, run_id: str, digest: str, *, number: int = 1, key: str | None = None
) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/script-confirmation",
        json={"expected_revision": number, "story_sha256": digest},
        headers=who_headers(e, who, key or uuid4().hex),
    )


def to_confirmed_script(e: Env, who: str = "t1") -> tuple[str, str]:
    """A Teacher run at ``SCRIPT_REVIEW`` with its (generated) first story confirmed."""

    run_id = to_script_review(e, who)
    digest = str(story_rows(e, run_id)[-1]["story_sha256"])
    response = confirm_script(e, who, run_id, digest)
    assert response.status_code == 200, response.text
    return run_id, digest


# ----------------------------------------------------------------------------- the routes
def request_video(
    e: Env,
    who: str,
    run_id: str,
    digest: str,
    *,
    key: str | None = None,
    revision: int | None = None,
    reason: str | None = None,
    **extra: str,
) -> Any:
    body: dict[str, Any] = {
        "expected_revision": revision if revision is not None else run_revision(e, run_id),
        "story_sha256": digest,
    }
    if reason is not None:
        body["quality_reason_code"] = reason
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/video-generations",
        json=body,
        headers=who_headers(e, who, key or uuid4().hex, **extra),
    )


def mark_unsuitable(
    e: Env,
    who: str,
    run_id: str,
    generation_id: str,
    *,
    key: str | None = None,
    revision: int | None = None,
    reason: str = "QUALITY_LOW",
) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/video-unsuitable",
        json={
            "expected_revision": revision if revision is not None else run_revision(e, run_id),
            "generation_id": generation_id,
            "reason_code": reason,
        },
        headers=who_headers(e, who, key or uuid4().hex),
    )


def complete(
    e: Env, who: str, run_id: str, *, key: str | None = None, revision: int | None = None
) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/complete",
        json={"expected_revision": revision if revision is not None else run_revision(e, run_id)},
        headers=who_headers(e, who, key or uuid4().hex),
    )


def cancel(e: Env, who: str, run_id: str, *, key: str | None = None) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": run_revision(e, run_id)},
        headers=who_headers(e, who, key or uuid4().hex),
    )


def playback_token(e: Env, who: str, run_id: str) -> Any:
    return e.d.client.post(f"/v1/story-runs/{run_id}/playback-token", headers=who_headers(e, who))


def stream(
    e: Env, who: str, run_id: str, token: str | None, *, byte_range: str | None = None
) -> Any:
    extra: dict[str, str] = {}
    if token is not None:
        extra["X-Playback-Token"] = token
    if byte_range is not None:
        extra["Range"] = byte_range
    return e.d.client.get(f"/v1/story-runs/{run_id}/playback", headers=who_headers(e, who, **extra))


# ----------------------------------------------------------------------------- readers
def generations(e: Env, run_id: str) -> list[Any]:
    with e.sessions()() as db:
        return list(
            db.execute(
                select(VG)
                .where(VG.c.story_run_id == run_id)
                .order_by(VG.c.admission_started_at, VG.c.created_at)
            )
            .mappings()
            .all()
        )


def scenes_of(e: Env, generation_id: str) -> list[Any]:
    with e.sessions()() as db:
        return list(
            db.execute(select(VGS).where(VGS.c.video_generation_id == generation_id))
            .mappings()
            .all()
        )


def runner(v: VEnv, renderer: Any = None) -> FixtureVideoRunner:
    return FixtureVideoRunner(v.e.sessions(), v.e.storage, v.adapters, renderer)


# ----------------------------------------------------------------------------- composed steps
def accepted_generation(
    v: VEnv, who: str = "t1", *, run: tuple[str, str] | None = None
) -> tuple[str, str, str]:
    """A confirmed script and an accepted video request: ``(run_id, digest, generation_id)``."""

    run_id, digest = run or to_confirmed_script(v.e, who)
    response = request_video(v.e, who, run_id, digest)
    assert response.status_code == 202, response.text
    body = response.json()["video_generation"]
    assert body["state"] == "ACCEPTED", body
    return run_id, digest, str(body["generation_id"])


def regenerate_cycle(v: VEnv, run_id: str, generation_id: str, *, number: int) -> str:
    """unsuitable, rewrite (story revision ``number``), confirm, request again with a reason."""
    e = v.e
    assert mark_unsuitable(e, "t1", run_id, generation_id).status_code == 200
    assert rewrite(e, "t1", run_id, revision=number - 1).status_code == 202
    assert story_rows(e, run_id)[-1]["revision_no"] == number
    digest = str(story_rows(e, run_id)[-1]["story_sha256"])
    assert confirm_script(e, "t1", run_id, digest, number=number).status_code == 200
    response = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert response.status_code == 202, response.text
    return str(response.json()["video_generation"]["generation_id"])


def to_ready(v: VEnv, who: str = "t1") -> tuple[str, str, str]:
    """Walk an accepted request to ``READY`` with the fixture runner (an output asset, a wait)."""

    run_id, digest, generation_id = accepted_generation(v, who)
    final = runner(v).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "READY", final
    assert run_row(v.e, run_id)["run_state"] == "VIDEO_READY"
    return run_id, digest, generation_id
