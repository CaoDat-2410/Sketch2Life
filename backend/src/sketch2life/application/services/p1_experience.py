"""Deterministic P1 selection, ExperienceSpec compilation and Gate B.

The service accepts typed contracts and an injected template list.  It is
therefore usable by fixture tests without HTTP, a database, a model provider,
or any mobile runtime.  All hard eligibility checks run before the fit score.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from sketch2life.contracts.schemas.p1_experience import (
    ActivityFitEvaluationV1,
    ActivityHandoffV1,
    ActivityPlanV1,
    ActivityTemplateV1,
    BridgeSentenceV1,
    ExperienceSpecV1,
    IntegrationGateDecisionV1,
    LearningFocusV1,
    MediaContinuityPlanV1,
    P1ContextV1,
    P1FilterResultV1,
    SemanticAnchorSetV1,
    SemanticMatchEvidenceV1,
    VersionedRefV1,
)

SUPERVISION_RANK = {"NONE": 0, "NEARBY": 1, "DIRECT": 2}
FILTER_STATUS = Literal[
    "VALID_CANDIDATE",
    "MISSING_CONTEXT",
    "NO_ELIGIBLE_ACTIVITY",
    "UNKNOWN_ANCHOR",
    "AMBIGUOUS_ANCHOR",
    "CONFLICTING_ANCHOR",
]


@dataclass(frozen=True, slots=True)
class ExperienceCompilation:
    filter_result: P1FilterResultV1
    fit_evaluation: ActivityFitEvaluationV1 | None
    spec: ExperienceSpecV1 | None
    gate_b: IntegrationGateDecisionV1
    handoff: ActivityHandoffV1 | None


def _tokens(*values: str) -> set[str]:
    result: set[str] = set()
    for value in values:
        result.update(re.findall(r"[\w-]+", value.casefold(), flags=re.UNICODE))
    return {token for token in result if len(token) > 2}


class P1ExperienceCompiler:
    """Compile one immutable spec from one confirmed anchor and adult context."""

    def __init__(
        self,
        templates: Iterable[ActivityTemplateV1],
        objective_titles_vi: Mapping[str, str],
        *,
        policy_version: str = "P1_STRICT_CONTINUITY_V1",
    ) -> None:
        self._templates = tuple(templates)
        self._objective_titles = dict(objective_titles_vi)
        seen_template_ids: set[str] = set()
        duplicate_template_ids: set[str] = set()
        for template in self._templates:
            if template.template_id in seen_template_ids:
                duplicate_template_ids.add(template.template_id)
            seen_template_ids.add(template.template_id)
        if duplicate_template_ids:
            duplicates = ",".join(sorted(duplicate_template_ids))
            raise ValueError(f"DUPLICATE_TEMPLATE_ID:{duplicates}")
        missing_objective_titles = sorted(
            {
                ref.id
                for template in self._templates
                for ref in template.objective_refs
                if not self._objective_titles.get(ref.id, "").strip()
            }
        )
        if missing_objective_titles:
            raise ValueError(
                "OBJECTIVE_TITLE_MISSING:" + ",".join(missing_objective_titles)
            )
        self._by_id = {template.template_id: template for template in self._templates}
        self._policy_version = policy_version

    @staticmethod
    def _context_identity_failures(
        context: P1ContextV1,
        template: ActivityTemplateV1,
        objective: VersionedRefV1,
    ) -> tuple[str, ...]:
        failures: list[str] = []
        activity_id_present = context.selected_activity_id is not None
        activity_version_present = context.selected_activity_version is not None
        if activity_id_present != activity_version_present:
            failures.append("CONTEXT_ACTIVITY_REF_INCOMPLETE")
        elif activity_id_present and activity_version_present:
            if context.selected_activity_id != template.activity_ref.id:
                failures.append("CONTEXT_ACTIVITY_ID_MISMATCH")
            if context.selected_activity_version != template.activity_ref.version:
                failures.append("CONTEXT_ACTIVITY_VERSION_MISMATCH")

        objective_id_present = context.selected_objective_id is not None
        objective_version_present = context.selected_objective_version is not None
        if objective_id_present != objective_version_present:
            failures.append("CONTEXT_OBJECTIVE_REF_INCOMPLETE")
        elif objective_id_present and objective_version_present:
            if context.selected_objective_id != objective.id:
                failures.append("CONTEXT_OBJECTIVE_ID_MISMATCH")
            if context.selected_objective_version != objective.version:
                failures.append("CONTEXT_OBJECTIVE_VERSION_MISMATCH")
        return tuple(failures)

    def select(
        self,
        anchor_set: SemanticAnchorSetV1,
        context: P1ContextV1,
        *,
        preferred_template_id: str | None = None,
    ) -> P1FilterResultV1:
        missing = context.missing_fields()
        if not context.gate_a_confirmed:
            return self._blocked_filter("NO_ELIGIBLE_ACTIVITY", "BLOCK_GATE_A_UNCONFIRMED")
        if missing:
            return self._blocked_filter(
                "MISSING_CONTEXT", *(f"MISSING_CONTEXT:{field}" for field in missing)
            )

        if preferred_template_id is not None:
            template = self._by_id.get(preferred_template_id)
            if template is None:
                return self._blocked_filter("NO_ELIGIBLE_ACTIVITY", "STALE_TEMPLATE")
            templates: tuple[ActivityTemplateV1, ...] = (template,)
        else:
            templates = tuple(
                template
                for template in self._templates
                if self._anchor_match_score(anchor_set, template) > 0
            )
            if not templates:
                return self._blocked_filter("UNKNOWN_ANCHOR", "ANCHOR_NOT_IN_TEMPLATE_LIBRARY")

        allowed: list[tuple[int, ActivityTemplateV1]] = []
        blocked_reasons: list[str] = []
        for template in templates:
            context_reasons = self._context_identity_failures(
                context, template, template.objective_refs[0]
            )
            if context_reasons:
                blocked_reasons.extend(
                    f"{template.activity_ref.id}:{reason}" for reason in context_reasons
                )
                continue
            reasons = self._hard_rule_failures(template, context)
            if reasons:
                blocked_reasons.extend(f"{template.activity_ref.id}:{reason}" for reason in reasons)
            else:
                allowed.append((self._anchor_match_score(anchor_set, template), template))
        if not allowed:
            return self._blocked_filter("NO_ELIGIBLE_ACTIVITY", *blocked_reasons)

        allowed.sort(key=lambda item: (-item[0], item[1].template_id))
        best_score, selected = allowed[0]
        if len(allowed) > 1 and allowed[0][0] == allowed[1][0] and preferred_template_id is None:
            return self._blocked_filter("AMBIGUOUS_ANCHOR", "MULTIPLE_EQUAL_ANCHOR_MATCHES")
        objective = selected.objective_refs[0]
        return P1FilterResultV1(
            status="VALID_CANDIDATE",
            activity_ref=selected.activity_ref,
            objective_ref=objective,
            template_ref=VersionedRefV1(id=selected.template_id, version=selected.template_version),
            reason_codes=(f"ANCHOR_MATCH_SCORE:{best_score}",),
            candidate_refs=tuple(item[1].activity_ref for item in allowed),
        )

    def compile(
        self,
        anchor_set: SemanticAnchorSetV1,
        context: P1ContextV1,
        *,
        preferred_template_id: str | None = None,
        semantic_match: SemanticMatchEvidenceV1 | None = None,
    ) -> ExperienceCompilation:
        selected = self.select(anchor_set, context, preferred_template_id=preferred_template_id)
        if selected.status != "VALID_CANDIDATE":
            gate = IntegrationGateDecisionV1(
                status="BLOCKED",
                session_id=context.session_id,
                expected_session_version=context.expected_session_version,
                reason_codes=selected.reason_codes,
            )
            return ExperienceCompilation(selected, None, None, gate, None)

        assert selected.activity_ref is not None
        assert selected.objective_ref is not None
        assert selected.template_ref is not None
        template = self._by_id[selected.template_ref.id]
        objective = selected.objective_ref
        match_score = self._anchor_match_score(anchor_set, template)
        fit = self._fit_evaluation(anchor_set, template, objective, match_score, semantic_match)
        if fit.status != "PASS":
            rejected = selected.model_copy(
                update={"status": "NO_ELIGIBLE_ACTIVITY", "reason_codes": fit.reason_codes}
            )
            gate = IntegrationGateDecisionV1(
                status="BLOCKED",
                session_id=context.session_id,
                expected_session_version=context.expected_session_version,
                activity_ref=template.activity_ref,
                objective_ref=objective,
                template_ref=selected.template_ref,
                reason_codes=fit.reason_codes,
            )
            return ExperienceCompilation(rejected, fit, None, gate, None)

        spec = self._build_spec(anchor_set, context, template, objective, fit, semantic_match)
        gate = self.approve_gate_b(spec, context)
        if gate.status != "APPROVED":
            rejected = selected.model_copy(
                update={"status": "NO_ELIGIBLE_ACTIVITY", "reason_codes": gate.reason_codes}
            )
            return ExperienceCompilation(rejected, fit, None, gate, None)
        assert gate.spec_ref is not None
        assert gate.activity_ref is not None
        assert gate.objective_ref is not None
        assert gate.template_ref is not None
        handoff = ActivityHandoffV1(
            status="READY",
            session_id=context.session_id,
            spec_ref=gate.spec_ref,
            activity_ref=gate.activity_ref,
            objective_ref=gate.objective_ref,
            template_ref=gate.template_ref,
        )
        return ExperienceCompilation(selected, fit, spec, gate, handoff)

    def approve_gate_b(
        self,
        spec: ExperienceSpecV1,
        context: P1ContextV1,
    ) -> IntegrationGateDecisionV1:
        """Re-check identity/version locks against the current catalog."""
        template = self._by_id.get(spec.activity_template.template_id)
        if template is None or template.template_version != spec.activity_template.template_version:
            return IntegrationGateDecisionV1(
                status="BLOCKED",
                session_id=context.session_id,
                expected_session_version=context.expected_session_version,
                reason_codes=("STALE_TEMPLATE",),
            )
        context_identity_failures = self._context_identity_failures(
            context, template, spec.learning_focus.objective_ref
        )
        anchor_failures = self._anchor_template_continuity_failures(
            spec.anchor_set, template, spec.semantic_match
        )
        spec_identity_failures = self._spec_identity_failures(spec, template)
        if spec.session_id != context.session_id:
            reason: tuple[str, ...] = ("SESSION_ID_MISMATCH",)
        elif not context.gate_a_confirmed:
            reason = ("BLOCK_GATE_A_UNCONFIRMED",)
        elif context.missing_fields():
            reason = tuple(f"MISSING_CONTEXT:{field}" for field in context.missing_fields())
        elif context_identity_failures:
            reason = context_identity_failures
        elif spec.fit_evaluation.status != "PASS":
            reason = ("FIT_BELOW_THRESHOLD",)
        elif anchor_failures:
            reason = anchor_failures
        elif spec_identity_failures:
            reason = spec_identity_failures
        elif spec.learning_focus.objective_ref not in template.objective_refs:
            reason = ("OBJECTIVE_ACTIVITY_MISMATCH",)
        elif not self._spec_id_matches(spec):
            reason = ("SPEC_ID_MISMATCH",)
        elif not self._spec_hash_matches(spec):
            reason = ("SPEC_HASH_MISMATCH",)
        else:
            reason = ()
        status: Literal["APPROVED", "BLOCKED"] = "APPROVED" if not reason else "BLOCKED"
        return IntegrationGateDecisionV1(
            status=status,
            session_id=context.session_id,
            expected_session_version=context.expected_session_version,
            activity_ref=template.activity_ref if status == "APPROVED" else None,
            objective_ref=spec.learning_focus.objective_ref if status == "APPROVED" else None,
            template_ref=VersionedRefV1(id=template.template_id, version=template.template_version)
            if status == "APPROVED"
            else None,
            spec_ref=VersionedRefV1(id=spec.spec_id, version=spec.spec_version)
            if status == "APPROVED"
            else None,
            reason_codes=("GATE_B_EXACT_IDENTITY_LOCKED",) if status == "APPROVED" else reason,
        )

    def _build_spec(
        self,
        anchor_set: SemanticAnchorSetV1,
        context: P1ContextV1,
        template: ActivityTemplateV1,
        objective: VersionedRefV1,
        fit: ActivityFitEvaluationV1,
        semantic_match: SemanticMatchEvidenceV1 | None = None,
    ) -> ExperienceSpecV1:
        template_ref = VersionedRefV1(id=template.template_id, version=template.template_version)
        goal = self._objective_titles.get(objective.id, objective.id)
        anchor = anchor_set.primary_anchor
        video_plan = MediaContinuityPlanV1(
            consumer="VIDEO",
            source_artifact_id=anchor_set.source_artifact_id,
            anchor_id=anchor.anchor_id,
            objective_ref=objective,
            template_ref=template_ref,
            continuity_requirements=("KEEP_CONFIRMED_ANCHOR", "KEEP_OBJECTIVE", "KEEP_TEMPLATE"),
        )
        animation_plan = MediaContinuityPlanV1(
            consumer="ORIGINAL_ART_ANIMATION",
            source_artifact_id=anchor_set.source_artifact_id,
            anchor_id=anchor.anchor_id,
            objective_ref=objective,
            template_ref=template_ref,
            continuity_requirements=(
                "PRESERVE_ORIGINAL_ART",
                "KEEP_CONFIRMED_ANCHOR",
                "KEEP_OBJECTIVE",
            ),
        )
        activity_plan = ActivityPlanV1(
            activity_ref=template.activity_ref,
            template_ref=template_ref,
            objective_ref=objective,
            material_option_ids=template.material_option_ids,
            presentation_steps_vi=template.steps_vi,
            safety_rule_ids=template.safety_rule_ids,
        )
        bridge = BridgeSentenceV1(
            sentence_vi=(
                f"Cùng khám phá {anchor.normalized_label}, "
                f"rồi {goal.lower()} qua hoạt động này."
            ),
            anchor_id=anchor.anchor_id,
            objective_ref=objective,
            template_ref=template_ref,
        )
        unsigned = {
            "contract_name": "ExperienceSpecV1",
            "contract_version": "1.0",
            "spec_id": "PENDING",
            "spec_version": 1,
            "session_id": context.session_id,
            "source_artifact_id": anchor_set.source_artifact_id,
            "source_artifact_sha256": anchor_set.source_artifact_sha256,
            "anchor_set": anchor_set.model_dump(mode="json"),
            "learning_focus": LearningFocusV1(
                objective_ref=objective,
                selected_anchor_id=anchor.anchor_id,
                child_facing_goal_vi=goal,
                selection_policy_version=self._policy_version,
            ).model_dump(mode="json"),
            "activity_template": template.model_dump(mode="json"),
            "video_plan": video_plan.model_dump(mode="json"),
            "animation_plan": animation_plan.model_dump(mode="json"),
            "activity_plan": activity_plan.model_dump(mode="json"),
            "bridge_sentence": bridge.model_dump(mode="json"),
            "fit_evaluation": fit.model_dump(mode="json"),
            "semantic_match": semantic_match.model_dump(mode="json") if semantic_match else None,
            "policy_versions": (
                "P1_ELIGIBILITY_RULES_V1",
                "P1_FIT_WEIGHTS_V1",
                "P1_STRICT_CONTINUITY_V1",
            ),
        }
        digest = _canonical_hash(unsigned)
        spec_id = f"SPEC-{digest[:16]}"
        unsigned["spec_id"] = spec_id
        spec_hash = _canonical_hash(unsigned)
        return ExperienceSpecV1.model_validate({**unsigned, "spec_sha256": spec_hash})

    @staticmethod
    def _blocked_filter(status: FILTER_STATUS, *reasons: str) -> P1FilterResultV1:
        return P1FilterResultV1(status=status, reason_codes=tuple(reasons))

    @staticmethod
    def _anchor_match_score(anchor_set: SemanticAnchorSetV1, template: ActivityTemplateV1) -> int:
        anchor = anchor_set.primary_anchor
        labels = {item.casefold() for item in template.supported_anchor_labels}
        exact = {
            anchor.normalized_label.casefold(),
            *[tag.casefold() for tag in anchor.semantic_tags],
        }
        exact_hits = len(exact & labels)
        token_hits = len(
            _tokens(anchor.original_label, anchor.normalized_label, *anchor.semantic_tags) & labels
        )
        if exact_hits == 0 and token_hits == 0:
            return 0
        return exact_hits * 3 + token_hits

    @staticmethod
    def _hard_rule_failures(template: ActivityTemplateV1, context: P1ContextV1) -> tuple[str, ...]:
        assert context.age_months is not None
        assert context.readiness_ids is not None
        assert context.completed_activity_ids is not None
        assert context.available_material_option_ids is not None
        assert context.supervision_level is not None
        assert context.policy_flags is not None
        assert context.candidate_status is not None
        failures: list[str] = []
        if context.candidate_status != "ACTIVE_FIXTURE":
            failures.append("BLOCK_INACTIVE")
        if not template.age_months_min <= context.age_months <= template.age_months_max:
            failures.append("BLOCK_AGE")
        if not set(template.readiness_ids) <= set(context.readiness_ids):
            failures.append("BLOCK_MISSING_READINESS")
        if not set(template.prerequisite_activity_ids) <= set(context.completed_activity_ids):
            failures.append("BLOCK_MISSING_PREREQUISITE")
        if (
            SUPERVISION_RANK[context.supervision_level]
            < SUPERVISION_RANK[template.minimum_supervision]
        ):
            failures.append("BLOCK_INSUFFICIENT_SUPERVISION")
        if not set(template.policy_constraints) <= set(context.policy_flags):
            failures.append("BLOCK_POLICY_CONSTRAINT")
        if not set(template.material_option_ids) & set(context.available_material_option_ids):
            failures.append("BLOCK_MISSING_MATERIAL")
        return tuple(failures)

    @staticmethod
    def _anchor_template_continuity_failures(
        anchor_set: SemanticAnchorSetV1,
        template: ActivityTemplateV1,
        semantic_match: SemanticMatchEvidenceV1 | None = None,
    ) -> tuple[str, ...]:
        """Return hard failures for the confirmed primary anchor/template pair.

        Selection may use a ranked score to find candidates, but a PASS requires
        exact normalized-label/tag compatibility and a compatible semantic kind.
        Token overlap alone can never promote an unrelated activity.
        """
        if semantic_match is not None:
            return ()
        anchor = anchor_set.primary_anchor
        supported_labels = {item.casefold().strip() for item in template.supported_anchor_labels}
        anchor_labels = {
            anchor.original_label.casefold().strip(),
            anchor.normalized_label.casefold().strip(),
            *(tag.casefold().strip() for tag in anchor.semantic_tags),
        }
        failures: list[str] = []
        if anchor.kind not in template.supported_anchor_kinds:
            failures.append("ANCHOR_KIND_TEMPLATE_MISMATCH")
        if not anchor_labels & supported_labels:
            failures.append("ANCHOR_TEMPLATE_MISMATCH")
        return tuple(failures)

    @staticmethod
    def _bridge_identity_failures(
        bridge: BridgeSentenceV1,
        *,
        anchor_id: str,
        anchor_label: str,
        objective: VersionedRefV1,
        objective_title: str,
        template_ref: VersionedRefV1,
    ) -> tuple[str, ...]:
        sentence = bridge.sentence_vi.casefold()
        if (
            bridge.anchor_id != anchor_id
            or bridge.objective_ref != objective
            or bridge.template_ref != template_ref
            or anchor_label.casefold() not in sentence
            or objective_title.casefold() not in sentence
        ):
            return ("BRIDGE_IDENTITY_MISMATCH",)
        return ()

    def _spec_identity_failures(
        self,
        spec: ExperienceSpecV1,
        template: ActivityTemplateV1,
    ) -> tuple[str, ...]:
        """Re-check downstream identity before approving Gate B.

        ExperienceSpecV1 validates these links at construction time. Gate B also
        re-checks them so a copied/tampered fixture cannot bypass the final lock.
        """
        anchor_id = spec.anchor_set.primary_anchor.anchor_id
        template_ref = VersionedRefV1(id=template.template_id, version=template.template_version)
        objective = spec.learning_focus.objective_ref
        activity = template.activity_ref
        failures: list[str] = []
        if spec.learning_focus.selected_anchor_id != anchor_id:
            failures.append("ACTIVITY_IDENTITY_MISMATCH")
        if (
            spec.activity_template.activity_ref != activity
            or spec.activity_template.template_id != template.template_id
            or spec.activity_template.template_version != template.template_version
        ):
            failures.append("ACTIVITY_IDENTITY_MISMATCH")
        for plan in (spec.video_plan, spec.animation_plan):
            if (
                plan.source_artifact_id != spec.source_artifact_id
                or plan.anchor_id != anchor_id
                or plan.objective_ref != objective
                or plan.template_ref != template_ref
            ):
                failures.append("ACTIVITY_IDENTITY_MISMATCH")
                break
        if (
            spec.activity_plan.activity_ref != activity
            or spec.activity_plan.template_ref != template_ref
            or spec.activity_plan.objective_ref != objective
        ):
            failures.append("ACTIVITY_IDENTITY_MISMATCH")
        if self._bridge_identity_failures(
            spec.bridge_sentence,
            anchor_id=anchor_id,
            anchor_label=spec.anchor_set.primary_anchor.normalized_label,
            objective=objective,
            objective_title=self._objective_titles.get(objective.id, objective.id),
            template_ref=template_ref,
        ):
            failures.append("BRIDGE_IDENTITY_MISMATCH")
        if (
            spec.fit_evaluation.evaluated_template_ref != template_ref
            or spec.fit_evaluation.evaluated_catalog_ref != activity
        ):
            failures.append("ACTIVITY_IDENTITY_MISMATCH")
        return tuple(dict.fromkeys(failures))

    @staticmethod
    def _spec_id_matches(spec: ExperienceSpecV1) -> bool:
        payload = spec.model_dump(mode="json")
        recorded = payload.get("spec_id")
        payload.pop("spec_sha256", None)
        payload["spec_id"] = "PENDING"
        return isinstance(recorded, str) and recorded == f"SPEC-{_canonical_hash(payload)[:16]}"

    @staticmethod
    def _spec_hash_matches(spec: ExperienceSpecV1) -> bool:
        payload = spec.model_dump(mode="json")
        recorded = payload.pop("spec_sha256", None)
        return isinstance(recorded, str) and _canonical_hash(payload) == recorded

    @classmethod
    def _fit_evaluation(
        cls,
        anchor_set: SemanticAnchorSetV1,
        template: ActivityTemplateV1,
        objective: VersionedRefV1,
        match_score: int,
        semantic_match: SemanticMatchEvidenceV1 | None = None,
    ) -> ActivityFitEvaluationV1:
        anchor_failures = cls._anchor_template_continuity_failures(
            anchor_set, template, semantic_match
        )
        anchor_matches = not anchor_failures
        objective_alignment = 100 if objective in template.objective_refs else 0
        objective_matches = objective_alignment == 100

        # Hard mismatches zero the affected dimensions before weighted scoring.
        # This keeps REJECT scores below the schema threshold even when another
        # dimension is perfect, so a high score cannot override a hard gate.
        drawing = (
            semantic_match.score
            if semantic_match is not None
            else min(100, match_score * 20)
            if anchor_matches
            else 0
        )
        continuity = 100 if anchor_matches and objective_matches else 0
        safety = 100
        total = round(
            drawing * 0.30 + objective_alignment * 0.35 + continuity * 0.20 + safety * 0.15
        )
        reasons: list[str] = list(anchor_failures)
        if semantic_match is not None:
            reasons.extend(semantic_match.reason_codes)
        if not objective_matches:
            reasons.append("OBJECTIVE_TEMPLATE_MISMATCH")
        status: Literal["PASS", "REJECT"] = (
            "PASS" if anchor_matches and objective_matches and total >= 80 else "REJECT"
        )
        if status == "REJECT":
            reasons.append("FIT_BELOW_THRESHOLD")
        return ActivityFitEvaluationV1(
            status=status,
            drawing_relevance=drawing,
            objective_alignment=objective_alignment,
            video_continuity=continuity,
            montessori_safety=safety,
            total_score=total,
            reason_codes=tuple(dict.fromkeys(reasons)),
            evaluated_template_ref=VersionedRefV1(
                id=template.template_id, version=template.template_version
            ),
            evaluated_catalog_ref=template.activity_ref,
        )


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
