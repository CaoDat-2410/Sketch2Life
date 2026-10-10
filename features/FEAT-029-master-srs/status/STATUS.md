# FEAT-029 status

## Current canonical artifact — 2026-10-10

- Canonical SRS: v3.1, replacement collaborative creative learning scope and detailed system foundation, FEAT-039 documentation revision 3; owner confirmed replacement, Android, FastAPI and React Native.
- Current update/evidence owner: FEAT-039. Exact v2.0 and v3.0 preserved byte-for-byte there before edits.
- Added B19–B26: policy/state/recovery, detailed use cases, logical data/API/UI/privacy/NFR/traceability. Owner chose one-school pilot, managed profiles + QR/code without own child login and school-mediated consent evidence/purposes.
- Owner confirmed: age 36–155 completed months inclusive; one simultaneous class/up to 40 children pilot target; session/artwork default 90 days after end. Other data-class policies and measured capacity are separate.
- Target: 3–12; Child/Teacher/Super Admin; class/groups/collaborative canvas; approved knowledge video, off-screen and portfolio.
- Detailed policies, technology candidates and logical contracts remain proposed/TBD. Runtime/age/auth/storage remain unchanged by this task.
- The older status lines below describe the previous scope and historical amendments; they are not authority over v3.1.

- Status: OWNER_APPROVED_BASELINE_WITH_V2_0_DOCUMENTATION_AMENDMENT — v2.0 records the 2026-10-06 supported-age and capstone-trial package/payment/credit decisions.
- Artifact: artifacts/Sketch2Life_Master_SRS.md (v2.0, B1–B35 + Annex A).
- Current supported product age: under 9 years / 0–107 completed months; bands 0–3, 3–6, and 6–9. Ages 108+ are outside target; existing 9–12 catalog rows remain source data only.
- Package/payment: owner-approved capstone-trial package and top-up assumptions are recorded in B35. Provider choice, live billing implementation, refunds/taxes, and unused-credit expiry/rollover remain separate implementation decisions.
- v1.7 owner-confirmed story/video target: illustrated story short 40–60 seconds; age/readiness-based evidence query; quick and free-form script revision; exact adult script approval before image generation; selectable supported language/voice; separate TTS; retain Wan2.2 TI2V-5B baseline; redraw is a linked derivative and original remains immutable.
- v1.7 adds proposed content/story/video contract, API/job, validation, traceability and acceptance detail in B30–B32. All new schemas/endpoints remain `PROPOSED_UNADOPTED`; FEAT-020 implementation is not approved by this documentation update.
- Owner clarifications recorded: target workflow image and narrated story; historical age target 0–12 (superseded by the 2026-10-06 `<9` amendment); real Firebase Authentication project for test; mutually exclusive adult roles `PARENT`/`GUIDE`/`ADMIN`; no child role or credential; Parent own-child scope; Guide assignment/revoke; required desktop Guide Console; required responsive Parent Web; minimal Parent live projection; mandatory backend operational monitoring and test-stage rate limits.
- SRS v1.6 includes B1–B29 + Annex A: complete SRS introduction/overall description, external interfaces, AuthN/AuthZ, relationship/cardinality model, role/resource permission matrix, required Guide Console and Parent Web, logical schema/data dictionary, API/error/idempotency surface, use cases, offline and still-image fallback, research questions/objectives/deliverables/WPs, verification matrix, observability, retention/legal constraints, registration-to-SRS traceability, Pixi exploration and whiteboard MP4 job/provenance/readiness requirements, test topology, bounded contexts, state rules, API conventions, UI requirements, monitoring signals, synthetic personas and implementation sequence.
- Owner-approved closure now covers PixiJS exploration + whiteboard video/story, one Owner Caregiver per ChildProfile, multiple Guides, immediate assignment/revoke, stop-on-revoke, one session per Guide, Parent minimal live projection, required Parent Web, required Guide Console, full child/session retention classes with archive, separate audit retention, combined notification channels, Grafana/backend observability and break-glass Admin raw access.
- Remaining high-impact questions: exact notification channels/retry, Guide raw/history field-level permissions, Parent Web session-creation command UX, break-glass dual approval/time window/notice, physical storage/queue/Grafana deployment, legal guardian verification, consent for children 7+, backup/provider-copy deletion, SLO/RPO/RTO and account lifecycle.
- Source review/gap note: evidence/notes/REGISTRATION_SCOPE_REVIEW.md. Owner question set: artifacts/SRS_Clarification_Questions.md.
- DOCX text/tables and embedded logo images were inspected. Bundled renderer lacked LibreOffice, so page layout was not visually verified.
- No application code, provider configuration, cloud resource, real-child data, dataset publication, or pre-existing user file was modified.
- Historical 2026-09-23 whiteboard scope is superseded for story-video duration/pipeline by B30–B32. Prior evidence remains as history.
- Current owner-change review: evidence/notes/OWNER_CHANGE_STORY_VIDEO_20260928.md. No runtime tests, provider calls, or L4 benchmarks were run for v1.7.
