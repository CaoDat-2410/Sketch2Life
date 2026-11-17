"""X01: actual BE2-07 export is resolved and consumed by the BE2-08 pipeline."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from sketch2life.application.knowledge_video_media import (
    CheckedMediaValidator,
    VideoMediaPipeline,
)
from sketch2life.application.ports.knowledge_video_media import (
    RenderAttempt,
    VideoSourceMaterial,
)
from sketch2life.application.services.knowledge_bundle import CreateKnowledgeCommand
from sketch2life.contracts.schemas.knowledge_bundles import KnowledgeBundleExportV1
from sketch2life.domain.knowledge_video.media import DecodedMedia, MediaBlob, MediaProfile
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    Strategy,
    VideoError,
    VideoPin,
    VideoRun,
)
from sketch2life.infrastructure.cross_lane.knowledge_script_video import (
    KnowledgeScriptVideoSourceResolver,
)
from sketch2life.infrastructure.knowledge_bundle.harness import (
    TEACHER_A,
    KnowledgeHarness,
    build_knowledge_harness,
)

NOW = datetime(2026, 10, 20, tzinfo=UTC)
PAYLOAD = b"fixture-video-bytes-not-a-real-video"
PAYLOAD_HASH = hashlib.sha256(PAYLOAD).hexdigest()


def _ref(name: str, digest: str = "a" * 64) -> ExactRef:
    return ExactRef(name, 1, digest)


class _ExternalRenderChecks:
    """Synthetic BE1/foundation capability checks; BE2-07 is checked separately."""

    def __init__(self) -> None:
        self.phases: list[str] = []

    def check(self, attempt: RenderAttempt, phase: str) -> None:
        self.phases.append(phase)
        if attempt.capability != "fixture-private-capability":
            raise VideoError("VIDEO_STALE_CONTEXT")


class _CrossLaneRenderAuthority:
    def __init__(
        self,
        external: _ExternalRenderChecks,
        source: KnowledgeScriptVideoSourceResolver,
    ) -> None:
        self.external = external
        self.source = source

    def check(self, attempt: RenderAttempt, phase: str) -> None:
        self.external.check(attempt, phase)
        if phase in {
            "source",
            "source_returned",
            "generation",
            "generation_returned",
            "validation",
            "validation_returned",
        }:
            self.source.assert_current(attempt)


class _CapturingGenerator:
    def __init__(self, on_generate: Callable[[], None] | None = None) -> None:
        self.sources: list[VideoSourceMaterial] = []
        self.on_generate = on_generate

    def generate(
        self, attempt: RenderAttempt, source: VideoSourceMaterial, operation_key: str
    ) -> MediaBlob:
        del attempt, operation_key
        self.sources.append(source)
        if self.on_generate is not None:
            self.on_generate()
        return MediaBlob(PAYLOAD, PAYLOAD_HASH)


class _FixtureDecoder:
    def decode(self, blob: MediaBlob, encoding: ExactRef) -> DecodedMedia:
        del encoding
        return DecodedMedia(
            blob.sha256, "fixture.container", "fixture.codec", 16, 16, 500, 12, (), True
        )


class _ProfileResolver:
    def __init__(self, profile: MediaProfile) -> None:
        self.profile = profile

    def resolve(self, attempt: RenderAttempt) -> MediaProfile:
        del attempt
        return self.profile


class _InvalidatingSource(KnowledgeScriptVideoSourceResolver):
    def __init__(self, producer: KnowledgeHarness) -> None:
        super().__init__(producer.service, TEACHER_A, producer.coordinator)
        self.producer = producer

    def load(self, attempt: RenderAttempt) -> VideoSourceMaterial:
        material = super().load(attempt)
        changed_basis = replace(self.producer.topic, revision=self.producer.topic.revision + 1)
        self.producer.facts.publish_basis(changed_basis)
        return material


def _composition(
    *,
    invalidate_source_after_load: bool = False,
    invalidate_source_during_generation: bool = False,
) -> tuple[
    KnowledgeHarness,
    KnowledgeBundleExportV1,
    RenderAttempt,
    KnowledgeScriptVideoSourceResolver,
    _CapturingGenerator,
    VideoMediaPipeline,
]:
    producer = build_knowledge_harness()
    created = producer.service.create(
        CreateKnowledgeCommand(TEACHER_A, "cross-lane-create", producer.create_body())
    )
    record = created.record
    resolved = producer.service.resolve_exact(
        TEACHER_A, record.bundle_id, record.bundle_version, record.bundle_hash
    )
    assert resolved.ready and resolved.export is not None
    exported = resolved.export

    sources = tuple(
        sorted(
            (
                ExactRef(item.ref.source_id, item.ref.revision, item.ref.sha256)
                for item in exported.source_records
            ),
            key=lambda ref: (ref.ref, ref.version, ref.hash),
        )
    )
    pin = VideoPin(
        organization_id=exported.organization_id,
        session_id=exported.session_id,
        bundle=ExactRef(exported.bundle_id, exported.bundle_version, exported.bundle_hash),
        editorial_revision=exported.editorial_revision,
        context_revision=exported.context_revision,
        audience_revision=exported.audience_revision,
        sources=sources,
        strategy=Strategy.GENERATE,
        content_profile=_ref("profile"),
        encoding=_ref("encoding"),
        rights=_ref("rights"),
        retry_policy=_ref("retry"),
        policy=_ref("policy"),
        policy_epoch=1,
        model_profile=_ref("model"),
    )
    run = VideoRun("video-x01", 1, 1, 1, "job-x01", pin, NOW).start(1, "attempt-x01")
    attempt = RenderAttempt(run, 2, "fixture-private-capability")
    source: KnowledgeScriptVideoSourceResolver
    if invalidate_source_after_load:
        source = _InvalidatingSource(producer)
    else:
        source = KnowledgeScriptVideoSourceResolver(
            producer.service, TEACHER_A, producer.coordinator
        )
    external = _ExternalRenderChecks()
    authority = _CrossLaneRenderAuthority(external, source)
    profile = MediaProfile(
        pin.content_profile,
        pin.encoding,
        (Strategy.GENERATE,),
        ("fixture.container",),
        ("fixture.codec",),
        ((16, 16),),
        100,
        1000,
        128,
        2,
        (),
        0,
    )
    def invalidate_source_basis() -> None:
        changed_basis = replace(producer.topic, revision=producer.topic.revision + 1)
        producer.facts.publish_basis(changed_basis)

    generator = _CapturingGenerator(
        invalidate_source_basis if invalidate_source_during_generation else None
    )
    pipeline = VideoMediaPipeline(
        authority,
        _ProfileResolver(profile),
        source,
        CheckedMediaValidator(_FixtureDecoder()),
        generator=generator,
    )
    return producer, exported, attempt, source, generator, pipeline


def test_exact_be2_07_export_is_loaded_and_passed_to_be2_08_generation() -> None:
    _, exported, attempt, _, generator, pipeline = _composition()

    prepared = pipeline.prepare(attempt)

    assert len(generator.sources) == 1
    assert generator.sources[0].bundle == attempt.run.pin.bundle
    assert generator.sources[0].pin_digest == attempt.run.pin.digest()
    assert generator.sources[0].script == exported.script_text
    assert prepared.pin_digest == attempt.run.pin.digest()
    assert prepared.strategy is Strategy.GENERATE


def test_source_change_after_read_is_rejected_before_be2_08_generator_runs() -> None:
    _, _, attempt, _, generator, pipeline = _composition(
        invalidate_source_after_load=True
    )

    with pytest.raises(VideoError, match="VIDEO_SOURCE_UNAVAILABLE"):
        pipeline.prepare(attempt)

    assert generator.sources == []


def test_source_change_during_generation_is_rejected_before_media_is_returned() -> None:
    _, _, attempt, _, generator, pipeline = _composition(
        invalidate_source_during_generation=True
    )

    with pytest.raises(VideoError, match="VIDEO_SOURCE_UNAVAILABLE"):
        pipeline.prepare(attempt)

    assert len(generator.sources) == 1


def test_wrong_exact_bundle_hash_is_rejected_before_be2_08_generator_runs() -> None:
    _, _, attempt, source, generator, pipeline = _composition()
    wrong_pin = replace(
        attempt.run.pin,
        bundle=ExactRef(
            attempt.run.pin.bundle.ref,
            attempt.run.pin.bundle.version,
            "b" * 64,
        ),
    )
    wrong_run = replace(attempt.run, pin=wrong_pin)
    wrong_attempt = replace(attempt, run=wrong_run)

    with pytest.raises(VideoError, match="VIDEO_SOURCE_UNAVAILABLE"):
        source.load(wrong_attempt)

    assert generator.sources == []
