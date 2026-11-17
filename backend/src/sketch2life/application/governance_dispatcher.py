"""Fixed CMD-48 candidate dispatcher; concrete strict owner binding before effects."""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.contracts.schemas.governance import (
    DelegateResult,
    DelegateTarget,
    GovernanceSelection,
    select_governance,
)
from sketch2life.contracts.schemas.learning_content import (
    CONTENT_COMMAND_ADAPTER,
    ContentCommandResult,
    PublicationReviewSet,
)
from sketch2life.domain.learning_content.model import ContentError

CommandContra = TypeVar("CommandContra", bound=BaseModel, contravariant=True)


class DelegateHandler(Protocol[CommandContra]):
    """Owns independent current auth/policy/CAS/receipt/commit, not content rights."""

    def execute(self, principal_id: str, organization_id: str, command: CommandContra, *,
                expected_revision: int | None) -> DelegateResult: ...


class BoundGovernanceDelegate(Protocol):
    """A validation adapter, not a raw-payload business handler."""

    def invoke(self, principal_id: str, organization_id: str, raw: bytes,
               selection: GovernanceSelection, *,
               expected_revision: int | None) -> DelegateResult: ...

    def json_schema(self) -> dict[str, object]: ...


class StrictDelegateBinding[CommandT: BaseModel]:
    def __init__(self, model: type[CommandT], handler: DelegateHandler[CommandT]) -> None:
        if (model.model_config.get("extra") != "forbid"
                or model.model_config.get("strict") is not True
                or model.model_config.get("frozen") is not True):
            raise ValueError("strict frozen extra-forbid owner model required")
        self.model, self.handler = model, handler

    def json_schema(self) -> dict[str, object]:
        return self.model.model_json_schema()

    def invoke(self, principal_id: str, organization_id: str, raw: bytes,
               selection: GovernanceSelection, *,
               expected_revision: int | None) -> DelegateResult:
        try:
            command = self.model.model_validate_json(raw)
            encoded = command.model_dump_json().encode("utf-8")
            if select_governance(encoded) != selection:
                raise ValueError("owner model changed shared routing envelope")
        except (ValueError, ValidationError):
            raise ContentError("INVALID_GOVERNANCE_COMMAND") from None
        if selection.action != "create":
            try:
                DelegateTarget.model_validate({
                    "record_id": getattr(command, "record_id", None),
                    "target_version": getattr(command, "target_version", None),
                    "target_hash": getattr(command, "target_hash", None)})
                if selection.action in {"request_changes", "recall", "archive"}:
                    reason = getattr(command, "reason", None)
                    if not isinstance(reason, str) or not reason.strip() or len(reason) > 200:
                        raise ValueError("reason required")
                if selection.action == "publish":
                    proof = getattr(command, "review_ref", None)
                    if not isinstance(proof, PublicationReviewSet):
                        raise ValueError("typed publication review set required")
            except (ValueError, ValidationError):
                raise ContentError("INVALID_GOVERNANCE_COMMAND") from None
        result = self.handler.execute(principal_id, organization_id, command,
                                      expected_revision=expected_revision)
        # Revalidate a returned candidate object; model_construct/copy must not
        # smuggle unknown fields or mismatched organization through the boundary.
        try:
            result = DelegateResult.model_validate_json(result.model_dump_json())
        except (AttributeError, ValueError, ValidationError):
            raise ContentError("GOVERNANCE_DELEGATE_INVALID_RESPONSE") from None
        if (result.record.organization_id != organization_id
                or result.record.record_kind != selection.record_kind
                or result.record.policy_kind != selection.policy_kind
                or result.current_revision < result.record.revision):
            raise ContentError("GOVERNANCE_DELEGATE_INVALID_RESPONSE")
        if selection.action != "create":
            record_id = getattr(command, "record_id", None)
            target_version = getattr(command, "target_version", None)
            target_hash = getattr(command, "target_hash", None)
            if (result.record.record_id != record_id or type(target_version) is not int
                    or result.record.version != target_version + (selection.action == "edit")
                    or (selection.action != "edit" and result.record.hash != target_hash)):
                raise ContentError("GOVERNANCE_DELEGATE_INVALID_RESPONSE")
        return result


class GovernanceDispatcher:
    def __init__(self, content: ContentCommands, *,
                 preset: BoundGovernanceDelegate | None = None,
                 ai_policy: BoundGovernanceDelegate | None = None,
                 core_policy: BoundGovernanceDelegate | None = None) -> None:
        self.content = content
        self.preset, self.ai_policy, self.core_policy = preset, ai_policy, core_policy

    def request_schemas(self) -> tuple[dict[str, object], ...]:
        return (CONTENT_COMMAND_ADAPTER.json_schema(), *(binding.json_schema()
                for binding in (self.preset, self.ai_policy, self.core_policy)
                if binding is not None))

    def execute_json(self, principal_id: str, organization_id: str, raw: bytes, *,
                     expected_revision: int | None = None) -> ContentCommandResult | DelegateResult:
        try:
            selected = select_governance(raw)
        except ValueError:
            raise ContentError("INVALID_GOVERNANCE_COMMAND") from None
        if selected.action == "create":
            if expected_revision is not None:
                raise ContentError("CONTENT_UNEXPECTED_PRECONDITION")
        elif type(expected_revision) is not int or expected_revision < 1:
            raise ContentError("CONTENT_PRECONDITION_REQUIRED")
        if selected.branch == "learning_content":
            try:
                command = CONTENT_COMMAND_ADAPTER.validate_json(raw)
            except ValidationError:
                raise ContentError("INVALID_GOVERNANCE_COMMAND") from None
            return self.content.execute(principal_id, organization_id, command,
                                        expected_revision=expected_revision)
        delegate = {"preset": self.preset, "ai_policy": self.ai_policy,
                    "core_policy": self.core_policy}[selected.branch]
        if delegate is None:
            raise ContentError("GOVERNANCE_DELEGATE_UNAVAILABLE")
        return delegate.invoke(principal_id, organization_id, raw, selected,
                               expected_revision=expected_revision)
