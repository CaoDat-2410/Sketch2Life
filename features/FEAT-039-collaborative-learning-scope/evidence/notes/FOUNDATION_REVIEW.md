# Foundation SRS independent review — 2026-10-10

- Scope: documentation revision 3, SRS v3.1; no runtime validation implied.
- Independent drafting: use cases; data/interface contracts; UX/privacy/quality. Root owns state/policy/traceability and canonical integration.
- Reviewers cross-read other fragments and integrated canonical. Findings were reported before closeout and corrected in owned fragments/build input.

## Corrected findings

| Finding | Correction / final evidence location |
|---|---|
| Accepted operation retry after pause/lock incorrectly ran new-mutation guards first | B19.11/B22.1 verify current disclosure permission, then return immutable same-payload receipt; only new mutations run current consent/turn/lock/epoch/CAS guards |
| Video-skip could appear to replace off-screen | P-NFR-17 and scenarios require off-screen if session continues; explicit Teacher early-end is a separate disposition |
| Owner choice vs proposed organization schema / source-confirmed generating wait | B23.1 and core authority labels distinguish direct answers, SRC-NEW and detailed design |
| Observation required individual participant despite group observation UI | DATA-30 subject scope and conditional participant/group references; group note not individual judgement; rubric level candidates match B23 |
| Catalogue recommendation could hard-filter readiness/materials before discovery | DATA-29 separates catalogue discovery/preference from preparation/execution safety and feasibility; no silent adoption of old ranking policy |
| Publication review reference had no creation action | CMD-48 record_review with exact safety/pedagogical review; publishing consumes the appropriate review references |
| Assistance target/audience incomplete | DATA-21 individual/group target and bound-device participant semantics; typed audience/context guards |
| Tool flags implied unsupported geometry/layer/transform operations | B19/B21/B23 explicit extension contract/fixture gate before enabling tools |
| StartSession lacked detailed UC/FR trace | UC-004 explicit Teacher Lobby→Active with guards/AT; FR007/010 map CMD-19 |
| Leaving one child on shared tablet mapped only whole-device revoke | CMD-66 explicit participant leave and grant replacement for remaining children; no class unenrollment or history rewrite |
| B7 still allowed guest profile while owner chose managed profiles | Core required studentRef; anonymous/guest admission outside pilot baseline |
| Psychological inference was listed like a future evidence-based deliverable | GATE-05 preserves prohibition at every readiness level |
| Generic library review wrongly required child-session audience/consent | DATA-24 discriminated session vs generic library review context; session presentation remains a separate exact-version Teacher gate |
| Required consent verification input could prevent an ordinary recorder creating pending evidence | DATA-05 create derives pending verification/representative authority at server; only delegated CMD-54 verifier can establish verified/rejected decisions |
| Source age/pilot/retention questions remained open after owner answered | B6/B7/B11/B14/B17/B19/B20/B21/B24/B25/ADR/context updated; original v3.0 preserved |

## Final review boundary

Use-case reviewer checked core B1–B18 and B26, all previous findings and 38 UC/76 AT/35 DATA/66 CMD references; no remaining actionable finding reported. Privacy reviewer checked owner policies, consent/revoke/data-request state/copy status and quality evidence boundaries, then identified the final NFR07/recorder wording refinements. Root verified both corrections in integrated canonical, the library-review closed union, static coverage, JSON/link/hash checks and record pointers. No remaining actionable documentation finding at closeout.

No product acceptance test, model benchmark, Android usability study or legal compliance assessment was performed. Proposed contract/profile values remain proposed even though document references validate.
