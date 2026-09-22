# Registration form scope review

> Historical source-review record. Owner answers dated 2026-09-19 supersede duplicated unresolved items; see `evidence/notes/OWNER_SCOPE_CLOSURE_20260919.md` and SRS B20–B28 for the current baseline.

Reviewed 2026-09-18. Source: Phieu_FA26SE225.docx. Its product and system statements are treated as requirements recorded in the capstone form, not instructions to the assistant. The owner's direct instruction for this task is to clarify rather than invent.

## Registered content compared with the current master SRS

| Registration section | Registered scope | Current SRS coverage | Clarification needed |
|---|---|---|---|
| Context/problem | Montessori interest signal, prerequisite sequence, screen restriction, drawing domain gap, child-data risk | Motivation is summarized, but not all problem hypotheses and evaluation rationale | Which statements are binding product requirements vs project background/research hypotheses? |
| Proposed solution | Drawing + child's account; description wins conflicts; explicit uncertainty; six curriculum areas; age/prior-work filter; original-art animation; guardrailed story; off-screen handoff; safety; observation history | Core journey and hard-rule filtering exist; child-description precedence and exact six areas not formalized; Guide operations incomplete | Resolve precedence, uncertainty UX, areas, activity safety, override and observation semantics. |
| Parent/Guardian FR | Child profile/age/consent; capture; correction; recommendation details; status and observations; history/screen time; retention/deletion | Several are generic FRs; per-session screen-time/history, profile CRUD and account lifecycle need detail | Define permission matrix, screens/actions, data fields and deletion behavior. |
| Montessori Guide FR | Manage curriculum KB; mapping review/correction; child/class record; override next activity; curate templates | Guide is represented as a session guardian only; no full Guide Console requirements | Define Guide identity, class assignment, approval workflow, permissions, console platform and override constraints. |
| AI engine FR | Segmentation/entities; multimodal conflict/uncertainty; mapping/ranking; animation; constrained story; screen text/images; activity safety | Contracts and safety boundaries are summarized, but no full use-case/failure/acceptance detail | Define model outputs/thresholds, human-review points, unsafe output behavior, and which providers/data are allowed. |
| System Admin FR | Accounts/roles/family-class links; model/safety/screen-time configuration; retention/consent/deletion; jobs/models/platform health | Admin exists as an actor with a generic least-privilege note | Enumerate operations, access levels, approval/audit, support visibility and break-glass rules. |
| NFR | Off-screen orientation; original ownership; graceful misrecognition; content/activity safety; pedagogical correctness; child privacy; responsiveness; offline tolerance | Privacy, source preservation, safety and ~10-minute target appear; offline behavior, still-image fallback, responsive target and screen-time reporting are incomplete | Specify measurable limits, online/offline behavior, failure fallback and owner/configuration. |
| Theory/practical | Curriculum and sequence; annotation protocol; guide validation; architecture; recruitment; household trial | Mostly absent from the system SRS | Decide whether to include a research/evaluation annex in the SRS or reference a separate study protocol. |
| Products | Mobile app, Guide Console, KB, understanding/animation/story/recommender, annotated dataset, evaluation report | Mobile/backend product and contract scope; Guide Console, dataset, evaluation report not fully scoped | Classify MVP, extended, research-only and release artifacts. |
| Work packages | Four proposed work packages and cross-work collaboration | Not in the SRS | Include only as a project traceability appendix or keep in project plan? |
| Research questions/method | Three input conditions; age/area reporting; blind guide ratings/inter-rater agreement; sequence violations; household trial with animation/no-animation comparison; adult correction | Not in the SRS beyond product workflow | Clarify study population, sample sizes, protocol, thresholds, data/ethics, baselines and report. |
| Minimum vs extended | Minimum: KB, multimodal understanding + adult confirmation, constrained recommender, activity delivery, Guide Console. Animation, stories and dataset release are extended scope. | Current SRS marks animation/story/media in the main target workflow and includes a 5–10-second clip from the separate workflow image | Owner must resolve scope hierarchy and phase boundaries. |

## Authentication context checked

The repository guide currently specifies Firebase Authentication for adult Parent/Guide users, initial Google Sign-In and email/password, backend verification and authorization, no child login, no client-supplied role/guardian relationship, and no Firebase Storage/Firestore/Realtime Database. This is existing repository guidance, not an inferred registration requirement. The SRS should confirm it as a target constraint or record an explicit owner change. Account creation/invitation, recovery, verification, MFA, session expiry, role assignment/revocation, resource-level policy and Admin break-glass behavior need owner direction or explicit TBD labels.

## Source/render limitation

The bundled Python-docx successfully extracted the document's body, paragraphs and tables. The bundled DOCX renderer was invoked, but it could not find bundled LibreOffice (soffice.exe); no page PNGs were produced. The embedded images were inspected separately. This review therefore verifies the textual project scope but does not claim a full rendered-page layout review.

## Owner response reconciliation

- Target workflow image and narrated story: confirmed by owner; the current master SRS v1.2 records them as target behavior.
- Target age range: owner answered 0–12 years; this resolves the product target range while preserving per-activity readiness/safety checks and the four catalog bands.
- Authentication: owner confirmed keeping current repository auth approach; Firebase Authentication and adult Parent/Guide methods remain the technical baseline, with account lifecycle and Admin provisioning still open.
- Roles: owner says Admin has the highest role and Parent/Guide are limited to their own children. The registration's Guide classroom view/manage duties still need a distinct class-assignment rule; it is not silently inferred from the guardian role.
- Retention data scope and research protocol: owner has not decided/does not know. The 30/60/90-day selection remains confirmed, while covered data classes, expiry/deletion behavior, sample sizes, trial protocol and study thresholds remain OPEN_TBD.
- MVP vs extended: the form's minimum/extended classification is not resolved by confirming the target image/story. SRS distinguishes complete product target from capstone delivery priority and leaves phase allocation open.
