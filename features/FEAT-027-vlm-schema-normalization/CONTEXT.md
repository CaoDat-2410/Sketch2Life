# FEAT-027 — Real-AI VLM schema normalization

## Status

`IMPLEMENTED_WITH_LOCAL_TESTS_LIGHTNING_PENDING`

The user explicitly requested implementation after case 02 continued to fail
with `VISION_SCHEMA_INVALID / OUTPUT_MAPPING_FAILED /`
`SCHEMA_TYPE_OR_CONSTRAINT_INVALID`.

## Problem

Case 01 passes because Qwen emits a contract-compatible observation object.
Case 02 reaches the model and passes media validation, but its output is
parseable JSON that does not satisfy the observation contract. The current
bounded repair only handles missing collections, local IDs, omitted
confidence, scalar text, and a simple language string. It does not handle the
broader shape drift that a real model can produce.

## Goal

Make the real VLM boundary normalize common safe schema drift before contract
validation, while remaining fail-closed for unsafe or ambiguous content. Every
successful result must be a fully validated `VisionUnderstandingSuccessV2`;
there must be no partially-shaped success payload.

## Constraints

- no fixture output or hard-coded case-02 observation;
- no raw model output, prompt, or child data persisted;
- preserve the source observation meaning where possible;
- never invent relation/theme references;
- malformed optional candidates may be dropped with a closed diagnostic;
- strict adapter/test mode remains fail-closed by default;
- real CLI mode may enable only the approved bounded normalizer;
- V1/V2 public contracts remain additive/backward compatible.

## Implementation result

- Added a provider-agnostic bounded normalizer before
  `VisionUnderstandingSuccessV2` validation.
- Canonicalized collection aliases, wrappers, IDs, text/language fields,
  confidence values, nullable action references, and safe reference remapping.
- Relations and themes with unresolved references are dropped conservatively;
  entity/action references are calculated only from retained records.
- Unknown-only bounded payloads remain typed mapping failures instead of being
  converted into a false empty success.
- Strict adapter mode remains fail-closed.
- Focused adapter/schema/personalization/dependency tests, compile, Ruff, and
  architecture validation pass locally. Real Lightning case-01/case-02 smoke
  is still pending.
- Repository-wide harness/security gates remain blocked by the pre-existing,
  untracked `features/FEAT-026-current-system-srs/` artifact and missing
  evidence directories; these are not part of FEAT-027.
