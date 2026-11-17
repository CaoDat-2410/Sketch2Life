# FEAT-039 Plan revision 4 — classroom integration SRS amendment

- **Status:** APPROVED — documentation-only update, based on the owner's direct instruction to record the requested changes in the SRS.
- **Baseline:** canonical SRS v3.1 (SHA-256 `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9`).
- **Related feature:** FEAT-060 classroom integration and review remediation; its Plan Rev3 remains DRAFT and is not approved by this plan.
- **Scope:** prepare an additive SRS amendment recording the owner-confirmed six-digit shared room-code rule and the proposed backend contract clarifications already derived from B5/B19 and current FEAT-060 API review.
- **Out of scope:** product source/runtime changes, API/schema adoption, migration, FE/BE implementation, application tests, deployment, Modal calls, publication, or treating unconfirmed decisions as owner-confirmed. Update only the documentation generator/checker paths needed to preserve v3.1 and target v3.2; do not run application tests.

## Work

1. Preserve the exact v3.1 SRS bytes before editing.
2. Add an SRS section that distinguishes owner-confirmed admission behavior from proposed API/state refinements and open questions.
3. Keep the canonical SRS in FEAT-029 and consolidated feature copy in FEAT-039 byte-identical after the amendment; preserve the old v3.1 feature artifact under its v3.1 filename.
4. Update FEAT-039 context, decisions, approval, status, evidence index, and `docs/context/SOURCE_REGISTER.md`; update FEAT-060 plan/context/decision/proposal only where needed to accurately record the owner's answer.
5. Update the documentation composer/checker output path and B27 assembly so future regeneration cannot overwrite v3.2 with v3.1.
6. Review the targeted diff, verify SRS-copy equality and preserved-baseline hash, and run `git diff --check` on the edited paths.

## Acceptance criteria

- [x] Original v3.1 hash remains recoverable and unchanged.
- [x] The SRS says the six-digit code is shared by multiple children, is not an OTP or child identity, and both QR/deep-link and code stop accepting new joins when the Teacher starts the class.
- [x] The SRS says the product distinguishes full completion from a Teacher stopping early; implementation fields/guards remain open for BE1 review.
- [x] The learning stage remains a separate proposed persistent value from session lifecycle and group/member progress.
- [x] Completion versus a Teacher stopping early is explained in plain language and marked owner-confirmed semantics, with exact contract details still proposed.
- [x] Proposed API/storage behavior is traceable to FEAT-060 and is marked not implemented/not adopted.
- [x] Both current SRS copies match exactly; documentation tooling points to v3.2; no product source/test/runtime file is changed by this amendment.

## Verification

Document review, targeted diff review, unchanged baseline hash, identical current copies, and whitespace/error check only. No application tests or runtime actions are in scope.
