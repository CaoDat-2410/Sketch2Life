# Feature context

- Status: IN_PROGRESS
- Owner: project owner, direct push/dev merge request
- Goal: publish current branch and integrate dev without losing local work
- Scope: reviewed documentation and publishing hygiene; committed legacy branch history retained
- Non-goals: eight uncommitted legacy runtime files, provider/model/deployment or new product migration
- Dependencies: refreshed origin/dev ancestry, SRS/task/architecture/harness/security checks
- Risks: pending runtime/history differs from replacement SRS; all originals and local pending bytes must remain preserved

## Context snapshot

Current branch codex/pixi-ai-show-20261001 at original HEAD 7be3006. Canonical SRS v3.1 and four-person 57-card backlog are the new target documents. Owner “push nhánh này, merge lên dev” authorizes Git publication; optional scope question defaults to documentation only after reasonable opportunity to answer. FEAT-037 under-nine source edits have an existing unit fixture mismatch and are preserved locally. Current source/register/governance and FEAT-011 publishing constraints were reviewed before work. Security/harness hygiene preserves originals and source hashes; no deletion or force push.
