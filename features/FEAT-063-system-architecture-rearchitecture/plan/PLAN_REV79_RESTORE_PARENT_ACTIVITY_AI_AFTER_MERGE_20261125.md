# Plan Rev79 — Restore Parent activity AI after merge

**Status:** APPROVED — owner authorized the recovery on 2026-11-25.  
**Source scope:** only `<LOCAL_ROOT>/.codex-worktrees/fe`, branch `feature/fe-mobile-remediation`, HEAD `77635688deed0114ac62c28c3f936da62144d59c`.  
**Target:** root checkout `dev`, HEAD `d20c056c` plus its pre-existing local changes.  
**Product authority:** `docs/context/SRS_AUTHORITY.md` and canonical FEAT-063 SRS v2.7-draft, Rev57 baseline with amendments through Rev67; unsigned.

## 1. Objective

Restore the Parent activity suggestion behavior that exists in the latest FE worktree but is no longer invoked by the merged `dev` flow. Keep the newer Parent run, subject-role, story, and video APIs intact. The immediate regression is that Parent UI presents activity suggestions, but the mounted API returns only deterministic catalog rows and never calls the already-deployed Modal workload `suggest-parent-activities`.

This is a targeted reconciliation, not a wholesale merge of the feature branch. The worktree commit is already an ancestor of `dev`; its contents must be compared and reconciled at the affected contracts only.

## 2. Product rules and boundaries

Use canonical SRS BR-08, BR-15, FR-P-05 and §31.16–31.17:

1. After drawing subject confirmation, build candidates only from Parent-accessible `PUBLIC`/`SHARED` published lesson versions; a pinned lesson restricts the set to its exact version/hash.
2. Send bounded, minimized profile/topic/confirmed-subject/features/adult-confirmed narration and candidate data to Qwen through Modal. Never send image/audio bytes, child name, profile ID, Firebase identity or account identity to this workload.
3. For catalog matches, accept only request-scoped candidate IDs and hydrate canonical activity text from the source lesson version.
4. If no candidate fits, return exactly three structured AI drafts after the existing age, completeness, safety, outdoor, Montessori and duplicate quality gates. Keep drafts temporary and adult-reviewable; never write them to the lesson catalog.
5. Persist a selected activity as the run's main activity before story generation. A replacement suggestion set excludes previously shown/rejected activities. A failure or missing catalog candidate must not silently bypass adult selection.
6. Preserve latest `dev` subject-role confirmation and keyframe video behavior. Do not introduce video inference as part of this repair.

## 3. Scope

### Included

- Reconnect the current Parent activity API and Expo controller to the existing Modal `parent.activity.suggest` function.
- Carry the idempotent suggestion-set identity, selected activity snapshot, current understanding revision and run state through adult selection into the existing story-start gate.
- Keep catalog activity references verifiable against currently accessible published/shared lesson versions; allow a selected AI draft only when it belongs to the current persisted suggestion set.
- Preserve exclusion of previously shown/rejected suggestions on a new set request.
- Reconcile persistence with the active `dev` schema and migration graph before adding or changing DDL; avoid creating a second competing activity-selection table.
- Add focused contract/unit coverage for catalog match, no-match fallback, replay/duplicate exclusion, draft selection and stale revisions.
- Record findings and verification in FEAT-063 evidence and source register.

### Audited, unchanged unless found absent

- Main/secondary subject extraction, adult editing/confirmation, and story prompt projection.
- Role-aware keyframe video candidate pipeline and worker integration.
- Qwen model pin/configuration already present in current `dev`.

### Excluded

- Inspecting or copying any other worktree or branch.
- Live Modal inference/deployment, GPU calls, video inference, quota/payment, Firebase or external service changes.
- Broad SRS rewrite, unrelated UI redesign, legacy API removal, commit or push.
- Destructive DB cleanup or migration execution against a shared/local persistent database.

## 4. Acceptance criteria

1. The Parent Activity screen invokes the Parent activity suggestion API once per user action and displays the returned catalog selection or exactly three AI drafts with the correct source badge.
2. The backend calls `parent.activity.suggest` only for a no-pin Parent run; pinned lessons return only the exact pinned-version activities without a catalog-wide lookup.
3. The Modal request contains only allowlisted/minimized context and catalog candidate data; response candidate references are validated and canonical text is hydrated server-side.
4. The selected catalog activity or draft is persisted with an immutable snapshot and current revision. Only an activity from the latest valid suggestion set can pass the story-start gate.
5. A new suggestion set excludes prior shown/rejected content; idempotent replay returns the original result without another Modal call.
6. Activity AI failures surface a stable, actionable API/UI state and do not start story generation.
7. Existing main/secondary subject confirmation and role-aware video code remains present and its contracts remain unchanged.
8. Targeted tests/type checks pass. No live Modal request, DB migration execution, commit or push is performed.

## 5. Execution and safety

1. Compare only the source worktree and root `dev` at file/contract level; record exact regression commits.
2. Inspect current migrations and database metadata; resolve the selected persistence path before implementation. Keep the user's current uncommitted root changes and patch around them.
3. Implement backend persistence/API first, then connect Expo data flow and loading/error states.
4. Run only focused offline tests and type checks. Do not call Modal.
5. Verify subject-role/video paths still exist; document any live verification gap without claiming runtime success.
6. Add evidence and update FEAT-063 source register/status. Leave all changes uncommitted and do not push.

## 6. Known risks to resolve during M0

- `alembic heads` currently reports multiple module heads. The root contains more than one historical activity-selection schema. A focused inspection must establish which migration path the current Parent and video code actually uses before any schema mutation.
- Root `dev` is intentionally dirty (including Parent API, repository, migration and Android changes). No broad checkout/copy/reset is allowed; target only reviewed hunks.
- The deployed Modal function screenshot showed zero calls. This repair can verify source wiring offline but cannot claim live inference success without a separately requested Modal run.
