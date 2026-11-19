# FEAT-066 EV-048 — School Manager API integration plan (Rev40)

- Date: 2026-11-17.
- Type: planning and static contract inventory; no implementation.
- Plan: `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV40_SCHOOL_MANAGER_API_INTEGRATION_20261117.md` (SHA-256 `84E8779D7F169BEE9E5ECA8D02EABB571D23F66E11B167F782A04D04F261F070`).
- Requirement authority: FEAT-063 SRS v2.7-draft Rev60 via `docs/context/SRS_AUTHORITY.md`; unsigned.
- BE source: `origin/dev` commit `1c9148e88600a101887e477541c4c4893ba1c7df`.
- Web source: `codex/fe-ui-web-remediation` at `b72f9e46`; existing dirty worktree changes preserved.

## Inventory result

There are 17 Manager business route operations in the current source: six are called by the FE and eleven are backend-only. The proposed integration target is ten backend-only operations (organization read; profile list/create; consent list/record/revoke; Parent-group list/create/invite/member revoke). The class-teacher assignment command is excluded because no organization-scoped Teacher candidate-list API was found. Add shared `GET /api/auth/v1/me` for 18 BE routes relevant to the Manager flow. Firebase `signInWithEmailAndPassword` is an SDK call, not a BE endpoint; `POST /api/auth/v1/registrations` is registration, not login.

Existing Manager flow continues to use organization assignment, classes, pending PUBLIC grants, lesson detail and revision-aware grant decision routes. Exact immutable lesson-version read is absent; stale grant review must remain blocked. School quota/billing and organization feedback-thread endpoints were not found in the mounted routers; Q193 remains open.

## Limits

No endpoint was invoked. No app source, approval register, test, build, or runtime state was changed. Rev40 remains DRAFT and requires owner approval before implementation.
