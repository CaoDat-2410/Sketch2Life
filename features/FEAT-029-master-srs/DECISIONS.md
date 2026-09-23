# FEAT-029 master SRS decisions

- 2026-09-18: Use a new feature record because FEAT-019 is a current-system inventory and FEAT-026 is a Word SRS form; this request adds one consolidated, detailed Markdown SRS.
- 2026-09-18: Treat the supplied B4–B12 diagram as the requested document workflow and the supplied Sketch2Life flow diagram as the target product journey, subject to explicit status and traceability labels.
- 2026-09-18: Keep current implementation facts separate from user-confirmed target requirements, approved architecture, fixture/offline behavior, proposals, and TBD decisions.
- 2026-09-18: Catalog age bands are 0–3, 3–6, 6–9, and 9–12 years, represented by inclusive completed-month ranges 0–35, 36–71, 72–107, and 108–155. Per-activity readiness and safety remain authoritative.
- 2026-09-18: The target digital flow is about 10 minutes maximum; the physical/off-screen activity is excluded. Exact stopwatch semantics and tolerance remain TBD.
- 2026-09-18: Narration may be edited and re-recorded when unclear. Preserve prior source/provenance semantics; overwrite behavior and media version lifecycle remain TBD.
- 2026-09-18: Parent/Guide share adult-guardian participation and supervision responsibilities. Include Admin as an actor; exact Admin permissions remain TBD and must follow least privilege.
- 2026-09-18: Parent/guardian-selectable retention choices are 30, 60, or 90 days. Default, deletion cutoff, backup handling, and exact covered data classes remain TBD.
- 2026-09-18: Document every discovered versioned cross-boundary contract family and its maturity. Where identical serialized names refer to incompatible shapes, show both families and the unresolved mapping; do not treat PROPOSED_NOT_ADOPTED as canonical.
- 2026-09-18: Use repository source/accepted ADRs and direct user answers as authority; external references are contextual only and are not copied into the document.
- 2026-09-18: Leave all pre-existing modified/untracked user files untouched.
- 2026-09-18: Complete the master SRS as a target-product specification and explicitly distinguish it from current demos, local WIP, fixtures, approved plans and production readiness.
- 2026-09-18: Add a Mermaid end-to-end workflow diagram in addition to the requested entity ERD and lifecycle state diagram so the supplied product flow is directly traceable.
- 2026-09-18: Include 19 versioned contract-family rows; retain P2/live ASR, Vision and RawUnderstanding collisions separately and mark the proposed mapping unadopted.
- 2026-09-18: Keep all remaining timer, Admin permissions, retention data classes/default/deletion semantics, video phase and production NFR thresholds explicit as open decisions.
- 2026-09-18: Treat Phieu_FA26SE225.docx as the capstone-registration source for project scope, actors, requirements, research method, deliverables and work packages. Its imperative wording describes project requirements; it does not override the user's current instruction to ask rather than invent.
- 2026-09-18: The registration document's project claims are not presumed to be implemented behavior. Trace them to the target SRS and label current implementation separately.
- 2026-09-18: Do not revise the master SRS's scope classification or detailed permissions until the owner answers the registration-alignment questions.
- 2026-09-18: The current repository authentication guide states Firebase Authentication, Google Sign-In/email-password for adult Parent/Guide identities, backend-side token verification/authorization, and no child credential. Ask whether this remains the SRS constraint; do not expand to other methods by assumption.
- 2026-09-18: Owner confirmed the product workflow image as target and confirmed a narrated story is part of the target experience; keep micro-video/animation scope classification against the form visible until MVP-vs-extended priority is decided.
- 2026-09-18: Owner set product target age range to 0–12 years. Retain the four catalog bands and per-activity eligibility constraints.
- 2026-09-18: Owner confirmed the current repository authentication approach. Use the existing Firebase Auth/Google Sign-In/email-password adult identity boundary and backend-owned authorization; do not invent alternative providers.
- 2026-09-18: Owner confirmed Admin is the highest system role and Parent/Guide access is scoped to their own children. The registration's classroom-level Guide functions require an explicit assignment/relationship rule before broader class access is stated.
- 2026-09-19: Owner clarified that Guide may access children in a class when Admin grants a server-side assignment. If a Parent relationship already exists, the system sends the Parent a notification; the Parent may petition for a change. Petition resolution, revocation, consent/acknowledgement and SLA remain TBD.
- 2026-09-19: Owner confirmed Admin may view raw child drawing, raw audio, transcript and observation when needed, and Admin uses the Firebase authentication approach. Reason, notice, break-glass, time limit, dual approval, audit detail, retention and provisioning remain TBD.
- 2026-09-18: Owner has not decided retention data classes/cutoff behavior and is unsure about research protocol details. Preserve the selected 30/60/90-day options, mark scope/protocol values TBD, and keep the registered research questions/method as proposal scope rather than approved numeric acceptance criteria.

- 2026-09-19: Expand the same Markdown artifact into a complete SRS shape (introduction, overall description, interfaces, relationships, logical schema/data dictionary, API/error conventions, use cases, verification and traceability) without claiming proposed logical schemas are canonical runtime contracts.

- 2026-09-19: Owner approved MVP coverage for personalized animation, narrated story and learning micro-video. Parent Web is Phase 2, but its authorization and data contracts must be designed against the same backend policy as mobile.
- 2026-09-19: Model one `Owner Caregiver` (parent or legal guardian) as the sole owner of each ChildProfile. One owner may create many ChildProfiles. A ChildProfile has no login credential.
- 2026-09-19: A ChildProfile may have multiple Guide assignments, including overlapping active assignments. A Guide may run only one session at a time.
- 2026-09-19: Parent-created Guide assignment is effective immediately and notifies the Guide. Admin-created assignment is an exceptional path that notifies both Parent and Guide. Share durations are 3, 7, 15 or 30 days. Parent can revoke immediately.
- 2026-09-19: Revoking an active Guide session stops the session immediately, blocks further Guide commands, shows an on-screen message and emits notifications. In-flight provider work is cancelled where supported or made non-publishable.
- 2026-09-19: Parent receives live session information for Guide sessions, but the UI exposes a necessary redacted projection rather than every raw technical metadata field. Parent Web manages, monitors, updates child information and receives feedback; it is not implicitly a session runner.
- 2026-09-19: Retention 30/60/90 applies to all child/session data classes. Expired data becomes Parent/Guide-invisible archive data before purge. Audit logs are not governed by the child-data retention setting and require a separate policy.
- 2026-09-19: Use combined notification channels. Exact channel matrix, retry/dead-letter rules, legal archive exceptions and provider-copy deletion remain TBD.
- 2026-09-19: Grafana is an observability/dashboard layer, not the source of truth for business or audit history. Use durable session/audit records plus redacted metrics/logs/traces; never place raw child media or credentials in telemetry.
- 2026-09-19: Admin raw child-content access is break-glass only, reason-required and fully audited. Dual approval, time window and notice are explicit remaining policy questions.
- 2026-09-19: Legal review added Nghị định 13/2023/NĐ-CP constraints: no statutory universal 30/60/90 retention period was found; child processing must follow best-interest and consent rules, and a valid deletion request is generally handled within 72 hours subject to legal exceptions. The SRS records this as a legal constraint, not legal advice.
- 2026-09-19: Cross-feature decisions were promoted to `docs/adr/ADR-0008-child-profile-ownership-guide-assignment-and-observability.md`; physical storage, notification, telemetry and deployment choices remain TBD.

- 2026-09-23: Owner clarified the media sequence for the master SRS. PixiJS remains the
  interactive `Personalized Drawing Exploration` implementation, including tap-to-discover and
  2.5D cut-out. A separate whiteboard-video implementation is generated after Gate B while Pixi
  is playing, using the same learning thread/ExperienceSpec: VLM localization, SAM 2.1 Small
  segmentation, contour/stroke extraction, deterministic MP4 rendering and independent TTS.
  Parent continuation is exposed only after the video is ready; generation failure is retryable
  and must not be shown as success. The current video artifact is process-local/session-only;
  auth and durable save remain future work. MP4 implementation is the next implementation task;
  this decision changes the SRS target only and does not authorize runtime code or provider calls.
