"""Synchronous candidate CMD38/39; current disclosure and accepted history are distinct."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from sketch2life.application.ports.ai_jobs import ClockPort, Principal, PrincipalRole
from sketch2life.application.ports.knowledge_bundle import (
    KnowledgeAudit,
    KnowledgeConflict,
    KnowledgeFacts,
    KnowledgeReceipt,
    KnowledgeRepository,
    KnowledgeResult,
    KnowledgeUnitOfWork,
    ReceiptKey,
)
from sketch2life.contracts.schemas.knowledge_bundles import (
    CreateKnowledgeBundleV1,
    EditKnowledgeBundleV1,
    ExactKnowledgeRefV1,
    FactSectionV1,
    KnowledgeBundleExportV1,
    KnowledgeBundleRecordV1,
    KnowledgeSupersededV1,
    export_from_version,
    record_from_version,
)
from sketch2life.domain.knowledge_bundle import (
    DOCUMENT_MAX,
    AudienceContextV1,
    BasisRef,
    BundleHead,
    ContributorV1,
    FactSection,
    KnowledgeBasisV1,
    KnowledgeBundleVersion,
    KnowledgeRuleViolation,
    SourceRefV1,
    StorySection,
    attributed_claim,
    build_version,
    canonical_bytes,
    catalog_claim,
    opaque,
    plan_edit,
    require,
    revision,
    validate_audience,
    validate_basis,
    validate_claims,
    verify_version,
)


class KnowledgeBundleError(Exception):
    def __init__(self, code: str, status: int) -> None:
        self.code = code
        self.status = status
        super().__init__(code)


@dataclass(frozen=True)
class CreateKnowledgeCommand:
    principal: Principal
    idempotency_key: str | None
    body: CreateKnowledgeBundleV1 | str | bytes
    if_match: str | None = None


@dataclass(frozen=True)
class EditKnowledgeCommand:
    principal: Principal
    bundle_id: str
    idempotency_key: str | None
    if_match: str | None
    body: EditKnowledgeBundleV1 | str | bytes


@dataclass(frozen=True)
class KnowledgeCommandResult:
    result: KnowledgeResult
    replayed: bool = False
    no_content_change: bool = False

    @property
    def record(self) -> KnowledgeBundleRecordV1:
        return self.result.record

    @property
    def status(self) -> int:
        return self.result.status

    @property
    def code(self) -> str | None:
        return "NO_CONTENT_CHANGE" if self.no_content_change else None


@dataclass(frozen=True)
class KnowledgeResolution:
    ready: bool
    reason: str | None
    export: KnowledgeBundleExportV1 | None = None


@dataclass(frozen=True)
class KnowledgeDependencies:
    repository: KnowledgeRepository
    facts: KnowledgeFacts
    clock: ClockPort


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    normalized: set[str] = set()
    for key, value in pairs:
        nfc = unicodedata.normalize("NFC", key)
        if nfc in normalized:
            raise ValueError("duplicate normalized request key")
        normalized.add(nfc)
        result[key] = value
    return result


def _constant(value: str) -> object:
    raise ValueError("non-native JSON constant")


def _parse[Body: BaseModel](body: object, model: type[Body]) -> Body:
    try:
        raw = body.model_dump_json() if isinstance(body, BaseModel) else body
        if not isinstance(raw, str | bytes):
            raise ValueError("request document required")
        encoded = raw.encode("utf-8") if isinstance(raw, str) else raw
        if len(encoded) > DOCUMENT_MAX:
            raise KnowledgeBundleError("REQUEST_DOCUMENT_BOUNDS", 400)
        # The owned raw boundary rejects duplicates before a parser can discard them.
        json.loads(encoded.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
        return model.model_validate_json(encoded, strict=True)
    except KnowledgeBundleError:
        raise
    except (ValueError, TypeError) as exc:
        code = "FIELD_VALIDATION_FAILED"
        if isinstance(exc, ValidationError) and any(
            error["type"] == "extra_forbidden" for error in exc.errors()
        ):
            code = "FIELD_NOT_ALLOWED"
        raise KnowledgeBundleError(code, 400) from None


def _key(principal: Principal, contract: str, target: str, key: str | None) -> ReceiptKey:
    try:
        if not isinstance(key, str):
            raise ValueError("key required")
        opaque(key)
        opaque(target)
    except ValueError:
        raise KnowledgeBundleError("FIELD_VALIDATION_FAILED", 400) from None
    return principal.organization_id, principal.principal_id, contract, target, key


def _identity(key: ReceiptKey) -> str:
    return hashlib.sha256(canonical_bytes({"receipt_scope": list(key)})).hexdigest()


def _fingerprint(target: str, body: BaseModel) -> str:
    try:
        return hashlib.sha256(
            canonical_bytes(
                {
                    "target": target,
                    "body": body.model_dump(mode="json"),
                }
            )
        ).hexdigest()
    except KnowledgeRuleViolation as exc:
        raise KnowledgeBundleError(exc.code, 400) from None


def _header(value: str | None) -> None:
    if value is not None and (not isinstance(value, str) or not 0 < len(value) <= 512):
        raise KnowledgeBundleError("FIELD_VALIDATION_FAILED", 400)


class KnowledgeBundleService:
    def __init__(self, dependencies: KnowledgeDependencies) -> None:
        if dependencies.repository.coordination_token is not dependencies.facts.coordination_token:
            raise ValueError("knowledge facts and repository require the same coordinated boundary")
        self._d = dependencies

    def _disclose(
        self,
        principal: Principal,
        organization_id: str,
        session_id: str,
        contributors: tuple[ContributorV1, ...] = (),
    ) -> None:
        facts = self._d.facts
        allowed = (
            principal.role is PrincipalRole.TEACHER
            and principal.organization_id == organization_id
            and facts.teacher_allowed(organization_id, principal.principal_id, session_id)
            and facts.disclosure_allowed(organization_id, principal.principal_id, session_id)
        )
        if not allowed or any(
            not facts.contributor_disclosure_allowed(organization_id, session_id, contributor)
            for contributor in contributors
        ):
            raise KnowledgeBundleError("KNOWLEDGE_UNAVAILABLE", 404)

    def _context(
        self,
        principal: Principal,
        session_id: str,
        ref: BasisRef,
        context_revision: int,
        audience_revision: int,
        *,
        mutation: bool = False,
    ) -> tuple[KnowledgeBasisV1, AudienceContextV1, str]:
        facts = self._d.facts
        if mutation:
            require(
                facts.mutation_allowed(principal.organization_id, session_id), "MUTATION_PAUSED"
            )
        policy_ref, active = facts.policy()
        require(active, "POLICY_UNAVAILABLE")
        audience = facts.audience(principal.organization_id, session_id)
        require(audience is not None, "AUDIENCE_UNAVAILABLE")
        assert audience is not None
        validate_audience(
            audience, principal.organization_id, session_id, context_revision, audience_revision
        )
        basis = facts.basis(ref)
        require(basis is not None, "BASIS_UNAVAILABLE")
        assert basis is not None
        validate_basis(
            basis,
            ref,
            audience,
            principal.organization_id,
            session_id,
            lambda contributor: facts.contributor_allowed(
                principal.organization_id, session_id, contributor
            ),
        )
        self._disclose(principal, principal.organization_id, session_id, basis.contributors)
        return basis, audience, policy_ref

    def _current(
        self, principal: Principal, value: KnowledgeBundleVersion, *, mutation: bool = False
    ) -> None:
        verify_version(value)
        basis, audience, policy_ref = self._context(
            principal,
            value.session_id,
            BasisRef(value.basis.kind, value.basis.ref, value.basis.revision),
            value.audience.context_revision,
            value.audience.audience_revision,
            mutation=mutation,
        )
        require(basis == value.basis, "BASIS_CHANGED")
        require(audience == value.audience, "AUDIENCE_CHANGED")
        require(policy_ref == value.policy_ref, "POLICY_CHANGED")
        sources = validate_claims(
            value.knowledge_claims,
            self._d.facts.catalog_claims(),
            self._d.facts.sources(),
            basis,
            audience,
        )
        require(sources == value.source_records, "SOURCE_RECORD_CHANGED")

    def _replay(
        self, principal: Principal, receipt: KnowledgeReceipt, fingerprint: str, key: ReceiptKey
    ) -> KnowledgeCommandResult:
        value = receipt.version
        self._disclose(principal, value.organization_id, value.session_id, value.contributors)
        if receipt.fingerprint != fingerprint:
            raise KnowledgeBundleError("IDEMPOTENCY_PAYLOAD_MISMATCH", 409)
        # Verify immutable receipt content, without applying new mutation/current guards.
        expected = record_from_version(value)
        expected_status = 201 if key[2] == "CreateKnowledgeBundleV1" else 200
        require(
            receipt.key == key
            and receipt.result.status == expected_status
            and expected == receipt.result.record,
            "RECEIPT_CONTENT_MISMATCH",
        )
        return KnowledgeCommandResult(receipt.result, replayed=True)

    def _recover(
        self, principal: Principal, key: ReceiptKey, fingerprint: str
    ) -> KnowledgeCommandResult:
        # This runs after the losing unit rolled back and its queued facts drained.
        try:
            with self._d.repository.transaction() as tx:
                receipt = tx.get_receipt(key)
                if receipt is None:
                    raise KnowledgeBundleError("STALE_AGGREGATE", 409)
                return self._replay(principal, receipt, fingerprint, key)
        except KnowledgeRuleViolation as exc:
            raise KnowledgeBundleError(exc.code, 409) from None
        except RuntimeError:
            raise KnowledgeBundleError("STORAGE_UNAVAILABLE", 503) from None

    def create(self, command: CreateKnowledgeCommand) -> KnowledgeCommandResult:
        body = _parse(command.body, CreateKnowledgeBundleV1)
        _header(command.if_match)
        key = _key(
            command.principal,
            "CreateKnowledgeBundleV1",
            "knowledge-bundles",
            command.idempotency_key,
        )
        fingerprint = _fingerprint("knowledge-bundles", body)
        try:
            with self._d.repository.transaction() as tx:
                self._disclose(
                    command.principal, command.principal.organization_id, body.session_id
                )
                receipt = tx.get_receipt(key)
                if receipt is not None:
                    return self._replay(command.principal, receipt, fingerprint, key)
                if command.if_match is not None:
                    raise KnowledgeBundleError("CREATE_PRECONDITION_NOT_ALLOWED", 400)
                ref = BasisRef(body.basis_ref.kind, body.basis_ref.ref, body.basis_ref.revision)
                basis, audience, policy = self._context(
                    command.principal,
                    body.session_id,
                    ref,
                    body.expected_context_revision,
                    body.expected_audience_revision,
                    mutation=True,
                )
                catalog = self._d.facts.catalog_claims()
                by_id = {claim.claim_id: claim for claim in catalog}
                claims = tuple(
                    catalog_claim(by_id[ref]) for ref in body.catalog_claim_ids if ref in by_id
                )
                missing = len(claims) != len(body.catalog_claim_ids)
                try:
                    sources = validate_claims(
                        claims, catalog, self._d.facts.sources(), basis, audience
                    )
                except KnowledgeRuleViolation:
                    missing = True
                    sources = ()
                if missing:
                    claims, sources = (), ()
                imagined_map = {element.ref: element for element in basis.imagined_elements}
                require(
                    all(ref in imagined_map for ref in body.imagined_refs),
                    "UNKNOWN_IMAGINED_REFERENCE",
                )
                imagined = tuple(imagined_map[ref] for ref in body.imagined_refs)
                sections: tuple[FactSection | StorySection, ...] = (
                    (FactSection("facts", tuple(claim.claim_id for claim in claims)),)
                    if claims
                    else ()
                ) + (
                    (StorySection("story", tuple(item.ref for item in imagined)),)
                    if imagined
                    else ()
                )
                operation = _identity(key)
                value = build_version(
                    bundle_id="kb-" + operation,
                    basis=basis,
                    audience=audience,
                    claims=claims,
                    sources=sources,
                    sections=sections,
                    imagined_elements=imagined,
                    created_by=command.principal.principal_id,
                    created_at=self._d.clock.now().isoformat(),
                    policy_ref=policy,
                )
                result = KnowledgeResult(201, record_from_version(value))
                self._stage(tx, key, fingerprint, operation, command.principal, value, result)
                return KnowledgeCommandResult(result)
        except KnowledgeConflict:
            return self._recover(command.principal, key, fingerprint)
        except KnowledgeRuleViolation as exc:
            raise KnowledgeBundleError(exc.code, 409) from None
        except RuntimeError:
            raise KnowledgeBundleError("STORAGE_UNAVAILABLE", 503) from None

    def edit(self, command: EditKnowledgeCommand) -> KnowledgeCommandResult:
        body = _parse(command.body, EditKnowledgeBundleV1)
        _header(command.if_match)
        key = _key(
            command.principal, "EditKnowledgeBundleV1", command.bundle_id, command.idempotency_key
        )
        fingerprint = _fingerprint(command.bundle_id, body)
        try:
            with self._d.repository.transaction() as tx:
                head = tx.get_head(command.bundle_id)
                if head is None:
                    raise KnowledgeBundleError("KNOWLEDGE_UNAVAILABLE", 404)
                self._disclose(command.principal, head.organization_id, head.session_id)
                receipt = tx.get_receipt(key)
                if receipt is not None:
                    return self._replay(command.principal, receipt, fingerprint, key)
                if command.if_match is None:
                    raise KnowledgeBundleError("PRECONDITION_REQUIRED", 428)
                if command.if_match != head.etag:
                    raise KnowledgeBundleError("PRECONDITION_FAILED", 412)
                old = tx.get_version(head.bundle_id, head.current_version)
                require(old is not None, "VERSION_UNAVAILABLE")
                assert old is not None
                self._current(command.principal, old, mutation=True)
                require(
                    body.expected_context_revision == old.audience.context_revision,
                    "CONTEXT_REVISION_MISMATCH",
                )
                require(
                    body.expected_audience_revision == old.audience.audience_revision,
                    "AUDIENCE_REVISION_MISMATCH",
                )
                previous_claims = {claim.claim_id: claim for claim in old.knowledge_claims}
                claims = (
                    old.knowledge_claims
                    if body.claims is None
                    else tuple(
                        attributed_claim(
                            item.claim_id,
                            item.revision,
                            item.text,
                            tuple(
                                SourceRefV1(ref.source_id, ref.revision, ref.sha256)
                                for ref in item.source_refs
                            ),
                            self._d.facts.catalog_claims(),
                            command.principal.principal_id,
                            item.attestation_reason,
                            previous=previous_claims.get(item.claim_id),
                        )
                        for item in body.claims
                    )
                )
                sources = validate_claims(
                    claims,
                    self._d.facts.catalog_claims(),
                    self._d.facts.sources(),
                    old.basis,
                    old.audience,
                )
                sections = (
                    old.sections
                    if body.sections is None
                    else tuple(
                        FactSection(item.section_id, item.claim_refs)
                        if isinstance(item, FactSectionV1)
                        else StorySection(item.section_id, item.imagined_refs)
                        for item in body.sections
                    )
                )
                imagined = old.imagined_elements
                if body.imagined_refs is not None:
                    elements = {item.ref: item for item in old.basis.imagined_elements}
                    require(
                        all(ref in elements for ref in body.imagined_refs),
                        "UNKNOWN_IMAGINED_REFERENCE",
                    )
                    imagined = tuple(elements[ref] for ref in body.imagined_refs)
                operation = _identity(key)
                value = plan_edit(
                    old,
                    claims=claims,
                    sources=sources,
                    sections=sections,
                    imagined_elements=imagined,
                    correction_ref="kc-" + operation,
                    teacher_principal_id=command.principal.principal_id,
                    reason=body.correction_reason,
                )
                if value is None:
                    return KnowledgeCommandResult(
                        KnowledgeResult(200, record_from_version(old)), no_content_change=True
                    )
                result = KnowledgeResult(200, record_from_version(value))
                self._stage(tx, key, fingerprint, operation, command.principal, value, result, old)
                return KnowledgeCommandResult(result)
        except KnowledgeConflict:
            return self._recover(command.principal, key, fingerprint)
        except KnowledgeRuleViolation as exc:
            raise KnowledgeBundleError(exc.code, 409) from None
        except RuntimeError:
            raise KnowledgeBundleError("STORAGE_UNAVAILABLE", 503) from None

    @staticmethod
    def _stage(
        tx: KnowledgeUnitOfWork,
        key: ReceiptKey,
        fingerprint: str,
        operation: str,
        principal: Principal,
        value: KnowledgeBundleVersion,
        result: KnowledgeResult,
        old: KnowledgeBundleVersion | None = None,
    ) -> None:
        tx.put_head(
            BundleHead(
                value.bundle_id,
                value.organization_id,
                value.session_id,
                value.bundle_version,
                value.editorial_revision,
            ),
            0 if old is None else old.bundle_version,
        )
        tx.put_version(value)
        if old is not None:
            tx.put_correction(value.corrections[-1])
            tx.add_event(
                KnowledgeSupersededV1(
                    event_id="ke-" + operation,
                    organization_id=value.organization_id,
                    session_id=value.session_id,
                    old_bundle=ExactKnowledgeRefV1(
                        bundle_id=old.bundle_id,
                        bundle_version=old.bundle_version,
                        bundle_hash=old.bundle_hash,
                    ),
                    new_bundle=ExactKnowledgeRefV1(
                        bundle_id=value.bundle_id,
                        bundle_version=value.bundle_version,
                        bundle_hash=value.bundle_hash,
                    ),
                    correction_ref=value.corrections[-1].correction_ref,
                    operation_id="ko-" + operation,
                )
            )
        tx.put_receipt(KnowledgeReceipt(key, fingerprint, result, value))
        tx.add_audit(
            KnowledgeAudit(
                "ko-" + operation,
                "create" if old is None else "edit",
                value.bundle_id,
                value.bundle_version,
                principal.principal_id,
            )
        )

    def _resolve(
        self,
        tx: KnowledgeUnitOfWork,
        principal: Principal,
        bundle_id: str,
        version: int | None,
        bundle_hash: str | None,
    ) -> KnowledgeResolution:
        head = tx.get_head(bundle_id)
        if head is None:
            raise KnowledgeBundleError("KNOWLEDGE_UNAVAILABLE", 404)
        self._disclose(principal, head.organization_id, head.session_id)
        if version is not None:
            require(version == head.current_version, "BUNDLE_SUPERSEDED")
        value = tx.get_version(bundle_id, head.current_version)
        require(value is not None, "VERSION_UNAVAILABLE")
        assert value is not None
        require(
            (value.bundle_id, value.organization_id, value.session_id, value.editorial_revision)
            == (head.bundle_id, head.organization_id, head.session_id, head.editorial_revision),
            "EXACT_BUNDLE_MISMATCH",
        )
        if bundle_hash is not None:
            require(value.bundle_hash == bundle_hash, "EXACT_BUNDLE_MISMATCH")
        self._current(principal, value)
        if not value.knowledge_claims or not any(
            isinstance(s, FactSection) for s in value.sections
        ):
            return KnowledgeResolution(False, record_from_version(value).action_code)
        return KnowledgeResolution(True, None, export_from_version(value))

    def read(self, principal: Principal, bundle_id: str) -> KnowledgeResolution:
        return self._read(principal, bundle_id, None, None)

    def resolve_exact(
        self, principal: Principal, bundle_id: str, version: int, bundle_hash: str
    ) -> KnowledgeResolution:
        return self._read(principal, bundle_id, version, bundle_hash)

    def _read(
        self, principal: Principal, bundle_id: str, version: int | None, bundle_hash: str | None
    ) -> KnowledgeResolution:
        try:
            opaque(bundle_id)
            if version is not None:
                revision(version)
                require(
                    isinstance(bundle_hash, str)
                    and re.fullmatch(r"[0-9a-f]{64}", bundle_hash) is not None,
                    "INVALID_HASH",
                )
            with self._d.repository.transaction() as tx:
                return self._resolve(tx, principal, bundle_id, version, bundle_hash)
        except KnowledgeBundleError as exc:
            return KnowledgeResolution(False, exc.code)
        except KnowledgeRuleViolation as exc:
            return KnowledgeResolution(False, exc.code)
        except RuntimeError:
            return KnowledgeResolution(False, "STORAGE_UNAVAILABLE")
