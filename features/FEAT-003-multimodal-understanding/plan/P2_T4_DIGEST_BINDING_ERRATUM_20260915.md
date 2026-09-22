# P2-T4 digest-binding erratum

- Status: **READY FOR INDEPENDENT ERRATUM REVIEW — NOT OWNER REAPPROVED**
- Erratum identifier: `P2_T4_DIGEST_BINDING_ERRATUM_20260915` (the date names the 2026-09-15
  integrity audit that this erratum resolves)
- Issued: 2026-09-16
- Owner: Person 2
- Feature: FEAT-003 Multimodal understanding, task P2-T4
- Kind: immutable, documentation-only digest-binding erratum (owner-selected Option A)
- Owner decision: the project owner accepted the `VERIFIED_INTEGRITY_DEFECT` finding and selected
  Option A (`approvals/TASK_APPROVAL.md`, "P2-T4 digest-binding integrity defect acceptance and
  Option A erratum authorization")
- Identity computation tree: `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` (clean working tree)
- Independent erratum review: **NOT YET PERFORMED**
- Renewed owner binding approval against the corrected identities: **NOT GRANTED**
- Seven-file remediation implementation: **NOT APPROVED**; G6–G9: **PAUSED**

This erratum corrects which identities bind four already-committed P2-T4 documents. It does not
edit, replace, supersede, or reinterpret the content of freeze revisions 11/12 or package
revisions 15/16. It is not a freeze revision, a package revision, an approval, an evidence record,
or an implementation authorization. Writing it does not constitute independent review, renewed
owner approval, or implementation approval.

## 1. Artifacts covered and byte preservation

| Artifact | Repository path | Source commit |
|---|---|---|
| Freeze revision 11 (immutable G1 predecessor) | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` |
| Freeze revision 12 (successor) | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` |
| Package revision 15 (immutable G1 predecessor) | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` |
| Package revision 16 (successor) | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` |

All four artifacts are preserved byte-for-byte. Before issuance it was verified that:

- the working-tree and `HEAD` bytes of revisions 12 and 16 equal their blobs at `5b6501b`, the only
  commit that has ever changed those paths;
- the working-tree and `HEAD` bytes of revisions 11 and 15 equal their blobs at `18d0c33`, and no
  later commit has changed those paths;
- none of the four files contains a byte-order mark or a `CR` byte, and each is valid UTF-8.

This erratum edits none of the four files, including their in-document binding tables, which
continue to display the legacy digest values (section 6, rule 6).

## 2. Defect

### 2.1 Documented algorithm

Freeze revisions 11/12 (section 10.1) and package revisions 15/16 (section 7) each define their
normalized digest as follows: normalize `CRLF` and lone `CR` line endings to `LF`; remove the
binding table from its exact header through the blank line after its final row; remove the
complete section beginning at the exact revision-history heading through end of file; UTF-8
encode the remaining text; hash it with SHA-256. The heading is `## 13. Revision history` for the
freezes and `## 12. Revision history` for the packages.

### 2.2 Legacy implementation defect

The four recorded digests were computed by locating the revision-history heading with a
first-substring search (for example `text.index(heading)`) instead of an exact full-line match. In
every one of the four documents, the heading string first occurs inline, quoted inside the
sentence of section 10.1 or section 7 that describes the algorithm itself, 107 to 157 lines before
the real heading. The legacy cut therefore lands mid-sentence inside the algorithm description, and
each recorded digest hashes only a prefix of its document's intended scope.

The recorded values are reproduced exactly by the first-substring search and are not reproduced
by a full-line match. The earlier reproductions described as "two differently coded
implementations" therefore shared the same substring behaviour, and their cross-check against the
already-approved revision 11/15 values, which carried the same defect, could not detect it.

### 2.3 Consequence

The recorded digests are reproducible and were computed over the unchanged committed bytes, but
each binds less content than the approval records that cite it state. No document byte drifted;
only the digest scope was wrong. The project owner accepted this finding as
`VERIFIED_INTEGRITY_DEFECT`.

## 3. Corrected normalization

The corrected normalized SHA-256 is computed from the exact committed bytes of an artifact at its
source commit, using that artifact's binding-table header line and revision-history heading line:

```text
Freeze revisions 11 and 12
  binding-table header line:   | Field | Required value/format | Current docs-only value |
  revision-history heading:    ## 13. Revision history
Package revisions 15 and 16
  binding-table header line:   | Field | Required format | Current docs-only record |
  revision-history heading:    ## 12. Revision history
```

(The indentation and labels above are presentation only; each value is the text after the label.)

1. **Line endings.** Decode the bytes as UTF-8, replace every `CRLF` sequence with `LF`, then
   replace every remaining lone `CR` with `LF`.
2. **Binding-table header.** Locate the header as an exact full line: a line whose entire
   content, from the start of the text or an `LF` to the next `LF` or the end of the text, equals
   the header string exactly. Exactly one such line must exist; otherwise the identity is not
   computable.
3. **Table removal.** Remove the header line and every following line up to and including the
   first empty line after it (the table's final row is the line immediately before that empty
   line).
4. **Revision-history heading.** In the remaining text, locate the heading as an exact full line,
   using the same definition as step 2. Exactly one such line must exist. An occurrence of the
   heading string inside any other line is never a match.
5. **History removal.** Remove the text from the first character of that heading line through the
   end of the file. The `LF` that terminates the preceding line is retained.
6. **Digest.** Encode the remaining text as UTF-8 without a byte-order mark and compute the
   lowercase hexadecimal SHA-256 of those bytes.

In all four artifacts the header and the heading each match exactly one full line, and every
removed table line other than the final empty line begins with `|`.

The other two identities are defined as follows:

- **Raw-file SHA-256:** the lowercase hexadecimal SHA-256 of the exact committed file bytes, with
  no normalization.
- **Git blob ID:** the object ID reported by `git rev-parse <source commit>:<path>`, equal to the
  SHA-1 of `blob <byte length>`, a NUL byte, and the committed file bytes (repository object format
  `sha1`).

Non-normative reference sketch (Python):

```python
text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
lines = text.split("\n")
starts = [i for i, line in enumerate(lines) if line == header_line]
assert len(starts) == 1
end = lines.index("", starts[0])            # first empty line after the header
kept = lines[: starts[0]] + lines[end + 1:]
heads = [i for i, line in enumerate(kept) if line == heading_line]
assert len(heads) == 1
corrected = hashlib.sha256("".join(line + "\n" for line in kept[: heads[0]]).encode("utf-8")).hexdigest()
```

## 4. Identity record

Legacy values are historical and non-canonical (section 6, rule 1).

### 4.1 Freeze revision 11

| Field | Value |
|---|---|
| Path | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` |
| Source commit | `18d0c33d35431ca96a76692a68c6b992098699e7` |
| Git blob ID | `87227e5be0a58db88ac9f91ee7ddbdfa9bf4b05f` |
| Raw-file SHA-256 | `9521cb1482a10cefd235ea9596882d210912897289c182205aa93ee5a6685197` |
| Corrected normalized SHA-256 | `2b920e34f779ccbeabfec91e44858957b4f032dd6583879403b0fb748e367050` |
| Legacy first-substring SHA-256 (historical, non-canonical) | `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2` |
| Size | 62,792 bytes; 989 lines |

### 4.2 Freeze revision 12

| Field | Value |
|---|---|
| Path | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` |
| Source commit | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` |
| Git blob ID | `1e7e487362efec02b3b5f3bbf9dd4c64eabaa0d9` |
| Raw-file SHA-256 | `b9606292e00b1b956ec38e141eb27f868bad2835f8ea5e8d20693a18acd2fa20` |
| Corrected normalized SHA-256 | `103695e5e1c49d9f9b1cc85fd5286f42980580f338578db799febdeedb310ee5` |
| Legacy first-substring SHA-256 (historical, non-canonical) | `d592b135d2d8a90024d48d1b8335321660e8d7f089873e48687707c760e3d3e9` |
| Size | 80,834 bytes; 1,193 lines |

### 4.3 Package revision 15

| Field | Value |
|---|---|
| Path | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` |
| Source commit | `18d0c33d35431ca96a76692a68c6b992098699e7` |
| Git blob ID | `a4ade521f288c0d07c8c9cfdb1f6bbe6b41fa839` |
| Raw-file SHA-256 | `255034c587e89f8b72122c7377566684dd7a718257555c7fa92175a444255681` |
| Corrected normalized SHA-256 | `7c76208d2ab3c98f9681fce67641049a93b21d2f0c2e9c843de1cac9e4d70b96` |
| Legacy first-substring SHA-256 (historical, non-canonical) | `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7` |
| Size | 34,337 bytes; 451 lines |

### 4.4 Package revision 16

| Field | Value |
|---|---|
| Path | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` |
| Source commit | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` |
| Git blob ID | `8784e84a537260668e81c6c889aadc8688086857` |
| Raw-file SHA-256 | `8ce46b5f762b27b556030d85666ccb6827a1fdbaeb56312dc8490d6e214a75ce` |
| Corrected normalized SHA-256 | `75cd5d69e6896d7fae10d3771a90019003e0644fff1138161b7ac330e840b270` |
| Legacy first-substring SHA-256 (historical, non-canonical) | `ad886d261d2807bcc95264d05d6a385dc79cd2f0cad44e2b4f004531b8097d4f` |
| Size | 43,682 bytes; 530 lines |

## 5. Content omitted by the legacy digests

Positions are 1-based `line:column` in the committed file. Raw byte ranges are half-open
`[start, end)` over the committed file. In every artifact the binding table lies entirely before
the legacy cut, and the omitted span runs from the inline heading occurrence up to, but not
including, the real heading line. Every omitted span lies inside the corrected normalized scope.

| Artifact | Binding table | Legacy cut (inline occurrence) | Real heading | Omitted span | Characters | UTF-8 bytes | Raw byte range |
|---|---|---|---|---|---|---|---|
| Freeze rev 11 | L844–L855 | L865:C16 | L975 | rest of L865 + L866–L974 (109 complete lines) | 7,143 | 7,143 | `[53417, 60560)` |
| Freeze rev 12 | L995–L1009 | L1021:C16 | L1178 | rest of L1021 + L1022–L1177 (156 complete lines) | 10,570 | 10,572 | `[66745, 77317)` |
| Package rev 15 | L306–L317 | L326:C33 | L433 | rest of L326 + L327–L432 (106 complete lines) | 5,619 | 5,619 | `[26050, 31669)` |
| Package rev 16 | L379–L393 | L402:C33 | L511 | rest of L402 + L403–L510 (108 complete lines) | 5,853 | 5,857 | `[33954, 39811)` |

### 5.1 Freeze revision 11 — omitted headings and content

Omitted headings: L869 `### 10.2 Future fixture and schema-parity requirements`; L914
`## 11. Governance and deferred boundaries`; L930
`## 12. Independent review checklist and final handoff`; L932 `### Pass 1 - technical completeness`;
L949 `### Pass 2 - governance and security`; L962 `### Post-remediation final audit record`; L971
`### Final task status`.

Also omitted: the rest of the section 10.1 algorithm sentence, including the package-digest rule;
the exact seven-path offline allowlist (L875–L881, the only place the four code and test paths
occur, while the three fixture paths otherwise occur only in the excluded binding table); the
schema-parity oracle, fixture coverage, and privacy-sentinel requirements; the section 11
governance boundaries; the section 12 review checklist and audit record; and the final task status.

### 5.2 Freeze revision 12 — omitted headings and content

Omitted headings: L1025 `### 10.2 Fixture and schema-parity requirements for the narrow remediation`;
L1096 `## 11. Governance and deferred boundaries`; L1115
`## 12. Independent review checklist and final handoff`; L1117
`### Required independent review (not yet performed)`; L1123
`#### Pass 1 - technical completeness (pending)`; L1155
`#### Pass 2 - governance and security (pending)`; L1173 `### Final task status`.

Also omitted: the rest of the section 10.1 algorithm sentence; the exact seven-path remediation
allowlist (L1032–L1038, the only place the four code and test paths occur, while the three fixture
paths otherwise occur only in the excluded binding table); the `P2T4FusionInputRejectionV2`
schema-parity oracle requirement; the fixture impact of the V2 rejection identity (16 `REJECTED`
entries change, 26 entries stay byte-identical, and the manifest `rejection_contract` changes); the
six match-view fixture scenarios; privacy sentinels, including for the observed match-view token;
the section 11 governance boundaries; the section 12 review checklist; and the final task status.

### 5.3 Package revision 15 — omitted headings and content

Omitted headings: L337 `## 8. Mapping and deferred-boundary record`; L359
`## 9. Required independent reviews`; L361 `### Pass 1 - technical completeness`; L371
`### Pass 2 - governance and security`; L386 `### Review completion record - 2026-09-14`; L402
`## 10. Validation and non-actions`; L426 `## 11. Final task status`.

Also omitted: the rest of the section 7 algorithm sentence and the schema-parity oracle
requirement; the deferred and unapproved boundary list; the review requirements and completion
record; the validation commands and non-actions; and the final task status. The package's
seven-path list (section 5, L207–L215) lies before the cut.

### 5.4 Package revision 16 — omitted headings and content

Omitted headings: L414 `## 8. Mapping and deferred-boundary record`; L436
`## 9. Required independent reviews (not yet performed)`; L438 `### Pass 1 - technical completeness`;
L453 `### Pass 2 - governance and security`; L471 `### Review completion record`; L479
`## 10. Validation and non-actions`; L503 `## 11. Final task status`.

Also omitted: the rest of the section 7 algorithm sentence and the `P2T4FusionInputRejectionV2`
schema-parity oracle requirement; the deferred and unapproved boundary list; the review
requirements, including the 16-of-42 fixture-change check and the separate-approval prerequisites;
the validation commands and non-actions; and the final task status. The package's seven-path list
(section 5, L262–L270) and the section 6 handoff lie before the cut.

## 6. Identity rules

1. **Legacy digests are historical and non-canonical.** The four legacy first-substring digests in
   section 4 remain as written in existing records, which are not rewritten. They must not be used
   as the sole identity of these artifacts in any future approval or evidence record. This erratum
   labels them as historical legacy first-substring digests wherever it cites them.
2. **Corrected normalized SHA-256 binds semantic content.** It covers all document text except the
   binding table and the revision-history section.
3. **Raw-file SHA-256 binds every byte**, including the binding table and the revision-history
   section.
4. **Git blob ID plus source commit and path provide Git traceability.**
5. **Future evidence carries all three.** Every future evidence record that identifies one of these
   artifacts must carry its corrected normalized SHA-256, its raw-file SHA-256, and its Git blob ID
   together with its source commit and path. Under rule 1, no future approval or evidence record may
   use a legacy digest as the sole identity of these artifacts.
6. **In-document binding tables are not edited.** The `freeze_draft_sha256` and
   `implementation_package_sha256` values displayed in freeze section 10.1 and package section 7 are
   the legacy digests. They are historical, and they are not a complete binding for any purpose.
7. **Corrected identities are pending approval.** This erratum establishes the corrected
   identities for independent review. They become an owner-approved binding only through a renewed
   owner approval recorded after that review. Until then, no P2-T4 approval is bound to the
   corrected identities.
8. **`manifest-v1.json` is rebound only in a separately approved remediation.**
   `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json` currently
   records the legacy revision 11/15 digests with freeze commit `18d0c33`. This erratum does not
   change it. It may be rebound only during a later, separately approved seven-file remediation.
9. **This erratum has no normalized self-digest.** Once committed, its identity is its raw-file
   SHA-256, Git blob ID, commit, and path, to be recorded by the independent review and any renewed
   approval record. No self-referential digest is asserted here.

## 7. Unchanged semantics and pending gates

- No contract or package semantics change. The fused-result identity `P2T4.P2T4FusedResultV1@1.0`,
  the outer rejection identity `P2T4.P2T4FusionInputRejectionV2@2.0`, owner decisions MV-1 through
  MV-5, and the Vision match-view admissibility invariant remain exactly as written in freeze
  revision 12 and package revision 16.
- The existing G1, G2, and successor contract-freeze approval records remain on record as written
  and cite the legacy digests. Identity reconciliation is pending: renewed owner binding approval
  against the corrected identities requires independent review of this erratum first, and has not
  been granted.
- Under rule 1, a future remediation-implementation approval cannot use the legacy digests as the
  sole identity of these artifacts.
- The seven-file remediation implementation remains **NOT APPROVED**, and G6–G9 remain **PAUSED**.
  Evidence, integration, runtime, provider/model, GPU, Lightning, network, migration, production,
  and live execution remain **NOT APPROVED**.

## 8. Independent erratum review checklist (not yet performed)

### Pass 1 - technical, hash, and traceability

- [ ] Recompute the legacy, corrected, raw-file, and blob identities of all four artifacts with at
      least two independently written implementations; every value matches section 4.
- [ ] Confirm section 3 implements exact full-line matching, and confirm the legacy values
      reproduce only with the first-substring cut.
- [ ] Confirm revisions 12/16 are byte-identical to their blobs at
      `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2`, and revisions 11/15 to their blobs at
      `18d0c33d35431ca96a76692a68c6b992098699e7`.
- [ ] Confirm the section 5 binding-table ranges, cut positions, omitted spans, counts, and
      omitted headings.
- [ ] Confirm the seven remediation paths are unchanged since
      `064ba62f32f1ffb964bc2208577eb0650b98e26a`.

### Pass 2 - governance, scope, and security

- [ ] The status is exactly `READY FOR INDEPENDENT ERRATUM REVIEW — NOT OWNER REAPPROVED`, and no
      approval is granted or implied.
- [ ] Revisions 11/12/15/16, the seven remediation paths, FEAT-018, P2-T3, and lockfiles are
      untouched.
- [ ] The governance records record only: defect accepted, Option A selected, erratum awaiting
      independent review, no renewed binding approval, and no implementation authority.
- [ ] Legacy digests are labelled historical and non-canonical wherever this erratum cites them.
- [ ] No credentials, absolute machine paths, raw media, transcripts, or real child data appear.

## 9. Author verification record and non-actions

This record is the author's own verification. It is not the independent review required by
section 8.

- The section 4 identities were computed at tree `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` with
  two independently written implementations: a Python line-list implementation and a Windows
  PowerShell/.NET offset-scanning implementation. All legacy, corrected, raw-file, and blob values
  agreed exactly. Each computed blob ID matched the object ID Git reports for the source commit and
  path, and each legacy value equals the value recorded in the approval records.
- The seven remediation paths were confirmed unchanged since
  `064ba62f32f1ffb964bc2208577eb0650b98e26a`.
- Repository validator results for this issuance are reported with the issuance task rather than
  in this erratum, so this document's bytes do not depend on them.
- This issuance did not modify the four artifacts, the seven remediation paths, FEAT-018, P2-T3,
  or lockfiles. It added no approval, staged or committed nothing, and performed no G6–G9, runtime,
  provider/model, GPU, Lightning, network, migration, or live work.

## 10. Revision history

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-16 | Initial issuance under owner-selected Option A. Records legacy (historical, non-canonical), corrected normalized, raw-file, and Git identities for freeze revisions 11/12 and package revisions 15/16. Status `READY FOR INDEPENDENT ERRATUM REVIEW — NOT OWNER REAPPROVED`; no artifact, approval, or implementation change. |
