# Merge reconciliation and verification boundaries

Date: 2026-10-10, Asia/Saigon. Source f9594268b22c026f6b8ba837e3f3f9e8831a7280, dev396b4f67ddcb413f1ae72fdc9ca0746419f449a4, pre-merge approval checkpoint075605423d8ad5896e13a43273302b339be170b7.

## Six actual conflicts

- backend/.env.example and Settings: additive whiteboard/story fields; existing dev Pixi and deployment/provider policy retained. New feature flags remain False.
- backend HTTP app.py: retains all dev validation redaction, early Settings initialization, child preferences, auto-rig/Pixi ports/state/helpers. Adds incoming story/whiteboard routers and services with shared image artifact-store wiring. Backend composition delta is173 insertions and zero deletions across those three files.
- ArtworkCards: keeps valid dev JPG references, layout and JellyBounce accessibility; retains additive unused SVG exports. Kid3DButton's automatically removed disabled/accessibility behavior was restored to exact dev bytes.
- Flow2Screens: keeps StatusBar plus incoming Video import and experimental READY-only playback lane. AppContext's historically approved READY-only handoff remains; this is not replacement-SRS recovery-policy implementation.
- BACKEND_INTEGRATION.md: keeps actual /v1 workflow contracts from dev; appends precise experimental video endpoints and limitations. Incoming inaccurate /api examples were not adopted.

## Concrete regression and environment repairs

Unused BaoStandaloneApp copied root-relative imports incorrectly; corrected local module imports without changing active App/BaoApp entrypoint. Twenty-four inactive scaffold screens use existing colors.bgLight. Standalone voice timer uses context-owned recording time instead of an undefined setter/fake duration.

Nine missing PNG references in ErrorAndSettingsScreens and BaoStandaloneScreens now resolve to same-basename JPGs already committed on dev. Each target asset byte hash matched dev; no image was generated, materially edited or selected. Static literal image-reference audit reports27 references and zero missing. Thirty-four incoming target PNG/crops stay inactive and unapproved; four incoming FEAT-030 contact sheets are documented synthetic milestone evidence.

The codec-failure unit test now explicitly mocks renderer dependency availability, verifies that the encoder probe runs once and reports libx264 unavailable, preserving production fail-closed preflight. This makes the test independent of optional package installation.

Two required evidence directories for existing FEAT-030 auto-rig and four directories for incoming FEAT-030 story-video were absent from committed checkout. Added tracked empty placeholders only; no test evidence fabricated. Four Markdown trailing hard breaks became backslash hard breaks with identical intended line separation.

## Test environment and initial failures

Existing Python3.12.14 virtualenv and Node dependency trees are reused without modifying originals or installing packages. Worktree-only node_modules junctions point at existing dependencies. System Python3.14 is used only for stdlib/static governance tools. Backend imports prioritize the candidate via PYTHONPATH; test env uses disabled AI and real-provider E2E opt-in0. No .env/secret files are copied.

Initial command included a nonexistent backend/tests/integration directory; actual repository has unit/contract/e2e. Collection exposed12 optional media modules requiring imageio/imageio_ffmpeg. They are explicitly listed in MEDIA_ENVIRONMENT_GATES.json as REQUIRES_LIGHTNINGAI_TEST, plus one runtime media test. No missing Windows dependency was installed and no media/GPU/provider acceptance was inferred.

A first available run lacked the parent of pytest basetemp; repeated setup errors are retained as a published excerpt with full redacted log preserved under feature evidence/local and SHA lineage in BACKEND_INITIAL_LOG_ARCHIVE.json. Subsequent fixture-smoke failures showed that source tools intentionally require outputs outside Git; final runner uses a fresh, verified path under OS temp, without deleting an existing path. Mobile tests require app cwd; retry used the project script's expected cwd, preserving the earlier failure record.

Nine vision-quality mock failures came from eight ignored images absent in a clean worktree. The original package declares synthetic-only, approved deterministic CPU geometry, and recipe/image hashes. Only those eight existing images were copied into the same ignored worktree directory after verifying every hash before/after; source files, manifest, ground truth and matching rules stay untouched. See SYNTHETIC_FIXTURE_RECOVERY.json. This is mock/fixture validation, not a real-model benchmark.

Expo first detected missing PNGs; later attempts exposed physical dependency indexing/resolution for junctions. Metro reconciliation and final build outcome are recorded in the final validation note. No claim of Android visual/native acceptance is made.

## Immutable boundaries

Canonical/mirrored SRSv3.1, exact v2.0/v3.0 archives and reviewed57-card task artifact match all five protected hashes. Original checkout branch and eight protected pending runtime hashes remain unchanged; pending child_age.py is not added to this merge. FEAT-030 remains experimental with prior visual-QA and Wan OOM limits, without deployment/live provider work.
