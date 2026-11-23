# FEAT-081 — Plan Revision 26: accept catalog-canonicalized Parent topic labels

- **Status:** APPROVED under the owner's direct instruction on 2026-11-20 (Asia/Saigon): “fix tiếp đi, nào nó chạy đc hết thì dùng”.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Authority:** FEAT-063 canonical working SRS v2.7-draft with local amendments through Rev72; current product requirements remain unsigned.
- **Relationship:** Narrow implementation amendment to Plan Revision 25, based on a reproduced Parent UI/API mismatch. It does not expand the live AI-call budget.

## 1. Observed defect

The real Expo UI sent a custom topic (`Dong vat`) to the authenticated catalog endpoint. The backend resolved the alias to the canonical catalog label `Động vật` and returned three curated activity-subject cards with HTTP 200. The UI then compared the returned canonical label and the input using exact string equality, rejected the valid response, stayed on the topic screen, and showed a generic account/authentication message. No Modal workload was called for this catalog-backed request.

## 2. Goal and implementation

- Compare topic labels using a deterministic, Vietnamese-aware normalization that folds case, whitespace, combining diacritics, and `đ/Đ` while preserving the original display text.
- Keep server response validation strict for contract, draft ID, card count, unique IDs and suggestion-set history.
- On valid catalog resolution, use the server's canonical topic ID and display label for the next step.
- Map an invalid subject-suggestion response to a Parent-flow-specific safe message instead of the unrelated generic account/authentication message.
- Add focused pure unit coverage for accent/case/spacing equivalence and different-topic rejection.

## 3. Verification and live-call bounds

- Run the focused mobile topic-normalization test and the existing mobile typecheck.
- Rebuild/reload the real Android app and make one catalog-only UI request for the same synthetic run/topic path. This is a deterministic local catalog call, not an AI inference.
- Continue the already-approved Plan Revision 25 E2E only after the UI displays the three animal subject cards. Existing caps remain: no more than two post-fix activity calls (8 minutes each), one story inference after activity receipt/review, and one silent LTX-2.5 video request after all prior gates. Do not spend or renew any inference allowance as part of this amendment.

## 4. Boundaries

- Synthetic account/profile/artwork only; no fixture/mock, real child data, consent fabrication, direct DB mutation, `.env`/secret edits, quota/payment work, schema/migration, SRS change, model/provider substitution, retries, warm-up, commit, push, or unrelated service shutdown.
- Do not change the topic catalog, add new topics, or call `parent.topic-subjects.suggest` or any other AI workload for this defect.
- Preserve existing worktree changes. Stop only task-used processes/services after recording evidence; leave the Android emulator online.

## 5. Authorized paths

- `apps/ui-mobile/src/parent/domain/topicMatching.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/tests/parentTopicMatching.test.ts`
- This plan, `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`, `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`, and evidence under `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.

