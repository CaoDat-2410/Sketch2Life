# BE2-07 → BE2-08 cross-lane X01 review — 2026-10-20

## Result

**X01 is PARTIAL. The BE2-01–14 integration is not connected end to end.**
The implementation reads a real BE2-07 exact export through its service and
passes the script into the real BE2-08 media-preparation pipeline. It rejects a
source that becomes stale before generation. It does not submit a foundation
job, commit a BE2-08 run/artifact, or hold a producer validity fence through
such a commit.

## Reviewed boundary and implementation

- `KnowledgeScriptVideoSourceResolver` calls BE2-07
  `KnowledgeBundleService.resolve_exact` with the exact bundle ID, version,
  and hash. It checks organization/session, editorial/context/audience
  revisions, source refs, and non-empty script text. It does not read another
  feature's repository directly.
- The integration test creates the source using the real BE2-07 service,
  resolves it, then passes the resulting pin through BE2-08
  `VideoMediaPipeline.prepare`. The generator and decoder are deterministic
  external-system fakes; the producer output and consumer pipeline are real.
- A changed BE2-07 source basis is detected at the next BE2-08 source
  checkpoint before the generator is called. A second race test changes the
  source while the generator is running; the post-generation check rejects the
  prepared result. A wrong exact bundle hash also fails before generation.
- The resolver uses BE2-07's process-local fixture coordinator only to make
  its own exact read consistent. Rechecks at pipeline phases are observations;
  they do not create a cross-feature fence around a BE2-08/foundation commit.

## Edge inventory after review

| Edge | State | Review result and next missing boundary |
|---|---|---|
| X01: BE2-07 → BE2-08 generation | `PARTIAL` | Exact export consumption and stale-source rejection are tested. A cross-owner commit/fence, real foundation job lineage, and committed result artifact are still missing. |
| X02: BE2-07 invalidation → BE2-09 | `NOT_IMPLEMENTED` | The candidate has BE2-07 invalidation/outbox pieces and a recording consumer fixture, but no evidenced delivery into BE2-09 review/playback with idempotent invalidation. |
| X03: BE2-12 publication → BE2-08 | `NOT_IMPLEMENTED` | BE2-12 `ContentConsumerQueries` resolves published references, but no adopted BE2-08 resolver binds that contract to its source/library port and job pin. |
| X04: BE2-12 → BE2-09/11 | `NOT_IMPLEMENTED` | The shared content reference/lifecycle contracts exist; no cross-lane consumer binding and behavior proof for both consumers is present in this composition. |
| X05: BE2-08 output → BE2-09 review/playback | `NOT_IMPLEMENTED` | BE2-08 preparation returns uncommitted `PreparedVideoMedia`; no accepted artifact/foundation completion is available for BE2-09 to review and authorize for playback. |
| X06: BE2-08 failure → BE2-10 | `NOT_IMPLEMENTED` | BE2-10 has a `FailureBridge` port, but this candidate has no adopted BE2-08/foundation event bridge with duplicate/late-result behavior proof. |
| X07: BE2-13 preset → BE2-01 | `NOT_IMPLEMENTED` | Preset automation exists; an approved dispatch adapter that creates the exact foundation job and pins policy generation is absent. |
| X08: BE2-14 policy → BE2-03/04/08/13 | `NOT_IMPLEMENTED` | BE2-14 policy services exist, but consumer adoption is absent or gated. This change does not wire fixture policy or bypass owner approval. |
| X09: BE2-01 routing → BE2-08/13 | `NOT_IMPLEMENTED` | The existing SK1 test router handles Vision and Sketch jobs only. No cross-lane consumer registry routes BE2-08/13 jobs through their owner services. |

The key stop condition is X01's commit boundary: BE2-08 explicitly describes
its prepared media as uncommitted, and its atomic submission port has no
runtime adapter in this candidate. Treating the pipeline result as a completed
foundation job or artifact would overstate the evidence. Close this gap only
after the owners define and approve how BE2-07 validity, BE2-08 run/artifact,
and BE2-01 job/attempt/outbox commit together. X02–X09 need their own owner
contract adoption and behavior tests; do not infer them from this first edge.

## Verification

Environment: existing ignored `backend/.venv`, CPython 3.12.10. No packages
were installed. Final source-bound checks:

| Check | Result |
|---|---:|
| Cross-lane registry + X01 behavior suite | 14 passed, 0 failed, 0 skipped |
| Direct BE2-07/08 adjacent unit suites | 282 passed, 0 failed, 0 skipped |
| Ruff on cross-lane adapter and tests | PASS |
| mypy strict on adapter and cross-lane tests | PASS |
| Harness, repository security, architecture, skeleton validators | PASS |
| `git diff --check` | PASS |

JUnit and logs are under `evidence/raw/cross-lane-x01-20261020/`; exact
commands, source hashes, and JUnit SHA256 values are in
`evidence/metrics/CROSS_LANE_X01_20261020.json`.

## Scope and current state

- Candidate branch remains `feature/be2-backend-ai-integration` at
  `1649b72978877d82b4d7662040ff3555dee0a3a7`; the pre-existing dirty worktree
  was preserved.
- No card-owned source, contract, migration, status, or acceptance record was
  changed. No SQL, provider, Lightning/Studio, HTTP server, or live worker ran.
- No files were staged, committed, pushed, merged, or deployed.
- FEAT-057 remains IN_PROGRESS. Overall result remains PARTIAL until X01 is
  completed and X02–X09 each have their own source-bound outcome.
