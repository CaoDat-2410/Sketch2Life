# Independent Cold Review Capture — FR-C-08 Contract Draft 2 and M3–M6 Roadmap Draft 1

Date: 2026-11-15  
Reviewer: fresh-context independent reviewer /root/frc08_and_roadmap_review  
Record type: coordinator capture of the reviewer’s final response. The independent reviewer returned its findings in chat and did not create an in-repository report file. This capture preserves that result; it is not owner approval.

## Reviewed inputs and pin verification

- Lifecycle Contract Draft 2: 46,791 bytes; SHA-256 567B28A6C85BD3BB8608C7B48D1F60CABC36B5AEA28E25D52784A11FB2BAC712.
- Roadmap Draft 1: 12,869 bytes; SHA-256 9D0133539CA336F675B4AC924E21E8CA215EF2B1DF8FBE6000FF171888669AF2.
- All 38/38 pin rows in the contract draft matched. All eight pinned inputs in Roadmap Draft 1 matched.
- SRS authority pointer: 4,313 bytes; SHA-256 D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60.
- Canonical working SRS Rev68: 639,948 bytes; SHA-256 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944.

## Verdict

Combined package: CHANGES REQUIRED — 0 P1, 3 P2, 0 P3.

- Lifecycle Contract Draft 2: CLEAN — 0 P1, 0 P2, 0 P3. It explicitly states the D-208 item 7 / Rev68 §29.2 real-data gate in §§2, 4.6, 5, and 8, without claiming the gate is satisfied. Its blocked/not-approved/not-launched boundary remains.
- Roadmap Draft 1: CHANGES REQUIRED — 0 P1, 3 P2.

### Findings

1. Roadmap §2 M3 omits Parent text/voice idea input and adult review/edit/confirmation of a Whisper transcript when voice is used. Rev68 §1, §5.1 and BR-23 require this.
2. Roadmap §2 M3 omits FR-P-11 details for the optional line guide: explicit adult opt-in, no job when disabled/skipped, generic-topic-only input, no child data egress, adaptive 4–8 steps, and private/provenance/lifecycle constraints. See Rev68 BR-46/BR-54 and §31.17.
3. Roadmap §2 M4 does not preserve §31.17’s editable lesson-presentation scope: editing slide text/order, image/SVG/video placement, media preview/reordering, review/submission, and immutable published revisions.

The reviewer confirmed that Roadmap Draft 1 correctly maps M3/M4/M5/M6 to P1/P2/P3/P4, distinguishes M2 S1/S2/S3 from SRS phases, treats the prior roadmap as historical planning baseline, and does not imply production or real-data authorization.

## Boundaries

The review was read-only. No tests, validators, builds, runtime, database, provider, or deployment operations were run. This review does not approve implementation, data use, or launch.