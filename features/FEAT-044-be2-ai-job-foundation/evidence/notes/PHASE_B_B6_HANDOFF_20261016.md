# Phase B handoff (B-12) — what BE2-01 does not prove — 2026-10-16

- Scope: plan rev3 §8 B-12. This is a boundary list, **never a PASS**. The durable conformance
  runner prints the same list as its B-12 row (status HANDOFF).
- Original status at writing: B6_CODE_COMPLETE — PENDING_CODEX_REVIEW. Current (2026-10-16):
  Q01/B6_A17FIX01_CLOUD_RECEIPTS_VERIFIED_PENDING_STUDIO. Received cloud raw receipts show
  221 B2–B6 +224 Phase A PASS/0 failure/error/skip and43/43 required durable PASS on manifest5b76868d.
  Exact two-file correction is ported locally; Studio A17-fix01 NOT_RUN, B6-CR01 open, B-12 still
  HANDOFF. See PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md in this notes directory.
- Component decisions Q1–Q8 are PROJECT_OWNER_DIRECTIVE (decision record rev9 §13), not role
  sign-off.

| Deferred item | What BE2-01 provides now | Receiving owner |
|---|---|---|
| Real owner fence (OwnerFenceV1): fence rows/function, decision change + notice in one owner transaction, notice transport (Q2/Q3/Q8) | Port `OwnerFencePort`; FOR SHARE hold on the UoW connection; ASSUMED_CONTRACT `owner_fence_fixture` proving the protocol | P2 / BE1 |
| Production audit storage and artifact quarantine adapter (Q4/Q5) | Deterministic event ids; leased at-least-once delivery; component sinks deduplicating by event id | BE1 audit/artifact owners |
| Worker capability key provisioning, `key_id` rotation, process wiring (Q6) | HMAC attempt-bound capability; multi-key verification; per-run ephemeral test keys | P4 / INTG-02 |
| Live router/namespace and HTTP surface beyond the CMD-44 fixture app | Fixture app (GET CMD-44 only); not wired into the live app | P4 / INTG-02, later BE2 cards |
| Provider inference and real provider adapters; any exactly-once execution | Fake provider; no claim journal by design (§7.1 W07) | BE2-04 / BE2-08 |
| Durable ProviderCopyLifecycle and actual provider-copy deletion | Phase A fake (A-18) and contract candidates | BE2-14 |
| Production policy values (retry, dispatch, capability TTL, notice bound) and deployment | `fixture.durable_jobs.v0`, PROPOSED | Project owner / INTG-02 |
| P1/P2/P4 role sign-off, registry and production adoption | PROJECT_OWNER_DIRECTIVE component decisions | P1 / P2 / P4 |

Rules for receivers:
- Use the versioned ports and contracts. There must be no direct coupling to `ai_jobs` tables.
- Treat Phase B fixture results as component evidence only.
- Workflow per decision 116: one reviewed task branch per card, integrated through dev.
