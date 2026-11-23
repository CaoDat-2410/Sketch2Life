# FEAT-066 SEED-2 — realistic seed data and the Phase A-C stages (plan, 2026-11-22)

Status: plan for the task given by the owner's coordinating session on 2026-11-22. Branch
`claude/seed-2-realistic-fd970c` (worktree `seed-2-realistic-fd970c`), cut from the integration tip
`258ff4c0`. Nothing is pushed. The Task Approval entry is a draft outside the repository
(`tmp/seed-2/TASK_APPROVAL_DRAFT.md`); the coordinator appends it after the owner accepts. Current
requirements: SRS FEAT-063 v2.7-draft (SHA-256 prefix `443A3CA3`).

## 1. Goal

The owner tests the web and Android apps against a seeded local database. SEED-1 shows
`[SEED] ...` text and templated lesson text, and has no rows for the APIs that goal v3 built in
Phases A, B and C. SEED-2 (a) replaces every visible string with realistic Vietnamese display data
and (b) adds stages that seed the Phase A-C screens. Child data stays synthetic: fictional names
only, `data_origin = SYNTHETIC_DEV`, `age_source = SYNTHETIC_FIXTURE`, no consent row, no real file.

Out of scope: S2-S4 (capacity, lifecycle, quota: Billing lane of the teammate), anything Phase D
builds (child selections, Teacher-created runs, projection) and the deferred tasks.

## 2. Part 1 — realistic display data for SEED-1 (`backend/tools/seed/data.py`)

Kept unchanged: every internal id and subject (`seed-org-a`, `seed-tch-a1`, `seed-admin`,
`seed-ch-a-1-1`, `seed-lesson-l1`, ...), all S1 row counts, every synthetic and real-data flag,
`SEED_SYNTHETIC_FAILURE`, `SEED_ISSUER`, the guard and the insert-if-absent rule.

| Item | Change |
|---|---|
| Organizations | 8 names `Trường Mầm non <name>` (org A = `Hoa Sen`) |
| Classes | `Lớp Mầm n`, `Lớp Chồi n`, `Lớp Lá n` by age group; org A: Mầm 1, Chồi 1, Lá 1, Lá 2 |
| Managed profiles | fictional Vietnamese full names, unique in the whole seed; ages follow the class group (Mầm 36-47, Chồi 48-59, Lá 60-71 months) — a deliberate change from the former 36/54/78/96/120 cycle, one constant to revert |
| Parent groups | `Phụ huynh lớp Mầm 1`, `Phụ huynh lớp Chồi 1` |
| Parent child profiles K1-K5 | fictional given names, interests as a natural sentence |
| Lessons L1-L3 | real-sounding titles, objectives, materials, preparation, step-by-step instructions, observation and safety notes, age-fit activities (no "Mục tiêu: <title>" template) |
| Parent runs (S1 and S7a) | topics and typed ideas read like a parent wrote them |

A fresh database is needed to see the new text: S1 is insert-if-absent and never updates a row.

## 3. Part 2 — new stages (one module each, shared plumbing in `stage_common.py`)

Every stage: guarded (S7a order plus the `frc08_` name prefix), idempotent through fixed
idempotency keys or insert-if-absent on deterministic ids, counts-only output (table names use
`[A-Za-z0-9_]` only so the kit's count filter keeps the lines), no provider call, no Modal, no
storage object. Application services are used where they exist; direct rows only where a command is
an HTTP route function, and then every CHECK, trigger and the route's own write set is mirrored.

| Module | Phase | What it seeds | How |
|---|---|---|---|
| `s8_lessons` | A | org A lesson occurrences with documents (metadata only), document revisions (extraction, Teacher edit, reviewed) and plan revisions (draft, approved, superseded) with their activities | `LessonOccurrenceService`, `PlanRevisionService` as the seeded Teachers; document rows direct (the attach command needs an uploaded object) |
| `s9_classes` | B | one archived and one suspended class, keyed class profile creates, an enrollment move with history | direct rows mirroring `_change_class_state`, the keyed profile create and `move_profile` (route functions) |
| `s7b_story_states` | B | Parent StoryRuns spread over INPUT_REVIEW, SUBJECT_REVIEW, SCRIPT_REVIEW, VIDEO_READY, COMPLETED, ABANDONED, FAILED with transcripts, ideas, story revisions and video generation rows | Parent run service and repository methods with the fixture adapters (`story_inputs/fixtures.py`, `story_video/fixture_runner.py`, `story_video/local_adapters.py`); direct rows only for an inactive history run if no service reaches it |
| `s10_inbox` | C | inbox items for Teacher, School Manager and Parent, some read, some unread | `SqlNotificationProducer.enqueue`, `NotificationInboxService.mark_read` |
| `s11_org_run_shares` | C | one Teacher-cancelled organization run; private lesson shares of versions in non-approved review states (T-10d) | Teacher cancel service if it exists, else a direct `DELETE_PENDING` row like S1 K1; Lesson Library service for the shares |
| `seed2_abc` | all | runs the five stages in order and prints one table per stage | one new kit module name |

Rules inherited from the design (Draft 9): no Modal import, no purge consumer, outbox publisher or
sweep run on the seed database (§11.8), synthetic data only, one transaction per command. Changes
to S7a: it must accept a seed run that a later stage advanced (run state past INPUT_PROCESSING)
and count only its own runs.

## 4. Verification

Fresh database `frc08_seed2_<yyyymmddhhmmss>` on the container `frc08-pg-20261119110418`;
`alembic upgrade heads`; every stage run twice (second run: 0 new rows, all counts `yes`); seed unit
and PostgreSQL tests; backend unit and contract suite against the 83-id base list (0 new failures);
`validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`,
`git diff --check`; one independent review on Sonnet 5.5 (high); one local commit.

## 5. Kit changes (not edited here; the api-test-kit session owns the kit)

`seed_runner.py`: add `"tools.seed.seed2_abc"` to the `choices` tuple of `--module`.
`Invoke-Seed.ps1`: after the S7a call, run the same command with `--module tools.seed.seed2_abc`
and include its output in `$seedOutput`. Details are in the final report.

## 6. Result and recorded deviations (2026-11-22)

Verified on disposable databases of the `frc08` container (never dropped): `alembic upgrade heads`, then S1,
S7a and `seed2_abc` each twice. The second run created 0 rows and every count matched. Seed unit tests
(184), the seed PostgreSQL tests (each on its own empty database), ruff, mypy, the three validators and
`git diff --check` pass. Backend unit+contract suite: 78 failing ids, 0 outside the 83-id base list.
`tests/integration/test_seed_s1_postgres.py::test_runs_read_back_through_the_product[r3]` fails identically
at the base commit (a DELETE_PENDING lifecycle record has no `story_content`); it is not changed here.

Seeded in org A (Hoa Sen): classes Mầm 1, Chồi 1, Lá 1, Lá 2 from S1 plus Mầm 2 (archived) and Chồi 2
(suspended) from S9; five lesson occurrences with documents (metadata only), document revisions and plan
revisions (draft, approved, superseded); three Teacher-created profiles and one enrollment move; three
lessons shared while DRAFT, PENDING_REVIEW and CHANGES_REQUESTED; one Teacher-cancelled organization run;
15 inbox items (5 read). Parents: p3 gets a new profile with one completed run and one run in INPUT_REVIEW,
p4 holds a run in SUBJECT_REVIEW, p5 a run in VIDEO_READY, p1 a new ABANDONED run.

Deviations and limits:

- **SCRIPT_REVIEW is not seeded.** A Parent holds one active run, there are five Parents, and S1 already uses
  p1 (INPUT_PROCESSING) and p2 (PREPARATION_REVIEW); INPUT_REVIEW, SUBJECT_REVIEW and VIDEO_READY take the three
  free slots. Trading one of them for SCRIPT_REVIEW is a one-line data change in `s7b_story_states.py`.
- **Ages follow the class group** (Mầm 36-47, Chồi 48-59, Lá 60-71 months) instead of the former 36/54/78/96/120
  cycle. The child moved from Mầm 1 to Lá 1 is a deliberate "moved up" case.
- **Three names start with `Synthetic `**: the keyed class-profile create requires that prefix while the real-data
  gate is off, so the rows match what the API leaves.
- **No file, object or job row exists for seeded documents, drawings, audio and video.** The rows carry opaque
  references only; reading the bytes or `GET /v1/jobs/{job_ref}` for a seeded document does not work.
- **S9 raises the class revision** of the S1 classes 1 and 3 to 2 (profile creates and the move), so a request
  with a hard-coded `If-Match: "1"` on those classes is stale.
- **S10 follows S7b and S8**: its deep links name the real runs and occurrences, so S10 alone on a database
  without them stops with `S10_REFERENCE_MISSING`.
- **A database seeded by SEED-1 is not upgraded**: S1 is insert-if-absent and S7a refuses a foreign run.
  Use a fresh database to see the new text.
