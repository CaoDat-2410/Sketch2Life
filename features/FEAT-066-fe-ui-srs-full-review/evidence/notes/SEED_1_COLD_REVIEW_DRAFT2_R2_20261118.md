# SEED-1 Draft 2 — cold review record (round 2, 2026-11-18)

- **Artifact:** `plan/PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT2_20261118.md`, 13,754 B, SHA-256 `EB105D57CB980BEB2DAE9DE8C3CA6920DEBD84976CCD41EA87AEB5E30D2F0424`.
- **Reviewer:** a fresh subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only and statically.
- **Pin check:** PASS. It covered Draft 2, the round-1 record (`33C2AC3D…`), the seed design Draft 6 (`CABC4BCA…`) and HEAD `08439b22`.
- **Verdict:** **NOT READY**. P1 = 0, P2 = 2, P3 = 6. All findings are text-level. The scope and the application of SD-1 to SD-5 are sound.
- **Coordinator spot-check:** both points below are confirmed in source.
  - `_recalculate_visibility` (`service.py:1280–1309`) counts only ACTIVE grants with `expires_at` NULL or in the future. With no qualifying grant it falls back to the lesson's own `internal_visibility`, not to PRIVATE.
  - `_current_input` raises 409 `PARENT_STORY_CONTEXT_UNAVAILABLE` when `current_input_revision` is NULL (`parent_story_repository.py:1555–1557`).
- **Round-1 status:**
  - Fixed: S1R-03 to S1R-07 and S1R-10.
  - Partly fixed: S1R-02, S1R-08 and S1R-09.
  - Not fixed: S1R-01; the fix introduced S2R-01.

## Findings

| ID | Sev | Finding (short) | Same class as round 1? |
|---|---|---|---|
| S2R-01 | P2 | The pure visibility rule is wrong in two ways: it ignores `expires_at`, and it uses a PRIVATE fallback where the product uses `internal_visibility`. L3 would come out PRIVATE instead of SCHOOL, so tests 6 and 7 would fail. GR1's `expires_at` is unstated | Yes (S1R-01) |
| S2R-02 | P2 | The StoryRun column rules are still incomplete: `current_input_revision` (NULL makes every run unreadable), `revision` and `version` greater than 0, `actor_scope_kind = PARENT_ACCOUNT`, UUID-parsed `profile_ref` and `source_profile_revision_ref`, `active_owner_parent_account_id` holding the Parent's `account_id`, `child_age_months` belonging on `story.runs`, the product-shaped context snapshot and its hash, `lesson_pin_snapshot` as SQL NULL. There is no read-back test through `get_run` | Yes (S1R-02) |
| S2R-03 | P3 | Principal reference columns (`audience_ref`, `parent_principal_ref`, `created_by`, `granted_by`, `invited_by`) hold the adult subject, not the account UUID. This is unstated | No |
| S2R-04 | P3 | §5 is inconsistent: working directories and paths do not match, the env-prefix syntax is not PowerShell, the mypy strict baseline makes a pass undefined, and `git diff --check` skips untracked files | Yes (S1R-09) |
| S2R-05 | P3 | §2 lists 4 of 13 Alembic heads. The runbook leaves `S1A_P_ALEMBIC_DATABASE_URL` optional, but `env.py` then falls back to other settings | No |
| S2R-06 | P3 | Guard tests must use `monkeypatch` and clear the caches on teardown. The test 7 parity check must roll back, because the product method updates `updated_at` | No |
| S2R-07 | P3 | Table coverage: `lesson.version_activities`, `parent.command_receipts` and `story.command_receipts` are unmentioned. The source-document exclusion is not called a design departure. Who writes the governance records is unstated | Yes (S1R-08, S1R-10) |
| S2R-08 | P3 (info) | §8 quotes the owner verbatim in Vietnamese | No |

## Review-limit check (D-171 item 11)

| Round | P1 + P2 |
|---:|---:|
| 1 | 4 |
| 2 | 2 |

- P1 + P2 fell, so the "not falling" condition is not met.
- S2R-01 and S2R-02 repeat the classes of S1R-01 and S1R-02, so the **repeat-class condition is met**.
- The coordinator does not start Draft 3 on its own; the owner decides (rounds used: 2 of 5).
