# Console contract and architecture review

- Date: 2026-08-25
- Result: PASS
- Selection mode: `EXPLICIT_ACTIVITY_ONLY`
- Runtime dependencies: Python standard library and committed local JSON only

The console requires one Golden Activity ID/version and accepts only the closed synthetic input fields approved in revision 1. Unknown fields, IDs, enum values, versions, cross-activity materials, path traversal, and unsafe evidence run IDs fail closed.

`tools/montessori_golden/eligibility.py` is the single pure evaluator imported by both the Golden validator and console. Catalog loading, presentation, and evidence writes are separate adapters. No module retrieves, scores, ranks, recommends, persists product data, or imports backend/mobile/provider code.
