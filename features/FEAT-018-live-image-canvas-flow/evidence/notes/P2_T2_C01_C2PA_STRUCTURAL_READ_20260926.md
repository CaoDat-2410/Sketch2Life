# C01 C2PA structural read — supplemental, non-binding

- Date: 2026-09-26 (Asia/Saigon)
- Status: local read-only observation following the owner's choice to review the embedded C2PA store before deciding whether byte-preserving staging may carry it.
- This note records tool output only. It is not an owner carry decision, fixture binding, approval, or authorization for staging, upload, session creation, or live use.

## Target and integrity

Target: logical custody copy of C01, SHA-256 `4a947a6fd682bc8804745f1756e120c6646df9efa3d491f2b6e8f894be6b2465`, 1,933,530 bytes. It was read-only before and after inspection. Pre- and post-inspection SHA-256 and byte length matched; no fixture bytes or attributes were changed by this inspection.

## Tool and method

- Tool: `c2patool` 0.28.0, Windows x86-64 release. The release archive SHA-256 was `107640295867f6784501729da88adfd84e87761f8f642d5e6624f807b88c4aa0`; the executable SHA-256 was `a7eabd1394c0328215b56d5c4e801026cfc9ca2df01e1dbbd38ea7651ca73d2e`. The executable reported Authenticode status `NotSigned` and was kept in a temporary directory, not installed on PATH.
- Ran a detailed structural read with settings disabling `verify_after_reading`, `verify_after_sign`, `verify_trust`, `verify_timestamp_trust`, `ocsp_fetch`, and `remote_manifest_fetch`.
- The tool output was parsed and reduced to a structural summary; raw JSON and any embedded image payload were not saved in this repository or displayed. No image was opened or sent to an AI service during this check.
- The settings disable the listed verification and remote-fetch behaviors; there was no separate packet-level network monitoring, so this note does not claim a network audit.

## Observations

- The command exited successfully and returned one manifest, marked active.
- Reported structural names included `c2pa.actions.v2`, `c2pa.hash.data`, and `c2pa.icon`; the reported action was `c2pa.created`.
- A recursive field-name filter over the parsed output found no names matching `ingredient`, `component`, or `parent`. This is a limited structural observation, not proof that no such relationship exists in every representation or external source.
- The value/payload under `c2pa.icon` was not inspected.
- No signature or trust verification was performed. The manifest's signature validity and trust status remain unknown.

## Remaining decisions and limits

OD-04's carry decision remains open: this read does not decide whether the embedded store may be carried into staging. The C01 fixture is not bound in D6; D8 retention/deletion, consent, D11 seam binding, owner D1/D12 resolution, and Stage 4 approval remain outstanding. No staging, transmission, session, or live use is authorized by this note.

This is supplemental evidence pending owner review. It does not amend the plan, approval, context, decision record, candidate package, or any prior independent review.

## Erratum — 2026-09-26 (Asia/Saigon): incomplete action list

- Recorded: 2026-09-26, about 14:00 +07:00, by Claude Code (Claude Opus 5.5) in the independent review session, at Person 2's request.
- Append-only: the text above is unchanged. This section corrects the action statement under "Observations" and adds the reviewer's supporting observations.

**Correction.** The statement "the reported action was `c2pa.created`" is incomplete. The complete action list in the `c2pa.actions.v2` assertion is `c2pa.created`, `c2pa.converted`, and `c2pa.watermarked.unbound`.

**Basis: a separate read by the independent reviewer.**

- This is a separate read by the independent reviewer, performed on 2026-09-26 during the review cited below. It is not the earlier `c2patool` run recorded above.
- It did not use a custody copy. Its target was the ignored candidate copy `tmp/feat018-p2t2-new-image-set-20260925/C01.png`, whose size and SHA-256 equal the target identity recorded above.
- The check used only Python's standard library, wrote no file, and used no network. It emitted only allowlisted labels, counts, and yes/no flags, plus the file's SHA-256 for the identity check. The candidate copy's size, modification time, and SHA-256 were unchanged after the read.
- The complete assertion set is `c2pa.icon`, `c2pa.actions.v2`, and `c2pa.hash.data`. The reviewer found no `ingredient`, `component`, or `parent` fields in the decoded claim and assertion data.
- Source: `tmp/feat018-p2t2-od04-c2pa-carry-readiness-independent-review-20260926/REPORT.md`, 50,879 bytes, SHA-256 `d727b5208000a0b38ef9c8be14faea8c6623d382871a6d12cab65e51e08656cd`. That report is local and ignored. Its Section 3 and Appendix A give the method and the exact script.

**Still unreviewed or unknown.**

- The `c2pa.icon` payload is a 2,415-byte SVG. It was not viewed or extracted.
- The manifest's text values were not reviewed.
- Signature validity, the certificates, and signer trust remain unknown, as stated in the report.
- Pending: Person 2 plans to inspect the icon and text values locally.

This erratum corrects evidence only. It does not decide OD-04 or select or bind C01. It does not change the status of D6, D8, D11, the owner D1/D12 resolution, Stage 4, or live-use authorization.

## Owner OD-04 decision — 2026-09-26 (Asia/Saigon)

Person 2 completed the requested local review of C01's embedded C2PA text fields and `c2pa.icon` without using an AI service or sending the file or extracted icon elsewhere. The reviewed C01 identity was SHA-256 `4a947a6fd682bc8804745f1756e120c6646df9efa3d491f2b6e8f894be6b2465`, 1,933,530 bytes, 1254x1254, unchanged by the read.

- The displayed text was limited to generic generator metadata: `image.png`, `OpenAI Media Service API`, `ChatGPT`, `gpt-image`, version/specification fields, timestamps, and a random instance identifier. No personal, child, or unexplained content was reported.
- The embedded SVG was viewed locally as source and as a rendered image. It was a static black OpenAI logo/vector mark. No script, event handler, external reference, `foreignObject`, entity/doctype, animation, or other active-content indicator was found by the preceding static scan or local inspection.
- The owner selected **OD-04 = Branch A — carry C2PA store as opaque bytes**. The decision permits byte-preserving carriage of the existing store only; no workflow decision relies on its unvalidated metadata, icon, signature, certificate, or signer trust.

This is an owner scope decision, not a fixture selection or D6 binding. It does not resolve D8 retention/deletion, D11, owner D1/D12 resolution, Stage 4, consent, staging, transmission, session creation, or live use. Exact-byte preservation remains required if C01 is later staged. Signature validity and signer trust remain unchecked.

## Owner OD-04 correction — 2026-09-27 (Asia/Saigon)

This section is append-only. Lines above remain unchanged. It corrects the disclosure wording in the preceding owner-decision paragraph and adds the scope clarifications required before this note is cited by a later binding package.

- C01 itself was not uploaded as a file. However, during the 2026-09-26 local review, terminal output from the helper and screenshots of the SVG source and rendered icon were shared in an assistant chat. The earlier wording that the review used no AI service or that no extracted material was sent elsewhere is superseded by this correction. No C01 pixel image was shared in those screenshots.
- The static scan was run locally by Person 2 on 2026-09-26 using `inspect_c01_c2pa.py`. The exact time, helper version/hash, extracted-SVG hash, temporary-copy location, and cleanup time were not recorded. The scan output was limited to the listed boolean indicators and identity checks; its output was later shared in the assistant chat as described above.
- The thirteen excluded-content categories apply to C01's rendered pixel content. The embedded C2PA metadata and `c2pa.icon` SVG are reviewed separately as non-rendered metadata. Person 2 accepts the observed static OpenAI logo and generic generator text only as embedded metadata, not as fixture content or evidence of origin, authorship, or authenticity.
- This scope applies to C01 only: SHA-256 `4a947a6fd682bc8804745f1756e120c6646df9efa3d491f2b6e8f894be6b2465`, 1,933,530 bytes, 1254x1254. It does not apply to C02-C08 or to any copy whose bytes or embedded store differ.
- The earlier wording that OD-04 was open or pending is superseded for OD-04 only. The decision remains **OD-04 = Branch A — carry C2PA store as opaque bytes**. The generator assertions `c2pa.converted` and `c2pa.watermarked.unbound` are unverified generator claims, not claims about Person 2's handling of the file.
- If C01 is ever staged, the store, icon, certificate chain and signature-related metadata travel only under a separately authorized, byte-preserving operation whose staged SHA-256 equals the source SHA-256. This correction authorizes no upload, staging, session creation, transmission or live use, and does not select or bind C01 in D6 or resolve OD-01, OD-02, OD-03, D8, D11, D1-D12, E-7 or E-8. Signature validity, certificates and signer trust remain unchecked.
