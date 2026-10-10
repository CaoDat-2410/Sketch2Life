# Independent allocation review

Three reviewers drafted separate FE/core/AI workstreams, then reviewed the other partitions and the assembled master. Root reviewed technical integration and source/governance consistency. Review is of documentation, not implemented runtime or classroom quality.

## Findings and resolution

1. Initial gallery/video integration depended on the entire Sketch pipeline. Removed INTG-05 hard prerequisite from INTG-06; Teacher-confirmed meaning and shared review schema support a no-Sketch path. INTG-06/09 acceptance explicitly exercises both paths.
2. Non-AI organization/purpose/retention policy for A10 had no concrete producer. BE1-15 now owns bounded policy application/version/audit behavior; CMD-48 sole P3 dispatcher invokes its versioned port. BE2-14 owns AI policy; no cross-module policy DB writes.
3. Provider-copy discovery/cancel/purge receipts were consumed without explicit producing work. BE2-14 owns ProviderCopyLifecycle contract, BE2-01 generic fake/repository support, BE2-04/08 actual provider hooks; H-DATA-REQUEST is bidirectional. Unsupported/Pending/Exception cannot be reported as actual deletion.
4. Durable DATA-25 jobs/migrations/outbox/attempt CAS lacked a delivery owner. BE2-01 P3 has a separately gated runtime follow-on; initial fixture runner stays independent. P2 generic persistence contracts do not transfer AI job logic/adapters to P2/P4.
5. Screen-time/elapsed warnings lacked explicit clock ownership. BE1-11 provides monotonic/durable session-clock/pause-resume/policy events; FE-05 consumes them. Unknown individual/offline exposure cannot be invented. OD11 numeric values/hard-stop remain open.
6. P3 cards lacked individual reviewers. All 14 now list boundary reviewers and positive/negative/evidence fields.
7. Shared DATA-24 review schema could appear to require real Sketch for video/publication. BE2-09/12 now depend only on shared foundation contract; runtime DAG explicitly excludes Sketch prerequisites for video/library.
8. FR052/053/054 mapping followed dispatcher IDs and omitted actual preset/automation owner. Added BE2-13 and BE1-11 override support, plus relevant BE2-03/14 workload/policy participants. CMD-48 retains one primary dispatcher.
9. B26 mapping section reference was wrong. Corrected to SRS B26.2.
10. FR065 Phase 2 lacked explicit integration probes. INTG-04/09 now own bounded gated proposal→Teacher override→atomic commit wiring and duplicate/stale roster/grant fault tests. Manual grouping pilot does not wait for this extension.
11. Reviewed-library video had an unnecessarily broad generation-model prerequisite. BE2-08 separates library rights/content/profile/encoding/audience/final Teacher review from generation model/provider/budget gates; full generation completion still needs actual evidence.

## Confirmed review outcomes

- 57 unique cards; 66 CMD, 35 DATA, 34 UI have one primary maintainer; all 14 modules/66 FR covered.
- Four foundation nodes have no hard dependencies; internal runtime DAG resolves all 57 nodes. Handoff candidate fixtures are separate from live-runtime prerequisites.
- Four roles match owner answers; P4 intentionally integrates, component owners retain logic/adapters/tests/fixes. No names, dates/duration estimates or forced framework/provider/model values added.
- Source FR descriptions/statuses and SRS hash retained; gate/provenance/consent/retention/video/Teacher-review constraints preserved.
- No remaining blocking documentation finding after the listed corrections. Actual conformance/quality/capacity must be evidenced in the future implementation features.

Final post-correction read-only reviewer verdict: PASS, no blocker. Verified FR052–054 participants, B26.2 citation, shared-review consumers, bidirectional provider lifecycle, library strategy gates, gated Phase 2 integration probes, and the no-Sketch path in the rebuilt master. Static coverage/DAG/source checks also pass.
