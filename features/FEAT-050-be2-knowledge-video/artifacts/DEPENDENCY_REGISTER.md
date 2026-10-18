# BE2-08 dependency register — P1 candidate boundaries

2026-10-18; baseline be64b99 / approval checkpoint1ea7b53. This is not cross-owner
contract adoption. No foundation/shared contract or migration modified.

| ID | Required boundary / owner | Current status / required action |
|---|---|---|
| D01 | BE2-07 exact DATA-26 bundle resolver, content hash algorithm, source/editorial/context/audience revisions, current eligibility | ShapeSpec only located; candidate adapter must verify stored bytes against07 hash, not invent replacement canonicalization. Need current snapshot lease/guard/invalidation contract. No extra mandatory pre-render script approval. |
| D02 | BE1 authenticated principal/org/session/audience/current consent/grant/stage and artifact finalization | Actual bindings owner-deferred. Need scoped held guard across acceptance, immutable storage refs, quarantine/no-late-exposure. No raw session DB writes. |
| D03 | BE2-01 atomic run + job + dispatch intent / attempt completion | Job UoW exists, no08 run bridge adopted. Need same-transaction participant or recoverable owner-approved intent protocol and exact rollback/CAS tests before durable atomicity claim. No two commits marketed atomic. |
| D04 | BE2-14 policy/profile/rights definitions, budget/current-use pin, generation-safe stop | Owned policy/copy contracts exist; actual registry/authority/kill-generation adoption open. Bind exact original scope/policy epoch/profile; no broad notice fallback. |
| D05 | BE2-09 DATA-27 review/playback extension |08 create/status subset exposes pending_media/ready_for_review and not_started only. These enum labels and response extension need consumer conformance; not adopted shared09 schema. No playback URL or fake Teacher approval. |
| D06 | Provider/model/license/profile/encoding/quality/deadline/retry / owner | No selection made. reviewed_library independent of generation-model gate; provider calls/weights/packages/GPU require separate decision sheet. |

## Owned candidate choices

C2c update: explicit strategy/source/profile/decoder/authority ports and media
preparation component now exist. No actual07/rights/authority/provider/decoder
adopter supplied; catalog version hash is distinct from media-byte hash. See
C2C_MEDIA_STRATEGY_HANDOFF.md for current duties and no-durable-completion boundary.

C2b update: own VideoRunRows participant/codec/migration and candidate HTTP exist,
but D03 actual authorized foundation bridge remains OPEN. HTTP snapshot is bound
and normalized inside current creation lease; no default identity/session binding
or production registration. Details: C2B_HTTP_STORAGE_HANDOFF.md. Other pending
owner adoptions below are not changed by passing local tests.

- CMD-40 body follows DATA-27; optional exact library/profile refs are candidate
  refinements, not proof that upstream registry adopted their shape. Server context
  owns principal/org/session; route composition must resolve those explicitly.
- Own pin stores exact lineage, including original policy epoch, not current
  authorization. Own pin hash: UTF8 sorted compact JSON/no NaN, no text normalization;
  source refs set-ordered by (id,version,hash). Never substitute for07 bundle hash.
- Reviewed-library pin requires exact chosen library asset and no generation model;
  generate requires model and no library; compose requires chosen library and may
  have a model only if the selected composition implementation uses one.
- Model/profile/policy refs and enum schemas here remain0.1-candidate. Missing
  current-owner/definition bindings must fail closed in subsequent composition.
- P1 pure transitions are not proof of decoder, authority or atomic job completion.
  P2/P3 add held guards and foundation binding, or record explicit CR/gate.
