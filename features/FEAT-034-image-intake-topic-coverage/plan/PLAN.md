# Feature plan

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Approval boundary: documentation and read-only diagnosis only; no implementation is authorized yet.

## Goal

Handle common static image inputs predictably and review/correct every active Montessori catalog mapping so a confirmed subject is connected to the complete, genuinely relevant age-appropriate activity list. A giraffe drawing must not produce “no activity” merely because `hươu cao cổ` was not mapped to the animal concept family. If no suitable reviewed activity truly exists, explain the actual reason and recovery path instead of reporting a generic empty result.

## Scope

### A. Image intake and actionable failures

- Audit the pinned Expo SDK 52 / `expo-image-picker` 16.0.6 behavior on Android and any other supported mobile platform. Treat URI, filename, byte size, dimensions, and MIME metadata as potentially absent or contradictory; identify format from bounded file content, not extension alone.
- Proposed input target: static JPEG, PNG, WebP, and HEIC/HEIF. Normalize supported inputs on-device to the existing backend JPEG/PNG contract, while preserving the selected original as the immutable session source and recording a derived-artifact reference, source hash, output hash, and normalization policy/version. If the pinned native decoder cannot safely read a format, do not claim support; show the exact unsupported-format guidance.
- Keep the existing backend admission ceiling (5 MB, 4 MP, 4,096-pixel longest edge, one static frame) unless measured device/runtime evidence and a separately reviewed policy change justify otherwise. Bound source bytes/dimensions before expensive decode; verify output bytes/dimensions after normalization. Preserve drawing detail and transparency where applicable; document quality trade-offs.
- Explicitly classify picker cancel, busy/duplicate selection, expired URI/access, unsupported format, animated/multi-frame media, oversized bytes, excessive dimensions, corrupt/truncated input, normalization failure, upload/network failure, and backend admission failure. Cancellation is silent and must not discard a previously valid selection. Errors must state what was rejected and what the adult can do next, without exposing URI/path, EXIF, credentials, or raw exceptions.
- Keep server reason codes typed through the versioned workflow result. Add a contract version only if the current public result cannot represent the required sanitized reason; do not infer errors from UI text or silently coerce MIME.

### B. Confirmed-subject normalization and activity coverage

- Expand the bounded, reviewed concept adapter for common Vietnamese/English animal names and synonyms (including `hươu cao cổ` / `giraffe`), mapping them to reviewed concepts such as generic animal/mammal without replacing the adult-confirmed display label. Keep synonyms deterministic and test polysemy/unknown subjects; no extra model call is required for known aliases.
- Audit and correct the full active catalog, not a sample: all 300 P1/semantic activity records and their user-visible cards, including all concept IDs, exact phrases/aliases/negative phrases, activity-family ownership, age-band variants, objectives, actions, material/safety metadata, and activity-to-topic links. Produce a row-level audit manifest with disposition (`KEEP`, `CORRECT`, `DEPRECATE`, `NEEDS_REVIEW`) and rationale; no record may silently retain an unreviewed mapping.
- Resolve the known taxonomy contamination: separate butterfly-only concepts from general animal observation/classification/movement, and ensure generic concepts do not make a species-specific card appear appropriate for a giraffe. Preserve valid multi-topic activities only when the activity objective/action genuinely supports each mapped concept.
- Build a coverage matrix by every reviewed topic family × four age bands × semantic relevance tier × displayability/safety. The complete-discovery endpoint must cover every relevant, displayable activity for the confirmed topic and exact age, then use confirmed child interests only to rank. Preserve existing adult/caregiver and safety/policy gates; do not reintroduce readiness/material questionnaires.
- Owner-confirmed recommendation policy (2026-09-30): show the complete eligible list and have AI rank/highlight three; never limit the screen to only three. First return/render the deterministic full list, then run one bounded asynchronous rank request over the complete eligible candidates. Deterministic topic/age/safety/policy eligibility runs first; the model may return only IDs from the server-recomputed reviewed eligible set, with a validated catalog-grounded reason, and may not invent, rewrite, or remove activities. If AI ranking is slow/unavailable, keep the safe full list visible and clearly say AI did not finish ranking. Do not automatically retry. This records a plan choice, not implementation approval.
- Do not increase catalog size merely to inflate counts. After all mappings are reviewed, add only reviewed records needed to close measured topic/age gaps. Candidate subject-grounded directions include observable animal features/adaptations, habitats/needs, classification, and life-cycle/observation work where age-appropriate. Keep the story centered on the pictured subject while explaining broader zoology connections. Every addition needs a learning objective, concrete child action, safe materials, age variant, provenance, and qualified Montessori review; no AI-generated catalog entries.
- Distinguish `TOPIC_UNMAPPED`, `NO_RELEVANT_ACTIVITY_FOR_AGE`, `RELEVANT_ACTIVITY_BLOCKED_BY_SAFETY_OR_ADULT_PRESENCE`, `CATALOG_CARD_NOT_DISPLAYABLE`, and backend/transport failure in sanitized response diagnostics. The UI must not describe a real service failure as “no activity”, or claim that the full matching list loaded when it is empty. Preserve confirmed topic/profile state and give a next action (e.g. edit/reconfirm topic, choose another topic, or retry a temporary failure).

## Steps

1. Freeze a synthetic, metadata-only baseline of current picker/admission behavior and enumerate image format/size/dimension/error boundaries. Do not copy user photos or child data into evidence.
2. Add a fixture-driven image admission/normalization matrix for JPEG, PNG, WebP, HEIC/HEIF, MIME/extension conflicts, missing metadata, broken files, animated inputs, access expiration, and each byte/pixel/edge boundary. Measure memory, latency, and visual fidelity on the actual supported mobile runtime before enabling a format.
3. Add a reviewed Vietnamese/English subject-alias/concept table and regression fixtures for giraffe, bird, butterfly, plant, multiple subjects, and unknown labels. Keep displayed topic claims grounded in Gate A/adult confirmation.
4. Review all 300 active catalog records and every user-facing card; produce a complete audit manifest, correct all inaccurate/missing/overbroad mapping, and run topic × four-age-band × safety/display coverage reports. Separately identify genuine content gaps and propose only qualified additions.
5. Implement the owner-selected two-stage behavior: return/render the complete deterministic list first, then request one bounded backend AI ranking of eligible IDs and highlight three without removing other entries. The backend recomputes eligibility against session version/catalog revision; mobile cannot inject IDs or criteria. Do not automatically retry. Preserve exact age and hard-safety filters, confirmed-interest semantics, and the selected recovery behavior.
6. Verify backend unit/contract suites, full-catalog lint/coverage reports with zero unreviewed rows, mobile validation/typecheck, Android emulator picker-to-recommendation happy path, and representative invalid-input paths. Record feature-local evidence and update status/context/decisions. Run repository security validation before any later commit/push.

## Acceptance criteria

- Static JPEG, PNG, WebP, and HEIC/HEIF either normalize and pass backend admission on each explicitly supported runtime or are clearly reported as unsupported. No format is declared supported on documentation alone.
- Corrupt, animated, inaccessible, oversized, excessive-dimension, conflicting-metadata, and transient-server cases have stable typed reason codes and concise actionable Vietnamese copy. No raw paths, EXIF, image bytes, child data, tokens, or exception tracebacks enter UI/logs/evidence.
- Selecting/canceling/rejecting an image does not silently erase the last valid selection or advance the workflow. Output respects current backend byte/pixel/edge/frame limits unless a separately approved change exists.
- `hươu cao cổ` and `giraffe` resolve to a reviewed animal concept without changing the confirmed topic label. Deterministic tests cover direct labels, aliases, tags, unknown labels, and four catalog age bands.
- The audit manifest accounts for 300/300 active catalog records and display cards. Every concept/tag has an approved definition and owner; no known cross-topic contamination remains; every correction/deprecation is tested and provenance-preserving.
- For tested giraffe scenarios with at least one approved, displayable, safe, age-fit animal activity, the endpoint returns a non-empty complete list (not top three), contains no unrelated species-only cards, and orders by confirmed interests without excluding by them.
- The AI rank request returns only existing, eligible catalog IDs; all highlighted activities pass deterministic age/topic/safety checks, reasons are grounded in catalog fields, the top-three display count is exact, and malformed/out-of-catalog model output is rejected. Catalog audit and alias tests do not depend on a live model.
- The full deterministic list becomes visible before the AI rank request completes. A valid rank highlights/reorders only the top three while preserving every other eligible activity; timeout/provider/invalid-output cases leave the full list intact, display the approved notice, and trigger no automatic retry.
- Catalog coverage report identifies, for every age band, valid animal-topic families and any genuine gaps. Any content additions have qualified review and provenance; counts are not an acceptance substitute.
- A genuine zero-match response states whether the topic mapping, age coverage, hard safety/adult requirement, card metadata, or service failed. UI copy/action matches the reason and does not misleadingly say “all activities loaded” in the zero-result state.
- Existing age boundaries, adult/caregiver participation, safety/policy gates, full-list behavior, session-only child profile, and topic/story identity pass regression tests unchanged.
- Android emulator evidence covers successful supported image selection through activity display and representative clear failures; evidence uses synthetic fixtures only and is stored under this feature.

## Risks and mitigations

- Native decoding varies by Android/iOS version and file provider. Maintain a runtime matrix and advertise only verified formats; cap original bytes/dimensions before decoding.
- Image re-encoding can blur pencil details or alter transparency/orientation. Keep the original immutable, compare normalized outputs visually with synthetic drawings, and record transformation metadata.
- Broadening concepts can create false-positive activities. Keep species-only concepts separate, use taxonomy lint and negative tests, and do not let interests override topic/age/safety constraints.
- Catalog expansion can add quantity without pedagogical fit. Require age-specific objectives and qualified review; expand only after alias/tag repair and measured coverage gaps.
- Reviewing 300 records can surface content needing Montessori expertise. Track unresolved pedagogical judgments explicitly and do not mark the catalog fully corrected until qualified review closes them.
- Diagnostics can leak data. Log only stage, bounded reason code, request/session correlation IDs already permitted by policy, and non-sensitive byte/dimension buckets; never log URI/path/EXIF or photo content.

## Verification plan

- Backend: image admission/normalization unit tests; workflow contract tests for every typed error and topic-empty reason; full 300-record mapping manifest validation, catalog lint, age/topic coverage audit, and (if approved) AI ranking/schema/session-version tests; existing topic, profile, and recommendation suites.
- Mobile: unit tests for metadata normalization, selected-source preservation, cancellation/busy behavior, error mapping, and image state; TypeScript and existing lint/test checks.
- Device: synthetic fixture matrix on the supported Android emulator plus a representative device/runtime when available; verify original rendering, upload, backend admission, Gate A, and full activity list. No real Lightning call is required for deterministic alias/catalog acceptance.
- Review: qualified Montessori reviewer signs off on new or materially changed activity content before `PRODUCTION_APPROVED`; product owner approves content/policy changes.
- Repository: `python tools/validate_repository_security.py` before any future commit/push.

## Evidence plan

Store only synthetic fixtures or fixture hashes, aggregate compatibility/performance results, test commands/output, sanitized reason-code traces, and review notes under `features/FEAT-034-image-intake-topic-coverage/evidence/`. Never store a user's drawing, child profile, URI, EXIF, provider output, secret, or account data.

Implementation is blocked until `approvals/TASK_APPROVAL.md` says `APPROVED` for this exact plan revision and hash.
