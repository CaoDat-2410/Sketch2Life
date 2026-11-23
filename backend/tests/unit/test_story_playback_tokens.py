"""FEAT-066 T-1c: the signed playback token, the byte-range parser and the playback service
(SRS l.575-576, l.1676, l.1691-1693).

Offline: no database, no network. The token is a stateless MAC token (the recorded TD-07
deviation), so what the token itself must guarantee is pinned here: strict shape, constant-time
signature, key id rotation, expiry only for an authentic token, binding to one run, one generation
and one actor digest, and no token text in any error.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any
from uuid import uuid4

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_video import (
    PlaybackResolution,
    PlaybackStatus,
    PlaybackTarget,
    PlaybackTokenError,
)
from sketch2life.application.services.story_run_playback import (
    IssuedPlayback,
    RangeNotSatisfiable,
    StoryPlaybackService,
    check_playback_token,
    parse_byte_range,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.story_video import playback_tokens
from sketch2life.infrastructure.story_video.playback_tokens import (
    MAX_GRANT_LENGTH,
    PlaybackTokenCodec,
    actor_digest,
    build_playback_codec,
)

KEY_A = b"synthetic-signing-secret-A-0123456789abcdef"
KEY_B = b"synthetic-signing-secret-B-0123456789abcdef"
RUN = str(uuid4())
GENERATION = str(uuid4())
ACTOR = actor_digest("owner-scope-ref")


class Clock:
    def __init__(self, now: float = 1_900_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def codec(clock: Clock | None = None, **keys: bytes) -> PlaybackTokenCodec:
    return PlaybackTokenCodec(
        active_key_id="k1", keys=keys or {"k1": KEY_A}, ttl_seconds=300, clock=clock or Clock()
    )


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def refuses(
    token: str, expected: str = "INVALID_TOKEN", target: PlaybackTokenCodec | None = None
) -> None:
    with pytest.raises(PlaybackTokenError) as raised:
        (target or codec()).verify(token)
    assert raised.value.code == expected
    assert not token or (token not in str(raised.value) and token not in repr(raised.value))


# ----------------------------------------------------------------------------- token
def test_a_token_round_trips_and_names_one_run_one_generation_one_actor() -> None:
    clock = Clock()
    issuer = codec(clock)
    token, expires_at = issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    assert token.startswith("ptk1.") and len(token) <= MAX_GRANT_LENGTH
    assert expires_at == int(clock.now) + 300
    grant = issuer.verify(token)
    assert (grant.run_id, grant.generation_id, grant.actor_digest) == (RUN, GENERATION, ACTOR)
    assert grant.expires_at == expires_at
    assert len(token.split(".")) == 4
    # no padding, no URL-unsafe character, no secret in the token
    assert set(token) <= set(
        "ptk1.ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    )
    assert KEY_A.decode() not in token


def test_two_tokens_of_the_same_grant_share_no_stored_state_and_are_deterministic_per_second() -> (
    None
):
    issuer = codec()
    first = issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    second = issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    assert first == second  # stateless: nothing to revoke, which is why every use is rechecked


def test_expiry_is_reported_only_for_an_authentic_token() -> None:
    clock = Clock()
    issuer = codec(clock)
    token, _ = issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    clock.now += 299
    assert issuer.verify(token).run_id == RUN
    clock.now += 1
    refuses(token, "TOKEN_EXPIRED", issuer)
    # a tampered expired token is plainly invalid: the clock is never consulted before the MAC
    header, payload, mac = token.split(".")[1:]
    refuses(f"ptk1.{header}.{payload}.{b64(b'x' * 32)}", "INVALID_TOKEN", issuer)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda parts: parts[:-1] + [parts[-1][:-1] + ("A" if parts[-1][-1] != "A" else "B")],
        lambda parts: [parts[0], parts[1], parts[2] + "A", parts[3]],
        lambda parts: [parts[0], parts[1], b64(json.dumps({"r": RUN}).encode()), parts[3]],
        lambda parts: ["ptk2", *parts[1:]],
        lambda parts: parts[:-1],
        lambda parts: [*parts, "extra"],
        lambda parts: [parts[0], "", parts[2], parts[3]],
        lambda parts: [parts[0], parts[1], parts[2], ""],
        lambda parts: [parts[0], parts[1], parts[2], parts[3] + "="],
        lambda parts: [parts[0], parts[1], parts[2], parts[3] + "!"],
    ],
)
def test_every_malformed_or_tampered_shape_is_invalid(mutate: Any) -> None:
    token, _ = codec().issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    refuses(".".join(mutate(token.split("."))))


def test_oversize_empty_nonascii_and_garbage_are_invalid() -> None:
    for bad in ("", "x", "ptk1....", "ptk1." + "A" * 600, "ptk1.é.é.é", "\x00", "..."):
        refuses(bad)
    token, _ = codec().issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    refuses(token + "A" * MAX_GRANT_LENGTH)


def test_a_token_signed_by_another_key_or_with_an_unknown_key_id_is_invalid() -> None:
    other = PlaybackTokenCodec(active_key_id="k1", keys={"k1": KEY_B}, clock=Clock())
    token, _ = other.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    refuses(token)
    unknown = PlaybackTokenCodec(active_key_id="k9", keys={"k9": KEY_A}, clock=Clock())
    token, _ = unknown.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    refuses(token)


def test_a_rotated_key_still_verifies_the_previous_one_for_a_live_token() -> None:
    clock = Clock()
    old = PlaybackTokenCodec(active_key_id="k1", keys={"k1": KEY_A}, clock=clock)
    token, _ = old.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    rotated = PlaybackTokenCodec(active_key_id="k2", keys={"k2": KEY_B, "k1": KEY_A}, clock=clock)
    assert rotated.verify(token).run_id == RUN
    fresh, _ = rotated.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    assert json.loads(base64.urlsafe_b64decode(fresh.split(".")[1] + "==")) == {
        "alg": "HS256",
        "kid": "k2",
    }
    dropped = PlaybackTokenCodec(active_key_id="k2", keys={"k2": KEY_B}, clock=clock)
    refuses(token, "INVALID_TOKEN", dropped)  # the previous key was retired


def test_a_payload_with_a_wrong_field_is_invalid_even_when_the_mac_is_right() -> None:
    clock = Clock()
    issuer = codec(clock)
    header = b64(json.dumps({"alg": "HS256", "kid": "k1"}, separators=(",", ":")).encode())
    import hashlib
    import hmac

    def sign(payload: dict[str, Any]) -> str:
        body = b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        mac = hmac.new(KEY_A, f"ptk1.{header}.{body}".encode(), hashlib.sha256).digest()
        return f"ptk1.{header}.{body}.{b64(mac)}"

    good = {"a": ACTOR, "e": int(clock.now) + 60, "g": GENERATION, "r": RUN}
    assert issuer.verify(sign(good)).run_id == RUN
    for broken in (
        {**good, "r": "not-a-uuid"},
        {**good, "g": GENERATION.upper()},
        {**good, "a": "xyz"},
        {**good, "e": "soon"},
        {**good, "e": True},
        {**good, "x": 1},
        {k: v for k, v in good.items() if k != "a"},
    ):
        refuses(sign(broken), "INVALID_TOKEN", issuer)


def test_the_codec_refuses_an_unusable_configuration() -> None:
    with pytest.raises(ValueError):
        PlaybackTokenCodec(active_key_id="missing", keys={"k1": KEY_A})
    with pytest.raises(ValueError):
        PlaybackTokenCodec(active_key_id="k1", keys={"k1": KEY_A}, ttl_seconds=901)
    with pytest.raises(ValueError):
        PlaybackTokenCodec(active_key_id="k1", keys={"k1": KEY_A}, ttl_seconds=0)


def test_the_actor_binding_is_a_domain_separated_digest_and_not_the_scope_reference() -> None:
    digest = actor_digest("owner-scope-ref")
    assert len(digest) == 32 and "owner-scope-ref" not in digest
    assert digest != actor_digest("other-scope-ref")
    assert codec().actor_binding("owner-scope-ref") == digest


# ----------------------------------------------------------------------------- settings
def settings(**values: Any) -> Settings:
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


def test_with_no_secret_staging_and_production_build_no_codec_and_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # attach to the module logger itself: other tests of the suite reconfigure the root logging
    messages: list[str] = []

    class _Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    logger = playback_tokens._LOG
    handler = _Collect(level=logging.WARNING)
    monkeypatch.setattr(logger, "disabled", False)
    monkeypatch.setattr(logger, "level", logging.WARNING)
    monkeypatch.setattr(logger, "propagate", False)
    logger.addHandler(handler)
    try:
        for env in ("staging", "production"):
            config = settings(
                env=env,
                auth_provider="firebase",
                firebase_project_id="synthetic-project",
                ai_provider="runpod",
                runpod_endpoint_id="synthetic-endpoint",
                runpod_api_key_file="synthetic.key",
            )
            assert config.story_playback_signing_secret is None
            assert build_playback_codec(config) is None
    finally:
        logger.removeHandler(handler)
    assert len(messages) == 2
    for message in messages:
        assert "story_playback_signing_secret_missing" in message
        assert "setting=story_playback_signing_secret" in message


def test_local_and_test_use_a_per_process_key_and_a_set_secret_is_used_everywhere() -> None:
    for env in ("local", "test"):
        built = build_playback_codec(settings(env=env))
        assert built is not None
        token, _ = built.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
        assert built.verify(token).generation_id == GENERATION
        # another process draws another key: its tokens are INVALID_TOKEN here
        other = build_playback_codec(settings(env=env))
        assert other is not None
        refuses(token, "INVALID_TOKEN", other)
    secret = "s" * 40
    configured = build_playback_codec(
        settings(env="test", story_playback_signing_secret=secret, story_playback_key_id="k7")
    )
    assert configured is not None
    twin = build_playback_codec(
        settings(env="test", story_playback_signing_secret=secret, story_playback_key_id="k7")
    )
    assert twin is not None
    token, _ = configured.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    assert twin.verify(token).run_id == RUN  # the same secret works on another worker


def test_secret_rules_ttl_bounds_and_rotation_settings_never_echo_a_value() -> None:
    bad_values = ("short", "x" * 31, "x" * 31 + " ", "é" * 40, ("a" * 31) + "\n")
    for value in bad_values:
        with pytest.raises(ValueError) as raised:
            settings(env="test", story_playback_signing_secret=value)
        assert value.strip() not in str(raised.value) or not value.strip()
    assert (
        settings(env="test", story_playback_signing_secret="   ").story_playback_signing_secret
        is None
    )
    for ttl in (29, 901):
        with pytest.raises(ValueError):
            settings(env="test", story_playback_token_ttl_seconds=ttl)
    assert settings(env="test").story_playback_token_ttl_seconds == 300
    with pytest.raises(ValueError):  # a previous secret needs the active one and its own key id
        settings(env="test", story_playback_previous_secret="p" * 40)
    with pytest.raises(ValueError):
        settings(
            env="test",
            story_playback_signing_secret="a" * 40,
            story_playback_previous_secret="p" * 40,
            story_playback_previous_key_id="k1",
        )
    rotating = build_playback_codec(
        settings(
            env="test",
            story_playback_signing_secret="a" * 40,
            story_playback_key_id="k2",
            story_playback_previous_secret="p" * 40,
            story_playback_previous_key_id="k1",
        )
    )
    assert rotating is not None


# ----------------------------------------------------------------------------- ranges
@pytest.mark.parametrize(
    ("header", "size", "expected"),
    [
        (None, 100, None),
        ("", 100, None),
        ("bytes=0-9", 100, (0, 9)),
        ("bytes=10-", 100, (10, 99)),
        ("bytes=-10", 100, (90, 99)),
        ("bytes=-500", 100, (0, 99)),
        ("bytes=95-5000", 100, (95, 99)),
        ("bytes=99-99", 100, (99, 99)),
        (" bytes=0-0 ", 100, (0, 0)),
    ],
)
def test_valid_single_ranges(
    header: str | None, size: int, expected: tuple[int, int] | None
) -> None:
    assert parse_byte_range(header, size) == expected


@pytest.mark.parametrize(
    ("header", "size"),
    [
        ("bytes=100-", 100),
        ("bytes=5-2", 100),
        ("bytes=0-1,4-5", 100),
        ("bytes=-0", 100),
        ("bytes=-", 100),
        ("bytes=", 100),
        ("items=0-1", 100),
        ("bytes=a-b", 100),
        ("bytes=0-9", 0),
        ("bytes=-5", 0),
        ("bytes = 0-9", 100),
        ("bytes=0-9;x", 100),
        ("bytes=" + "9" * 40 + "-", 100),
    ],
)
def test_refused_ranges(header: str, size: int) -> None:
    with pytest.raises(RangeNotSatisfiable):
        parse_byte_range(header, size)


# ----------------------------------------------------------------------------- service
PRINCIPAL = VerifiedPrincipal("adult-1", "issuer-1", frozenset())


class Reader:
    def __init__(self, resolution: PlaybackResolution) -> None:
        self.resolution = resolution
        self.calls: list[tuple[str, str | None]] = []

    def resolve_playback(
        self, *, principal: VerifiedPrincipal, run_id: str, generation_id: str | None
    ) -> PlaybackResolution:
        self.calls.append((run_id, generation_id))
        return self.resolution


def playable(scope_ref: str = "owner-scope-ref") -> PlaybackResolution:
    return PlaybackResolution(
        PlaybackStatus.PLAYABLE, PlaybackTarget(RUN, GENERATION, scope_ref, "parent/x/output.mp4")
    )


def test_issue_maps_the_resolution_and_fails_closed_without_a_codec() -> None:
    service = StoryPlaybackService(Reader(playable()), codec())
    issued = service.issue(principal=PRINCIPAL, run_id=RUN)
    assert isinstance(issued, IssuedPlayback)
    assert issued.run_id == RUN and issued.generation_id == GENERATION
    assert issued.token not in repr(issued)  # the secret is not in the repr
    assert codec().verify(issued.token).actor_digest == ACTOR
    for status, expected in (
        (PlaybackStatus.NOT_FOUND, (404, "RESOURCE_NOT_FOUND")),
        (PlaybackStatus.NOT_PLAYABLE, (409, "INVALID_STATE_TRANSITION")),
    ):
        with pytest.raises(ParentStoryRunError) as raised:
            StoryPlaybackService(Reader(PlaybackResolution(status)), codec()).issue(
                principal=PRINCIPAL, run_id=RUN
            )
        assert (raised.value.status_code, raised.value.code) == expected
    # no secret: 503 only after the 404 and 409 checks (a foreign actor never sees 503 first)
    with pytest.raises(ParentStoryRunError) as raised:
        StoryPlaybackService(Reader(PlaybackResolution(PlaybackStatus.NOT_FOUND)), None).issue(
            principal=PRINCIPAL, run_id=RUN
        )
    assert raised.value.status_code == 404
    with pytest.raises(ParentStoryRunError) as raised:
        StoryPlaybackService(Reader(playable()), None).issue(principal=PRINCIPAL, run_id=RUN)
    assert (raised.value.status_code, raised.value.code) == (503, "PROVIDER_UNAVAILABLE")


def test_check_token_maps_the_two_failures_and_503_without_a_codec() -> None:
    with pytest.raises(ParentStoryRunError) as raised:
        check_playback_token(None, "anything")
    assert (raised.value.status_code, raised.value.code) == (503, "PROVIDER_UNAVAILABLE")
    for bad in (None, "", "junk"):
        with pytest.raises(ParentStoryRunError) as raised:
            check_playback_token(codec(), bad)
        assert (raised.value.status_code, raised.value.code) == (401, "INVALID_TOKEN")
    clock = Clock()
    issuer = codec(clock)
    token, _ = issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    clock.now += 400
    with pytest.raises(ParentStoryRunError) as raised:
        check_playback_token(issuer, token)
    assert (raised.value.status_code, raised.value.code) == (401, "TOKEN_EXPIRED")
    assert token not in str(raised.value)


def test_authorize_is_the_uniform_404_for_every_mismatch() -> None:
    issuer = codec()
    token, _ = issuer.issue(run_id=RUN, generation_id=GENERATION, actor_digest=ACTOR)
    grant = issuer.verify(token)
    ok = StoryPlaybackService(Reader(playable()), issuer)
    assert ok.authorize(principal=PRINCIPAL, run_id=RUN, grant=grant).generation_id == GENERATION

    def refused(service: StoryPlaybackService, run_id: str = RUN) -> tuple[int, str]:
        with pytest.raises(ParentStoryRunError) as raised:
            service.authorize(principal=PRINCIPAL, run_id=run_id, grant=grant)
        return raised.value.status_code, raised.value.code

    uniform = (404, "RESOURCE_NOT_FOUND")
    assert refused(ok, run_id=str(uuid4())) == uniform  # another run in the path: no store read
    for status in (PlaybackStatus.NOT_FOUND, PlaybackStatus.NOT_PLAYABLE):
        assert refused(StoryPlaybackService(Reader(PlaybackResolution(status)), issuer)) == uniform
    # a valid token presented by another actor (the target is that actor's scope): the same 404
    assert refused(StoryPlaybackService(Reader(playable("someone-else")), issuer)) == uniform
    assert refused(StoryPlaybackService(Reader(playable()), None)) == (503, "PROVIDER_UNAVAILABLE")
    reader = Reader(playable())
    StoryPlaybackService(reader, issuer).authorize(principal=PRINCIPAL, run_id=RUN, grant=grant)
    assert reader.calls == [(RUN, GENERATION)]  # the token's generation is what is rechecked
