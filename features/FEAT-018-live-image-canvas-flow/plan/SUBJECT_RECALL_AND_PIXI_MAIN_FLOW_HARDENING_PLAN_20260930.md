# Subject recall and Pixi main-flow hardening — 2026-09-30

- Feature: FEAT-018 live image/canvas flow, with FEAT-030 renderer consumer.
- Revision: 1
- Status: `APPROVED — IMPLEMENTATION AUTHORIZED`
- Approval basis: owner approved the bird-recall correction, chose adult-confirmed manual continuation,
  editable/addable subjects, and one explicit shared re-query; owner then directed a bounded potential-bug
  audit and fixes for this main flow, especially Pixi.
- Decisions: (1) if AI still misses after re-query, an adult-entered subject can proceed as a clearly
  adult-confirmed correction; (2) adults can edit detected subjects and add a missing one; (3) AI re-query
  is user-triggered, at most once per image session, sharing the existing direction-requery budget.

## Problem and evidence

The supplied examples show a visible bird omitted from primary topic choices while branch/leaf claims
remain, and Pixi reports `MASK_BACKGROUND_RECONSTRUCTION_FAILED`. Source review found that exact-label
normalization can map unlisted ASCII labels to a generic phrase later filtered from topics, and subject
ranking does not distinguish a whole subject from a plant part. A no-grounded-claims result returns the
session to `CREATED`, where the current mobile path stops before Gate A. The existing Gate A V1 requires
at least one AI claim ID, so it cannot represent a manually supplied subject without misattributing it.
The existing explicit direction re-query is limited to one per session and only accepts `GATE_A_PENDING`.

The Pixi failure has an offline synthetic regression: a seven-pixel saturated outline blocked the prior
five-pixel credible-paper search; the renderer search has been increased to a bounded 12 pixels. This
plan adds a flow-level audit around that repair and the startup/bridge/artifact/playback states; it does
not assert live SAM/model quality from synthetic fixtures.

## Goal

Do not silently drop a valid subject claim or strand an adult when vision misses one. Keep the original
image safe and make every Pixi preparation/playback stage either advance or report a bounded, retryable
failure. Model recognition itself is probabilistic; the guarantee is a user-visible correction path,
not that AI can always perceive every drawing.

## Approved scope

1. Review and extend exact subject aliases/canonicalization for common object and animal labels at the
   backend/mobile boundaries. Preserve unknown but valid model labels for adult review instead of
   silently replacing them with a filtered generic label. Never fuzzy-invent a claim or its source IDs.
2. Rank a recognized whole subject ahead of reviewed part/background labels while retaining distinct,
   grounded secondary directions and the current maximum of three directions.
3. Let the adult edit a detected subject or add a missing subject in Gate A. On a no-grounded-claims
   result, expose an explicit recovery state rather than trapping the session at the prior screen.
4. Add a versioned Gate-A representation for an adult-supplied primary subject when no usable model
   claim exists. Bind it to the admitted source artifact/hash and adult confirmation, identify its origin
   as adult-entered, and never synthesize an AI claim ID. Preserve backward compatibility for V1 clients.
5. Allow one explicit user-triggered re-query using the entered correction, shared with the existing
   direction-change re-query limit. It is never automatic. If it fails or still omits the subject, keep
   the entered value and allow adult-confirmed continuation; do not loop or silently discard it.
6. Audit and fix reproducible Pixi main-flow defects across native/WebView readiness and launch replay,
   package/source/mask capability validation, bounded cutout preparation, player startup, terminal
   completion/failure, and retry. Each failure remains typed/allowlisted; preserve the exact original
   drawing, do not switch to V1 automatically, and avoid infinite loading or auto-retry.
7. Add synthetic regressions and feature-local evidence. Run relevant backend, mobile, renderer,
   contract/schema, typecheck, security and build checks. Use a local Android smoke only when it can be
   run without invoking live AI/provider inference.

## Acceptance criteria

- AC-SUBJECT-01: Common reviewed bird/animal/object aliases map consistently at backend and mobile;
  a valid unknown subject claim remains visible/editable and is not silently filtered as generic detail.
- AC-SUBJECT-02: When a whole-subject claim competes with branch/leaf/scene-part claims, the whole
  subject is the primary direction when supported; all directions retain valid source-claim IDs and
  no unsupported subject is invented.
- AC-SUBJECT-03: Gate A allows adult edits to detected labels and addition of a missing primary subject;
  UI clearly distinguishes AI-detected claims from adult-entered correction.
- AC-SUBJECT-04: Zero-grounded-claim and re-query-failure paths reach a recoverable adult correction
  state; a single explicit re-query is supported from that state and shares the existing per-session
  budget. No automatic or repeated model calls are added.
- AC-SUBJECT-05: An adult-only primary subject can pass Gate A through the new versioned contract with
  source artifact/hash and adult provenance, without a fake model claim ID; legacy V1 remains valid.
- AC-PIXI-01: Tests cover bridge readiness/idempotent replay, validated artifact handoff, cutout
  success/failure, player start/completion, and retryable terminal errors; no state can remain loading
  indefinitely without a bounded terminal result.
- AC-PIXI-02: Dense-pigment synthetic cutout uses only credible local paper donors within the bound,
  preserves every outside-mask source pixel byte-for-byte, and fails closed if no donor exists.
- AC-PIXI-03: Any renderer failure preserves the original drawing, exposes only an allowlisted safe
  code in development diagnostics, and never automatically downgrades to V1 or whole-art animation.
- AC-VERIFY-01: Focused and relevant full backend/mobile/renderer suites, contract/schema checks,
  typechecks, UI-copy validation, security validation, and renderer bundle build pass. Any unavailable
  live-provider or emulator acceptance is explicitly recorded, never inferred from HTTP 200.
- AC-PRIVACY-01: No live provider call is initiated by Codex; no user artwork, raw model output,
  credentials, personal/child data, or sensitive payload is stored in repository evidence.

## Exclusions and safety boundaries

- No promise of perfect model perception; no fuzzy claim fabrication, extra inference retry, prompt/model
  or checkpoint change, SAM request, localization call, provider call, or schema change outside the
  additive adult-subject/Gate-A contract described above.
- No unrelated Montessori/catalog, profile storage, Pixi visual redesign, asset generation, backend
  restart, commit, push, or release work.
- No real child artwork in fixtures or evidence. Live acceptance, if desired, is owner-operated.

## Verification and evidence

Use deterministic synthetic claim payloads, synthetic no-claim/re-query outcomes, synthetic adult-only
Gate-A fixtures, and synthetic source/mask pixels. Record exact commands, pass/fail totals, schema/hash
compatibility, feature-local evidence paths, device connectivity and limitations. Do not claim Android
visual acceptance unless a fresh local synthetic Pixi launch actually renders and plays.
