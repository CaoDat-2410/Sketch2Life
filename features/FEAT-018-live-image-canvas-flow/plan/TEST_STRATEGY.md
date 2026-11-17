# FEAT-018 test strategy

- Unit: image validator, provenance/hash, request contract, missing narration, Gate A/B invariants, Pixi message validation.
- Integration: backend image handoff to local Lightning adapter with fake and live-dev modes; typed provider failures and fallback.
- Device: Android emulator picker/import, canvas source/reveal rendering, renderer lifecycle, full supervised flow to feedback.
- Evidence: sanitized metadata and screenshot only; no raw image, prompt, output, token, or signed URL.

## Test matrix expansion

The full-flow device matrix covers all 20 golden activities. Each row runs a valid path and a safe failure/fallback path. The 100 MVP records are validated offline for schema, objective references, prerequisites, safety, provenance, and no-eligible behavior before any broader device rollout.

## Contract test layers

| Layer | Required check | Owner | Evidence |
|---|---|---|---|
| Schema | JSON Schema/Pydantic/TypeScript parity, extra-field rejection, version registry | shared/P1 | contract compatibility report |
| Media | source hash/status, validation reasons, no-provider-on-recapture | P2 | media validation matrix |
| AI | exact model provenance, structured output, typed failures, missing narration | P2 | AI contract fixtures + sanitized smoke |
| Gate/session | expected session version, idempotency, Gate A mandatory, Gate B identity pair | shared/P1 | state-machine traces |
| Catalog | 100 MVP + 20 golden references, objective/prerequisite/safety rules | P1 | catalog validation report |
| Renderer | source preservation, plan bounds, bridge protocol/events, fallback | P3 | renderer/bridge evidence |
| Media/cache | exact cache key, stale/corrupt/unsafe fallback, identity preservation | P4 | cache/fallback replay |
| Device | all 20 golden rows, valid + failure path, screenshot and redaction | shared/P4 | device pilot report |

A contract layer is not accepted from a single unit test. It needs a positive case, malformed case, stale/version case, and redaction/provenance case.
