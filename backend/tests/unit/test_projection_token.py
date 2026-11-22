"""FEAT-066 T-5a: the class projection token, the stream decision table and ``sample_facts``
(SRS l.1662, l.1691-1693; plan Draft 3 D6, D7, C5, R2 N-2 and N-7).

Offline: no database, no network. The token is the T-1c stateless MAC token with three more signed
claims. What the codec itself must guarantee is pinned here (two closed key sets, no mix, strict
values, at most 512 bytes, expiry only for an authentic token); what the stream service decides on
every request is pinned with fakes (each check fails alone, the owner-view path and the projection
path never share a guard, a bad token never reaches the store).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_video import (
    PlaybackGrant,
    PlaybackResolution,
    PlaybackStatus,
    PlaybackTarget,
    PlaybackTokenError,
    ProjectionClaims,
)
from sketch2life.application.services.story_run_playback import (
    StoryPlaybackService,
    check_playback_token,
)
from sketch2life.infrastructure.story_video import repository as video_repository
from sketch2life.infrastructure.story_video.playback_tokens import (
    MAX_GRANT_LENGTH,
    PlaybackTokenCodec,
    actor_digest,
)
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref

KEY = b"synthetic-signing-secret-A-0123456789abcdef"
RUN = str(uuid4())
GENERATION = str(uuid4())
OCCURRENCE = str(uuid4())
CONFIRMED_MS = 1_795_341_600_123
NOW = 1_900_000_000.0


class Clock:
    def __init__(self, now: float = NOW) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def codec(clock: Clock | None = None, key_id: str = "k1") -> PlaybackTokenCodec:
    return PlaybackTokenCodec(
        active_key_id=key_id, keys={key_id: KEY}, ttl_seconds=300, clock=clock or Clock()
    )


def principal(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer="synthetic-issuer", roles=frozenset())


TEACHER_A = principal("teacher-a")
TEACHER_B = principal("teacher-b")
DIGEST_A = actor_digest(parent_scope_ref(TEACHER_A))
DIGEST_B = actor_digest(parent_scope_ref(TEACHER_B))
CLAIMS = ProjectionClaims(OCCURRENCE, CONFIRMED_MS)


def issue_projection(issuer: PlaybackTokenCodec | None = None, digest: str = DIGEST_A) -> str:
    token, _ = (issuer or codec()).issue(
        run_id=RUN, generation_id=GENERATION, actor_digest=digest, projection=CLAIMS
    )
    return token


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def sign(payload: dict[str, Any], key_id: str = "k1") -> str:
    header = b64(json.dumps({"alg": "HS256", "kid": key_id}, separators=(",", ":")).encode())
    body = b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    mac = hmac.new(KEY, f"ptk1.{header}.{body}".encode(), hashlib.sha256).digest()
    return f"ptk1.{header}.{body}.{b64(mac)}"


def refuses(
    token: str, expected: str = "INVALID_TOKEN", target: PlaybackTokenCodec | None = None
) -> None:
    with pytest.raises(PlaybackTokenError) as raised:
        (target or codec()).verify(token)
    assert raised.value.code == expected


GOOD_OWNER: dict[str, Any] = {"a": DIGEST_A, "e": int(NOW) + 60, "g": GENERATION, "r": RUN}
GOOD_PROJECTION: dict[str, Any] = {
    **GOOD_OWNER,
    "c": CONFIRMED_MS,
    "o": OCCURRENCE,
    "u": "projection",
}


# ----------------------------------------------------------------------------- the codec
def test_a_projection_token_round_trips_with_its_three_claims() -> None:
    clock = Clock()
    issuer = codec(clock)
    token, expires_at = issuer.issue(
        run_id=RUN, generation_id=GENERATION, actor_digest=DIGEST_A, projection=CLAIMS
    )
    grant = issuer.verify(token)
    assert (grant.run_id, grant.generation_id, grant.actor_digest) == (RUN, GENERATION, DIGEST_A)
    assert grant.expires_at == expires_at == int(NOW) + 300
    assert (grant.audience, grant.occurrence_id, grant.confirmed_ms) == (
        "projection",
        OCCURRENCE,
        CONFIRMED_MS,
    )
    payload = json.loads(base64.urlsafe_b64decode(token.split(".")[2] + "=="))
    assert set(payload) == {"a", "c", "e", "g", "o", "r", "u"}
    assert payload["u"] == "projection"


def test_an_owner_view_token_has_no_audience_and_no_projection_claim() -> None:
    issuer = codec()
    token, _ = issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=DIGEST_A)
    grant = issuer.verify(token)
    assert (grant.audience, grant.occurrence_id, grant.confirmed_ms) == (None, None, None)
    assert set(json.loads(base64.urlsafe_b64decode(token.split(".")[2] + "=="))) == {
        "a",
        "e",
        "g",
        "r",
    }
    # two tokens that differ only in the projection claims are different tokens
    assert token != issue_projection()


def test_the_two_key_sets_are_closed_and_a_mix_is_invalid_even_with_a_right_mac() -> None:
    issuer = codec()
    assert issuer.verify(sign(GOOD_OWNER)).audience is None
    assert issuer.verify(sign(GOOD_PROJECTION)).audience == "projection"

    def without(*names: str) -> dict[str, Any]:
        return {k: v for k, v in GOOD_PROJECTION.items() if k not in names}

    for broken in (
        {**GOOD_OWNER, "u": "projection"},  # an owner set with the audience
        {**GOOD_OWNER, "o": OCCURRENCE},
        {**GOOD_OWNER, "c": CONFIRMED_MS},
        {**GOOD_OWNER, "o": OCCURRENCE, "c": CONFIRMED_MS},  # no audience
        without("u"),
        without("o"),
        without("c"),
        {**GOOD_PROJECTION, "x": 1},
        {**GOOD_PROJECTION, "u": "owner"},
        {**GOOD_PROJECTION, "u": "PROJECTION"},
        {**GOOD_PROJECTION, "u": 1},
        {**GOOD_PROJECTION, "o": "not-a-uuid"},
        {**GOOD_PROJECTION, "o": OCCURRENCE.upper() + "x"},
        {**GOOD_PROJECTION, "o": 7},
        {**GOOD_PROJECTION, "c": "1795341600123"},
        {**GOOD_PROJECTION, "c": True},
        {**GOOD_PROJECTION, "c": -1},
        {**GOOD_PROJECTION, "c": 1.5},
        {**GOOD_PROJECTION, "r": "not-a-uuid"},
        {**GOOD_PROJECTION, "a": "xyz"},
    ):
        refuses(sign(broken), "INVALID_TOKEN", issuer)


def test_a_tampered_claim_breaks_the_mac() -> None:
    token = issue_projection()
    header, payload, mac = token.split(".")[1:]
    original = json.loads(base64.urlsafe_b64decode(payload + "=="))
    for field, value in (("c", CONFIRMED_MS + 1), ("o", str(uuid4())), ("u", "owner")):
        forged = b64(
            json.dumps({**original, field: value}, sort_keys=True, separators=(",", ":")).encode()
        )
        refuses(f"ptk1.{header}.{forged}.{mac}")


def test_expiry_is_reported_only_for_an_authentic_projection_token() -> None:
    clock = Clock()
    issuer = codec(clock)
    token = issue_projection(issuer)
    clock.now += 299
    assert issuer.verify(token).audience == "projection"
    clock.now += 1
    refuses(token, "TOKEN_EXPIRED", issuer)
    header, payload, _mac = token.split(".")[1:]
    refuses(f"ptk1.{header}.{payload}.{b64(b'x' * 32)}", "INVALID_TOKEN", issuer)


def test_the_worst_case_projection_token_fits_the_512_byte_limit() -> None:
    long_key = "k" * 16  # the settings bound of the key id
    big = ProjectionClaims(str(uuid4()), 9_999_999_999_999)  # a 13-digit millisecond number
    issuer = codec(key_id=long_key)
    token, _ = issuer.issue(
        run_id=str(uuid4()), generation_id=str(uuid4()), actor_digest="f" * 32, projection=big
    )
    assert len(token) <= MAX_GRANT_LENGTH == 512
    assert len(token) < 430  # about 400: the limit is not close
    assert issuer.verify(token).confirmed_ms == big.confirmed_ms
    # the default key id of the settings
    assert len(issue_projection()) < len(token)


def test_a_token_names_the_caller_digest_not_the_organization() -> None:
    """R2 N-2: two Teachers of one organization have two different digests, and a token minted for
    one is refused for the other by the digest comparison alone, whatever else is right."""

    assert DIGEST_A != DIGEST_B
    issuer = codec()
    grant = issuer.verify(issue_projection(issuer, DIGEST_A))
    reader = Reader(playable("same-run-same-organization", scope_ref=parent_scope_ref(TEACHER_B)))
    service = StoryPlaybackService(reader, issuer, Port(True))
    with pytest.raises(ParentStoryRunError) as raised:
        service.authorize_projection(principal=TEACHER_B, run_id=RUN, grant=grant)
    assert (raised.value.status_code, raised.value.code) == (404, "RESOURCE_NOT_FOUND")


# ----------------------------------------------------------------------------- the service
class Reader:
    def __init__(self, resolution: PlaybackResolution) -> None:
        self.resolution = resolution
        self.calls: list[tuple[str, str | None]] = []

    def resolve_playback(
        self, *, principal: VerifiedPrincipal, run_id: str, generation_id: str | None
    ) -> PlaybackResolution:
        self.calls.append((run_id, generation_id))
        return self.resolution


class Port:
    def __init__(self, answer: bool) -> None:
        self.answer = answer
        self.calls: list[dict[str, Any]] = []

    def confirmation_is_current(self, **kwargs: Any) -> bool:
        self.calls.append(kwargs)
        return self.answer


def playable(_label: str = "", *, scope_ref: str | None = None) -> PlaybackResolution:
    return PlaybackResolution(
        PlaybackStatus.PLAYABLE,
        PlaybackTarget(RUN, GENERATION, scope_ref or parent_scope_ref(TEACHER_A), "parent/x/o.mp4"),
    )


def uniform(raised: pytest.ExceptionInfo[ParentStoryRunError]) -> tuple[int, str]:
    return raised.value.status_code, raised.value.code


def projection_grant() -> PlaybackGrant:
    return codec().verify(issue_projection())


def test_a_good_projection_token_passes_and_asks_the_port_the_exact_question() -> None:
    reader, port = Reader(playable()), Port(True)
    target = StoryPlaybackService(reader, codec(), port).authorize_projection(
        principal=TEACHER_A, run_id=RUN, grant=projection_grant()
    )
    assert (target.run_id, target.generation_id) == (RUN, GENERATION)
    assert reader.calls == [(RUN, GENERATION)]  # the token's generation is what is rechecked
    assert port.calls == [
        {
            "principal": TEACHER_A,
            "run_id": RUN,
            "generation_id": GENERATION,
            "occurrence_id": OCCURRENCE,
            "confirmed_ms": CONFIRMED_MS,
        }
    ]


@pytest.mark.parametrize(
    "case",
    [
        "other_run_in_path",
        "run_not_found",
        "run_not_playable",
        "other_digest",
        "confirmation_not_current",
        "owner_view_token",
    ],
)
def test_each_projection_check_fails_alone_with_the_uniform_404(case: str) -> None:
    grant = projection_grant()
    resolution = playable()
    port = Port(True)
    run_id = RUN
    if case == "other_run_in_path":
        run_id = str(uuid4())
    elif case == "run_not_found":
        resolution = PlaybackResolution(PlaybackStatus.NOT_FOUND)
    elif case == "run_not_playable":
        resolution = PlaybackResolution(PlaybackStatus.NOT_PLAYABLE)
    elif case == "other_digest":
        resolution = playable(scope_ref=parent_scope_ref(TEACHER_B))
    elif case == "confirmation_not_current":
        port = Port(False)
    elif case == "owner_view_token":
        grant = codec().verify(
            codec().issue(run_id=RUN, generation_id=GENERATION, actor_digest=DIGEST_A)[0]
        )
    reader = Reader(resolution)
    with pytest.raises(ParentStoryRunError) as raised:
        StoryPlaybackService(reader, codec(), port).authorize_projection(
            principal=TEACHER_A, run_id=run_id, grant=grant
        )
    assert uniform(raised) == (404, "RESOURCE_NOT_FOUND")
    if case in {"other_run_in_path", "owner_view_token"}:
        assert reader.calls == [] and port.calls == []  # refused before any store read


def test_the_port_is_asked_last_and_only_after_the_run_and_the_digest_passed() -> None:
    for resolution in (
        PlaybackResolution(PlaybackStatus.NOT_FOUND),
        PlaybackResolution(PlaybackStatus.NOT_PLAYABLE),
        playable(scope_ref=parent_scope_ref(TEACHER_B)),
    ):
        port = Port(True)
        with pytest.raises(ParentStoryRunError):
            StoryPlaybackService(Reader(resolution), codec(), port).authorize_projection(
                principal=TEACHER_A, run_id=RUN, grant=projection_grant()
            )
        assert port.calls == []


def test_a_projection_service_without_a_codec_or_a_port_fails_closed_with_503() -> None:
    for service in (
        StoryPlaybackService(Reader(playable()), None, Port(True)),
        StoryPlaybackService(Reader(playable()), codec(), None),
    ):
        with pytest.raises(ParentStoryRunError) as raised:
            service.authorize_projection(principal=TEACHER_A, run_id=RUN, grant=projection_grant())
        assert uniform(raised) == (503, "PROVIDER_UNAVAILABLE")


def test_the_owner_view_path_refuses_a_projection_grant_before_any_read() -> None:
    reader = Reader(playable())
    with pytest.raises(ParentStoryRunError) as raised:
        StoryPlaybackService(reader, codec(), Port(True)).authorize(
            principal=TEACHER_A, run_id=RUN, grant=projection_grant()
        )
    assert uniform(raised) == (404, "RESOURCE_NOT_FOUND")
    assert reader.calls == []  # the two kinds never share a guard


def test_the_owner_view_path_is_unchanged_for_an_owner_view_token() -> None:
    issuer = codec()
    grant = issuer.verify(
        issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=DIGEST_A)[0]
    )
    reader = Reader(playable())
    target = StoryPlaybackService(reader, issuer).authorize(
        principal=TEACHER_A, run_id=RUN, grant=grant
    )
    assert target.generation_id == GENERATION and reader.calls == [(RUN, GENERATION)]


def test_a_bad_token_is_refused_before_any_store_read() -> None:
    reader = Reader(playable())
    issuer = codec()
    token = issue_projection(issuer)
    header, payload, _mac = token.split(".")[1:]
    for bad in (f"ptk1.{header}.{payload}.{b64(b'x' * 32)}", "junk", "", token + "A"):
        with pytest.raises(ParentStoryRunError) as raised:
            check_playback_token(issuer, bad)
        assert uniform(raised) == (401, "INVALID_TOKEN")
    assert reader.calls == []  # the guard order: no store is consulted by the token check


# ----------------------------------------------------------------------------- sample_facts
class _Result:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self._row = row

    def mappings(self) -> _Result:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self._row


class _Session:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row
        self.statements: list[Any] = []

    def execute(self, statement: Any) -> _Result:
        self.statements.append(statement)
        return _Result(self.row)


def compile_postgres(session: _Session) -> str:
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    return str(session.statements[0].compile(dialect=dialect)).upper()


def facts_of(session: _Session, *, lock: bool = False) -> Any:
    return video_repository.sample_facts(cast("Session", session), RUN, lock=lock)


def _row(**changes: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "run_id": RUN,
        "occurrence_ref": OCCURRENCE,
        "run_state": "VIDEO_READY",
        "video_generation_id": GENERATION,
        "generation_state": "READY",
        "output_asset_ref": "parent/x/o.mp4",
        "technical_validation_state": "PASSED",
        "consistency_validation_state": "PASSED",
        "safety_validation_state": "PASSED",
        "completed_at": datetime(2026, 11, 22, 10, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 11, 22, 11, 0, tzinfo=UTC),
        "lesson_pin_snapshot": {
            "plan_revision_id": "plan-1",
            "plan_revision_no": 2,
            "plan_hash": "a" * 64,
        },
    }
    return {**base, **changes}


def test_sample_facts_maps_a_playable_run_and_its_plan_pin() -> None:
    session = _Session(_row())
    facts = facts_of(session)
    assert facts is not None
    assert (facts.run_id, facts.occurrence_ref, facts.generation_id) == (
        RUN,
        OCCURRENCE,
        GENERATION,
    )
    assert facts.playable is True
    assert facts.ready_at == datetime(2026, 11, 22, 10, 0, tzinfo=UTC)  # completed_at wins
    assert (facts.plan_revision_id, facts.plan_revision_no, facts.plan_hash) == (
        "plan-1",
        2,
        "a" * 64,
    )
    compiled = compile_postgres(session)
    assert "FOR SHARE" not in compiled and "FOR UPDATE" not in compiled


def test_sample_facts_locks_the_run_row_share_only_when_asked() -> None:
    session = _Session(_row())
    facts_of(session, lock=True)
    compiled = compile_postgres(session)
    assert "FOR SHARE OF RUNS" in compiled
    assert "FOR UPDATE" not in compiled


def test_sample_facts_uses_updated_at_when_a_row_has_no_completion_time() -> None:
    facts = facts_of(_Session(_row(completed_at=None)))
    assert facts is not None and facts.ready_at == datetime(2026, 11, 22, 11, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "changes",
    [
        {"run_state": "COMPLETED"},
        {"run_state": "SCRIPT_REVIEW"},
        {"generation_state": "REJECTED_BY_ADULT"},
        {"output_asset_ref": None},
        {"safety_validation_state": "FAILED"},
        {"technical_validation_state": "PENDING"},
        {"video_generation_id": None, "generation_state": None},
    ],
)
def test_sample_facts_playable_is_the_single_is_playable_predicate(changes: dict[str, Any]) -> None:
    facts = facts_of(_Session(_row(**changes)))
    assert facts is not None and facts.playable is False


@pytest.mark.parametrize("state", ["DELETE_PENDING", "DELETED"])
def test_sample_facts_treats_a_run_being_deleted_and_a_missing_run_as_absent(state: str) -> None:
    assert facts_of(_Session(_row(run_state=state))) is None
    assert facts_of(_Session(None)) is None


@pytest.mark.parametrize(
    "snapshot",
    [None, {}, {"plan_revision_no": "2"}, {"plan_revision_no": True, "plan_hash": 5}, [1, 2]],
)
def test_sample_facts_never_trusts_a_malformed_pin(snapshot: Any) -> None:
    facts = facts_of(_Session(_row(lesson_pin_snapshot=snapshot)))
    assert facts is not None
    assert facts.plan_revision_no is None and facts.plan_hash is None
    assert facts.plan_revision_id is None


def test_sample_facts_carries_no_storage_key_no_name_and_no_seed() -> None:
    facts = facts_of(_Session(_row()))
    assert facts is not None
    text = repr(facts)
    assert "parent/x" not in text and "mp4" not in text
    assert set(facts.__slots__) == {
        "run_id",
        "occurrence_ref",
        "run_state",
        "generation_id",
        "ready_at",
        "playable",
        "plan_revision_id",
        "plan_revision_no",
        "plan_hash",
    }
