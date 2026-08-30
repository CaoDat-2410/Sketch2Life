# Evidence index

| ID | Related task | Type | Result |
|---|---|---|---|
| EV-003-T1-01 | P2-T1 | Validation and review | `notes/P2_T1_MEDIA_VALIDATION.md`: deterministic PNG/WAV validation, source-hash preservation, all reason-code coverage, and repository checks passed. |
| EV-003-T2-PLAN-01 | P2-T2 | Research inputs | `notes/P2_T2_ASR_RESEARCH_SOURCES.md`: handbook and upstream-source findings that constrain the ASR research plan; no model run was performed. |
| EV-003-T2-PLAN-02 | P2-T2 | External-review brief | `notes/P2_T2_CLAUDE_REVIEW_BRIEF.md`: self-contained Vietnamese brief and checklist for an independent plan review; no implementation is authorized. |
| EV-003-T2-PLAN-03 | P2-T2 | External-review findings | `notes/P2_T2_CLAUDE_REVIEW_FINDINGS.md`: independent review result — `CHANGES_REQUIRED`; the 5 required findings are now folded into `plan/P2_T2_ASR_RESEARCH_PLAN.md` (resolution logged in the same note). Implementation approval is still separate and outstanding. |
| EV-003-T2-PLAN-04 | P2-T2 | Logic/constraint disambiguation review | `notes/P2_T2_LOGIC_CONSTRAINT_REVIEW.md`: discriminated-union `AsrResultV1`, empty-transcript Case A/B rule, retry/repair matrix, source-vs-working-copy split, closed `AsrProfileCatalogV1`, and P2-T2/P2-T5 ownership check, plus two wording-consistency addenda fixing residual `source_audio_ref`-required ambiguity, no-Whisper-placeholder ambiguity, `attempt_number`/fake-adapter wording, and an out-of-catalog `requested_profile_id` routing gap. Verdict `READY_FOR_APPROVAL` for Phase A (contract/fake-adapter) scope only; Phase B and P2-T5 remain separately gated. Implementation approval is still separate and outstanding. |

Future P2-T2 through P2-T5 evidence will add fixture manifests, model/config hashes, schema validation output, quality metrics, latency, and provider-failure cases after their separate approvals.
