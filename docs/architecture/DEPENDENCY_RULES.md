# Architecture review checklist

Use this checklist in every feature review.

- [ ] Domain logic is framework-independent.
- [ ] Use cases are explicit and testable without a database or network.
- [ ] Ports/interfaces are defined where the application needs external behavior.
- [ ] Infrastructure implements ports; it is not imported by the domain.
- [ ] Contracts are versioned and validated at boundaries.
- [ ] No feature reads another feature's private storage or implicit runtime memory.
- [ ] Original/derived/generated artifact lineage is preserved.
- [ ] Async jobs carry an expected aggregate/session version and stale results cannot mutate newer state.
- [ ] Failure has an explicit fallback or recovery state.
- [ ] Tests and evidence prove the acceptance criteria.
