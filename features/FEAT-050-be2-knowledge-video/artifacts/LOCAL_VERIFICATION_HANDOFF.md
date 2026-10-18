# BE2-08 — consolidated local checks and external test handoff

Parent d55e9ca;2026-10-18. Approved revision1 P4/P5 preparation, not actual
provider/SQL activation. Start from repository root using the EXISTING backend
environment, no dependency installation by this runner.

## One local batch

Windows PowerShell:

```powershell
backend/.venv/Scripts/python.exe features/FEAT-050-be2-knowledge-video/src/run_component_checks.py
```

On an already prepared Linux environment, use its existing Python for that same
script. This is not authorization to install tools, download weights or start GPU.

The script collects/pins exact node IDs for owned and1435 existing policy/content/
foundation regressions, executes local suites, validates exact JUnit identities/
failure/error/skip counts, Ruff/Mypy19 sources and governance/security/diff checks.
Source manifest re-enumerates all backend Python, feature source scripts, backend
config, own reviewed plan/approval/inventory and validation tools before/after.
New/deleted/changed source fails. Mutable status/context/evidence prose excluded
from executable-source closure to avoid self-referential reporting.

Private unique `.runtime/knowledge-video-component/<UTC>/` holds collection logs,
per-pack JUnit/process logs and summary.json with path-keyed SHA256 source map.
PASS is LOCAL_COMPONENT_ONLY, not full card completion. Changed tests need an
explicitly reviewed update of src/TEST_INVENTORY.json, not an auto-rebaseline flag.
Process timeout300s is a local check watchdog, NOT a provider runtime policy.

SQL11 is collection ONLY, even if inherited KV08 SQL environment variables were
set: runner removes those two variables from children and never executes the SQL
suite. No provisioning/network/provider/model command is in this pack. It does
not run nested14/12 runners or mutate their inventory/count expectations.

## Decoder fixture scope

tests/knowledge_video_decoder_fixtures.py records authored synthetic rights and
builds2 tiny solid RGB GIF frames in memory. Explicit test-only encoding/profile,
500ms/8x8/no audio. Existing Pillow loads every frame, checking full frame content,
not only a header.13 cases exercise corrupt/truncated/header-only/wrong container,
codec/hash/duration/dimensions/frame-count/encoding and byte bound. These are real
fixture bytes, not production video decoding or generation evidence. No selected
production codec/duration/decoder, executable sandbox/deadline or audio coverage.

## Separately authorized SQL/runtime work

- SQL: actual11 own-row cases prepared under
  backend/tests/integration/knowledge_video/test_run_rows_sql.py. Need owner-approved
  isolated PostgreSQL17 database, explicit schema-DDL opt-in and private loopback
  kv08_* URL; never reuse prior14 provisioning authority or existing owned schema.
  Run directly from backend ONLY after that approval/environment:
  `python -m pytest tests/integration/knowledge_video/test_run_rows_sql.py -q`.
  No connection string/credential committed here. Existing fixture refuses unsafe
  targets and tears down only own schema. This is NOT adopted run/job bridge proof.
- Foundation/BE1/07/14 adoption: original request/attempt/current owner/profile/
  consent/source/policy epoch/deadline held through actual transaction/effect.
  Same-UoW submission/start/completion, restart/lost-ACK and accepted-vs-cleanup
  concurrency need real adopter tests. Never substitute two commits or mocks.
- Production decoder: chosen explicit runtime must fully decode actual selected
  container/video/audio bytes with bounded resources/deadline; prepare supported
  rights-cleared fixtures and verify all negatives, not GIF-only or header probes.
- Generation: fill RUNTIME_DECISION_SHEET.md and obtain separate approval before
  provider/weights/packages/GPU calls. Actual per-copy lifecycle receipts and
  authenticated missing-source inventory remain required, no fake Deleted.

## Candidate CMD-40 example (fixture only)

```json
{
  "bundle_id": "fixture-bundle",
  "bundle_version": 1,
  "bundle_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "audience_context_revision": 0,
  "strategy": "generate"
}
```

POST /api/collaboration/v1/knowledge-videos with opaque Idempotency-Key, verified
identity/session supplied by server. Bundle must actually resolve; example hash
does not authenticate content.202 queue snapshot is pending_media/not_started,
not playback permission.401 unauthenticated;403 VIDEO_FORBIDDEN;409 stale/context/
idempotency/profile/unsupported conflicts;422 invalid DTO;503 closed unavailable
dependency. No raw child/script/provider errors or URL. Router unmounted by default.
No extra mandatory pre-render script approval.09 owns final Teacher review/play.

Dependency owner/action matrix remains artifacts/DEPENDENCY_REGISTER.md and
CR_ATOMIC_VIDEO_SUBMISSION.md. Current acceptance: ACCEPTANCE_AUDIT.md. Do not
count local pass or teammate-deferred wiring as waiver of full acceptance.
