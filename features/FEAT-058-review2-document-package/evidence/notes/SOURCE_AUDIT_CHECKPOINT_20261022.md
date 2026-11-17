# Source review checkpoint

- Date: 2026-10-22 Asia/Saigon
- Reviewer: Codex, source/document analysis only
- Inputs: exact local registration v1.2, canonical Master SRS v3.1, school Report1–7 templates and October 2026 BM01/Review2 guide.
- Source hashes and paths: ../metrics/source_manifest.json. External extracts/contact details: ignored ../local/.
- Reproduction: src/inspect_sources.py reads pinned Git objects without checkout or merge; ../metrics/branch_snapshot.json and inspected_objects.json pin source provenance.

## Scope and owner decisions

The supplied registration describes the collaborative classroom scope and agrees with the current canonical SRS on ages 36–155 months, Teacher-managed child profiles without child login, per-Sketch Teacher approval, child hide/decline choice, true video state and Teacher retry/skip/end disposition, one-school/one-class pilot target of 40 children, default session/artwork retention 90 days after end, and separate Child Android/Teacher Desktop/Super Admin surfaces.

Owner mapping: Bảo FE, Khoa BE1, Hiếu BE2, Đạt fullstack. Generate diagrams from the SRS. Owner accepts durable classroom runtime as main product composition and separate entrypoints for legacy Parent/Guide/in-memory demos. Modal is selected for AI hosting, with exact deployment information still to come. See DECISIONS.md D06–D10 and ADR-0019.

## Pinned branch findings

- dev / origin/dev / origin/FE_UI_Teacher: f220781876472950093856e97bbdaaec5170a7c1, 2026-10-15. Teacher remote ref does not add commits beyond dev at this snapshot.
- origin/feature/be2-backend-ai-integration: af3e28fc402f69e5a10ba55a54631c5d1f995a50, 2026-10-22, 255 commits ahead of dev, not contained in dev.
- origin/FE_UI_Admin: 46f245e2de77bcd438e89c957823c42819b221a5, 2026-10-19, 105 commits ahead, not contained in dev. Source authService returns a mock token and fixed identity; UI presence does not establish real authentication/integration.
- origin/feature/feat018-p2t5-evaluation-harness and origin/feature/feat018-p2t4-mapping-diagnostics: b11bc7b870f615e493afb1bc723b888befdb58c9, 2026-10-21. The difference from dev consists of diagnostics/manifest/evidence/tests rather than an independently proven deployed evaluation service.
- Other related branches are listed in branch_snapshot.json; a branch name does not prove which features are integrated.

## Runtime and persistence findings

- Latest backend app.py mounts durable BE1 and multiple legacy/demo routers and initializes several process-local stores. The listed BE2 application/services/routers are not all composed into the default HTTP app. Separate route declarations from actually mounted endpoints.
- BE1 ORM persists scoped classes/profiles/session/membership/groups/turns/artifacts/gallery/observations and lifecycle requests. Consent table currently permits pending/revoked only; the feature explicitly blocks child-data success until an approved consent verifier/purpose catalogue exists. A proposed verified consent workflow requires an approved implementation/schema change, not a fabricated demo grant.
- BE1 actual persisted session states are configured/lobby/active/paused/finished. Canonical SRS candidate display states include additional distinctions. A target-state diagram must state whether it describes desired domain behavior or current wire enums, and document any mapping/migration.
- BE2 AI job schema owns job/attempt/receipts/outbox. Knowledge video, content, policy, review, activities and presets have isolated schemas. Cross-context links remain opaque, without direct BE1 foreign keys. Diagram dashed logical joins must not be presented as existing SQL foreign keys.
- Captured migration graph has separate schema-owned roots/heads. Cross-lane evidence applies a bounded subset, not proof that a complete release migration strategy has been accepted.
- Two current Android baselines exist: apps/ui-mobile Expo 52/RN 0.76.9 and apps/mobile bare RN 0.87.0. Owner asks to wait for new UI split across the three surfaces; neither is selected by this task.

## Historical test evidence verified by reading artifacts

The JUnit bytes were read from the pinned BE2 branch and hashes/counts independently computed. These are historical receipts, not tests run in FEAT-058:

- 2026-10-22 bounded persisted BE2-07 → BE2-01 → BE2-08 seam: 9 tests, 0 failed/errors/skipped. JUnit SHA256 7ffb20af163f69c7b4c95d4723253805fd3df92e9aadcdf4dd6288ef85399214. Receipt describes PostgreSQL 17.11 with synthetic records, no provider/server/Modal/Lightning. Latest status still says X01 PARTIAL and BE1 handoff NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION.
- 2026-10-20 Modal CPU package: 296 tests, 0 failed/errors/skipped. JUnit SHA256 552cf4ead2dd17f409676dc77dbfccf0822a450779c1de4e25cfd25b6b31e4a3. Receipt explicitly uses 2 CPU cores/4 GiB and no GPU. It does not demonstrate a deployed inference endpoint, GPU model behavior, production performance or full BE2 integration.

Machine-readable evidence: ../metrics/verified_historical_receipts.json.

## Template and rendering checkpoint

- Template execution contract: ignored ../local/artifact.md; section geometry, styles, intended slot changes and package inventories recorded.
- School Report7 reference: 10 pages; BM01 reference: 3 pages. Source template includes broken cached TOC bookmarks and example/guidance text that must be replaced.
- Packaged render_docx.py was attempted and fails at soffice.exe lookup. Installed Microsoft Word 16 exported both references successfully; bundled Poppler rasterized their pages. Use src/render_word.ps1 and the same PDF/PNG inspection fallback for final outputs.
- Reference contact sheets and cover were visually inspected; full-page final review remains a required later gate. Preserve original input hashes.

## Resume point

Wait for new UI inputs as requested. Refresh refs at resume, record newly supplied UI commits, update the source audit, then author the consolidated Reports1–5/Tracking and separate four-page BM01 plus Appendix A. Keep Modal platform selection distinct from unsupplied deployment parameters. No final artifact exists yet; no runtime code, original form or existing dirty user file was changed.


## Final refresh after Child UI push — 2026-10-23

The owner reported that `FE_UI_Child` had been pushed and asked to fetch it before authoring. Refreshed tip `ca3779869dfc1385cbbc7b8ca730f780386af7b2` was merged into local `dev` at `0a7ce768c153f2104cff930569c3eda6e484532c`. Use this final `dev` SHA as the document source baseline; the earlier Child no-op and old `32d8bc7` baseline are historical. `apps/child-ui` is Expo SDK 55 / React Native 0.83.10; `childApiFetch` returns a stub success payload and `verifySessionPin` uses a local fixture. Do not report the app as backend-connected or claim its tests passed. Final branch evidence is in `BRANCH_MERGE_RESULT_20261023.md` and `merged_branch_snapshot_20261023.json`.

The current app package scripts show no automated test script for Child UI. Admin auth returns a mock token. Teacher and Child screens use fixtures/stub services. These UI branches establish source presence only. Existing `app.py` still mounts BE1 durable routes alongside local demo routers, while target composition is classroom-first as documented in ADR-0019. Modal remains selected but deployment details and live inference evidence are absent.
