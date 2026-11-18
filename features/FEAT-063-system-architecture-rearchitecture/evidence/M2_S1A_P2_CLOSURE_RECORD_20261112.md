# M2 S1a-P2 Closure Record — Draft for Owner Acceptance

**Status:** ACCEPTED WITH KNOWN GAP
**Record state:** ACCEPTED by the owner on 2026-11-13. This record closes S1a-P2 with the known gap documented below; it does not verify PostgreSQL PATCH, DELETE, or list.

## Gate P2 attempt 1

Run ID `20261112T190546Z_gate_p2_1e9cc01d24e3`; FAILED with `GATE_P2_POST_INVENTORY_MISMATCH`. The pre-inventory matched the accepted Gate B baseline; no post-inventory was produced. Owner-run read-only counts show only create committed: parent.child_profiles +1, parent.profile_revisions +1, parent.command_receipts +1. The approval is CONSUMED and must not be reused. No second attempt on the M2 task database is authorized. Three extra synthetic rows remain; no cleanup.

The best-supported cause is an INFERENCE from code because the runner safety scan withheld pytest output: the read-only ownership pre-check left an implicit transaction open before the repository transaction. The owner accepted this hypothesis. The fix scopes the pre-check in its own transaction and is covered by two offline regressions (an autobegin Session double for ownership/PATCH/DELETE and a real SQLAlchemy Session with in-memory SQLite for SELECT-then-begin). This does not verify PostgreSQL behavior.

## Offline results

Coordinator pytest run 4, same ten files: `1 failed, 125 passed in 75.59s`; only the unchanged baseline OpenAPI catalog test failed. Stdout 38,358 bytes / `D440DA6E8353E7CD9E3486D081DF5FFFCC081C7F4F44CB4C4F8AA28B84CD2009` at `tmp/m2-s1a-p2-impl/coordinator_post_run4_20261113T093225/pytest.stdout.txt`; no exit-code receipt in the listed folder. Targeted mypy --strict and Ruff on the two changed files each exited 0 with 0 diagnostics (mypy 44 B / `0C37C4158C91EF55C724BA017BF6465F26018199BADB08E3FF13F98ACDF056C2`; Ruff 19 B / `82B3E6A6C090A57601D22943BD23FCA9218D1031DBE5A7B754092F9A156B4F18`). Widening consumed; full mypy/Ruff remain non-PASS baseline comparisons.

| Changed file | Current bytes | Current SHA-256 | Prior R5 pin | Pre-rework Gate P2 pin |
|---|---:|---|---|---|
| backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py | 19813 | `1AF38B44ACBB40C94BD0B77F54A1BF0B1C90AE5F8C9F9D9A95DA055B5F4D1742` | `4D9C502FEA7E482607CF485CB11767C5280FFF3BA1F9E4055353978EB7424751` | `680FF349F7ED340EDE4C80AE085EFB0CC8DE788EA0620993115F617FA5488D63` |
| backend/tests/unit/test_parent_profiles_service.py | 10243 | `99A82152F2DA3D72BB085FB7A967EB3113FB98CF743637EC6FB0681DEF57989C` | `B9B3346B766E821B2712FFED1B7CA858AD5C29284D107B8175480DECDD44F218` | `49FB5493AFD8544A36617F09B701510D87978388698D5B2B164A072823CCCB7B` |

## Known gap and NOT VERIFIED

Real-PostgreSQL PATCH, DELETE, and list are NOT VERIFIED; this remains open on a scratch DB, never the M2 task DB, before merge to dev. Production BE1 role adapter remains NOT COVERED under D-190; Codex did not query the database. No second Gate P2 attempt or cleanup is authorized. Post-rework validators and git diff --check are NOT RUN. No DB, Alembic, runner, Docker, Modal, provider, network, stage, commit, or push action was performed by Codex in this drafting step. OWNER_MODAL_CALL_APPROVED=NO.

## Dry-run append pins

D-193 scratch append: 184,622 bytes / `E6199F504B5DF2EB4B375996F951D5C19E6690D319E4BF1BD47279CB0066E39D`. Task Approval addendum scratch append: 401,733 bytes / `F009A6298B3B1857F825FAE57287B76B24F074E5D66BAE26BA1CBAB6AEC1C1B2`. These are not live pins until the owner authorizes appends.
