"""Explicit local/test composition for the analysis-only synthetic vision pilot."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import Lock
from typing import cast
from uuid import uuid4

from sqlalchemy import Connection, Engine, select, text
from sqlalchemy.orm import Session

from sketch2life.application.ports.ai_jobs import (
    OWNER_FENCE_CONTRACT,
    AiProviderPort,
    ArtifactDescriptor,
    AuditEvent,
    AuditPort,
    AuthorizationAction,
    AuthorizationDecision,
    AuthorizationPort,
    ClockPort,
    DispatchMessage,
    EligibilityDecision,
    EligibilityPort,
    FenceResult,
    IdGeneratorPort,
    OwnerFence,
    OwnerFencePort,
    Principal,
    QuarantineIntent,
    VerifiedCapability,
    WorkerCapabilityIssuer,
    WorkerCapabilityVerifier,
)
from sketch2life.application.ports.assistance import (
    AnalysisOutcomePort,
    AssistanceAuthority,
    AssistanceAuthorityPort,
    AssistanceJobPort,
    AssistanceJobReader,
    CanvasFacts,
    ResolvedSource,
    SketchStagePort,
)
from sketch2life.application.ports.vision_analysis import (
    AnalysisAction,
    AnalysisAuthorityPort,
    AuthorityReason,
    InvocationGuardState,
    ObservationFailed,
    ObservationFailureCode,
    ObservationRequest,
    VisionObservationPort,
)
from sketch2life.application.ports.vision_analysis import (
    AuthorityDecision as VisionAuthorityDecision,
)
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    AiJobDependencies,
    AiJobService,
)
from sketch2life.application.services.assistance import AssistanceDependencies, AssistanceService
from sketch2life.application.services.vision_analysis import (
    VisionAnalysisDependencies,
    VisionAnalysisService,
)
from sketch2life.contracts.schemas.be1_runtime import CanvasSourceExportV1
from sketch2life.domain.ai_jobs.completion import (
    CompletionClaim,
    Moderation,
    OutcomeKind,
    OutputRef,
)
from sketch2life.domain.ai_jobs.model import JobScope, RequestRef
from sketch2life.domain.assistance import NON_TERMINAL, AssistanceRequest, ResolvedFacts
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityBasis, EligibilityScope
from sketch2life.domain.vision_analysis import (
    VISION_ANALYSIS_JOB_TYPE,
    AnalysisScope,
    AssistancePin,
    ObservationClaim,
    ProviderContextMode,
)
from sketch2life.domain.vision_context import ContextCapability
from sketch2life.infrastructure.ai.lightning_client import read_secret_file
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobRepository
from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker, WorkerOutcome
from sketch2life.infrastructure.assistance.be1_canvas_source_adapter import (
    PostgresCanvasSourceAdapter,
)
from sketch2life.infrastructure.assistance.be1_owner_adapter import PostgresAssistanceOwnerAdapter
from sketch2life.infrastructure.assistance.owner_fence import (
    BE1OwnerFenceScope,
    PostgresBE1OwnerFence,
    ResolvedFactsResolver,
    build_owner_fence,
    decode_owner_fence_scope,
)
from sketch2life.infrastructure.assistance.pilot_policy import (
    PILOT_SYNTHETIC_POLICY_V1,
)
from sketch2life.infrastructure.assistance.sql_repository import (
    SqlAssistanceRepository,
    SqlAssistanceUnitOfWork,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomSessionModel,
    DeviceGrantModel,
    OrganizationAssignmentModel,
    SessionMembershipModel,
)
from sketch2life.infrastructure.storage.persistent_local_artifacts import LocalArtifactStore
from sketch2life.infrastructure.vision_analysis.invocation_guard import (
    InvocationGuardedVisionObservationPort,
    InvocationLedgerGuard,
)
from sketch2life.infrastructure.vision_analysis.job_lineage import AiJobRepositoryLineage
from sketch2life.infrastructure.vision_analysis.ledger import InvocationLedger
from sketch2life.infrastructure.vision_analysis.legacy_v2 import LegacyVisionV2Bridge
from sketch2life.infrastructure.vision_analysis.pilot_policy import PILOT_VISION_RETRY_POLICY
from sketch2life.infrastructure.vision_analysis.pilot_queue import InProcessDispatchQueue
from sketch2life.infrastructure.vision_analysis.repository import SqlAnalysisRepository
from sketch2life.infrastructure.vision_analysis.transport import HttpJsonTransport

CurrentRequestFactsResolver = Callable[[str, str], tuple[AssistanceRequest, ResolvedFacts] | None]
ObservationBindingResolver = Callable[[DispatchMessage], "PilotObservationBinding | None"]
VisionServiceFactory = Callable[
    ["PilotObservationBinding", InvocationLedgerGuard], VisionAnalysisService
]

_AUTH_FENCE_PREFIX = "be1-pilot-auth-v1:"
_ARTIFACT_FENCE_PREFIX = "be1-pilot-artifact-v1:"


def _decode_artifact_fence_scope(scope: str) -> dict[str, str] | None:
    if not scope.startswith(_ARTIFACT_FENCE_PREFIX):
        return None
    try:
        payload = json.loads(scope.removeprefix(_ARTIFACT_FENCE_PREFIX))
    except (TypeError, ValueError):
        return None
    if (
        not isinstance(payload, dict)
        or set(payload) != {"artifact_ref", "organization_id", "sha256"}
        or not all(isinstance(value, str) and value for value in payload.values())
        or len(payload["sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in payload["sha256"])
    ):
        return None
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return payload if scope == _ARTIFACT_FENCE_PREFIX + canonical else None


@dataclass(frozen=True, slots=True)
class PilotObservationBinding:
    organization_id: str
    assistance_id: str
    input_snapshot_ref: str
    request_revision: int
    input_hash: str
    context_revision: int
    correlation_id: str


class PostgresBe1PilotAuthorization(AuthorizationPort):
    """Authorize only a current Teacher/Admin assignment or admitted Child device."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def decide(
        self, principal: Principal, action: AuthorizationAction, scope: JobScope
    ) -> AuthorizationDecision:
        if (
            action is not AuthorizationAction.CREATE_JOB
            or not scope.session_id
            or not scope.organization_id
            or len(scope.subject_refs) != 1
            or scope.purpose_code != PILOT_SYNTHETIC_POLICY_V1.purpose_code
        ):
            return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
        try:
            with self._engine.connect() as connection:
                session = (
                    connection.execute(
                        select(
                            ClassroomSessionModel.state.label("state"),
                            ClassroomSessionModel.configuration.label("configuration"),
                            ClassroomSessionModel.class_id.label("class_id"),
                        ).where(
                            ClassroomSessionModel.organization_id == scope.organization_id,
                            ClassroomSessionModel.session_id == scope.session_id,
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    session is None
                    or session["state"] != "active"
                    or not _synthetic_session(session["configuration"], scope.purpose_code)
                ):
                    return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
                payload = _authorization_payload(connection, principal, scope, session["class_id"])
        except Exception:
            return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
        if payload is None:
            return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
        return AuthorizationDecision(
            True,
            fence=OwnerFence(
                _AUTH_FENCE_PREFIX + json.dumps(payload, sort_keys=True, separators=(",", ":")),
                1,
            ),
        )


class CurrentFactsBe1PilotEligibility(EligibilityPort):
    """Revalidate job pins against persisted request data and recomputed BE1 facts."""

    def __init__(self, resolve_current: CurrentRequestFactsResolver) -> None:
        self._resolve_current = resolve_current

    def check(
        self, *, scope: JobScope, request_ref: RequestRef, job_type: str
    ) -> EligibilityDecision:
        if (
            job_type != VISION_ANALYSIS_JOB_TYPE
            or scope.target_id != request_ref.request_id
            or len(scope.subject_refs) != 1
        ):
            return EligibilityDecision(False, "STALE_CONTEXT", 0)
        try:
            resolved = self._resolve_current(scope.organization_id, request_ref.request_id)
        except Exception:
            resolved = None
        if resolved is None:
            return EligibilityDecision(False, "STALE_CONTEXT", 0)
        request, facts = resolved
        if (
            request.assistance_id != request_ref.request_id
            or request.status not in NON_TERMINAL
            or request.facts.organization_id != scope.organization_id
            or request.request_revision != request_ref.request_revision
            or request.facts.source.input_hash != request_ref.input_hash
            or facts.source.input_hash != request_ref.input_hash
            or request.facts.context_revision != request_ref.context_revision
            or facts.context_revision != request_ref.context_revision
            or request.assistance_context_digest != facts.digest()
            or facts.session_id != scope.session_id
            or facts.audience != scope.subject_refs
            or facts.purpose_code != scope.purpose_code
            or not _synthetic_facts(facts)
        ):
            return EligibilityDecision(False, "STALE_CONTEXT", facts.context_revision)
        try:
            fence = build_owner_fence(facts)
        except (TypeError, ValueError):
            return EligibilityDecision(False, "STALE_CONTEXT", facts.context_revision)
        return EligibilityDecision(
            True,
            None,
            facts.context_revision,
            fence,
        )


class _CombinedBe1OwnerFence(OwnerFencePort):
    contract_version = OWNER_FENCE_CONTRACT

    def __init__(
        self,
        connection: Connection,
        resolve_facts: ResolvedFactsResolver,
        *,
        lock_timeout_ms: int,
        artifacts: PilotFakeArtifacts,
    ) -> None:
        self._connection = connection
        self._resolve_facts = resolve_facts
        self._lock_timeout_ms = lock_timeout_ms
        self._artifacts = artifacts

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        auth_fences: list[OwnerFence] = []
        facts_fences: list[OwnerFence] = []
        artifact_fences: list[OwnerFence] = []
        seen_scopes: set[str] = set()
        for fence in fences:
            scope = fence.fence_scope
            if scope in seen_scopes:
                return _stale(fences)
            seen_scopes.add(scope)
            if scope.startswith(_AUTH_FENCE_PREFIX):
                auth_fences.append(fence)
            elif scope.startswith(_ARTIFACT_FENCE_PREFIX):
                artifact_fences.append(fence)
            elif decode_owner_fence_scope(scope) is not None:
                facts_fences.append(fence)
            else:
                return _stale(fences)
        if len(auth_fences) > 1:
            return _stale(fences)
        try:
            if auth_fences:
                if not self._connection.in_transaction():
                    return _stale(fences)
                self._connection.execute(
                    text("SELECT set_config('lock_timeout', :timeout, true)"),
                    {"timeout": f"{self._lock_timeout_ms}ms"},
                )
                if not _hold_authorization_fence(self._connection, auth_fences[0]):
                    return _stale(fences)
            if facts_fences or auth_fences:
                result = PostgresBE1OwnerFence(
                    self._connection,
                    self._resolve_facts,
                    lock_timeout_ms=self._lock_timeout_ms,
                ).hold(tuple(facts_fences))
                if not result.current:
                    return _stale(fences)
            if artifact_fences and not self._artifacts.hold_fences(tuple(artifact_fences)).current:
                return _stale(fences)
            return FenceResult(True)
        except Exception:
            return _stale(fences)


class _CombinedBe1OwnerFenceFactory:
    def __init__(
        self,
        resolve_facts: ResolvedFactsResolver,
        lock_timeout_ms: int,
        artifacts: PilotFakeArtifacts,
    ) -> None:
        self._resolve_facts = resolve_facts
        self._lock_timeout_ms = lock_timeout_ms
        self._artifacts = artifacts

    def __call__(self, connection: Connection) -> OwnerFencePort:
        return _CombinedBe1OwnerFence(
            connection,
            self._resolve_facts,
            lock_timeout_ms=self._lock_timeout_ms,
            artifacts=self._artifacts,
        )


class PilotFakeIds(IdGeneratorPort):
    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"


class PilotSystemClock(ClockPort):
    def now(self) -> datetime:
        return datetime.now(UTC)


class PilotFakeAudit(AuditPort):
    def __init__(self) -> None:
        self.events: dict[str, AuditEvent] = {}

    def record(self, event: AuditEvent) -> None:
        self.events.setdefault(event.event_id, event)


class PilotFakeArtifacts:
    """Process-local pilot artifacts and fences.

    This store is non-durable and does not provide production or cross-process locking.
    """

    def __init__(self) -> None:
        self._items: dict[str, ArtifactDescriptor] = {}
        self._bodies: dict[str, bytes] = {}
        self._quarantined: dict[str, str] = {}
        self._epochs: dict[str, int] = {}
        self._lock = Lock()

    def write_output(
        self, organization_id: str, body: bytes, *, job_id: str, attempt_id: str
    ) -> OutputRef:
        if not organization_id or not body:
            raise ValueError("pilot artifact identity and body are required")
        digest = sha256(body).hexdigest()
        artifact_ref = f"pilot-fake-artifact:{uuid4()}"
        with self._lock:
            self._bodies[artifact_ref] = body
            self._epochs[artifact_ref] = 0
            self._items[artifact_ref] = ArtifactDescriptor(
                artifact_ref,
                digest,
                organization_id,
                producer_job_id=job_id,
                producer_attempt_id=attempt_id,
                fence=self._fence(artifact_ref, organization_id, digest, 0),
            )
        return OutputRef(artifact_ref, digest)

    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None:
        with self._lock:
            descriptor = self._items.get(artifact_ref)
            if descriptor is None:
                return None
            return ArtifactDescriptor(
                descriptor.artifact_ref,
                descriptor.sha256,
                descriptor.organization_id,
                descriptor.producer_job_id,
                descriptor.producer_attempt_id,
                self._quarantined.get(artifact_ref),
                self._fence(
                    artifact_ref,
                    descriptor.organization_id,
                    descriptor.sha256,
                    self._epochs[artifact_ref],
                ),
            )

    def hold_fences(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        """Check process-local state under the lock; this is a point-in-time pilot fence.

        The lock is released when this method returns, before the caller commits its SQL
        transaction. It does not prevent quarantine between this check and that commit.
        """
        with self._lock:
            for fence in fences:
                if type(fence.epoch) is not int or fence.epoch < 0:
                    return _stale(fences)
                payload = _decode_artifact_fence_scope(fence.fence_scope)
                if payload is None:
                    return _stale(fences)
                artifact_ref = payload["artifact_ref"]
                descriptor = self._items.get(artifact_ref)
                if (
                    descriptor is None
                    or artifact_ref in self._quarantined
                    or descriptor.organization_id != payload["organization_id"]
                    or descriptor.sha256 != payload["sha256"]
                    or fence.epoch != self._epochs.get(artifact_ref)
                ):
                    return _stale(fences)
        return FenceResult(True)

    def quarantine(self, intent: QuarantineIntent) -> None:
        with self._lock:
            for ref in intent.artifact_refs:
                if ref not in self._quarantined:
                    self._quarantined[ref] = intent.reason_code
                    self._epochs[ref] = self._epochs.get(ref, 0) + 1

    @staticmethod
    def _fence(artifact_ref: str, organization_id: str, digest: str, epoch: int) -> OwnerFence:
        scope = json.dumps(
            {
                "artifact_ref": artifact_ref,
                "organization_id": organization_id,
                "sha256": digest,
            },
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return OwnerFence(_ARTIFACT_FENCE_PREFIX + scope, epoch)


class PilotFakeCapabilities(WorkerCapabilityIssuer, WorkerCapabilityVerifier):
    def __init__(self, clock: ClockPort) -> None:
        self._clock = clock
        self._claims: dict[str, VerifiedCapability] = {}
        self._lock = Lock()

    def issue(self, job_id: str, attempt_id: str, now: datetime) -> str:
        token = f"pilot-fake-capability:{uuid4()}"
        claim = VerifiedCapability(job_id, attempt_id, now, now + timedelta(days=365), "pilot")
        with self._lock:
            self._claims[token] = claim
        return token

    def verify(self, capability: str) -> VerifiedCapability | None:
        with self._lock:
            claim = self._claims.get(capability)
        if claim is None or claim.expires_at <= self._clock.now():
            return None
        return claim


PILOT_FAKE_IDS = PilotFakeIds
PILOT_FAKE_AUDIT = PilotFakeAudit
PILOT_FAKE_ARTIFACTS = PilotFakeArtifacts
PILOT_FAKE_CAPABILITIES = PilotFakeCapabilities


@dataclass(slots=True)
class PilotVisionComposition:
    jobs: AiJobService
    queue: InProcessDispatchQueue
    worker: DispatchWorker
    provider: AiProviderPort
    invocation_ledger: InvocationLedger
    fake_artifacts: PilotFakeArtifacts
    fake_audit: PilotFakeAudit

    def dispatch_one(self) -> WorkerOutcome | None:
        self.jobs.dispatch_outbox()
        outcome = self.queue.run_one(self.worker)
        return outcome if isinstance(outcome, WorkerOutcome) else None


class GuardedVisionJobProvider(AiProviderPort):
    """Worker adapter that creates one durable invocation guard for each message attempt."""

    def __init__(
        self,
        *,
        ledger: InvocationLedger,
        resolve_binding: ObservationBindingResolver,
        service_factory: VisionServiceFactory,
        artifacts: PilotFakeArtifacts,
        ids: PilotFakeIds,
    ) -> None:
        self._ledger = ledger
        self._resolve_binding = resolve_binding
        self._service_factory = service_factory
        self._artifacts = artifacts
        self._ids = ids

    def run(self, message: DispatchMessage) -> CompletionClaim:
        ref = message.request_ref
        binding = self._resolve_binding(message)
        if (
            binding is None
            or binding.assistance_id != ref.request_id
            or binding.request_revision != ref.request_revision
            or binding.input_hash != ref.input_hash
            or binding.context_revision != ref.context_revision
            or not binding.organization_id
        ):
            return _failed_claim(message, "STALE_CONTEXT")
        guard = InvocationLedgerGuard(
            ledger=self._ledger,
            run_id=str(uuid4()),
            job_id=message.job_id,
            attempt_id=message.attempt_id,
            organization_id=binding.organization_id,
        )
        try:
            service = self._service_factory(binding, guard)
            # Construction of InvocationGuardedVisionObservationPort enforces this identity.
            provider = getattr(getattr(service, "_d", None), "provider", None)
            if not isinstance(provider, InvocationGuardedVisionObservationPort) or (
                getattr(provider, "_guard", None) is not guard
            ):
                return _failed_claim(message, "PROVIDER_UNAVAILABLE")
            result = service.record_observation(
                ObservationClaim(
                    job_id=message.job_id,
                    job_attempt_id=message.attempt_id,
                    assistance_id=binding.assistance_id,
                    expected_request_revision=ref.request_revision,
                    input_snapshot_ref=binding.input_snapshot_ref,
                    context_revision=ref.context_revision,
                ),
                correlation_id=binding.correlation_id,
            )
        except Exception:
            return _failed_claim(message, "PROVIDER_UNAVAILABLE")
        if (
            guard.state is InvocationGuardState.SUCCEEDED
            and result.authoritative
            and result.analysis_id is not None
        ):
            artifact = self._artifacts.write_output(
                binding.organization_id,
                f"analysis:{result.analysis_id}".encode(),
                job_id=message.job_id,
                attempt_id=message.attempt_id,
            )
            return CompletionClaim(
                message.job_id,
                message.attempt_id,
                ref.request_revision,
                ref.input_hash,
                ref.context_revision,
                OutcomeKind.SUCCESS,
                outputs=(artifact,),
                moderation=Moderation.PASSED,
            )
        # The pilot never retries an observation, including UNKNOWN/HOLD outcomes.
        return _failed_claim(message, "PROVIDER_UNAVAILABLE")


def build_pilot_vision_composition(
    *,
    settings: Settings,
    engine: Engine,
    resolve_current_request: CurrentRequestFactsResolver,
    resolve_owner_facts: ResolvedFactsResolver,
    resolve_observation_binding: ObservationBindingResolver,
    vision_service_factory: VisionServiceFactory,
    fake_artifacts: PilotFakeArtifacts | None = None,
    queue_capacity: int = 32,
    lock_timeout_ms: int = 1000,
) -> PilotVisionComposition | None:
    """Construct the isolated T8 composition only behind the local synthetic-pilot gate.

    ``resolve_current_request`` and ``resolve_owner_facts`` must use the A2 PostgreSQL
    adapters on the caller's current BE1 facts. ``vision_service_factory`` must compose the
    A2 source/admission adapter and the supplied attempt guard. No default provider or live
    transport is created here.
    """

    if settings.env not in {"local", "test"} or settings.synthetic_pilot_enabled is not True:
        return None
    if engine.dialect.name != "postgresql":
        raise ValueError("the synthetic pilot requires the PostgreSQL BE1 repository")
    if not 1 <= lock_timeout_ms <= 5000:
        raise ValueError("lock timeout must be between 1 and 5000 milliseconds")

    artifacts = fake_artifacts or PILOT_FAKE_ARTIFACTS()
    audit = PILOT_FAKE_AUDIT()
    ids = PILOT_FAKE_IDS()
    clock = PilotSystemClock()
    capabilities = PILOT_FAKE_CAPABILITIES(clock)
    queue = InProcessDispatchQueue(capacity=queue_capacity)
    invocation_ledger = InvocationLedger(engine)
    provider = GuardedVisionJobProvider(
        ledger=invocation_ledger,
        resolve_binding=resolve_observation_binding,
        service_factory=vision_service_factory,
        artifacts=artifacts,
        ids=ids,
    )
    owner_fences = _CombinedBe1OwnerFenceFactory(resolve_owner_facts, lock_timeout_ms, artifacts)
    repository = SqlAiJobRepository(engine, owner_fences)
    jobs = AiJobService(
        AiJobDependencies(
            repository=repository,
            authorization=PostgresBe1PilotAuthorization(engine),
            eligibility=CurrentFactsBe1PilotEligibility(resolve_current_request),
            worker_capability=capabilities,
            capability_issuer=capabilities,
            clock=clock,
            ids=ids,
            artifacts=artifacts,
            audit=audit,
            queue=queue,
            retry_policy=PILOT_VISION_RETRY_POLICY,
            dispatch_policy=FIXTURE_DISPATCH_POLICY,
        )
    )
    worker = DispatchWorker(
        jobs,
        provider,
        provider_job_types=frozenset({VISION_ANALYSIS_JOB_TYPE}),
    )
    return PilotVisionComposition(
        jobs, queue, worker, provider, invocation_ledger, artifacts, audit
    )


class _PilotAssistanceAuthorityDenied(AssistanceAuthorityPort):
    """The pilot composes no assistance command or disclosure route; deny those ports."""

    def decide(self, principal: Principal, canvas: CanvasFacts) -> AssistanceAuthority:
        del principal, canvas
        return AssistanceAuthority(False)

    def disclose(self, principal: Principal, request: AssistanceRequest) -> bool:
        del principal, request
        return False


class _PilotAnalysisAuthorityDenied(AnalysisAuthorityPort):
    """Analysis read/correction authority is outside this worker-only pilot."""

    def decide(
        self, principal: Principal, action: AnalysisAction, scope: AnalysisScope
    ) -> VisionAuthorityDecision:
        del principal, action, scope
        return VisionAuthorityDecision(False, AuthorityReason.ROLE_NOT_PERMITTED)


class _PilotUnavailableVisionProvider(VisionObservationPort):
    """Default-off transport when no local Lightning configuration is present."""

    def __init__(self, guard: InvocationLedgerGuard) -> None:
        self._guard = guard

    @property
    def invocation_guard_identity(self) -> InvocationLedgerGuard:
        return self._guard

    @property
    def supported_context_modes(self) -> frozenset[ProviderContextMode]:
        return frozenset({ProviderContextMode.IMAGE_ONLY})

    @property
    def context_capability(self) -> ContextCapability | None:
        return None

    def observe(self, request: ObservationRequest) -> ObservationFailed:
        del request
        return ObservationFailed(ObservationFailureCode.PROVIDER_UNAVAILABLE, False)


class _PilotReadOnlyUnconfiguredPort:
    """Unused AssistanceService ports fail if a non-read method is accidentally called."""

    def __getattr__(self, name: str) -> object:
        raise RuntimeError(f"pilot assistance operation is not configured: {name}")


def _assistance_pin(request: AssistanceRequest) -> AssistancePin:
    facts = request.facts
    return AssistancePin(
        assistance_id=request.assistance_id,
        request_revision=request.request_revision,
        input_snapshot_ref=facts.source.snapshot_ref,
        context_revision=facts.context_revision,
        scope=AnalysisScope(
            organization_id=facts.organization_id,
            class_id=facts.class_id,
            session_id=facts.session_id,
            canvas_id=facts.canvas_id,
            group_id=facts.group_id,
            contributor_participant_id=facts.contributor_participant_id,
            audience_participant_ids=facts.audience,
            purpose_code=facts.purpose_code,
        ),
        context_digest=(
            f"sha256:{request.assistance_context_digest}"
            if any(member.eligibility_basis is not None for member in facts.members)
            else None
        ),
    )


def _read_assistance_request(
    connection: Connection, organization_id: str, assistance_id: str
) -> AssistanceRequest | None:
    return SqlAssistanceUnitOfWork(connection, organization_id).get(assistance_id)


def _be1_owner_and_source_ports(
    connection: Connection,
    *,
    settings: Settings,
    artifacts: LocalArtifactStore,
    request: AssistanceRequest,
) -> tuple[PostgresAssistanceOwnerAdapter, PostgresCanvasSourceAdapter]:
    from sketch2life.interfaces.http.routers.be1_canvas import build_canvas_source_export

    facts = request.facts

    def export_source(organization_id: str, canvas_id: str) -> CanvasSourceExportV1:
        with Session(bind=connection) as session:
            return build_canvas_source_export(
                session,
                organization_id=organization_id,
                session_id=facts.session_id,
                canvas_id=canvas_id,
                document_epoch=request.checkpoint_ref.document_epoch,
            )

    owner = PostgresAssistanceOwnerAdapter(
        connection,
        organization_id=facts.organization_id,
        class_id=facts.class_id,
        session_id=facts.session_id,
        environment=settings.env,
        pilot_enabled=settings.synthetic_pilot_enabled is True,
        export_source=export_source,
    )
    sources = PostgresCanvasSourceAdapter(
        connection,
        session_id=facts.session_id,
        export_source=export_source,
        load_artifact=artifacts.get,
        environment=settings.env,
        pilot_enabled=settings.synthetic_pilot_enabled is True,
    )
    return owner, sources


def _resolve_request_facts_on_connection(
    connection: Connection,
    *,
    engine: Engine,
    settings: Settings,
    artifacts: LocalArtifactStore,
    request: AssistanceRequest,
) -> ResolvedFacts | None:
    from sketch2life.infrastructure.assistance.pilot_policy import PilotSyntheticPolicy

    owner, sources = _be1_owner_and_source_ports(
        connection, settings=settings, artifacts=artifacts, request=request
    )
    disabled = _PilotReadOnlyUnconfiguredPort()
    service = AssistanceService(
        AssistanceDependencies(
            repository=SqlAssistanceRepository(engine, request.facts.organization_id),
            owner=owner,
            authority=_PilotAssistanceAuthorityDenied(),
            sources=sources,
            policy=PilotSyntheticPolicy(
                environment=settings.env,
                pilot_enabled=settings.synthetic_pilot_enabled is True,
            ),
            jobs=cast(AssistanceJobPort, disabled),
            job_reader=cast(AssistanceJobReader, disabled),
            analyses=cast(AnalysisOutcomePort, disabled),
            sketch_stage=cast(SketchStagePort, disabled),
            clock=PilotSystemClock(),
            ids=PilotFakeIds(),
            auto_schedule=False,
            analysis_only=True,
        )
    )
    try:
        facts = service.current_resolved_facts(
            request.assistance_id, request=request, owner=owner, sources=sources
        )
    except Exception:
        return None
    if facts is None or not _synthetic_facts(facts):
        return None
    return facts


def _read_current_request_facts(
    engine: Engine,
    *,
    settings: Settings,
    artifacts: LocalArtifactStore,
    organization_id: str,
    assistance_id: str,
) -> tuple[AssistanceRequest, ResolvedFacts] | None:
    try:
        with engine.connect() as connection:
            request = _read_assistance_request(connection, organization_id, assistance_id)
            if request is None or request.status not in NON_TERMINAL:
                return None
            facts = _resolve_request_facts_on_connection(
                connection,
                engine=engine,
                settings=settings,
                artifacts=artifacts,
                request=request,
            )
    except Exception:
        return None
    if (
        facts is None
        or request.facts.organization_id != organization_id
        or request.assistance_context_digest != facts.digest()
    ):
        return None
    return request, facts


def _resolve_owner_facts_on_connection(
    connection: Connection,
    scope: BE1OwnerFenceScope,
    *,
    engine: Engine,
    settings: Settings,
    artifacts: LocalArtifactStore,
) -> ResolvedFacts | None:
    from sketch2life.infrastructure.vision_analysis import tables as vision_tables
    from sketch2life.infrastructure.vision_analysis.codec import from_payload

    target_key = scope.target.key()
    payloads = (
        connection.execute(
            select(vision_tables.requests.c.payload).where(
                vision_tables.requests.c.organization_id == scope.organization_id,
                vision_tables.requests.c.session_id == scope.session_id,
                vision_tables.requests.c.target_key == target_key,
            )
        )
        .scalars()
        .all()
    )
    matching: list[ResolvedFacts] = []
    for payload in payloads:
        try:
            request = from_payload(payload, AssistanceRequest)
            stored = request.facts
            if (
                request.status not in NON_TERMINAL
                or stored.organization_id != scope.organization_id
                or stored.class_id != scope.class_id
                or stored.session_id != scope.session_id
                or stored.canvas_id != scope.canvas_id
                or stored.group_id != scope.group_id
                or stored.audience != scope.audience
                or stored.contributor_participant_id != scope.contributor_participant_id
                or stored.purpose_code != scope.purpose_code
                or stored.target != scope.target
                or stored.region_id != scope.region_id
                or stored.source != scope.source
                or tuple(member.evidence_ref for member in stored.members) != scope.proof_ids
            ):
                continue
            current = _resolve_request_facts_on_connection(
                connection,
                engine=engine,
                settings=settings,
                artifacts=artifacts,
                request=request,
            )
            if current is not None and current.digest() == scope.resolved_facts_digest:
                matching.append(current)
        except Exception:
            continue
    return matching[0] if len(matching) == 1 else None


def build_default_pilot_vision(settings: Settings, engine: Engine) -> PilotVisionComposition | None:
    """Compose the real local/test pilot from PostgreSQL/A2 adapters.

    Production is never enabled by default.
    """

    if (
        settings.env not in {"local", "test"}
        or settings.synthetic_pilot_enabled is not True
        or engine.dialect.name != "postgresql"
    ):
        return None
    source_artifacts = LocalArtifactStore(settings.be1_artifact_root)
    pilot_artifacts = PILOT_FAKE_ARTIFACTS()

    def resolve_current_request(
        organization_id: str, assistance_id: str
    ) -> tuple[AssistanceRequest, ResolvedFacts] | None:
        return _read_current_request_facts(
            engine,
            settings=settings,
            artifacts=source_artifacts,
            organization_id=organization_id,
            assistance_id=assistance_id,
        )

    def resolve_owner_facts(
        connection: Connection, scope: BE1OwnerFenceScope
    ) -> ResolvedFacts | None:
        return _resolve_owner_facts_on_connection(
            connection, scope, engine=engine, settings=settings, artifacts=source_artifacts
        )

    def resolve_observation_binding(message: DispatchMessage) -> PilotObservationBinding | None:
        resolved = resolve_current_request(
            _organization_for_job(message, engine),
            message.request_ref.request_id,
        )
        if resolved is None:
            return None
        request, facts = resolved
        ref = message.request_ref
        if (
            request.request_revision != ref.request_revision
            or facts.source.input_hash != ref.input_hash
            or facts.context_revision != ref.context_revision
        ):
            return None
        return PilotObservationBinding(
            facts.organization_id,
            request.assistance_id,
            facts.source.snapshot_ref,
            request.request_revision,
            facts.source.input_hash,
            facts.context_revision,
            f"pilot-{uuid4().hex}",
        )

    def vision_service_factory(
        binding: PilotObservationBinding, guard: InvocationLedgerGuard
    ) -> VisionAnalysisService:
        from sketch2life.infrastructure.vision_analysis.analysis_only import (
            A2AnalysisSourceAdmissionPort,
        )
        from sketch2life.infrastructure.vision_analysis.resolved_facts_context import (
            ResolvedFactsAnalysisContext,
        )

        def resolve_canvas_source(organization_id: str, snapshot_ref: str) -> ResolvedSource | None:
            resolved = resolve_current_request(organization_id, binding.assistance_id)
            if resolved is None:
                return None
            request, _facts = resolved
            if request.facts.source.snapshot_ref != snapshot_ref:
                return None
            try:
                with engine.connect() as connection:
                    _owner, sources = _be1_owner_and_source_ports(
                        connection,
                        settings=settings,
                        artifacts=source_artifacts,
                        request=request,
                    )
                    return sources.resolve(
                        organization_id, request.facts.canvas_id, request.checkpoint_ref
                    )
            except Exception:
                return None

        sources = A2AnalysisSourceAdmissionPort(resolve_canvas_source)

        def current_facts(assistance_id: str) -> ResolvedFacts | None:
            resolved = resolve_current_request(binding.organization_id, assistance_id)
            return None if resolved is None else resolved[1]

        context = ResolvedFactsAnalysisContext(current_facts)

        def make_provider() -> VisionObservationPort:
            if (
                settings.env == "test"
                or settings.ai_provider != "lightning_dev"
                or not settings.lightning_ai_base_url
                or settings.lightning_ai_token_file is None
            ):
                return _PilotUnavailableVisionProvider(guard)
            try:
                token = read_secret_file(settings.lightning_ai_token_file)
                transport = HttpJsonTransport(
                    base_url=settings.lightning_ai_base_url,
                    guard=guard,
                    total_timeout_seconds=min(settings.ai_request_timeout_seconds, 160.0),
                    headers={"Authorization": f"Bearer {token}"},
                )
                return LegacyVisionV2Bridge(
                    transport=transport,
                    render_loader=lambda ref: (
                        source_artifacts.get(ref) or (_raise_missing_artifact())
                    ),
                    endpoint_path=settings.lightning_vision_v2_path,
                )
            except (OSError, ValueError):
                return _PilotUnavailableVisionProvider(guard)

        guarded_provider = InvocationGuardedVisionObservationPort(make_provider(), guard)
        job_repository = SqlAiJobRepository(
            engine,
            _CombinedBe1OwnerFenceFactory(resolve_owner_facts, 1000, pilot_artifacts),
        )
        return VisionAnalysisService(
            VisionAnalysisDependencies(
                repository=SqlAnalysisRepository(engine, binding.organization_id),
                authority=_PilotAnalysisAuthorityDenied(),
                context=context,
                sources=sources,
                admission=sources,
                requests=_SqlAssistancePinPort(engine, binding.organization_id),
                jobs=AiJobRepositoryLineage(job_repository),
                provider=guarded_provider,
                clock=PilotSystemClock(),
                ids=PilotFakeIds(),
                required_context_mode=ProviderContextMode.IMAGE_ONLY,
            )
        )

    return build_pilot_vision_composition(
        settings=settings,
        engine=engine,
        resolve_current_request=resolve_current_request,
        resolve_owner_facts=resolve_owner_facts,
        resolve_observation_binding=resolve_observation_binding,
        vision_service_factory=vision_service_factory,
        fake_artifacts=pilot_artifacts,
    )


class _SqlAssistancePinPort:
    def __init__(self, engine: Engine, organization_id: str) -> None:
        self._engine = engine
        self._organization_id = organization_id

    def get(self, assistance_id: str) -> AssistancePin | None:
        try:
            with self._engine.connect() as connection:
                request = _read_assistance_request(connection, self._organization_id, assistance_id)
        except Exception:
            return None
        return None if request is None else _assistance_pin(request)


def _organization_for_job(message: DispatchMessage, engine: Engine) -> str:
    from sketch2life.infrastructure.ai_jobs.sql import tables as job_tables

    try:
        with engine.connect() as connection:
            organization_id = connection.execute(
                select(job_tables.job.c.organization_id).where(
                    job_tables.job.c.job_id == message.job_id
                )
            ).scalar_one_or_none()
    except Exception:
        return ""
    return organization_id if isinstance(organization_id, str) else ""


def _raise_missing_artifact() -> bytes:
    raise KeyError("pilot render artifact is unavailable")


def _authorization_payload(
    connection: Connection, principal: Principal, scope: JobScope, class_id: str
) -> dict[str, str] | None:
    if principal.organization_id != scope.organization_id:
        return None
    child_id = scope.subject_refs[0]
    if principal.role.value in {"teacher", "admin"}:
        identity = connection.execute(
            select(AdultIdentityModel.subject, AdultIdentityModel.state).where(
                AdultIdentityModel.subject == principal.principal_id
            )
        ).one_or_none()
        role = "teacher" if principal.role.value == "teacher" else "school_admin"
        predicate = [
            OrganizationAssignmentModel.organization_id == scope.organization_id,
            OrganizationAssignmentModel.subject == principal.principal_id,
            OrganizationAssignmentModel.role == role,
            OrganizationAssignmentModel.active.is_(True),
        ]
        if role == "teacher":
            predicate.append(OrganizationAssignmentModel.class_id == class_id)
        else:
            predicate.append(OrganizationAssignmentModel.class_id.is_(None))
        assignments = (
            connection.execute(select(OrganizationAssignmentModel.assignment_id).where(*predicate))
            .scalars()
            .all()
        )
        if identity is None or identity.state != "active" or len(assignments) != 1:
            return None
        return {
            "kind": "adult",
            "organization_id": scope.organization_id,
            "subject": principal.principal_id,
            "assignment_id": assignments[0],
            "role": role,
            "class_id": class_id,
            "session_id": scope.session_id or "",
            "child_id": child_id,
        }
    if principal.role.value != "device" or not principal.principal_id.startswith("device:"):
        return None
    grant_id = principal.principal_id.removeprefix("device:")
    grant = connection.execute(
        select(DeviceGrantModel).where(
            DeviceGrantModel.grant_id == grant_id,
            DeviceGrantModel.organization_id == scope.organization_id,
            DeviceGrantModel.session_id == scope.session_id,
            DeviceGrantModel.admitted_child_id == child_id,
            DeviceGrantModel.state == "admitted",
        )
    ).scalar_one_or_none()
    if grant is None:
        return None
    memberships = (
        connection.execute(
            select(SessionMembershipModel.membership_id).where(
                SessionMembershipModel.organization_id == scope.organization_id,
                SessionMembershipModel.class_id == class_id,
                SessionMembershipModel.session_id == scope.session_id,
                SessionMembershipModel.child_id == child_id,
                SessionMembershipModel.device_grant_id == grant_id,
                SessionMembershipModel.state == "admitted",
            )
        )
        .scalars()
        .all()
    )
    if len(memberships) != 1:
        return None
    return {
        "kind": "device",
        "organization_id": scope.organization_id,
        "subject": principal.principal_id,
        "grant_id": grant_id,
        "membership_id": memberships[0],
        "class_id": class_id,
        "session_id": scope.session_id or "",
        "child_id": child_id,
    }


def _hold_authorization_fence(connection: Connection, fence: OwnerFence) -> bool:
    if type(fence.epoch) is not int or fence.epoch != 1:
        return False
    try:
        payload = json.loads(fence.fence_scope.removeprefix(_AUTH_FENCE_PREFIX))
    except (TypeError, ValueError):
        return False
    if not isinstance(payload, dict) or payload.get("kind") not in {"adult", "device"}:
        return False
    if payload["kind"] == "adult":
        identity = connection.execute(
            select(AdultIdentityModel.subject)
            .where(
                AdultIdentityModel.subject == payload.get("subject"),
                AdultIdentityModel.state == "active",
            )
            .with_for_update(read=True)
        ).scalar_one_or_none()
        assignment = connection.execute(
            select(OrganizationAssignmentModel.assignment_id)
            .where(
                OrganizationAssignmentModel.assignment_id == payload.get("assignment_id"),
                OrganizationAssignmentModel.organization_id == payload.get("organization_id"),
                OrganizationAssignmentModel.subject == payload.get("subject"),
                OrganizationAssignmentModel.class_id
                == (payload.get("class_id") if payload.get("role") == "teacher" else None),
                OrganizationAssignmentModel.role == payload.get("role"),
                OrganizationAssignmentModel.active.is_(True),
            )
            .with_for_update(read=True)
        ).scalar_one_or_none()
        return identity == payload.get("subject") and assignment == payload.get("assignment_id")
    grant = connection.execute(
        select(DeviceGrantModel.grant_id)
        .where(
            DeviceGrantModel.grant_id == payload.get("grant_id"),
            DeviceGrantModel.organization_id == payload.get("organization_id"),
            DeviceGrantModel.session_id == payload.get("session_id"),
            DeviceGrantModel.admitted_child_id == payload.get("child_id"),
            DeviceGrantModel.state == "admitted",
        )
        .with_for_update(read=True)
    ).scalar_one_or_none()
    membership = connection.execute(
        select(SessionMembershipModel.membership_id)
        .where(
            SessionMembershipModel.membership_id == payload.get("membership_id"),
            SessionMembershipModel.organization_id == payload.get("organization_id"),
            SessionMembershipModel.class_id == payload.get("class_id"),
            SessionMembershipModel.session_id == payload.get("session_id"),
            SessionMembershipModel.child_id == payload.get("child_id"),
            SessionMembershipModel.device_grant_id == payload.get("grant_id"),
            SessionMembershipModel.state == "admitted",
        )
        .with_for_update(read=True)
    ).scalar_one_or_none()
    return grant == payload.get("grant_id") and membership == payload.get("membership_id")


def _synthetic_session(configuration: object, purpose_code: str) -> bool:
    return (
        isinstance(configuration, dict)
        and configuration.get("purpose_ref") == purpose_code
        and isinstance(configuration.get("pilot_run_ref"), str)
        and bool(configuration["pilot_run_ref"])
    )


def _synthetic_facts(facts: ResolvedFacts) -> bool:
    if (
        not facts.group_id
        or not facts.audience
        or len(set(facts.audience)) != len(facts.audience)
        or tuple(member.participant_id for member in facts.members) != facts.audience
        or facts.contributor_participant_id not in facts.audience
        or len(facts.members) != 1
    ):
        return False
    member = facts.members[0]
    return (
        member.eligibility_basis == EligibilityBasis.SYNTHETIC_DEV
        and member.basis_version == BASIS_VERSION
        and member.eligibility_scope
        == EligibilityScope(
            facts.organization_id, facts.class_id, member.participant_id, facts.purpose_code
        )
        and member.consent_record_ref is None
        and member.consent_revision is None
        and not member.consent_effective
        and not member.purpose_granted
        and isinstance(member.evidence_ref, str)
        and bool(member.evidence_ref.strip())
    )


def _failed_claim(message: DispatchMessage, reason: str) -> CompletionClaim:
    ref = message.request_ref
    return CompletionClaim(
        message.job_id,
        message.attempt_id,
        ref.request_revision,
        ref.input_hash,
        ref.context_revision,
        OutcomeKind.FAILURE,
        failure_code="PROVIDER_UNAVAILABLE",
        retryable=False,
        diagnostic=reason,
    )


def _stale(fences: tuple[OwnerFence, ...]) -> FenceResult:
    return FenceResult(False, fences)


__all__ = [
    "CurrentFactsBe1PilotEligibility",
    "GuardedVisionJobProvider",
    "PilotFakeArtifacts",
    "PilotFakeAudit",
    "PilotFakeCapabilities",
    "PilotFakeIds",
    "PILOT_FAKE_ARTIFACTS",
    "PILOT_FAKE_AUDIT",
    "PILOT_FAKE_CAPABILITIES",
    "PILOT_FAKE_IDS",
    "PilotObservationBinding",
    "PilotVisionComposition",
    "PostgresBe1PilotAuthorization",
    "PilotSystemClock",
    "build_pilot_vision_composition",
]
