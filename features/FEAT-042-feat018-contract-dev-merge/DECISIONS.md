# Integration decisions

- D01: use exact matching remote codex/feat-018-contract-plan f959426, not stale local same-name branch at base 5959215.
- D02: isolated worktree from dev 396b4f6 preserves dirty original checkout; source merge includes its full 208-commit history.
- D03: latest canonical SRS v3.1, ADR-0014/0015 and reviewed task artifact remain authoritative and byte-identical. Historical runtime integration is not replacement scope completion.
- D04: direct owner request approves integration; write plan/approval before merge and record actual fixes/evidence.
- D05: isolated clone harness exposed two required FEAT-030 auto-rig evidence directories absent from Git. Add empty tracked placeholders only, without inventing screenshots or metrics.
