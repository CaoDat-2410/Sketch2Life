# Publication review

Two read-only reviewers checked current source changes and security/harness errors. Original branch HEAD is 7be3006; refreshed dev ancestry is rechecked before integration.

Pending runtime implements historical FEAT-037 under-nine boundary, not replacement-scope migration. Existing test_run_v2_shares_scene_and_reports_personalized_or_fallback_modes includes 9–12 and conflicts with the pending guard. FEAT-037 did not claim those checks ran. Eight runtime paths are preserved and excluded by default.

FEAT-036 is a read-only UI audit with implementation AWAITING_APPROVAL. Only audit/planning text is eligible; captures/archive remain local. FEAT-037 external/form outputs/rendered extracts remain local; historical documentation/provenance/hashes are eligible. Current SRS/ADR supersession notices distinguish historical targets from new requirements.

Security hygiene excludes root .tmp and .pytest-tmp-* plus external rendered/form/capture binaries without deleting local data or removing tracked history. Machine-path prose becomes owner-local attachment basename references; SHA/version/authority unchanged, original prose copied into ignored local backup with hash manifest. This does not change source document bytes or approved product decisions.

Harness hygiene adds .gitkeep for missing FEAT-037 raw/screenshots/metrics and FEAT-038 raw/screenshots/metrics/notes; no test evidence or feature-completion claim is invented.
