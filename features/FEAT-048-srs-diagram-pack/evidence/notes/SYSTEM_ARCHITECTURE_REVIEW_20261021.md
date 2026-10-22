# System Architecture review — 2026-10-21

## Source and scope

- Canonical authority: SRS v3.1, section B8, source-register ID `collaborative-srs-v3-20261010`.
- Approved feature scope: the three-page SRS diagram pack, including the System Architecture page and AC-03 in plan revision 6.
- Repository rule: dependencies point inward; interfaces/adapters -> application -> domain; infrastructure implements ports.

## Finding

The previous System Architecture page showed direct arrows from Application to the Realtime adapter and Infrastructure adapters. Those arrows could be read as compile-time dependencies on outer adapters, contradicting B8's framework/provider-independent application/domain boundary and the repository dependency rule.

## Revision 7 correction

- Application now points to the Outbound ports interface box (`uses outbound port contracts`).
- The proposed Infrastructure adapters point back to that port box (`implements outbound ports • proposed`).
- The ports list includes repository, artifact, job, model, identity, and realtime interfaces. The candidates box includes relational DB, object store, queue/worker, realtime/presence, and backend-only AI provider adapters.
- Direct Application-to-adapter arrows were removed. This depicts dependency direction; queue/realtime runtime transport remains proposed and is not presented as a technology decision.
- The builder now replaces only the System Architecture page in an existing three-page artifact. This protects owner-authored ERD and Package page edits during later regenerations.

## Owner revision preservation and local checks

- Before editing Drive, its latest owner-saved revision was fetched: 84,271 bytes, modified `2026-10-21T14:55:37.614Z`, in the supplied folder.
- That Drive revision contained newer ERD edits (168 cells) and retained the existing Package Diagram. Both pages were preserved exactly at page level in the merged local artifact; only the System Architecture page was replaced.
- Local page counts after revision 7: ERD 168 cells, System Architecture 35, Package Diagram 38. All Architecture edge endpoints resolve; Application uses ports, and the proposed adapter implements those ports. No direct Application-to-adapter edge remains.
- Updated the same Drive file ID in place after confirming its metadata had not changed since the raw read. Final metadata readback verified 82,965 bytes, modified `2026-10-21T15:01:58.601Z`, and the supplied parent folder. Downloaded Drive bytes have the same SHA-256 as the local merged artifact; Drive reports 168/35/38 cells across the three pages.
- Rendered visual QA is still pending because a diagrams.net renderer/editor is unavailable in this execution. No rendered-image review is claimed.
