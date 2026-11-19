# CONV-1 Draft 4 — cold review record (round 4, 2026-11-18)

- **Artifact:** `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT4_20261118.md`, 45,611 B, SHA-256 `A159A84EB403F0762C7DB2A4BD36A3992E5A3F2C5494482F88FD60EEBA60F511`.
- **Reviewer:** a fresh subagent, distinct from the reviewers of rounds 1 to 3. Model Sonnet 5.5 (`claude-sonnet-5-5`), reasoning effort high, both set explicitly. It worked read-only and statically.
- **Reviewer deviation:** the reviewer reported that it briefly wrote `/tmp/r4_*.txt` in one command by mistake and deleted it at once. Its other scratch files are under `tmp/feat066-conv1-review-r4/`. The temp-file rule was broken once; no repository file was affected.
- **Pin check:** PASS. It covered Draft 4, the SRS, the conventions contract and the round-3 record (3,242 B, `80DE3C1E…`).
- **Verdict:** **READY WITH NOTES**. P1 = 0, P2 = 0, P3 = 5.

**P1 + P2 by round:**

| Round | P1 + P2 |
|---:|---:|
| 1 | 9 |
| 2 | 2 |
| 3 | 2 |
| 4 | 0 |

- No earlier P1 or P2 class repeats at P1 or P2 level.
- R4-01 and R4-03 touch the OpenAPI-mechanism class, but only as documentation gaps (P3).

**Round-3 status:** R3-01 to R3-09 are all fixed. The reviewer judged the R3-01 catch widening safe, for three reasons:
- an unauthenticated caller is stopped earlier, with 401;
- the set of callers that fall through is unchanged; only the status carrying them changes;
- the service still returns 404 to a non-manager who is not the member.

## Findings (all P3)

| ID | Finding (short) | Fix (Draft 5) |
|---|---|---|
| R4-01 | About four BE1 operations have no catalog row: `POST /assistance-requests`, its cancel, and the two `pilot_assistance` routes. Their docs keep FastAPI's 422, so AC8's "BE1 operations" is too broad | Say "catalogued BE1 operations" in item 8 and AC8, and add these operations to the accepted-mismatch note |
| R4-02 | BE1 `be1_sessions.py:430–433` returns 409 `IDEMPOTENCY_KEY_REUSED`, where §21.4 says `INVALID_IDEMPOTENCY_KEY`. It is not on the kept or deferred lists, and item 2e overstates "used only" | Add it to the §2 kept list and the §6 C-M row. Qualify item 2e as "on Lesson Library" |
| R4-03 | 11 Lesson Library operations already have a catalog 400 row (the `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` group). `declared_responses` is keyed by status, so a new generic 400 must merge with it, not duplicate it. Row 8 does not name the new constants | State the merge in item 8. Add `BE1_KEPT_422_OPERATIONS` and `LESSON_LIBRARY_KEPT_422_OPERATIONS` to row 8 |
| R4-04 | `be1_api_smoke.py` also asserts 401 `AUTHENTICATION_REQUIRED` and 404 `NOT_FOUND`, but row 11's limit is too narrow | Widen row 11 to "its status, code and OpenAPI-response assertions" |
| R4-05 | The legacy demo 413 already sets `x-request-id`, so AC5's "legacy demo" exception is wrong | Drop it from AC5 |

## Outcome

The package is ready for owner approval after the five P3 fixes. The coordinator writes Draft 5 with those fixes only. Whether Draft 5 needs a re-review is the owner's decision; the precedent is the seed design Draft 6, where P3-only fixes were not re-reviewed by owner instruction.
