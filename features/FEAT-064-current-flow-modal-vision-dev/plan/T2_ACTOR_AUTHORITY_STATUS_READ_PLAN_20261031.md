# FEAT-064 T2 — Actor / authority / context adapters and the status-read guard (DRAFT, AWAITING_APPROVAL)

- Status: **DRAFT.** It grants nothing. Implementation needs a new `TASK_APPROVAL.md` entry that pins this file's SHA-256, the T0 files and the T1 commit, and states the file allowlist chosen at the owner decisions below. Not yet reviewed.
- Source rows: `PLAN.md` T2 ("actor/authority/context and AI-capability adapters; split status-read from the write guard"; depends on T1; acceptance "server verifies grant, identity, scope and eligibility; a write needs a turn; status-own needs no active turn but still blocks a revoked or foreign scope"), T0 contract freeze sections D-05 item 5 and D-06, and manifest rows O02, O08, O09, O10.
- Base: T1 is committed locally as `7515d019` (the typed decision `LEGAL_CONSENT | SYNTHETIC_DEV | DENIED`, `eligibility_ready`, the write guard `get_verified_device`). Its BE1 owner confirmation is still pending, so T2 is local-only until that exists.

## 1. Why T2 exists (verified in the code at `7515d019`)

1. **BE2 still rejects a synthetic Child.** `application/services/vision_analysis.py:278` and `:667` return a denial unless `context.consent_effective` is true, and `domain/assistance.py:379` does the same for `member.consent_effective`. T1 deliberately never maps synthetic to `consent_effective=true` (T0 D-05 item 5: BE2 facts stay `false` and gain a versioned `eligibility_basis`). Until the BE2 gate accepts `eligibility_basis = SYNTHETIC_DEV` for the approved pilot contract only, no BE1 synthetic Child can reach analysis. This is the "BE2 gate" half of PLAN T1 that the B4a plan marked NOT_IN_T1 (guards G15 and G16).
2. **There is no status-read guard.** `get_verified_device` requires an admitted grant, an active session, an admitted membership, a writable group **and an active turn**, then the typed eligibility check. The Child must be able to poll "what happened to my request" after the turn closes or the session pauses (D-06), so a read guard with fewer conditions is needed, while a revoked grant, a foreign scope or lost eligibility must still deny.

## 2. Scope proposal (each part can be approved separately)

**Part A — BE1 status-read guard (small, no BE2 change).**
- Add a request dependency beside `get_verified_device` in `interfaces/http/be1_runtime.py` (`get_verified_device_status`, name is a proposal). It checks, from server-side rows only: grant exists, state `admitted`, device key hash matches; the session exists and is in an allowed state (OD-T2-1); the membership is `admitted` for that grant; the typed eligibility decision is still ready (`eligibility_ready`, no success audit); the path organization and session equal the grant's. It does **not** require an active turn or a writable group.
- The write guard stays exactly as it is. No new HTTP route is added here (the status route belongs to T9).
- Tests (no database): pure-seam tests like T1's, plus static checks that the write guard still requires the turn and that the status guard does not import canvas or write helpers.

**Part B — BE1-to-BE2 fact adapter and the BE2 gate (needs an inventory first; larger).**
- Read-only inventory step before any edit: every place BE2 reads `consent_effective` / `purpose_granted` (`vision_analysis.py` service, `assistance.py` domain), how `MemberFact` and `ContextDecision` are built, and who builds them from BE1 rows today (O08, O09, O10).
- Proposed result: the adapter that builds these facts from BE1 sets `consent_effective=false` for a synthetic Child and adds a versioned `eligibility_basis` (`LEGAL_CONSENT | SYNTHETIC_DEV`); the BE2 gate grants only when `consent_effective` is true **or** `eligibility_basis == SYNTHETIC_DEV` under the approved pilot contract version; REAL, legacy, pending, revoked and unknown values deny; DTO changes stay backward compatible.
- This touches BE2 domain, ports, services and contracts (O08 to O10), which are owned by `AnhKhoaa157` per the manifest, and `OwnerFenceV1` (T7b) is **not** part of T2.

## 3. Owner decisions needed before approval

- OD-T2-1: session states that allow a status read (proposal: `active` and `paused`; `finished` only if the Child must see the final outcome — T0 D-06 should be re-read before deciding).
- OD-T2-2: approve Part A alone first (recommended: it is small and independent of BE2), or A and B together.
- OD-T2-3: confirm that the eligibility check on the status path is the same typed gate with no success audit (proposal), not a looser "grant only" check.
- OD-T2-4: file allowlist and writer/reviewer per file (manifest rows for `be1_runtime.py` and, for Part B, the BE2 files are `NEEDS_OWNER` for reviewers).

## 4. Phases (test first)

P0 preflight and baseline (same five CI files, from `backend/`, `PYTHONPATH=src`, no `BE1_TEST_DATABASE_URL`; reference 26 passed, 4 skipped, plus the T1 files: 227 passed, 4 skipped). P1 Part A tests, then the guard. P2 Part B inventory report (read-only). P3 Part B tests, then adapter and gate, only if approved. P4 regression, Ruff with `--config backend/pyproject.toml`, `mypy --strict` on edited paths (separate pre-existing errors), the three validators and `git diff --check`. P5 evidence report; independent review; one commit after the owner asks.

## 5. Not in T2

No database, Alembic or provider call; no status HTTP route (T9); no `OwnerFenceV1` or run ledger (T7b, T7c); no Child or Teacher UI (T10, T11); no change to the T1 write guard or to the legal path; no real child data.

## 6. Risks

- Part B widens the BE2 gate: the main risk is a path that turns `SYNTHETIC_DEV` into a general bypass. Mitigation: one versioned contract value, a closed set of accepted bases, deny-by-default tests per basis, and the T1 rule that synthetic never becomes `consent_effective`.
- A status read that is too permissive can disclose another Child's request: the guard must bind to the grant's own membership and the path scope, and the T9 route must re-check ownership of the request reference.
- The PostgreSQL behavior of all of this stays unverified until T12.
