# EV-063-29 — UI component patterns and interaction states (Plan Rev36)

- Date: 2026-10-30, Asia/Saigon.
- Visual review timestamp: 2026-10-30 02:55:35 Asia/Saigon.
- Reviewer: Codex visual pass over generated images; owner visual approval remains pending.
- Environment: Windows workspace `repository root`; built-in `image_gen.imagegen`; generated originals retained in CODEX_HOME and copied to FEAT-063.
- Approved plan: `plan/PLAN_REV36_UI_COMPONENT_PATTERNS_AND_STATES_20261030.md`.
- Plan SHA-256: `300104684514C4C6F67614F58DDE402668AAC24AF2204F9B1BCA7A5BBEA2D336`.
- Final index: `assets/generated/ui-components-rev36-20261030/COMPONENT_INDEX.md`.
- Sources: SRS v2.3-draft §3, §20, §21.5–§21.6, §22.4, §31.2–§31.7; Rev31-reconciled Lesson Library API contract; Rev31 API inventory; Rev32 API purpose catalog; Rev35 UI mockups as visual reference.
- Data: fictional lesson/school/file examples; no real child data or provider credentials supplied.

## Final component-board outputs

| ID | Final output | Image-generation source |
|---|---|---|
| UI01 | `assets/generated/ui-components-rev36-20261030/ui01-foundations-controls/components.png` | `ImageGen result/exec-96af5649-7b72-49b2-bea3-94c05afb1c86.png` |
| UI02 | `assets/generated/ui-components-rev36-20261030/ui02-parent-dialogs-sheets/components.png` | `ImageGen result/exec-edf20532-bf84-49a2-84e7-2110bc308ed5.png` |
| UI03 | `assets/generated/ui-components-rev36-20261030/ui03-web-decision-dialogs/components.png` | `ImageGen result/exec-0d5adcc8-7d44-40c4-b541-eff5746f2ebb.png` |
| UI04 | `assets/generated/ui-components-rev36-20261030/ui04-toast-inline-notices/components.png` | `ImageGen result/exec-defdf4ee-a754-40c3-8c51-ba23b4dc75fa.png` |
| UI05 | `assets/generated/ui-components-rev36-20261030/ui05-api-client-states/components.png` | `ImageGen result/exec-86b2714a-f67e-42ab-b1bb-198da444f4a5.png` |
| UI06 | `assets/generated/ui-components-rev36-20261030/ui06-upload-extraction-states/components.png` | `ImageGen result/exec-2509b262-69c2-4632-9aa5-f55aa38282cf.png` |
| UI07 | `assets/generated/ui-components-rev36-20261030/ui07-quota-ai-job-states/components.png` | `ImageGen result/exec-3ed2a0c1-5f4c-445f-85e0-2a6912212b55.png` |
| UI08 | `assets/generated/ui-components-rev36-20261030/ui08-sharing-access-grants/components.png` | `ImageGen result/exec-8784c5c6-dd5c-460f-b1b6-3a7dce3800d2.png` |
| UI09 | `assets/generated/ui-components-rev36-20261030/ui09-feedback-notifications/components.png` | `ImageGen result/exec-4ac0f7ec-d4b5-4708-a770-1aedab2bec91.png` |

## Final PNG SHA-256

| ID | SHA-256 |
|---|---|
| UI01 | `5A3909A9AEA9D31EADDBFFF39A99FDA1EE829596C72E4BAFBF72C5AE547740B4` |
| UI02 | `DE82080297E7CDA873867799EAA94D952ADD960AA124F9FCB622BFA852A7BF57` |
| UI03 | `02867E2B8BB1431E2839BB0A66CAD29F6C6779CBF4721CC03F6CDFBA165FE996` |
| UI04 | `2CAA707E417B61AFC4D20B075E977382304A6E0EF14CD38C40EF79DB744CDA48` |
| UI05 | `2C8BD86A4F1B976DDBCA82785C5673D67D0ACCFDCEE6992D95CAC258BDCC472A` |
| UI06 | `58C3605A465E6578186B7299ECA020C7194268FB841C3AC9D596AEBED7A62ECC` |
| UI07 | `15914B91E6751E109C8511311E79D5BE40E439D406E2822ADB933327C28FE6E3` |
| UI08 | `DADB043F7538FA63DF1B064375ECF3C790AFF9B1E2132EC4927A75731A6DE175` |
| UI09 | `9415B88FB1C38800BAE7E182CA051A43DD260108AF71A5F47C3E98FBAB58D92E` |

## Review notes and limits

- Nine final 1,586 × 992 PNG boards were visually inspected; each component group has a separate folder, prompt brief and motion note.
- UI02 was regenerated to state explicitly that quota for an accepted video request is not refunded if the adult cancels. UI03 was regenerated to remove an unsupported promise that an archived lesson can always be restored. UI05 was regenerated to include the SRS expired-session/reauthentication state. UI06 was regenerated to use a 5–6-year illustrative age band rather than school grade.
- UI01's token values are image-generation suggestions only and do not change app design tokens. Age labels and quota/package values remain illustrative; no price or fixed quota was added.
- UI08 keeps child-profile fields generic because the exact share-field list is still open. It explicitly distinguishes lesson grants from child-profile grants and child media access.
- The index identifies SRS-only APIs that were not implemented in Rev31 (video/quota, child-profile grants, LessonOccurrence history/feedback). Existing Demo feedback/story routes are not treated as those product APIs.
- Motion notes specify API-driven state updates, truthful upload bytes/job stages, non-refundable quota copy, reduced-motion behavior and retry guards. No component or animation behavior is implemented.
- No product code, APIs, schema, database, tests/builds or runtime behavior was changed or verified. Assets remain under `assets/generated/` pending owner visual approval.
