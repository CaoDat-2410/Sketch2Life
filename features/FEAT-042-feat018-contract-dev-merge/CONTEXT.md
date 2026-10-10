# FEAT-018 contract branch integration context

- Status: IN_PROGRESS
- Owner: project owner, direct merge instruction
- Goal: merge the existing FEAT-018 contract branch into dev after FEAT-041 publication
- Scope: pinned committed branch history, conflict reconciliation and necessary offline regression repairs
- Non-goals: replacement SRS implementation, new visual generation, live provider calls, deployment or pending local runtime changes
- Dependencies: origin/dev 396b4f6; source f959426; current source register, SRS v3.1, ADR-0014/0015 and existing FEAT-018/030 approvals
- Risks: source includes legacy whiteboard/story-video and UI beyond its branch label; preserve current dev improvements and requirements authority

## Source snapshot

The owner requested “sau khi xong thì merge cái feat 18 contract j đó vào dev luôn”. Exact matching remote branch is codex/feat-018-contract-plan at f9594268b22c026f6b8ba837e3f3f9e8831a7280, 208 source-only commits versus dev at 396b4f67ddcb413f1ae72fdc9ca0746419f449a4. Merge base is 5959215f8134d179b354abd4a669786c4d09e3ee. The local same-named branch is stale at the merge base; remote history is authoritative for this merge. Current workspace stays untouched; an isolated managed worktree starts from dev.

Canonical SRS v3.1 and current staffing/architecture decisions remain authoritative. Incoming historical approvals and runtime are integration context, not proof that the replacement product is implemented. Eight pending runtime files in the original workspace retain FEAT-041 manifest hashes. Source register and governance policies were read before creating this plan.

## Validated merge candidate

All six conflicts are reconciled and necessary concrete regressions repaired. Available offline checks pass: backend2001, mobile22 and renderer67 tests; exact-index Expo web export succeeds. See evidence/notes/VALIDATION.md for twelve excluded media files, one deselected media test, 24 optional skips and unresolved GPU/device/visual gates. Remote publication remains pending; protected original workspace and five immutable artifacts remain verified.
