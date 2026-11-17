# FEAT-063 Independent Architecture Audit

**Date:** 2026-10-27  
**Review type:** Independent architecture/product/data review  
**Reviewer:** One delegated subagent, synthesized and source-checked by the primary reviewer  
**Disposition:** Read-only review; no implementation, schema change, test, provider call, deployment, PDF or final diagram was made.

## 1. Executive verdict

The product direction is coherent for a synthetic-data demo: separate Parent Android and Teacher web entry points; one child per run; a simple organization roster; Teacher lesson preparation and one representative child per occurrence; a human-confirmed script before video; and a backend modular monolith that stores durable state in PostgreSQL while using Modal for inference. This is a reasonable scale for the current repository and does not call for microservices or Kubernetes.

The current SRS is a strong architecture proposal, but it is **not yet a closed specification for a reliable end-to-end demo or production launch**. The largest gaps are: no fully specified local-storage-to-Modal data path; no explicit automated safety check of rendered video/audio before playback; mismatches between target profile/enrollment rules and existing BE1 database constraints; unclear enforcement of separate Firebase accounts; incomplete field-level mapping for 51 tables retained/refactored; and no clear canonical owner for several duplicated facts. Production hosting is intentionally left open, so it is appropriate for a local demo but not yet a production deployment design.

These findings do not reverse the owner's product choices. They identify the decisions and technical proofs required before implementation can be called safe, consistent and reproducible.

## 2. What the review covered and limits

The reviewer read the FEAT-063 SRS, data-table register, ADR-0021, context, decisions, source register, status, governance/architecture guidance and relevant app/backend/Compose files. Current model, GPU, database, payment and privacy references were checked against primary/official sources linked at the end.

No live database was queried, no test or build was run, no Model/Modal/payment call was made, and no actual child data was used. The declared source-table count is not evidence that every mapped table exists in a deployed database. Product legal obligations are not interpreted here; the real-data gate needs qualified privacy/legal review.

## 3. Strengths to preserve

1. **The product boundaries are clear.** Parent and Teacher data are separate, each run contains exactly one child, the Teacher selects one sample child and one activity, and the removed collaboration runtime is not allowed to leak back into the product flow.
2. **The architecture is appropriately modest.** A Python modular monolith with domain/application/adapter boundaries, PostgreSQL, an outbox and versioned contracts is easier to build and operate here than a fleet of services. Redis/RQ is acceptable as delivery/backpressure if PostgreSQL remains the authoritative job ledger and redelivery is idempotent.
3. **The AI boundary is server-side.** Keeping Modal and payment credentials out of the clients, preserving source assets and pinning model/config provenance are sound controls.
4. **The requirements capture difficult failure cases.** The SRS covers stale jobs, duplicate payment callbacks, deletion lifecycle, safe errors, rate limiting, backup/restore and a runbook outline.
5. **Real-child data is gated.** Synthetic-only local demo data is the right boundary while provider transfer, purpose, access, retention and privacy controls are unresolved.
6. **The adult script gate matches the user's choice.** A completed video is shown without a separate human approval step. The recommendations below add automated safety validation before playback; they do not add a manual video-approval gate.

## 4. Findings by priority

### Blockers before the full synthetic end-to-end demo

#### AUD-01 — Define the byte path between local Docker and Modal

The SRS itself states that local MinIO is not reachable from Modal and leaves a bounded transfer POC open. A drawing, optional voice, lesson-derived context and generated clips/video all have to cross this boundary. The drawing's accepted byte/dimension limits and the actual authenticated transfer shape are also still open.

**Why it matters:** Without a concrete upload, execution, result-return and cleanup path, the advertised end-to-end workflow cannot run. It is a blocking integration design, not just a later performance optimization.

**Recommendation:** Before building the full UI, choose one transport design and document maximum bytes, image dimensions, request/result size, encryption/authentication, timeouts, idempotency, regional path, cancellation and cleanup. Run one synthetic image-to-video vertical slice through local API/storage → Modal → private playback storage. Keep Modal access restricted to a single run's inputs/results.

**Evidence:** [SRS local-to-Modal transfer boundary](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:251); image/transfer limits are explicitly open in [§14](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:772). [Compose currently has only Postgres/Redis/MinIO](../../../compose.yaml:1).

#### AUD-02 — Add automated safety validation of rendered output before playback

The SRS requires content checks for transcripts, extracted lesson text, story/script, storyboard and scene prompts. Yet FR-AI-09 publishes after technical validation, and the run state machine moves to playable `VIDEO_READY` without an explicit video/audio safety-validation state. Technical correctness (codec, dimensions, duration) does not establish that generated frames, narration or subtitles are safe for children.

**Recommendation:** Add a server-side, versioned automated output-safety stage for sampled video frames, narration/transcript and subtitles. Quarantine an unsafe result and show a stable, safe error/recovery path. Publish only after both technical validation and this check. This is an automated safety gate, not human approval of the finished video. Define what is checked, thresholds, false-positive handling, retention of evidence and how a failed clip consumes retry budget.

**Evidence:** [FR-AI-09](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:332) publishes after technical validation; [FR-AI-12](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:335) lists pre-publication text/prompt safety checks; [BR-16/36](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:134) defines immediate playback and safety policy; [state model](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:225).

### High priority before schema/API implementation

#### AUD-03 — Reconcile target profile and roster rules with existing BE1 constraints

The existing `be1_managed_profiles` model requires `age_months` 36–155, non-null `class_id`, `consent_id` and `consent_purpose_ref` ([BE1 model](../../../backend/src/sketch2life/infrastructure/persistence/be1_models.py:98)). The target does not define that age range, uses enrollment history as the roster model, adds a separate profile revision head, and says synthetic demo does not represent real consent.

**Why it matters:** New profile creation can fail for ages outside the inherited constraint; `managed_profiles.class_id` and `enrollments.class_id` can diverge; and a synthetic profile may be forced to reference a consent record that is not real. The new design cannot simply reuse these rows without defining the projection and migration semantics.

**Recommendation:** Decide the supported age range; name the canonical roster relation (`enrollments` is the natural history source); mark `managed_profiles.class_id` as removed, derived or authoritative; define immutable revision vs current profile-head ownership; and define an explicit synthetic-data fixture state that cannot be mistaken for real consent. Map each old field/constraint to target behavior before changing BE1.

**Evidence:** [BE1 profile and enrollment source models](../../../backend/src/sketch2life/infrastructure/persistence/be1_models.py:98); [target BE1 mappings and consent statements](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:94); [profile revision tables](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:231).

#### AUD-04 — Make “separate accounts” enforceable at the identity boundary

The owner explicitly requires separate Parent and Teacher accounts. The SRS chooses Firebase Authentication and says the server performs authorization, but it does not state whether one Firebase UID can be provisioned in both role scopes or how login/registration prevents cross-surface reuse. Firebase token verification gives the backend an authenticated UID; the backend still needs its own role/organization policy.

**Recommendation:** Explicitly enforce one role scope per principal in the server identity/role tables (or choose separate Firebase projects if that is truly intended). Do not treat separate apps or client UI as account separation. Define Parent signup/recovery, Teacher invitation/activation, organization bootstrap and account deprovisioning before launch. Verify role changes/revocation on the backend, not from client-supplied claims.

**Evidence:** [SRS authorization and role provisioning](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:109); [FR-O-09 open onboarding detail](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:363). Firebase's official guidance explains that the custom backend verifies the ID token and derives the UID; its authorization still needs to be enforced server-side ([verify ID tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens), [custom claims](https://firebase.google.com/docs/auth/admin/custom-claims)).

#### AUD-05 — The headline “88 active tables” is not yet a complete implementation dictionary

The arithmetic is internally consistent as a proposal: 51 retained/refactored + 37 new = 88 active; plus 35 legacy = 123 physical if all 86 source declarations exist in the real database. The SRS correctly says no live DB was inspected. However, the register gives detailed logical fields for the 37 new tables, while the 51 retained/refactored tables mostly have responsibility summaries. It does not give field-by-field source-to-target disposition for those 51, and 25 active `ai_policy` tables are carried forward without a per-table demonstration that each serves a new runtime or required platform concern.

**Recommendation:** Keep the 88/123 figures labeled provisional. Before migration work, inspect actual schemas/data, then create a field/constraint/index/backfill map for every retained/refactored table. For each table, link the reason for retention to a BR/FR/NFR or an explicit platform operation. Separate product-domain ERD from operational ledgers/legacy capability where that clarifies ownership. Do not delete the legacy data; any eventual removal remains separately approved.

**Evidence:** [SRS target counts and caveat](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:54); [register's retained/new table breakdown](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:185).

#### AUD-06 — Establish one canonical owner for duplicated state

The register correctly prohibits direct private-table coupling, but some facts appear in multiple records without fully specifying which record is authoritative and how projections stay current:

- class membership in `be1_managed_profiles.class_id` and `be1_enrollments`;
- Teacher successful sample in `lesson.occurrences.successful_sample_run_ref` and `story.runs.occurrence_ref`/success constraint;
- scene retry counts in `story.video_generation_scenes` and attempts in `ai_jobs.attempt`;
- result assets in `ai_jobs.job_result_assets`, `core_asset_metadata` and `core.asset_lineage`;
- existing BE1 consent records vs Parent-specific `parent.data_authorizations` (different scopes may be correct, but the scope split must be explicit).

**Recommendation:** For each pair, document canonical write owner, transaction boundary, event/projection direction, rebuild/reconciliation rule and deletion behavior. Keep only one counter/source for retries and one source for sample-slot consumption; other rows should be explicitly historical evidence or projections. Add concurrency tests for the cross-module invariants in the implementation plan.

**Evidence:** [profile and lesson/story data dictionary](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:231); [occurrence and run ownership](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:241).

#### AUD-07 — Revoke or cancel in-flight work when Teacher assignment is removed

BR-06/FR-T-14 revoke access when a Teacher loses class assignment. The SRS says subsequent reads/playback must re-check authorization, but does not fully specify what happens to an already-running Modal job, a late result, an unexpired playback token or the current run lock.

**Recommendation:** On assignment revocation, atomically deny new access, request cancellation if possible, invalidate grants, reject late completion and lifecycle-delete/quarantine unauthorized generated media. Define whether the run fails and whether a Teacher/admin may recover the occurrence. Preserve the user's rule that the former Teacher cannot access the run.

**Evidence:** [BR-06](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:124); [FR-T-14](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:317).

#### AUD-14 — Specify who sees the Teacher sample in the classroom

The SRS gives the creating Teacher private app access to a run and says an occurrence produces one representative child's sample video. It does not say whether the Teacher may present that individualized video to the whole class, to the selected child only, or to the child's parent. A private playback token prevents a public URL; it does not decide the intended audience of a classroom projection.

**Why it matters:** The video is based on one child's drawing, age/profile snapshot and potentially voice idea. Playing it to peers can reveal that child's work or personal context even when the model never receives the child's name. This is a product/permission question, not a request to restore classroom collaboration.

**Recommendation:** State the allowed playback audience and whether classroom display is an intended use. If class display is allowed, require a specific adult confirmation/authorization for that use, remove identifying narration/text, define who may initiate playback, and prevent other users from saving/accessing the underlying asset. Keep the existing one-child-per-run invariant.

**Evidence:** [SRS class/run access rule](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:124); [no export rule](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:143); [Teacher occurrence sample workflow](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:179).

### Medium priority / clarify before calling requirements closed

#### AUD-08 — Define sample-slot behavior for quality regeneration and deletion

The rules allow one initial video plus two completed quality regenerations inside a run, while saying one sample video per Teacher occurrence. That is consistent if the occurrence has one current/accepted output and regenerations replace it. The register stores a generation row per output, so there may be up to three physical videos. The run/slot behavior after deleting a completed run or after a quality regeneration fails technically is not explicit.

**Recommendation:** State that there is one current sample result per occurrence; previous generations are internal history and not additional samples. Define whether deleting the run leaves a non-content occurrence tombstone that keeps the sample slot used. Define whether a technically failed regeneration consumes a quality-regeneration count and whether the last output remains playable until a replacement passes all validations.

**Evidence:** [BR-10–17](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:128); [generation records](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:260).

#### AUD-09 — Guard model spend and queue backlog across many accounts

Per-adult request limits and one active run/account do not bound aggregate Modal cost across accounts. With the stated maxima, a run could require up to 15 scenes × 3 complete videos × 3 scene attempts = 135 scene-inference attempts in the worst successful retry pattern, plus VLM/LLM/ASR/TTS. The SRS records GPU seconds and resource ledgers but does not set an operator cap, organization budget, global concurrency ceiling, timeout budget or kill switch.

**Recommendation:** Keep the demo usable, but define configurable global Modal concurrency, per-run maximum GPU seconds, queue age/backlog limits, timeout and alert thresholds, and an operator kill switch. An organization/account soft quota can warn without blocking normal demos. Benchmark the actual end-to-end cost and latency before enabling multiple accounts.

**Evidence:** [scene/video attempt limits](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:129); [initial request limits](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:648).

#### AUD-10 — Complete billing-capacity state and business pricing

The product decisions establish 10 included slots and a configurable per-extra-slot monthly/yearly rate. The SRS correctly leaves actual VND prices and taxes open. The base monthly/annual amount is described as “may have a fee,” so whether the 10 slots are bundled/free or part of a paid base plan is still not decided. `capacity_periods.suspended_at_period_end` records a flag but the logical dictionary does not show a durable list/revision of which classes the admin selected to suspend. The exact billing admin/contact is represented as a reference but its assignment lifecycle is not described.

**Recommendation:** Before charging real money, define base-plan price semantics, the payment administrator assignment, the persistence of each selected class suspension and its effective date, invoice/e-receipt scope, taxes, proration period boundaries and cancellation/support policy. Provider recurring API availability does not replace merchant contract/sandbox validation.

**Evidence:** [price/subscription/capacity tables](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:267); [billing implementation gates](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1544).

#### AUD-11 — Tighten Parent activity relevance and reduce review friction

Parent currently gets a list of approved activities; approval ensures catalog safety, but does not itself make the list relevant to the child's age, chosen subject, interests, weather/setting or physical/accessibility needs. Parent and Teacher also pass through multiple review stages (transcript, subject, activity, context, script), which is safe but could feel long, especially on a phone or during a class session.

**Recommendation:** Add catalog metadata for age bands, setting, duration, accessibility/safety constraints and subject/theme tags; filter/rank only published activities while keeping the adult in control. For UX, combine related confirmations into a small number of screens, make optional voice/context genuinely optional, show understandable queue/wait/recovery, and perform short task-based usability sessions. Do not remove the owner-approved script gate.

**Evidence:** [Parent flow and gates](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:159); [catalog-only requirement](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:293).

#### AUD-12 — Make the implementation boundary and operating target explicit

The existing mobile app is a fixture-only harness, not a live product flow; the older `apps/ui-mobile` is only a behavior reference, and its integration notes say the current flow uses a single image picker, with camera/audio and persistent profile work not implemented. The current root Compose file only runs Postgres, Redis and MinIO. The target adds API, worker, observability, Mailpit and Teacher UI; production host/region/object store/email/SLO/RPO/RTO remain open.

**Recommendation:** Describe this as a port/rebuild from behavior reference into the current app, not a simple restoration. List exact screen/API cutover scope. Keep Compose as the local synthetic-demo topology. Before production, select cloud API/database/object storage, secret manager, email/alerts, data region, SLO, backup/restore objectives and a staged migration plan. Pin container images; the current root Compose uses `minio/minio:latest`.

**Evidence:** [current mobile fixture harness](../../../apps/mobile/README.md:53); [older flow integration limits](../../../apps/ui-mobile/BACKEND_INTEGRATION.md:108); [current Compose services](../../../compose.yaml:1); [production topology gate](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1324).

#### AUD-13 — Align document language and operational requirements

`CONTEXT.md` calls this a Vietnamese SRS, while the SRS artifact is written in English. This creates avoidable review friction for the owner. The data table register and SRS also use a provisional 88/123 count; that count must not be described as the live database count.

**Recommendation:** Either provide a Vietnamese owner-review edition or correct the context to the artifact's actual language. Keep the count qualified until a live schema inventory is performed. Before real data, map the system controls to current Vietnamese privacy requirements; Law 91/2025/QH15 took effect on 2026-01-01, so the existing real-data gate should reference a current compliance review rather than only a generic future checklist.

**Evidence:** [FEAT-063 context](../../../features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md:5); [SRS states no live DB inspection](../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:56).

## 5. Technology assessment as of 2026-10-27

| Choice | Assessment | Recommendation |
|---|---|---|
| React Native/TypeScript Parent + React/Vite Teacher | Matches current repository foundations and is a reasonable two-client setup. | Keep; invest in generated contract types and accessibility rather than framework churn. |
| Python/FastAPI/Pydantic/SQLAlchemy/Alembic modular monolith | Current, understandable, testable, and appropriate for the team's scope. | Keep the modular monolith. The source [`pyproject.toml`](../../../backend/pyproject.toml:10) permits Python 3.12 and 3.13, whereas the SRS names 3.12; document the tested runtime matrix. Python 3.12 is still supported but is in security-only maintenance as of the review date; consider 3.13 if model/library support is verified. |
| PostgreSQL 17 | Still supported and already used by the repository Compose file; not obsolete. PostgreSQL 18 is the current stable major as of this review. | Keep 17 if source/migration compatibility is the priority; otherwise test 18 before locking the target. In either case pin a supported minor image rather than an unqualified floating tag. |
| Redis 8 + RQ + PostgreSQL outbox | A reasonable small-system delivery design. The Postgres ledger/outbox prevents Redis from becoming the source of truth. | Keep only with idempotent dispatch, reconciliation, retention and worker failure tests; avoid adding a second workflow state authority. |
| MinIO local + Modal cloud inference | Appropriate for local demo plus cloud GPU, but the storage/network bridge is still unresolved. | Treat the synthetic transfer vertical slice as a gate before broader UI implementation. |
| Modal L40S for LTX-2.5 | Technically plausible: Modal lists L40S at 48 GB and recommends it as an inference starting point; LTX documents 32 GB+ minimum and recommends A100 80 GB/H100. LTX-2.5 supports 720p image-to-video clips and native multi-shot. | Keep as a POC choice, not a guaranteed capacity claim; benchmark cold-start, 720p scene latency, clip consistency, throughput and cost. Compare per-scene clips against LTX's native multi-shot option. Because the product adds its own TTS narration and disables music, set the provider's `generate_audio: false` explicitly so model-generated audio cannot leak into output. Pin the model revision, CUDA/image and license. |
| MoMo/VNPAY recurring payment | Not an outdated choice: official MoMo subscription docs and VNPAY recurring-payment technical specs exist. | Keep adapters; verify account eligibility, current signed callback/IPN contract, sandbox workflows, failure/reconciliation behavior and commercial approval. |
| OpenTelemetry + Prometheus + Grafana + Mailpit | Good local observability/testing stack for demo. | Keep locally; select production exporters, retention, access control and alert destination later. |

Official references: [Modal GPU guide](https://modal.com/docs/guide/gpu), [LTX system requirements](https://docs-dev.ltx.io/open-source-model/getting-started/system-requirements), [LTX 2.5 capabilities and supported durations](https://docs.ltx.io/models/ltx-2-5), [LTX model license](https://huggingface.co/Lightricks/LTX-2.5), [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/), [PostgreSQL current release notes](https://www.postgresql.org/docs/current/release.html), [Python version status](https://devguide.python.org/versions/), [MoMo subscription API](https://developers.momo.vn/v3/docs/payment/api/wallet/subscription/), [VNPAY recurring-payment specification](https://sandbox.vnpayment.vn/apis/files/VNPAYGW_RecurringPayment_Techspec2.1.0-VN.pdf), and [Vietnam Personal Data Protection Law 91/2025/QH15](https://vanban.chinhphu.vn/?docid=214590&pageid=27160&typegroupid=3).

## 6. Recommended order of work before implementation approval

1. Resolve BE1 age/class/consent canonicalization and single-role identity enforcement.
2. Add an explicit post-generation safety validation state before playback, without changing the no-human-video-approval rule.
3. Select and prove one bounded synthetic storage-to-Modal transport; set drawing byte/dimension limits.
4. Define canonical owners/projections for roster, sample slot, attempts, assets and consent records; map all 51 retained tables field-by-field.
5. Specify revoke-during-job, run/profile deletion, sample-slot tombstone, failed quality regeneration and active-run recovery semantics.
6. Set global GPU concurrency, cost alerts/cap, job timeouts, queue-age alert and an operator kill switch.
7. Align signup/role provisioning, billing base price/contact, class downgrade persistence, Parent activity relevance and owner-review language.
8. Run a synthetic vertical slice and usability session, then review measured performance/cost before authorizing the broader implementation/migration plan.

## 7. Review conclusion

The system direction is not fundamentally misguided. It is a sound starting architecture with a clear product flow, but the current table count and high-level diagrams should not be treated as implementation-ready schema. The next review should focus on the eight gates above, then update the SRS, register and proposed ADR together. Product rules explicitly answered by the owner remain unchanged unless the owner makes a new decision.
