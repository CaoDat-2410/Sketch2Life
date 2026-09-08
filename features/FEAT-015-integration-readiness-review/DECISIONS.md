# Review decisions
- 2026-09-05: treat branch tips as evidence snapshots; retain all existing work. No merge or product-code change.
- 2026-09-05: ADR-0006 remains authoritative; ownership below will be a proposal only.

- 2026-09-05: record contract mismatch, P4 failure/identity gaps, P3 bridge gap, P2 fusion gap and harness status drift as readiness findings (EV-015-01).
- 2026-09-05: recommend an offline vertical slice first; no ADR or final allocation is changed by this proposal.

- 2026-09-05: owner selected P1 as canonical identity authority; Gate A is mandatory; conflicts remain visible until adult confirmation; missing eligibility context is collected before retry; the first slice uses fixtures/mocks through handoff.
- 2026-09-05: PixiJS asset handling is a first-class integration dependency. The slice validates a synthetic child-art asset and manifest/provenance/hash before renderer playback; product asset application remains behind the visual approval gate.

- 2026-09-05: keep renderer support for all planned asset kinds, but make WHOLE_DRAWING the first-slice path. Use fixture/demo only. Shared integration fixture is a new immutable cross-workstream test package; existing P3 butterfly fixture remains owned by P3 and unchanged.
