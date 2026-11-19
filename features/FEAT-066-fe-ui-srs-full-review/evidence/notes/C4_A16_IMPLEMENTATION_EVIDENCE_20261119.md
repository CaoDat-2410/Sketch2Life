# C4 slice A16 (Lesson Library list defaults) implementation evidence, 2026-11-19

Accepted by the goal under the program approval; the final check by the owner is pending.

Decision by the goal (SRS section 21.1 line 1642: cursor lists default to 25, max 100; plan row A16 of `plan/PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT2_20261118.md`): the `limit` default of four Lesson Library list routes goes from 50 to 25, as MGR-7 (`08439b22`) did for parent groups and access grants: `GET organizations/{org}/lessons`, `GET me/lessons`, `GET me/lesson-invitations` and `GET me/parent-group-invitations`. The last three go beyond the A16 row; they are the same SRS rule and the Parent app passes its own explicit limit. The validation (1 to 100) is unchanged. `GET platform-admin/v1/accounts` (offset paging, default 50) is not part of this change.

Change: `backend/src/sketch2life/interfaces/http/routers/lesson_library.py` (four literals) and `backend/tests/contract/test_openapi_contract_catalog.py` (the existing default/min/max check on the runtime OpenAPI now also covers the four routes).

Review: a fresh non-forked subagent (Sonnet 5.5 high; a session could not be started on that turn), ACCEPTABLE WITH NOTES (0 P1, 0 P2, 4 P3): frozen OpenAPI snapshot files still say 50 and no test gates on them (as after MGR-7); no handler-level default test; the plan's `limit_query()` helper is not used; scope note above.

Checks: `pytest tests/contract/test_openapi_contract_catalog.py` 5 passed; `pytest tests/unit tests/contract` in a clean environment: 83 failing or erroring ids, 0 new against the base list of 83; ruff counts for the two files equal the base versions; repository validators run before the commit.

Not done in task C4 (NOT STARTED in goal v2): plan rows A18, A19, B07, B08 (`Idempotency-Key` required), A24 and A25 (status 202 and the upload-session abort state) and the web callers. The package Draft 2 changes status codes and required headers across the backend, the web app, Bruno and the tests, and was not reviewed by the goal.
