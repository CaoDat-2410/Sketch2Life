"""FEAT-066 T-4a1: the Teacher run actor guard on the post-create StoryRun steps, on PostgreSQL.

SRS l.553 (FR-T-14: every Teacher step re-checks the CURRENT assignment), l.864-865 (one 404 for
an unknown and an out-of-scope resource), l.1664-1676 ("Actor của run"), l.364, l.593, l.1425 (a
suspended or archived class is read-only). Runs only against a disposable database whose name
contains ``be1_acceptance`` and ``frc08_v3_t4a1``; synthetic rows only.

The Teacher runs are FIXTURES: no product code creates an ``ORGANIZATION`` run before T-4b2 (the
interim storage is ``ORGANIZATION`` + organization id, ``profile_ref`` = the Managed Profile child
id, no lock column). They are seeded straight into the Story tables at the point a test needs.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import select, text, update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.story_inputs.fixtures import FixtureDrawingAnalyzer
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tests.unit.test_story_output import valid_story

ISSUER = "synthetic-t4a1-issuer"
SUBJECT = "dragon"
CONTEXT_SHA = "c" * 64
VOLATILE = {"request_id", "correlation_id"}


def digest_of(subject: str) -> str:
    return parent_scope_ref(VerifiedPrincipal(subject, ISSUER, frozenset()))


@dataclass
class Fixture:
    org: str
    foreign_org: str
    class_a: str
    class_b: str
    class_c: str
    child: str  # a Managed Profile in class A with a UUID child id
    synthetic_child: str  # a Managed Profile in class A with a non-UUID id
    subjects: dict[str, str]
    accounts: dict[str, str]


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    fx: Fixture

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t4a1" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t4a1*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    org, foreign_org = f"org-t4a1-{token}", f"org-t4a1-foreign-{token}"
    class_a, class_b, class_c = (f"class-{letter}-{token}" for letter in "abc")
    foreign_class = f"class-foreign-{token}"
    child = str(uuid4())
    synthetic_child = f"synthetic-{uuid4().hex[:12]}"
    roles = {
        "parent": "parent",
        "other_parent": "parent",
        "t1": "teacher",  # class A
        "t2": "teacher",  # class B
        "t3": "teacher",  # organization-wide teacher row
        "t4": "teacher",  # a second teacher of class A (same key, other actor)
        "guide": "teacher",
        "observer": "teacher",
        "manager": "school_manager",
        "foreign": "teacher",
        "admin": "platform_admin",
        "idle": "teacher",  # suspended identity with a class A row
    }
    subjects = {name: f"synthetic-t4a1-{name}-{token}" for name in roles}
    accounts: dict[str, str] = {}
    with runtime.session_factory.begin() as db:
        for name, role in roles.items():
            identity = AdultIdentityModel(
                subject=subjects[name],
                issuer=ISSUER,
                state="suspended" if name == "idle" else "active",
                account_role=role,
            )
            db.add(identity)
            accounts[name] = identity.account_id
        for organization in (org, foreign_org):
            db.add(OrganizationModel(organization_id=organization, display_name=organization))
        db.flush()
        for class_id, organization in (
            (class_a, org),
            (class_b, org),
            (class_c, org),
            (foreign_class, foreign_org),
        ):
            db.add(
                ClassroomModel(
                    class_id=class_id,
                    organization_id=organization,
                    display_name=class_id,
                    state="active",
                    created_by="fixture",
                )
            )
        db.flush()
        for child_id in (child, synthetic_child):
            db.add(
                ManagedProfileModel(
                    child_id=child_id,
                    organization_id=org,
                    class_id=class_a,
                    display_name="Synthetic child",
                    age_months=72,
                    age_source="SYNTHETIC_FIXTURE",
                    data_origin="SYNTHETIC_DEV",
                    state="active",
                    created_by="fixture",
                )
            )
        rows: tuple[tuple[str, str, str | None, str], ...] = (
            ("t1", org, class_a, "teacher"),
            ("t2", org, class_b, "teacher"),
            ("t3", org, None, "teacher"),
            ("t4", org, class_a, "teacher"),
            ("guide", org, class_a, "guide"),
            ("observer", org, class_a, "observer"),
            ("manager", org, None, "school_admin"),
            ("foreign", foreign_org, foreign_class, "teacher"),
            ("idle", org, class_a, "teacher"),
        )
        for name, organization, assigned_class, role in rows:
            db.add(
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization,
                    subject=subjects[name],
                    class_id=assigned_class,
                    role=role,
                    active=True,
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    fixture = Fixture(
        org, foreign_org, class_a, class_b, class_c, child, synthetic_child, subjects, accounts
    )
    try:
        with TestClient(app) as client:
            yield Api(app, client, fixture)
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------------- seeding
def seed_run(
    api: Api,
    *,
    teacher: bool,
    state: str = "PREPARATION_REVIEW",
    profile_ref: str | None = None,
    confirmed_context: bool = False,
    understanding: bool = False,
    story: bool = False,
    owner: str | None = None,
) -> str:
    """One run seeded into the Story tables: a Teacher fixture run or a Parent run."""

    fx = api.fx
    run_id = str(uuid4())
    now = datetime.now(UTC)
    if teacher:
        kind, ref, profile, lock = "ORGANIZATION", fx.org, profile_ref or fx.child, None
        confirmed_by = "teacher-fixture"
    else:
        owner = owner or fx.subjects["parent"]
        kind, ref = "PARENT_ACCOUNT", digest_of(owner)
        profile, lock = profile_ref or str(uuid4()), None
        confirmed_by = ref
    tombstone = state == "DELETED"
    context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": str(uuid4()),
        "age_months": 72,
        "interests_summary": "",
        "topic": "synthetic",
        "adult_confirmed_idea": "",
    }
    input_id = str(uuid4())
    with api.sessions().begin() as db:
        db.execute(
            story_tables.story_runs.insert().values(
                run_id=run_id,
                actor_scope_kind=kind,
                actor_scope_ref=ref,
                profile_ref=None if tombstone else profile,
                run_state=state,
                job_state="SUCCEEDED",
                revision=3,
                version=3,
                current_input_revision=None if tombstone else 1,
                understanding_revision=1 if understanding else None,
                subject_label=SUBJECT if understanding else None,
                confidence=0.9 if understanding else None,
                active_owner_parent_account_id=lock,
                created_at=now,
                updated_at=now,
            )
        )
        if tombstone:
            return run_id
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=input_id,
                run_id=run_id,
                input_revision=1,
                source_profile_revision_ref=str(uuid4()),
                context_revision=1,
                context_snapshot=context,
                context_snapshot_sha256=CONTEXT_SHA,
                context_confirmed_by=confirmed_by if confirmed_context else None,
                context_confirmed_at=now if confirmed_context else None,
                created_at=now,
            )
        )
        if understanding:
            db.execute(
                story_tables.understanding_revisions.insert().values(
                    understanding_revision_id=str(uuid4()),
                    run_id=run_id,
                    run_input_id=input_id,
                    revision_no=1,
                    subject_label=SUBJECT,
                    confidence=0.9,
                    canonical_result_sha256="d" * 64,
                    result_snapshot={
                        "result": {
                            "candidate_subject": SUBJECT,
                            "visible_features": ["wings", "tail"],
                            "confidence": 0.9,
                            "adult_confirmation_required": True,
                            "decision": "REVIEW_REQUIRED",
                        }
                    },
                    created_at=now,
                )
            )
        if story:
            content, digest = normalize_story_output(valid_story(), confirmed_subject=SUBJECT)
            revision_id = str(uuid4())
            db.execute(
                story_tables.story_revisions.insert().values(
                    story_revision_id=revision_id,
                    run_id=run_id,
                    revision_no=1,
                    status="DRAFT",
                    source_asset_sha256="a" * 64,
                    understanding_revision=1,
                    context_revision=1,
                    story_sha256=digest,
                    language=content["language"],
                    title=content["title"],
                    duration_ms=content["duration_ms"],
                    story_content=content["story"],
                    schema_version="sketch2life.story-revision.v1",
                    prompt_version="synthetic-prompt",
                    model_id="synthetic-model",
                    model_revision="1",
                    request_sha256="b" * 64,
                    created_at=now,
                )
            )
            for scene in content["scenes"]:
                db.execute(
                    story_tables.story_scenes.insert().values(
                        scene_id=str(uuid4()),
                        story_revision_id=revision_id,
                        scene_index=scene["scene_index"],
                        title=scene["title"],
                        action=scene["action"],
                        visual_prompt=scene["visual_prompt"],
                        narration=scene["narration"],
                        start_ms=scene["start_ms"],
                        duration_ms=scene["duration_ms"],
                        character_anchors=scene["character_anchors"],
                    )
                )
    return run_id


def story_digest() -> str:
    return normalize_story_output(valid_story(), confirmed_subject=SUBJECT)[1]


# ------------------------------------------------------------------------------- the routes
STEPS = ("read", "context", "subject", "script")


def call(
    api: Api,
    step: str,
    run_id: str,
    name: str,
    *,
    key: str | None = None,
    subject: str | None = None,
) -> Any:
    who = subject or api.fx.subjects[name]
    headers = {"X-Test-Principal": who}
    if step == "read":
        return api.client.get(f"/v1/story-runs/{run_id}", headers=headers)
    headers["Idempotency-Key"] = key or uuid4().hex
    bodies = {
        "context": (
            "context-confirmation",
            {
                "expected_context_revision": 1,
                "context_snapshot_sha256": CONTEXT_SHA,
                "confirmed": True,
            },
        ),
        "subject": (
            "subject-confirmation",
            {"expected_understanding_revision": 1, "confirmed_subject": SUBJECT},
        ),
        "script": (
            "script-confirmation",
            {"expected_revision": 1, "story_sha256": story_digest()},
        ),
    }
    path, body = bodies[step]
    return api.client.post(f"/v1/story-runs/{run_id}/{path}", json=body, headers=headers)


def wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE}


def run_row(api: Api, run_id: str) -> Any:
    with api.sessions()() as db:
        return (
            db.execute(
                select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )


def receipts(api: Api, run_id: str, operation: str | None = None) -> list[Any]:
    table = story_tables.story_command_receipts
    query = select(table).where(table.c.resource_ref == run_id)
    if operation is not None:
        query = query.where(table.c.operation == operation)
    with api.sessions()() as db:
        return list(db.execute(query).mappings().all())


def set_assignment(api: Api, name: str, *, active: bool) -> None:
    with api.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.subject == api.fx.subjects[name],
                OrganizationAssignmentModel.role == "teacher",
            )
            .values(active=active)
        )


def set_class_state(api: Api, class_id: str, state: str) -> None:
    with api.sessions().begin() as db:
        db.execute(
            update(ClassroomModel).where(ClassroomModel.class_id == class_id).values(state=state)
        )


WRONG_ACTORS = (
    "t2",  # a Teacher of another class
    "t3",  # an organization-wide teacher row
    "guide",
    "observer",
    "manager",
    "foreign",  # a Teacher of another organization
    "parent",
    "other_parent",
    "admin",
    "idle",  # an inactive identity with a class row
)


def seeded_for(step: str, api: Api, **kwargs: Any) -> str:
    if step == "read":
        return seed_run(api, teacher=True, **kwargs)
    if step == "context":
        return seed_run(api, teacher=True, **kwargs)
    if step == "subject":
        return seed_run(api, teacher=True, state="SUBJECT_REVIEW", understanding=True, **kwargs)
    return seed_run(
        api,
        teacher=True,
        state="SCRIPT_REVIEW",
        understanding=True,
        story=True,
        confirmed_context=True,
        **kwargs,
    )


# ======================================================================== the assigned Teacher
def test_the_class_teacher_reads_and_confirms_every_post_create_step(api: Api) -> None:
    fx = api.fx
    context_run = seeded_for("context", api)
    read = call(api, "read", context_run, "t1")
    assert read.status_code == 200, read.text
    teacher_view = read.json()["story_run"]
    parent_run = seed_run(api, teacher=False)
    parent_view = call(api, "read", parent_run, "parent").json()["story_run"]
    # T-4b2 D10: the Teacher view is the Parent view with a string profile ref in place of the
    # Parent profile UUID and the occurrence, plan and activity pins (None for this fixture row)
    assert set(teacher_view) == (set(parent_view) - {"parent_profile_id"}) | {
        "profile_ref",
        "occurrence_id",
        "plan",
        "activity",
    }
    assert teacher_view["occurrence_id"] is None and teacher_view["plan"] is None
    assert teacher_view["run_id"] == context_run and teacher_view["context_confirmed"] is False
    assert read.headers["etag"] and read.headers["cache-control"] == "private, no-cache"
    assert call(api, "read", context_run, "t1").headers["etag"] == read.headers["etag"]

    confirmed = call(api, "context", context_run, "t1", key="t1-context")
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["story_run"]["context_confirmed"] is True
    (receipt,) = receipts(api, context_run, "CONFIRM_CONTEXT")
    assert (receipt["actor_scope_kind"], receipt["actor_scope_ref"]) == (
        "ORGANIZATION",
        digest_of(fx.subjects["t1"]),
    )
    row = run_row(api, context_run)
    # the owner scope and the lock are untouched by a Teacher step
    assert (row["actor_scope_kind"], row["actor_scope_ref"]) == ("ORGANIZATION", fx.org)
    assert row["active_owner_parent_account_id"] is None and int(row["revision"]) == 4
    replay = call(api, "context", context_run, "t1", key="t1-context")
    assert wire(replay)[0] == 200 and len(receipts(api, context_run, "CONFIRM_CONTEXT")) == 1

    subject_run = seeded_for("subject", api)
    subject = call(api, "subject", subject_run, "t1", key="t1-subject")
    assert subject.status_code == 202, subject.text
    assert subject.json()["decision"] == "CONFIRMED"
    assert run_row(api, subject_run)["run_state"] == "PREPARATION_REVIEW"
    with api.sessions()() as db:
        decision = (
            db.execute(
                select(story_tables.review_decisions).where(
                    story_tables.review_decisions.c.run_id == subject_run
                )
            )
            .mappings()
            .one()
        )
    assert (decision["actor_scope_kind"], decision["actor_scope_ref"]) == (
        "ORGANIZATION",
        digest_of(fx.subjects["t1"]),
    )

    script_run = seeded_for("script", api)
    script = call(api, "script", script_run, "t1", key="t1-script")
    assert script.status_code == 200, script.text
    with api.sessions()() as db:
        review = (
            db.execute(
                select(story_tables.story_revision_reviews).where(
                    story_tables.story_revision_reviews.c.run_id == script_run
                )
            )
            .mappings()
            .one()
        )
        status = db.scalar(
            select(story_tables.story_revisions.c.status).where(
                story_tables.story_revisions.c.run_id == script_run
            )
        )
    assert (review["actor_scope_kind"], review["actor_scope_ref"]) == (
        "ORGANIZATION",
        digest_of(fx.subjects["t1"]),
    )
    assert status == "CONFIRMED"


def test_a_teacher_subject_edit_is_confirmed_at_once_and_never_reruns_the_vlm(api: Api) -> None:
    api.app.state.drawing_analyzer = FixtureDrawingAnalyzer()
    run_id = seeded_for("subject", api)
    response = api.client.post(
        f"/v1/story-runs/{run_id}/subject-confirmation",
        json={"expected_understanding_revision": 1, "confirmed_subject": "little dragon"},
        headers={"X-Test-Principal": api.fx.subjects["t1"], "Idempotency-Key": "t1-edit"},
    )
    assert response.status_code == 202, response.text
    assert response.json()["decision"] == "CONFIRMED"
    assert response.json()["understanding_revision"] == 2
    row = run_row(api, run_id)
    assert row["run_state"] == "PREPARATION_REVIEW" and row["job_state"] == "SUCCEEDED"
    assert api.app.state.drawing_analyzer.calls == []


# ================================================================== uniform 404, both directions
@pytest.mark.parametrize("step", STEPS)
def test_every_other_actor_gets_the_one_404_of_an_unknown_run(api: Api, step: str) -> None:
    run_id = seeded_for(step, api)
    unknown = wire(call(api, step, str(uuid4()), "t1"))
    assert unknown[0] == 404 and unknown[1]["code"] == "RESOURCE_NOT_FOUND"
    for name in WRONG_ACTORS:
        assert wire(call(api, step, run_id, name)) == unknown, (step, name)
    # the same actors on the very same run did not change anything
    assert run_row(api, run_id)["revision"] == 3
    assert receipts(api, run_id) == []
    # no Parent can reach a Teacher run (also the account that owns the Parent runs)
    assert wire(call(api, step, run_id, "parent")) == unknown


@pytest.mark.parametrize("step", STEPS)
def test_no_teacher_can_reach_a_parent_run_and_the_parent_still_can(api: Api, step: str) -> None:
    parent_run = (
        seed_run(api, teacher=False)
        if step in {"read", "context"}
        else seed_run(
            api,
            teacher=False,
            state="SUBJECT_REVIEW" if step == "subject" else "SCRIPT_REVIEW",
            understanding=True,
            story=step == "script",
            confirmed_context=step == "script",
        )
    )
    unknown = wire(call(api, step, str(uuid4()), "t1"))
    for name in ("t1", "t2", "t3", "t4", "guide", "observer", "manager", "foreign", "admin"):
        assert wire(call(api, step, parent_run, name)) == unknown, (step, name)
    assert wire(call(api, step, parent_run, "other_parent")) == unknown
    allowed = call(api, step, parent_run, "parent")
    assert allowed.status_code in {200, 202}, allowed.text


# ==================================================================== the current assignment
def test_a_revoked_assignment_is_404_on_every_step_and_an_old_key_replays_nothing(
    api: Api,
) -> None:
    runs = {step: seeded_for(step, api) for step in STEPS}
    context_key = "t1-before-revocation"
    assert call(api, "context", runs["context"], "t1", key=context_key).status_code == 200
    set_assignment(api, "t1", active=False)
    unknown = wire(call(api, "read", str(uuid4()), "parent"))
    for step in STEPS:
        assert wire(call(api, step, runs[step], "t1")) == unknown, step
    # the stored 200 is not replayed to a former Teacher (the owner check precedes the replay)
    assert wire(call(api, "context", runs["context"], "t1", key=context_key)) == unknown
    # a successor assigned to the class gets the run at the next request
    set_assignment(api, "t2", active=False)
    with api.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.subject == api.fx.subjects["t2"],
                OrganizationAssignmentModel.role == "teacher",
            )
            .values(class_id=api.fx.class_a, active=True)
        )
    assert call(api, "read", runs["read"], "t2").status_code == 200
    assert call(api, "subject", runs["subject"], "t2", key="t2-subject").status_code == 202
    assert wire(call(api, "read", runs["read"], "t1")) == unknown


def test_a_moved_child_moves_the_run_authority_with_it(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    assert call(api, "read", run_id, "t1").status_code == 200
    assert call(api, "read", run_id, "t2").status_code == 404
    with api.sessions().begin() as db:
        db.execute(
            update(ManagedProfileModel)
            .where(ManagedProfileModel.child_id == api.fx.child)
            .values(class_id=api.fx.class_b)
        )
    assert call(api, "read", run_id, "t2").status_code == 200
    assert call(api, "read", run_id, "t1").status_code == 404


def test_the_same_key_from_two_teachers_does_not_collide(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    first = call(api, "context", run_id, "t1", key="shared-key")
    second = call(api, "context", run_id, "t4", key="shared-key")
    assert first.status_code == 200 and second.status_code == 200, second.text
    rows = receipts(api, run_id, "CONFIRM_CONTEXT")
    assert sorted(row["actor_scope_ref"] for row in rows) == sorted(
        [digest_of(api.fx.subjects["t1"]), digest_of(api.fx.subjects["t4"])]
    )
    assert {row["actor_scope_kind"] for row in rows} == {"ORGANIZATION"}


# ============================================================================= the class state
@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_a_read_only_class_allows_reads_and_refuses_the_three_confirmations(
    api: Api, class_state: str
) -> None:
    runs = {step: seeded_for(step, api) for step in STEPS}
    set_class_state(api, api.fx.class_a, class_state)
    assert call(api, "read", runs["read"], "t1").status_code == 200
    for step in ("context", "subject", "script"):
        response = call(api, step, runs[step], "t1", key=f"ro-{step}")
        assert response.status_code == 409, (step, response.text)
        assert response.json()["code"] == "INVALID_STATE_TRANSITION"
        assert run_row(api, runs[step])["revision"] == 3
        assert receipts(api, runs[step]) == []
    set_class_state(api, api.fx.class_a, "active")
    assert call(api, "context", runs["context"], "t1", key="ro-context").status_code == 200
    # the Parent never sees a class state
    set_class_state(api, api.fx.class_a, class_state)
    parent_run = seed_run(api, teacher=False)
    assert call(api, "context", parent_run, "parent").status_code == 200
    set_class_state(api, api.fx.class_a, "active")


@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_an_earlier_success_is_still_replayed_in_a_read_only_class(
    api: Api, class_state: str
) -> None:
    """SRS l.1697: the class check follows the replay (T4A1-I-06 aligned with T-13a-DEC-2)."""

    runs = {step: seeded_for(step, api) for step in ("context", "subject", "script")}
    first = {
        step: call(api, step, run_id, "t1", key=f"early-{step}").status_code
        for step, run_id in runs.items()
    }
    assert all(code in {200, 202} for code in first.values()), first
    set_class_state(api, api.fx.class_a, class_state)
    try:
        for step, run_id in runs.items():
            replay = call(api, step, run_id, "t1", key=f"early-{step}")
            assert replay.status_code == first[step], (step, replay.text)
        # a new key in the read-only class is still refused
        fresh = seeded_for("context", api)
        assert call(api, "context", fresh, "t1", key="late-key").status_code == 409
    finally:
        set_class_state(api, api.fx.class_a, "active")


def test_a_withdrawn_child_keeps_the_run_readable_for_the_class_teacher(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    with api.sessions().begin() as db:
        db.execute(
            update(ManagedProfileModel)
            .where(ManagedProfileModel.child_id == api.fx.child)
            .values(state="withdrawn")
        )
    assert call(api, "read", run_id, "t1").status_code == 200


# ==================================================================== the typed ref and purge
def test_a_non_uuid_child_id_reads_and_confirms_as_the_teacher_view(api: Api) -> None:
    """T-4b2 D10 retired T-4a1-DEC-7: no 409 on the read, no commit-then-409 on a write."""
    run_id = seed_run(api, teacher=True, profile_ref=api.fx.synthetic_child)
    response = call(api, "read", run_id, "t1")
    assert response.status_code == 200, response.text
    view = response.json()["story_run"]
    assert view["profile_ref"] == {"kind": "MANAGED_PROFILE", "id": api.fx.synthetic_child}
    assert "parent_profile_id" not in view
    confirmed = call(api, "context", run_id, "t1", key="non-uuid-context")
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["story_run"]["context_confirmed"] is True
    assert confirmed.json()["story_run"]["profile_ref"]["id"] == api.fx.synthetic_child
    replay = call(api, "context", run_id, "t1", key="non-uuid-context")
    assert replay.status_code == 200 and replay.json()["story_run"]["context_confirmed"] is True


def test_a_run_being_deleted_reaches_the_class_teacher_content_free_and_a_tombstone_does_not(
    api: Api,
) -> None:
    pending = seed_run(api, teacher=True, state="DELETE_PENDING")
    response = call(api, "read", pending, "t1")
    assert response.status_code == 200, response.text
    assert set(response.json()) == {"request_id", "lifecycle"} and "etag" not in response.headers
    assert wire(call(api, "read", pending, "t2")) == wire(call(api, "read", str(uuid4()), "t1"))
    tombstone = seed_run(api, teacher=True, state="DELETED")
    assert call(api, "read", tombstone, "t1").status_code == 404
    parent_tombstone = seed_run(api, teacher=False, state="DELETED")
    assert call(api, "read", parent_tombstone, "parent").status_code == 200  # Q-4: only the Teacher


def test_a_teacher_replay_after_the_run_is_purged_is_the_projection_not_a_400(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    assert call(api, "context", run_id, "t1", key="purge-key").status_code == 200
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == run_id)
            .values(run_state="DELETE_PENDING")
        )
    different_payload = api.client.post(
        f"/v1/story-runs/{run_id}/context-confirmation",
        json={
            "expected_context_revision": 2,
            "context_snapshot_sha256": "e" * 64,
            "confirmed": True,
        },
        headers={"X-Test-Principal": api.fx.subjects["t1"], "Idempotency-Key": "purge-key"},
    )
    assert different_payload.status_code == 200, different_payload.text
    assert set(different_payload.json()) == {"request_id", "lifecycle"}
    # a live run with a changed payload on the same key is still the 400
    live = seed_run(api, teacher=True)
    assert call(api, "context", live, "t1", key="live-key").status_code == 200
    changed = api.client.post(
        f"/v1/story-runs/{live}/context-confirmation",
        json={
            "expected_context_revision": 1,
            "context_snapshot_sha256": "e" * 64,
            "confirmed": True,
        },
        headers={"X-Test-Principal": api.fx.subjects["t1"], "Idempotency-Key": "live-key"},
    )
    assert changed.status_code == 400 and changed.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


# ======================================================== the steps that stay Parent-only
def test_a_teacher_cannot_create_list_or_reach_parent_only_steps(
    api: Api,
) -> None:
    run_id = seed_run(api, teacher=True)
    unknown = wire(call(api, "read", str(uuid4()), "parent"))
    headers = {"X-Test-Principal": api.fx.subjects["t1"], "Idempotency-Key": "parent-only-1"}
    attempts = (
        api.client.post(
            "/v1/story-runs", json={"parent_profile_id": str(uuid4())}, headers=headers
        ),
        api.client.get("/v1/story-runs", headers=headers),
        # (the active run is the Teacher's own since T-4b2: its own assertion below)
        # cancel and DELETE are open to the class Teacher since T-13a (its own PostgreSQL module)
        api.client.get(f"/v1/story-runs/{run_id}/transcript", headers=headers),
        api.client.post(f"/v1/story-runs/{run_id}/playback-token", headers=headers),
        api.client.post(
            f"/v1/story-runs/{run_id}/complete", json={"expected_revision": 3}, headers=headers
        ),
    )
    for response in attempts:
        assert wire(response) == unknown, response.request.url
    row = run_row(api, run_id)
    assert row["run_state"] == "PREPARATION_REVIEW" and row["revision"] == 3
    # the active run of a Teacher is the one its Teacher lock holds: a fixture row holds none
    active = api.client.get("/v1/story-runs/active/current", headers=headers)
    assert active.status_code == 200 and active.json()["story_run"] is None


def test_a_teacher_gets_no_upload_target_for_a_teacher_run_and_no_parent_prefix(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    unknown = wire(call(api, "read", str(uuid4()), "parent"))
    response = api.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": "RUN_ARTWORK",
            "target_ref": run_id,
            "media_type": "image/png",
            "expected_size_bytes": 10,
            "expected_sha256": "f" * 64,
        },
        headers={"X-Test-Principal": api.fx.subjects["t1"], "Idempotency-Key": "upload-1"},
    )
    assert wire(response) == unknown, response.text
    assert "parent/" not in response.text
    with api.sessions()() as db:
        created = db.scalar(
            text("SELECT count(*) FROM storyrun_upload_sessions WHERE target_ref = :run"),
            {"run": run_id},
        )
    assert created == 0


# ================================================================================= the lock
def test_the_teacher_steps_never_touch_the_lock_columns_or_the_parent_unique_index(
    api: Api,
) -> None:
    runs = [seed_run(api, teacher=True) for _ in range(3)]  # no lock: several are allowed
    for run_id in runs:
        assert call(api, "context", run_id, "t1").status_code == 200
        assert run_row(api, run_id)["active_owner_parent_account_id"] is None
    with api.sessions()() as db:
        index = db.scalar(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE schemaname = 'story' AND indexname = 'uq_story_run_active_parent'"
            )
        )
    assert index is not None and "UNIQUE" in index and "active_owner_parent_account_id" in index
