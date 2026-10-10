# Publication validation

Date: 2026-10-10, Asia/Saigon. Commands and sanitized stdout are in own raw/metrics files.

- SRS static documentation/source/link/provenance PASS; canonical and feature copy v3.1 SHA remains a95c89589843e3555e967c5e486f3bcaf4bbdf9446cb3bc9c49ed16f672964d9.
- Four-person task static check PASS: 57 cards, 66 FR, 14 modules, 66 CMD/35 DATA/34 UI/14 handoffs, 57-node DAG without cycles.
- Architecture, global harness, skeleton, historical team allocation and repository security PASS after publishing hygiene. Skeleton outputs refer to existing legacy runtime, not adoption of every old provider/toolchain for the replacement target.
- Staged diff and index preservation PASS. Index has exact original v2/v3 backup hashes, canonical/mirror SRS hash and reviewed task-artifact hash. Narrow .gitattributes preserves byte-level archives/artifacts rather than normalizing their line endings.
- Ten source prose locators normalized with original prose backups/hash manifest; source-document SHA/version/authority unchanged. Normal published prose uses LF. Originals/rendered/form/capture/temp outputs stay local and ignored, not deleted.
- Eight uncommitted historical runtime paths remain byte-identical and excluded from index; seven tracked runtime index blobs equal HEAD. No product runtime/model/device/load/provider test is claimed by documentation publication.
- Publication action and actual remote SHA verification PASS for 967f643; recorded separately in PUBLICATION.md and REMOTE_PUBLICATION.json. No forced history or deletion.
- Post-publication lineage check identified that SOURCE_REGISTER's snapshot preceded the added publication-approval row. The exact single-row addition was verified; actual published hash is recorded separately from the immutable snapshot/original hashes. All other nine source prose hashes match directly, and original local backups remain unchanged.
- Independent read-only audit of all 2,125 committed tree blobs PASS: zero security errors, no added binary originals, no protected pending runtime paths in the commit. The 191 changed paths exclude all eight local runtime paths; their hashes remain unchanged.
