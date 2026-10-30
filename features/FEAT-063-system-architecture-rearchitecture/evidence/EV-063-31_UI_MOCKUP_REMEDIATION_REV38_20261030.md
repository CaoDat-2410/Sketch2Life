# EV-063-31 — UI mockup remediation Rev38

- Date: 2026-10-30.
- Feature: FEAT-063.
- Plan: `plan/PLAN_REV38_UI_MOCKUP_REMEDIATION_20261030.md`, approved SHA-256 `ADB45B054C5E4872629AFDAF52037053AB97470EEEAC6F225D007ED0B62ADB27`; approval is recorded in `approvals/TASK_APPROVAL.md`.
- Authority: user approved proceeding with the mockup corrections after the Rev35/Rev36 review. This approval covers generated drafts and the planned narrow documentation consistency correction. Final visual approval remains separate.
- Source baseline: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft, Rev37 API contract catalog, Rev35/36 visuals, and owner UI review supplied 2026-10-30.

## Work recorded

1. Corrected the contradictory AC-33 sentence in the unsigned v2.3 SRS: Parent may enable the generic line-sketch guide during drawing; Teacher may enable the occurrence Sketch Deck; disabled guide means no sketch job. Capture still precedes VLM subject suggestion, adult confirms/corrects the suggested subject, and the guide receives no child profile/artwork input.
2. Generated 23 role screens under `assets/generated/ui-mockups-rev38-20261030/` and nine component boards under `assets/generated/ui-components-rev38-20261030/`.
3. Added per-screen/per-board `PROMPT.md` and `MOTION.md`, indexes, prompt logs, motion specs and shared synthetic butterfly artwork. One shared artwork prompt is explicitly marked reconstructed because the image tool did not retain its exact original text.
4. Updated state/data details found during review: consistent Parent tabs and blue primary actions; scoped lesson feedback; Manager sample school/Teacher/class alignment; 2026 dates; Admin activity-catalog card; no purple Admin accents; accepted video failure stays counted; Parent quota component has no unsupported multi-item navigation; Teacher sample runtime is 1:00. P08 keeps the shared butterfly drawing recognizable in the video frame, though generated editing cannot guarantee pixel identity.
5. Added mounted-versus-target API labels. Rev37 records 135 declared operations and 124 mounted. Examples that are mounted include Parent lesson reads, Teacher lesson/upload/version APIs, Manager grant decisions and Platform Admin lesson moderation. Child profiles, story/video jobs, billing, class/occurrence management and Parent feedback remain SRS target contracts, not mounted Rev37 routes.

## Acceptance review

| Criterion | Result | Evidence |
|---|---|---|
| AC1 source consistency | Pass | AC-33 aligns with current Parent guide and Teacher Deck decisions; age-band question remains unresolved. |
| AC2 screen coverage | Pass | 23 screen PNGs, each with prompt and motion note. |
| AC3 component coverage | Pass | 9 component PNGs, each with prompt and motion note. |
| AC4 consistency | Pass with generation limits | Logo/style reference and role navigation are consistent; fictional child is Minh, age 5; Cô Thảo and Trường Mầm non Ánh Dương recur; sample dates are 2026. |
| AC5 product rules | Pass in reviewed mockups | No direct scene editing; 5-scene examples fall within 5–15; adult script confirmation precedes video; job states are discrete; safety is automatic; activities follow video; lesson/profile grants are distinct; feedback is lesson-scoped. |
| AC6 visual review | Pass with noted limitations | All 23 screens and 9 boards were visually inspected. Corrections were applied to P01/P03/P08/P09/P12/T06/T07/M02/A02 and UI07/UI08. |
| AC7 provenance/lifecycle | Pass | Per-folder prompt/motion records and the 33-file SHA-256 manifest follow. All assets remain in `assets/generated/`; Rev35/36 remain preserved. |
| AC8 scope | Pass | No app/API/schema/database changes, executable animation, test/build, external AI provider call, child data, commit or push. |

## Static checks

- Screen PNGs: 23 found.
- Component PNGs: 9 found.
- Missing per-folder prompt/motion files: 0.
- Shared sample drawing: 1.
- Plan SHA-256 verified against the approval record: `ADB45B054C5E4872629AFDAF52037053AB97470EEEAC6F225D007ED0B62ADB27`.
- AC-33 is present in the SRS at line 1069 at review time.
- No test or build was run.

## Visual review notes and limits

- The one-source drawing is used across the capture and playback examples; the final P08 player preserves its four colored wings, body and curled antennae without an added face. Image generation can still alter fine crayon texture and is not a pixel-preserving image compositor.
- UI04 information is persistent by design. UI07 uses “Lượt đã nhận vẫn được tính.” for technical failure after admission; it does not suggest a refund.
- M01 approval is disabled with unchecked checklist items. UI03 shows the same disabled state. A02 actions are role-scoped and state-aware.
- Age-band boundaries remain unresolved in the SRS; age 5 is only a fictional illustrative example. UI text should be copy-edited before implementation because image generation may render Vietnamese labels imperfectly.
- The SRS and API indexes describe different maturity levels: a screen marked SRS target has no current mounted endpoint unless explicitly listed as mounted. No runtime behavior was inferred from a mockup.
- Visual approval is pending. Do not copy these files to `assets/approved/` or `assets/applied/`, and do not reference them from application source before that approval.

## SHA-256 manifest

The manifest covers all final generated PNGs: 23 screens, 9 component boards and the shared synthetic artwork.

| Asset path (relative to FEAT-063) | Bytes | SHA-256 |
|---|---:|---|
| assets/generated/ui-mockups-rev38-20261030/parent/p01-lesson-library/screen.png | 1714608 | AE9DE3838CE519F1B4DA70A2929C96F04A602711AB27AF35B950EAA4B2387B21 |
| assets/generated/ui-mockups-rev38-20261030/parent/p02-lesson-detail/screen.png | 1534630 | 2A3FB97FB6618EFB0C04E47F8491F168D66496CAB7DE0E9C9B019B780A0CA766 |
| assets/generated/ui-mockups-rev38-20261030/parent/p03-drawing-line-guide/screen.png | 1879345 | A8D1AA50546C79CEB2ED21A25581B1719C9A2B5B46CB9E4E1AD7ACD88C81449C |
| assets/generated/ui-mockups-rev38-20261030/parent/p04-capture-subject-confirmation/screen.png | 1783300 | 801CF9A265B3B399AAD1DCB56CCECC7023E418B9ED4D5F5D2D81170E438F92DD |
| assets/generated/ui-mockups-rev38-20261030/parent/p05-context-idea-confirmation/screen.png | 1436740 | 530EB5937545B9446E5B06E0C17E2FE12F5A5D8105DD387B0F27BBDA627A426E |
| assets/generated/ui-mockups-rev38-20261030/parent/p06-story-review/screen.png | 1550404 | 7E37025D142610BC638FEAB9F25FDCD6F956196C522E2DDD50831CA6FBB75AD5 |
| assets/generated/ui-mockups-rev38-20261030/parent/p07-video-job-status/screen.png | 1400897 | 7B9D26F278BD86B4888DD82510DB41235C8F3F116AED70DBA5AF44B7727A926B |
| assets/generated/ui-mockups-rev38-20261030/parent/p08-video-and-activities/screen.png | 2090275 | F98523728E0163F2AA144982C48523B754B0205E59B999AA087FE2F4C29454A9 |
| assets/generated/ui-mockups-rev38-20261030/parent/p09-history-feedback/screen.png | 1606559 | 408742221E59A79368183F86FCF160F994AD78B38F565688109EBC0EBA162834 |
| assets/generated/ui-mockups-rev38-20261030/parent/p10-child-profiles/screen.png | 1220055 | DED4D6194DF09BAE547A4D6087C4A84A2B8F11F82A14964317F726DF795DC2E0 |
| assets/generated/ui-mockups-rev38-20261030/parent/p11-authentication/screen.png | 1185166 | 614D8061B8460E8B3146C4EBE3960BF9B5C2D14642541A62C096613867E92BC2 |
| assets/generated/ui-mockups-rev38-20261030/parent/p12-video-quota/screen.png | 1352764 | 714E4A298FC237DB6F306BFC5411DB6D680D9D63721CC5938E85A48E17064281 |
| assets/generated/ui-mockups-rev38-20261030/platform-admin/a01-content-moderation/screen.png | 1472419 | FF3D633D685C42A0FBB22EF073D620E98BBFBC6A27BE3F04D5EAF3C42218E3E9 |
| assets/generated/ui-mockups-rev38-20261030/platform-admin/a02-platform-operations/screen.png | 1551432 | 904F232D96FC977E8DF8F970C0AF3C0D160F6DCFAD39AB0C7CB65723FCFFCC42 |
| assets/generated/ui-mockups-rev38-20261030/school-manager/m01-publication-review/screen.png | 1355479 | 1055BD890E2393548A44C01229739146103B34BDE8D829475F345719D00D4179 |
| assets/generated/ui-mockups-rev38-20261030/school-manager/m02-organization-management/screen.png | 1479816 | 54212BDC030EBDB40CAA31C3210E99F4100F8ADA83BF340B962CDB09CAD4DBD9 |
| assets/generated/ui-mockups-rev38-20261030/teacher/t01-lesson-workspace/screen.png | 1321915 | 18767F925EC18A92A2EC055F67072A69FBE9D263AE083E8165ACCEBF8465F7ED |
| assets/generated/ui-mockups-rev38-20261030/teacher/t02-lesson-authoring/screen.png | 1656533 | CEDBE56CA3124DB75C78F6EFA00A97C70482C9401C30283C16AA04FD8084D058 |
| assets/generated/ui-mockups-rev38-20261030/teacher/t03-document-import-review/screen.png | 1581092 | 6684B8E29B964C101395D28DB478B98A3448D3270EE2919CE7EDAD0151DAC0C6 |
| assets/generated/ui-mockups-rev38-20261030/teacher/t04-session-sketch-deck/screen.png | 1351026 | 356367F3E3D44CC0B11F8FDEBE6238106F5E63F59F56D5A6ED87443ED6A20539 |
| assets/generated/ui-mockups-rev38-20261030/teacher/t05-classes-and-children/screen.png | 1182358 | 5D14F5EC37C8E17EDE65D9F3810EB72B814B896A2C0591E9DA49A150431739B1 |
| assets/generated/ui-mockups-rev38-20261030/teacher/t06-sample-story-run/screen.png | 1807583 | F38DF9D63BF5B9F2609C1511C1DC6E338E67BBB856725A2952F08461543B9B73 |
| assets/generated/ui-mockups-rev38-20261030/teacher/t07-video-presentation-confirmation/screen.png | 2028172 | 9080A265702306EFB6FCA67FBBA54BA7D512164D4A86E68A1E8F9507FA72CD18 |
| assets/generated/ui-components-rev38-20261030/ui01-foundations-controls/components.png | 1533261 | 323BC3C02040240448B7EA773E02489B61E51A893294EED324F6116DE5BA7271 |
| assets/generated/ui-components-rev38-20261030/ui02-parent-dialogs-sheets/components.png | 1504035 | 0049CC89FE9B5F5CF217E2A788ED4084FCD8BFB6F2CBAACC62D1900E2F999633 |
| assets/generated/ui-components-rev38-20261030/ui03-web-decision-dialogs/components.png | 1468801 | A3F9D0AC3E0DBA7708B1824DA3BF9E1EF339C593A141B7BE3107342DC2D0667C |
| assets/generated/ui-components-rev38-20261030/ui04-feedback-toasts/components.png | 1375790 | 569D9F3A50F6F6CE2C8C25223FDE6ECDB077D921E7D50A906F6811DDFC85F463 |
| assets/generated/ui-components-rev38-20261030/ui05-loading-empty-error/components.png | 1436986 | 721EBB212EB7D81A0054714AAFF2EDD92D48C9E06BE5830D26928CE7C80C0A92 |
| assets/generated/ui-components-rev38-20261030/ui06-teacher-import-review/components.png | 1429738 | 77AC67DB6A53BF814261C4B6ECB151D18E29167B5827DF19A1B69FD45621BAC2 |
| assets/generated/ui-components-rev38-20261030/ui07-video-quota/components.png | 1687509 | C2702AD16DCE3A1B5D498422C10738E966EB7BC0D333176B919DC3C5A7F6A5B9 |
| assets/generated/ui-components-rev38-20261030/ui08-access-grants/components.png | 1604434 | FD3FE37229F5349E8EB3B0E3752D51DF00372771D58C0CBE1828AB5B99737A4D |
| assets/generated/ui-components-rev38-20261030/ui09-lesson-feedback/components.png | 1392363 | 889D213149C331A59116BD7549AAEA549601F57727D8C73EA5E652BF3188AF93 |
| assets/generated/ui-mockups-rev38-20261030/shared/child-butterfly-art.png | 2820784 | 748F7C0D902C6062965D0B2E23CF556122B0924C4A064BAC3D8047F79B30A124 |
