# EV-063-28 — UI mockups and motion notes (Plan Rev35)

- Date: 2026-10-30, Asia/Saigon.
- Review timestamp: 2026-10-30 00:39:44 Asia/Saigon.
- Reviewer: Codex visual pass on the generated outputs; project-owner visual approval is still pending.
- Environment: Windows workspace `repository root`; built-in `image_gen.imagegen`; generated originals retained in the user's CODEX_HOME output folder and copied into FEAT-063.
- Feature: FEAT-063.
- Approved plan: `plan/PLAN_REV35_UI_SCREEN_MOCKUPS_AND_MOTION_NOTES_20261030.md`.
- Plan SHA-256: `0EBBE2D7E983663F448B167F39FE42AD6C89A2E38EE5390A054673FC2C42723C`.
- Generation tool: built-in `image_gen.imagegen`; one image generation per screen, 14 final PNGs.
- Output index: `assets/generated/ui-mockups-rev35-20261030/SCREEN_INDEX.md`.
- Source baseline: FEAT-063 SRS v2.3-draft §3, §6, §20, §21.5 and §31.1–§31.7; Rev31-reconciled Lesson Library API contract; Rev31 API inventory and Rev32 purpose catalog; current Parent assets and Teacher/Admin UI code.
- Reference style: existing `apps/ui-mobile/assets/images/` for Parent; `apps/teacher-ui/src/` and `apps/admin-ui/src/` for web layout/color.
- Data: synthetic butterfly, seed, whale and school examples only. No real child data or provider credentials were supplied.

## Screen output mapping

| ID | Final output | Image-generation source file |
|---|---|---|
| P01 | `assets/generated/ui-mockups-rev35-20261030/parent/p01-lesson-library/screen.png` | `ImageGen result/exec-5376052b-bd50-4fbd-9f03-13d9826fb02b.png` |
| P02 | `assets/generated/ui-mockups-rev35-20261030/parent/p02-lesson-detail/screen.png` | `ImageGen result/exec-ca240474-abc5-4dbc-a2ff-3cca8e25449c.png` |
| P03 | `assets/generated/ui-mockups-rev35-20261030/parent/p03-drawing-line-guide/screen.png` | `ImageGen result/exec-da16d036-e855-4520-8896-7775cc96014d.png` |
| P04 | `assets/generated/ui-mockups-rev35-20261030/parent/p04-capture-subject-confirmation/screen.png` | `ImageGen result/exec-8dabaa68-fec5-4e6a-b6f4-e5d6ecedc663.png` |
| P05 | `assets/generated/ui-mockups-rev35-20261030/parent/p05-story-review/screen.png` | `ImageGen result/exec-21a3b0fe-a5a2-49ea-a682-decfb0e149c1.png` |
| P06 | `assets/generated/ui-mockups-rev35-20261030/parent/p06-video-generation-progress/screen.png` | `ImageGen result/exec-ad18c30f-56da-4865-8d0c-49449bd38325.png` |
| P07 | `assets/generated/ui-mockups-rev35-20261030/parent/p07-video-and-activities/screen.png` | `ImageGen result/exec-3a254774-ac17-466b-83ef-7bc09cb354b8.png` |
| P08 | `assets/generated/ui-mockups-rev35-20261030/parent/p08-history-feedback/screen.png` | `ImageGen result/exec-e3ee3c8b-7ee6-4545-b319-91961caa68b8.png` |
| T01 | `assets/generated/ui-mockups-rev35-20261030/teacher/t01-lesson-workspace/screen.png` | `ImageGen result/exec-ae89ec18-942e-4d40-9813-f0040a6744bb.png` |
| T02 | `assets/generated/ui-mockups-rev35-20261030/teacher/t02-lesson-authoring/screen.png` | `ImageGen result/exec-45812d91-04cc-4285-900f-8418e0d2feab.png` |
| T03 | `assets/generated/ui-mockups-rev35-20261030/teacher/t03-document-import-review/screen.png` | `ImageGen result/exec-af03dd81-ca67-4b76-bdd7-0605a6c5c160.png` |
| T04 | `assets/generated/ui-mockups-rev35-20261030/teacher/t04-session-sketch-deck/screen.png` | `ImageGen result/exec-90bb020e-af91-4cc7-a7b8-1d1058c3fa3d.png` |
| M01 | `assets/generated/ui-mockups-rev35-20261030/school-manager/m01-publication-review/screen.png` | `ImageGen result/exec-36917663-d4d5-4bf1-a88b-fedeb7faa8f9.png` |
| A01 | `assets/generated/ui-mockups-rev35-20261030/platform-admin/a01-content-moderation/screen.png` | `ImageGen result/exec-aad52e62-1a88-4ec7-8377-1411e010d9f6.png` |

## Final asset SHA-256

| ID | SHA-256 |
|---|---|
| P01 | `107FAED11995F4F26368A075118727BD4EDD507B923CD4E4E12664E8AA087FB5` |
| P02 | `70E52EFC0C0D2265F908B1391DCB4383D076C8652E917369E098C5D7E5276726` |
| P03 | `AB0DC1795138308FAA43319DF17CD0A0A07232376E501220A3EEC9BD1BEC17F0` |
| P04 | `260BAC1DD0586936C5D8084626729A6DF3AA1C170662F09EF49C63EEDF933848` |
| P05 | `0EEC2F0605042C20715E0C3C1641233DFA04402B26AFA00827DC8D3368E99D87` |
| P06 | `C6BE50588A845DBE0D0D0671263FBCDF187F5FF4FA32EC047ED02FC27DA436F2` |
| P07 | `0E8A50910B0E9B64A0D0DA7A4D1886BE6F37A31E8E6647A595E9D30CC503AA83` |
| P08 | `BC1925944F164A125288F97BBA2667E8BF8E8D5CF4F7058A1DCE348CF187B4E6` |
| T01 | `C569C5934521E9E3E64FFAFCCCDD156E23220615FFC4E53031EDBB6B273144D8` |
| T02 | `30C7E06CE788E067729037317FC2B2CB5825AD11ACBCC09B52F10D3CE10CCCAA` |
| T03 | `131CCEEBC49CB8B581216170F52FABF6B16AF0BAE505994062B5F7BFF650B633` |
| T04 | `FB7C588D559FA94F2CA32E662DAEDB6F7F2103EB69C17F5138E77C9E122C3209` |
| M01 | `8D8B8D0FEC4AEC5AC70D554E8F7D223C499646724FF9096048BA567CB4FC9C2D` |
| A01 | `2D1E651E57DA89B3EA109158A7949C8DFFC19DA8AA792821737C3567307D8937` |

## Review notes and limits

- Generated PNGs were inspected as they were returned. All 14 requested role/screen concepts were generated; Parent imagery follows the existing child-friendly palette, while Teacher/Manager/Admin use the existing restrained desktop style.
- P06 was regenerated once to replace wording that could imply unrestricted profile use. The retained version states that only the drawing and information already confirmed are used for this video.
- P03 shows the optional line-sketch guide as a separate panel, never overlaid on or replacing the child's drawing.
- T03 shows document quarantine/filter/extraction and teacher confirmation before any filtered fields reach AI; it does not show sending the original document.
- T04 shows the Teacher deck as explicitly enabled and optional. M01 shows Manager review before Public; A01 shows platform lesson metadata without child media.
- Age chips/ranges and dates rendered in the illustrations are synthetic examples only. The exact age-band catalog remains open in the SRS; the images do not decide those values.
- Remaining visual review is required for exact product copy, typography, responsive behavior, accessibility, and any use in the application. ImageGen may still introduce visual or copy defects; these are concepts, not approved product assets.
- No UI code, API, database, tests, build, provider call, or runtime behavior was changed or verified.
