# FEAT-066 L5 — Bruno coverage plan (A-5) — Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT REVIEWED. This is a plan only. It authorizes no change to any Bruno file, no Bruno run, test or runtime.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. L5 is the owner's own lane (D-066-65).

**Inputs:**
- P4 Bruno inventory: `tmp/feat066-phase-a/bruno-inventory/BRUNO_COVERAGE_INVENTORY_DRAFT1_20261118.md`, 48,221 bytes, `50BACD27…`.
- A-1 register Draft 4: `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md`, 41,798 bytes, `0F3F35FD…`.
- Roadmap Draft 4, L5 card: `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`.
- Seed design Draft 6: `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT6_20261118.md`, 28,192 bytes, `CABC4BCA…`.
- Decisions D-066-68 (conventions C-D1 to C-D10) and D-066-69.
- The SRS of D-066-64.

**Collection:** `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/` in the root checkout. It has 145 request files, `bruno.json`, `ROLE_GUIDE.md` and `environments/local.bru`. It holds the owner's uncommitted edits: 13 modified and 5 untracked paths under `artifacts/be-full/`. This planning work read only:
- `bruno.json`;
- `ROLE_GUIDE.md`;
- request `parent-mobile-read-routes/137`;
- the first lines of the untracked `requests/firebase-auth-helper/001-parent-email-password-sign-in.bru`.

## 0. Security finding raised while planning (owner action, before anything else)

The untracked helper `requests/firebase-auth-helper/001-parent-email-password-sign-in.bru` holds an **e-mail address and a password in plain text** in its `vars:pre-request` block. This plan does not repeat the values.
- It is untracked: `git ls-files` does not list it, so it is not in Git today.
- If it is ever staged, the credentials enter the repository.

The tracked `environments/local.bru` also has a locally modified `bearerToken` value that P4 flagged REVIEW. This plan did not open that file.

**O-TOKEN, extended:** before any commit that touches the collection, the owner:
- (a) checks `local.bru` and puts a placeholder back for `bearerToken`;
- (b) moves the helper's e-mail and password out of the file, into Bruno's local-only process variables or the owner's shell, or keeps the helper out of Git;
- (c) changes that password if it is used anywhere real.

Nothing in L5 is committed until O-TOKEN is done.

## 1. Scope (from the register, per inventory)

| Group | Operations (frozen M2 list; register rows) | L5 coverage |
|---|---|---|
| Connected, no route-specific defect recorded | BRU-0 rows A02, A08, A17, A20, A22, A26, A27 | positive cases for the current behaviour now (BRU-0); target negatives later |
| Parent first slice C-P | M02, M03, M04, M05, M08, M09, M10, M11 | full cases (§3), including the 3 missing requests for M04, M05 and M08 |
| Other integrated or slice rows | the register §5 queues (CONV-1, C-M, C-T, C-A, the PROPOSED Parent Lesson Library slice, L2) | added **per slice, when that slice is verified** |
| Excluded or blocked | B03–B06 (EXCL); AI1–AI3, C02, M14, M23, M24 (COND or blocked) | auth-boundary and refusal cases only |
| Not audited (86 operations; O-L3SCOPE) | CB, CD, LE and PO + CB operations of register §4 | existing requests stay **as they are**; no new work until O-L3SCOPE is decided |
| Payment | none in the frozen list | owned by the payment teammate |

## 2. Rules

1. **Placeholders only** in `environments/*.bru`. Real tokens and passwords live only in Bruno's local process variables or the owner's shell, never in Git (§0).
2. **One token variable per role:** `tokenPlatformAdmin`, `tokenManager`, `tokenTeacher`, `tokenParent`, plus `tokenOtherOrgManager` for out-of-scope cases. Each request uses the token of its role. This replaces the single `bearerToken`.
3. **IDs come from the seed** (seed Draft 6 keys): `seed-org-a`, `seed-org-b`, `seed-org-c`, the class and profile IDs, and so on. The environment holds the stable seed IDs, which are not secrets.
4. **Runs are owner-run, outside the Codex sandbox.** On 2026-11-18 the sandbox hung on loopback sockets (MGR-8 G0 finding). Bruno calls a local app, so the same applies.
5. **Runs only against a disposable seeded environment:** a local app plus a `seed` database (seed Draft 6 guard). Never against `sketch2life_m2_s1a`, `be1_acceptance` or a shared database.
6. **The owner's uncommitted collection edits are preserved.** L5 file work starts only after the owner commits them or explicitly hands them over (O-BRU-BASE).
7. **Existing requests are not moved or renamed** without the owner's word. New requests go into new role folders (§4).

## 3. Case template per operation

All assertions follow D-066-68. Every response check also covers the envelope:
- `code`, `message`, `correlation_id`, `retryable`;
- `correlation_id` equals the `X-Request-ID` response header (C-D1, C-D2).

| Operation kind | Positive | Negatives |
|---|---|---|
| Read by ID | 200; key fields; flat DTO where M2 defines it | unknown ID → 404 `RESOURCE_NOT_FOUND`; another organization's ID (from `seed-org-b`) → the **same** 404 shape (C-D4); no token → 401 `AUTH_REQUIRED` |
| List | 200; `{items, next_cursor}`; default page size 25 | `limit=100` accepted; `limit=101` → 400 `INVALID_REQUEST` (C-D8); cursor continuation returns the next page |
| State-changing command | 2xx; returned revision | missing `Idempotency-Key` → 400 `INVALID_REQUEST` (C-D5); same key and payload → same result (C-D6); same key, different payload → 400 `INVALID_IDEMPOTENCY_KEY`; stale revision → 409 `STALE_REVISION` with `current_version` or the current ETag (C-D7); invalid body → 400 `INVALID_REQUEST` with `field_errors` (C-D3) |
| Role boundary | — | wrong role in the same organization → 403 `ACTION_NOT_ALLOWED`; out of scope → 404 (C-D4) |
| Seeded capacity and quota (after Billing slices) | — | org C create → 409 `CLASS_CAPACITY_REACHED`; org G create → 409 `SUBSCRIPTION_RESTRICTED`; exhausted scope → 409 `VIDEO_QUOTA_EXCEEDED`. These are **time-sensitive** (seed Draft 6 rule 5) |
| Privacy (D-066-69) | — | the School Manager roster read returns no profile contents (no name, no age) |

**Target versus current behaviour (O-BRU-TARGET).** Many negatives describe target behaviour that does not exist yet: the envelope, 400 instead of 422, 404 instead of 403, keys on routes that take none. Proposal:
- tag each such test `target:<slice>`, for example `target:CONV-1`;
- run them in a separate "target" profile, so a baseline run stays green while the target run lists the known gaps;
- never weaken an assertion to make a run pass.

## 4. Folder layout (new requests only)

New folders, with existing folders unchanged:

| Folder | Content |
|---|---|
| `requests/role-parent/` | C-P operations and their negatives |
| `requests/role-school-manager/` | C-M and W-* slices |
| `requests/role-teacher/` | C-T slices |
| `requests/role-platform-admin/` | C-A slices |
| `requests/shared/` | auth and health |
| `requests/refusal/` | excluded and blocked operations (auth boundary and refusal only) |

`ROLE_GUIDE.md` gets one table per role that lists both old and new requests.

**Stale and unmatched files (P4):**
- the org-level assignment requests 004/005 are path-drift candidates: the proposal is to prefix their names with `[STALE]` until W-ASSIGN fixes or removes them (owner's word);
- the 6 `dev`-only `storyrun-lite` upload and asset requests stay, labelled `[DEV-ONLY]`;
- the Firebase helper stays local-only (§0).

## 5. Work order

| Step | Content | Gate |
|---|---|---|
| L5-0 | O-TOKEN done; O-BRU-BASE (the owner's collection edits committed or handed over); environment variables per role (§2.2) as placeholders | owner |
| L5-1 = BRU-0 | Positive assertions for A02, A08, A17, A20, A22, A26, A27 (current behaviour) | L5-0; SEED-1 S1 on a seed database; G0 for the Lesson Library rows A17–A27 |
| L5-2 | C-P: 3 new requests (M04, M05, M08); full cases for the 8 operations | C-P verified (FEAT-081 addendum, D-066-70) |
| L5-3 | CONV-1 target negatives turn into baseline once CONV-1 is verified | CONV-1 |
| L5-4… | One step per verified slice (C-M, C-T, C-A, Billing B-2/B-3, Parent Lesson Library if approved) | each slice |
| L5-D | Full collection run on a clean seeded environment; run record | Phase D |

Each step has its own small Task Approval: the exact files, and the Bruno run as an owner-run command.

## 6. Run record (each run)

A run is recorded in an evidence note plus a summary file under `tmp/feat066-l5/`. The record holds:
- the Bruno app or CLI version;
- the environment name (placeholder values only);
- the seed stage, and the database name pattern (never the URL);
- the profile (baseline or target);
- counts of passed, failed and skipped;
- each failure, with the request file;
- the commit or pin of the collection.

## 7. Owner decisions

| ID | Question | Proposal |
|---|---|---|
| O-TOKEN (extended, §0) | Clean `local.bru` and the Firebase helper before any collection commit | do it now; change the password if it is real |
| O-BRU | Runner and who runs | the owner runs the Bruno CLI (`bru run`, version pinned) or the Bruno app in their own terminal, outside Codex. Whether the CLI is installed is NV |
| O-BRU-BASE | What happens to the owner's uncommitted collection edits | commit them first (their own commit), then L5 starts from that commit |
| O-BRU-AUTH | How each role gets a local token | the existing Firebase sign-in helper pattern (emulator or local project) per role, with the credentials outside Git; or a development auth provider if the owner prefers. This links to seed Draft 6 §7 "local FE sign-in for seeded adults" |
| O-BRU-TARGET | Encode target behaviour as tagged tests now, or wait per slice | tag now (§3) |
| O-BRU-STALE | Requests 004/005 | prefix `[STALE]` until W-ASSIGN |

## 8. Acceptance (for the later L5 tasks)

- No real token or password in any tracked file. This is checked by the security validator and a manual search.
- Every request in a step has assertions: the positive check plus the negatives of §3 that apply to it.
- A baseline run is green, or every failure is explained.
- A target run lists exactly the known gaps.
- `ROLE_GUIDE.md` matches the folders.

## 9. Not verified

- Whether the Bruno CLI is installed, and its version.
- How seeded adults sign in locally.
- The current status codes for each negative case. Many are expected to fail until their slices land.
- The content of the owner's uncommitted collection edits, beyond the files named above.
