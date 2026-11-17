# E07 — C3b video provider-copy component and handoff

2026-10-18 Asia/Saigon; parent e21c7dd, branch feature/be2-08-14. Approved
revision1 P3; no new provider/profile/provisioning/DB/GPU activation or adoption.

## Delivered / semantics

- Internal strict VideoCopyJournalEntry and video_copy_entry metadata producer:
  exact video/job/attempt/pin/media-operation lineage, subject scope, copy ID,
  original provider profile version/hash and source reference/hash. Input/script/
  output/cache/job roles; script maps to existing14 input, no shared kind change.
  Subject scope is explicit, never guessed from session. Provider profile is an
  explicitly resolved distinct reference, not assumed model/content/encoding ref.
- These values are metadata, NOT authenticated source proof or complete inventory.
  No raw script/bytes/capability/provider URL/token stored in this DTO. No claim
  that original registration happened or a copy exists just from construction.
- VideoProviderCopyHook consumes existing14 operation envelope without shared
  contract edits. Revalidates exact digest/key, authenticated original journal
  target/profile and current hook boundary before effect; confirms after effect.
  Malformed/foreign original never reaches control. No permissive actual boundary.
- Injected VideoCopyControl receives ORIGINAL envelope/key/body/profile. No
  fallback/retry loop/new key. Missing control => Unsupported. Provider error/lost
  ACK, malformed response or post-effect authority/guard failure => Pending with
  closed code and no guessed rollback, cancellation/deletion or raw diagnostics.
- Receipt_available passes exact reference/hash only to14's separate verifier.
  Hook return is not actual deletion, cancel confirmation or BE1 closure.
- Composition test uses14 dispatcher: claim commits first, control outside DB
  transaction, guarded delivery result recorded. MEMORY/ASSUMED authority/source
  and synthetic control only, NOT actual cross-owner/provider/DB integration.

## Actual adoption still required

1. Persist planned original keys/journal before or with generation-side effects;
   authenticate discovered copies including failed/ambiguous jobs. Retain exact
   subject/job/policy generation/profile/source binding for original-scope recovery.
   This component does not automatically journal/register copies in generation.
2. Connect producer metadata to14 inventory via current authenticated source and
   subject authority. Existing14 inventory API needs a data-request context; do NOT
   invent one during generation or bypass14 with direct writes/permissive grants.
   Bootstrap/discovery adapter and authenticated source completeness remain open.
3. Adopt VideoCopyHookBoundary actual source/current data-request authority and
   persisted14 claim/deadline checks, with no network calls under DB transaction.
   Cleanup authority is distinct from current teaching consent; stopped original
   attempts still require original-scope authenticated recovery/cleanup.
4. Actual provider control must enforce durable same-key/body dedup, approved
   deadlines, exact per-copy effects and supported/unsupported operations. Preserve
   originals/accepted references via actual fences; no broad purge or newer policy
   epoch cancellation. Real accepted-vs-cleanup races are NOT proven by local tests.
5. Selected provider must enumerate actual input/script/output/cache/job sources;
   report missing/unknown sources, no completeness claim from empty/fixture lists.
   Actual14 verifier must resolve authenticated receipt bytes/source/hash; no
   provider evidence fabricated just because hook returns a reference.

CR08-01/D01–D06 actual adoption remains OPEN. P3 owned hook surface exists;
actual start/completion/storage/provider-copy integration not complete. P4
consolidated runner/decoder pack/acceptance audit next, actual SQL11 NOT_RUN and
actual P5 generation separately gated. Whole08 remains IN_PROGRESS.

## Evidence

- New tests/unit/test_knowledge_video_copy.py:48 PASS. Includes5 roles x2 actions,
  explicit profile/scope, native source/boolean/role invalidity, original version
  mismatch,14 dispatcher outside-DB composition, missing control/source/current
  rights failures, ambiguous effect/guard exit, malformed response, separate
  receipt verification and same-key recovery without hook-side retry loop.
- First focused run35 PASS/1 FAIL: test referenced nonexistent receipt_ref instead
  of DeliveryResponse.reference; corrected assertion. Initial Ruff line length and
  Mypy optional attempt ID findings corrected before final runs, no ignored errors.
- Final51-suite regression:1857 PASS,0 failures/errors/skips,11.060s, exit0.
  Cumulative422 own =374+48;1435 existing policy/content/foundation regressions
  remain separate from08 acceptance. Suite selection: unit/contract files matching
  `test_(ai_policy_|learning_content_|knowledge_video_)`, plus existing
  ai_job_application/review_regressions/q00_followups suites; backend venv pytest
  `-q --disable-warnings --tb=short --junitxml=...`.
- Ignored private JUnit: `.runtime/knowledge-video/C3b-copy-20261018/regression.xml`.
  SHA25637644f4e80a0d750e45a5f3c13fc3ea41efa0d1ad9bca664c5c52683776ce480.
- Backend source inventory643 files: sorted unique `rg --files src tests alembic
  -g '*.py'` plus pyproject.toml/alembic.ini. Exact path/hash lines before/after
  unchanged=True. SHA256 of UTF8 newline-joined sorted Windows relative
  `path=UPPERCASE_FILE_SHA256` lines:
  a897895101b9b5e21bfc44939aab66a0f7a447e6b53e9877022f25913980d6f9.
  Documentation updated together after tests; outside this backend inventory.
- Ruff all19 owned sources/all own unit-contract and prepared integration suites/
  Alembic env/own migration PASS; Mypy19 --follow-imports=silent PASS. Architecture,
  feature harness, repository security and diff checks PASS; approval plan SHA256
  unchanged. Security scanner checked3366 publishable files, no sensitive findings.
- No actual PostgreSQL/provider/decoder/generation/deletion execution; fake
  conformance cannot be reported as actual cancellation/purge/integration proof.
