# FEAT-057 approved-scope execution manifest — 2026-10-21

## Source and authority

- Worktree: `feature/be2-backend-ai-integration`.
- Candidate HEAD observed before this work: `1649b72978877d82b4d7662040ff3555dee0a3a7`.
- Governing FEAT-057 plan: revision 4, SHA256
  `6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601`.
- Revision 3 remains preserved at SHA256
  `5500B0CA5ED839C4FF5150D66FC19F2751F6C1F93261DE37BB1629747FF41C04`.
- The owner approved the five exact card scope hashes recorded in the owning
  approval files. This manifest freezes the first minimal implementation subset;
  it does not modify those approved plan bytes.
- Execution is offline only. No Modal, Lightning, provider, server, database, or
  runtime command is authorized by this manifest.

## BE2-01 / FEAT-044 — manifest frozen

Approved addendum SHA256:
`AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD`.

Exact paths:

- Modify `backend/src/sketch2life/infrastructure/ai_jobs/worker.py`.
- Add `backend/src/sketch2life/infrastructure/ai_jobs/typed_dispatch.py`.
- Add `backend/tests/unit/test_ai_job_video_dispatch.py`.

The router receives the BE2-08 job-type discriminator and worker explicitly at
composition. It preserves the envelope object and delegates authoritative
identity/admission checks to `VideoWorker`; the route does not add fields or
persist broker data. Existing `sketch_assistance` provider behavior remains
registered. Other job types fail closed without reaching the provider. This is
offline routing behavior only; no production composition is inferred.

The existing `backend/tests/unit/test_ai_job_b5_capability.py` is a read-only
regression. It may be edited only if the approved routing behavior causes a
failure and a minimal correction inside the approved test boundary is necessary.

## Remaining four scopes — implementation not started

| Card | Approved scope SHA256 | Current stop condition |
|---|---|---|
| BE2-07 / FEAT-056 | `CA531682CCB0ABD12BB8B270F0258D9B3EBBCE4DBF917805FBC7A770BBF6EB24` | Exact reads exist, but no durable source fence can be held through BE2-08 finalization in the approved candidate boundary. Any implementation evidence that only re-reads the source remains X01 `PARTIAL`. |
| BE2-08 / FEAT-050 | `6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0` | CR08-01 has no adopted foundation-owned shared UoW/recovery entrypoint in the approved files. Do not implement two commits and describe them as one atomic boundary. |
| BE2-09 / FEAT-051 | `121699BE6A3134C65EF16917941FA75F00401EA18462BA929C2E897BCAB46285` | No adopted public BE2-08 artifact-read mapping is available for the exact CR09-01 projection. X05d remains `BLOCKED`; X05c/CR09-02 remains open. |
| BE2-14 / FEAT-049 | `417A740BA60E624BE2AA78D861E8DAEF80094AAF9992C3E65E782EB7EA78C9D8` | Existing current-use/accounting ports do not grant worker/provider execution and do not specify reservation expiry/renewal for BE2-08. Keep the generation gate closed; fixture values are not provider authorization. |

No source/test paths for those four cards are frozen here because no safe minimal
implementation subset can resolve the listed stop conditions without either a
new versioned contract, a wider owner boundary, or a scope revision. Each must
receive its own file manifest before edits. FEAT-057 composition code remains
governed by the separate FEAT-057 offline integration approval and must not
simulate missing durable contracts as passing behavior.

## Preserved gates

- X01 remains `PARTIAL` until the producer/consumer current-source fence is
  implemented and proven through the finalization commit.
- X05d remains `BLOCKED`.
- X05c/CR09-02 remains open.
- No card acceptance, card status, or runtime gate changes through this manifest.
