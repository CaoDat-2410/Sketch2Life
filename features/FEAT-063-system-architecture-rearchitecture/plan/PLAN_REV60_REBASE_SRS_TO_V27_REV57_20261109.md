# Plan Rev60 — rebase the working SRS to v2.7 Rev57

- **Feature:** FEAT-063 system architecture rearchitecture
- **Date:** 2026-11-09 (Asia/Saigon)
- **Change type:** SRS baseline correction and preservation of approved follow-up amendments
- **Approval basis:** Owner clarification in the current conversation: the expected latest SRS is v2.7, and the newest source must be checked. This authorizes aligning the working SRS and its authority pointers to that source while preserving Rev58/Rev59 work. The owner later explicitly authorized a scoped local-Git commit and normal push to the existing docs branch after the repository security validator passes.

## Source selection and baseline

- Remote read-only check of all `origin` heads found the latest FEAT-063 SRS revision at `docs/feat063-diagram-readiness-20261107`, commit `f21c6f34af1ee045caf9a0621e38376a2bfde390`; its SRS is v2.7-draft / Rev57. The remote `dev` and `main` heads remain on older content. The selected source branch remains `docs/feat063-diagram-readiness-20261107`; the approved publication is limited to this branch and does not force-push.
- Rev57 SRS git blob: `a979fe2740cb965015ab3ed0606bd5d293c3a75f`.
- Current local SRS before rebasing: SHA-256 `DF8C9FEE549CDBDEBC3A6A161B6223C24F72AB139D70CCA682F7D9C87D0FABC7`; preserve a temporary backup before replacing its base.
- The owner-supplied Rev57 six-group note has SHA-256 `1135F27038AFAC5DA51C69572C080EA29702068AA98CF720C49666CFE3FD08EA` and is used as an SRS consistency checklist. Incorporate only facts and decisions already supported by Rev57 or recorded owner clarifications; leave unresolved owner decisions and diagram/data/runtime gates open.

## Scope

1. Rebase `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` onto the complete v2.7-draft Rev57 source while retaining its Rev57 content and decision history.
2. Carry forward the local Rev58 CI/CD amendments: preserve Rev57 §§32.6–32.7 unchanged, carry forward the Rev58 CI/CD source snapshot and target release scenario in §32.8 with matching contents entries. Merge the Rev58 synthetic no-eligible case into §28.2 without representing BM04 test cases as CI/CD workflow content.
3. Carry forward Rev59 corrections on the v2.7 base: correct §1.1/§12 counts, NFR-16, AC-09/32/42; maintain the 17 `OPEN-OWNER` questions and correct Q183/Q192 references; align already-settled school/Parent quota and child-media deny-by-default statements where needed.
4. Set the SRS version to `2.7-draft`, add document-control entries for Rev58–Rev60, and keep unsigned status.
5. Update `AGENTS.md`, `docs/context/SRS_AUTHORITY.md`, `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`, and FEAT-063 source/context/status/decision/evidence indexes so the authority pointer agrees with the owner's v2.7 correction. Record that the target branch's matching v2.7-draft Data Table Register remains unchanged in this task.
6. Record source hashes, merged sections, static checks, the unchanged DTR boundary, remaining owner questions and unsigned status in new feature-local evidence.

## Boundaries

- Product artifact change is limited to the canonical SRS. The local Data Table Register, diagrams, data dictionary inputs, BM04 DOCX, code, APIs, database, migrations, secrets and deployment are not edited.
- No owner decision is closed or invented. The 17 questions remain `OPEN-OWNER`; any unresolved DTR section cross-reference is recorded for follow-up rather than silently creating a DTR change.
- No product tests/build/CI run, database operation, provider call, secret access, or deployment is performed. The owner explicitly authorized a commit containing only the SRS Rev60 and its scoped records, followed by a normal push to `docs/feat063-diagram-readiness-20261107` after the required repository security validator passes. No force-push or unrelated workspace changes are authorized.
- The SRS remains a draft; this task does not claim owner sign-off or final diagram readiness.

## Acceptance criteria

- **AC01 — Latest baseline:** the SRS identifies v2.7-draft / Rev57 as its baseline, preserves the complete Rev57 requirements and remains unsigned.
- **AC02 — Carry-forward:** Rev58 CI/CD and no-eligible scenario content and Rev59 count/open-question/privacy corrections are preserved on the v2.7 base; Rev57 §§32.6–32.7 are preserved and Rev58 is added as §32.8.
- **AC03 — Counts and questions:** counts distinguish pre-Rev31 86 source mappings, current 89 source mappings, historical v2.3 89/137, current target 92/140 and local snapshot 41; §31.10 contains 17 open questions and correct Q183/Q192 links.
- **AC04 — Authority:** project authority pointers identify the v2.7-draft SRS as the current owner-selected working baseline and state that it is unsigned; the target branch's v2.7-draft companion remains unchanged and is not misrepresented as a local v2.5 artifact.
- **AC05 — Scope:** no DTR, diagram, code, API, database, migration or BM04 file is changed by this task.
- **AC06 — Evidence:** static checks and output/source hashes are captured in FEAT-063 evidence; no product tests/runtime actions are claimed.
- **AC07 — Publication:** the repository security validator passes on the exact commit tree; only the allowlisted SRS and task records are committed and pushed normally to the selected branch, without force or unrelated files.

## Completion status

This documentation rebase and scoped publication complete while formal SRS sign-off, the 17 owner answers, physical schema evidence and final diagram gates remain open.
