# Final offline merge validation

Date: 2026-10-10, Asia/Saigon. Source f9594268b22c026f6b8ba837e3f3f9e8831a7280; prior dev396b4f67ddcb413f1ae72fdc9ca0746419f449a4.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Backend unit/contract, existing Python3.12 venv, candidate imports, disabled AI | PASS: 2001 passed, 24 skipped, 1 deselected; 194.76s | metrics/backend_complete.json; raw/backend_complete.txt; src/run_backend_offline.py |
| Mobile TypeScript | PASS | metrics/mobile_typecheck.json |
| Mobile fixture tests | PASS: 22 tests, 2 files | metrics/mobile_tests_final.json |
| Mobile UI copy/recovery | PASS | metrics/mobile_copy.json |
| Renderer TypeScript/tests | PASS: 67 tests, 14 files | metrics/renderer_typecheck.json; metrics/renderer_tests.json |
| Expo web export from exact staged snapshot | PASS: 321 indexed input files byte-equal, 583 modules, 29 assets, 33 exported files; 21.45s | metrics/mobile_build_verified.json; metrics/mobile_build_snapshot.json; raw/mobile_build_verified.txt |
| Architecture/harness | PASS | metrics/architecture.json; metrics/harness_final.json |
| Security | PASS, independently reviewed; rerun before each commit/push | metrics/security_candidate.json; final publication gates |
| Candidate/immutable/local integrity and staged whitespace | PASS: no conflicts, five protected artifact hashes, eight original runtime files unchanged | metrics/CANDIDATE_REVIEW.json; metrics/candidate_final.json |

## Explicit limits

Backend coverage above excludes twelve optional-media test files at collection, named in MEDIA_ENVIRONMENT_GATES.json, because imageio/imageio_ffmpeg are unavailable in the existing Windows environment. One media-renderer test is explicitly deselected for the same dependency gate. Twenty-four collected tests skip their optional runtime/environment paths; their skipped behavior is not claimed passed. The missing-media/model/GPU gate remains REQUIRES_LIGHTNINGAI_TEST. No real-provider E2E, model inference, native Android build/device acceptance, visual approval or deployment was performed. Web export demonstrates bundling, not Android acceptance or replacement SRS completion.

Initial failed backend and cross-drive Metro receipts remain as honest troubleshooting history. backend_complete.json supersedes earlier backend FAIL receipts for the available offline suite; mobile_build_verified.json supersedes earlier failed export attempts. Installed Metro0.81 cannot round-trip cross-drive paths; the successful export uses a same-volume indexed snapshot and existing dependency junctions, with no package install or original source change. Normal-checkout configuration retains two bounded watch roots and app-first React Native0.76.9; isolated snapshot adds only its physical app dependency root.

Eight approved synthetic vision fixture images were recovered only into ignored local paths with exact hashes; their manifest/ground truth stayed unchanged. No real child media, secret, provider endpoint or external handbook original is published. Incoming dormant target assets remain unapproved and unreferenced.

AC01/03/04/05 satisfied before commit. AC02/06 require actual remote publication and ancestry verification, to be recorded in PUBLICATION.md. The managed worktree remains available for review and its ignored full diagnostic.

Published command logs normalize trailing whitespace and final blank lines for Git hygiene; command content/results remain unchanged. The ignored full initial diagnostic and its recorded SHA are preserved byte-for-byte.
