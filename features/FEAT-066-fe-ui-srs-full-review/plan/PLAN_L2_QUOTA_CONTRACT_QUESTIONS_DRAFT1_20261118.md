# FEAT-066 L2 — Quota: class capacity and video quota — contract questions — Draft 1

- **Status:** DRAFT / NOT APPROVED. Phase A design of `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` (SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`). Lists what the SRS already fixes and what must be decided before a contract plan can be written. Authorizes nothing.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2 (lane L2 is the owner's own work).
- **Owner choice (O-PAY, 2026-11-18):** the owner builds the contracts, the consumer ports and the Billing module itself, **except payment** (quote, invoice, checkout, MoMo/VNPAY callbacks, refunds). The payment teammate's work calls into Billing to activate paid slots and top-up grants after a verified payment event. This choice is recorded here only; it is not yet a decision row.
- **SRS basis:** adopted working SRS (701,157 bytes, `B9B1F42D...`, D-209). **Source fact:** no Billing code, table or migration exists in `backend/src` or `backend/alembic`.

## 1. Fixed by the SRS (no question needed)

| Topic | Requirement | Where |
|---|---|---|
| Capacity model | 10 base class slots per organization plus paid add-on slots in the period, minus classes suspended by an effective downgrade; only active classes within capacity are writable; suspended classes readable, read-only | §23.1 line 1861; FR-T-03 line 542 |
| Create-time check | transactional capacity check; 201 or `CLASS_CAPACITY_REACHED` (409) | §21.2 line 1649; §9.8 |
| Subscription states | GRACE 7 days after failed renewal: creation still allowed; RESTRICTED: no new class/run, existing data readable and manageable; CANCEL_AT_PERIOD_END | §23.3 lines 1877–1890 |
| Downgrade | Billing writes one `subscription_events` row per selected class with a shared change group; at the next period a versioned `CapacityClassSuspensionScheduledV1` event projects the classes read-only in BE1; idempotent retry; no history deleted | §23.4 lines 1892–1899 |
| Video-quota owners | Parent quota per Parent account; Teacher videos count against the organization of the occurrence; no Teacher pool; scope derived server-side | §23.5 line 1903 |
| Ledger | Billing owns `billing.video_quota_grants` (append-only entitlement) and `billing.video_quota_usage` (append-only, one unit per accepted full-video request, referencing the grant used); balance = grants − usage, computed only in Billing | §23.5 line 1904 |
| Included grant | monthly, per Parent account or school organization; full allowance in the first month (no prorate); expires at month end Asia/Ho_Chi_Minh; no carry-over; top-up (if enabled) used after included, FIFO, does not expire | §23.5 line 1905 |
| Admission | versioned Billing port inside the Story saga: `ADMISSION_PENDING` → compute reservation (AI Policy) → Billing checks scope/grant and writes usage in its own transaction → `ACCEPTED` or `ADMISSION_REJECTED`; no cross-module transaction; reconcile by the same idempotency key after crash | §23.5 line 1906 |
| No refund | once usage is committed the unit is never returned (failure, safety block, cancel, delete); same key returns the same usage; at most 1 first + 2 quality re-generations per run | §23.5 line 1907 |
| Exhaustion | `409 VIDEO_QUOTA_EXCEEDED`, no generation, no usage, no dispatch; playback and delete still allowed | §23.5 line 1908 |
| Read API | `GET /v1/video-quota`: granted/used/available and period, scope derived from the actor | §21.2 line 1678 |
| Separation | quota ≠ rate limit ≠ GPU/cost capacity | §23.5 line 1911 |

## 2. Questions for the owner (needed before a contract plan)

| ID | Question | Why it matters |
|---|---|---|
| Q-L2-1 | Billing module placement: a new bounded module (`billing` schema, own ports and adapters) inside the backend, alongside BE1 and Story? | Defines new paths for the allowlist; the SRS names the `billing.*` tables |
| Q-L2-2 | Capacity admission protocol for class create: synchronous Billing check inside BE1's create transaction via a port with a capacity version and a short-lived reservation, or a Billing-issued admission receipt that BE1 must present? (D-066-63 forbids a read-then-insert and direct reads of Billing storage) | Concurrency guarantee for "no over capacity" |
| Q-L2-3 | Public outcome when Billing cannot answer (fail closed is decided): status and code (503 with a dependency code is only a proposal), `retryable`, `Retry-After` | FE error state for class create |
| Q-L2-4 | Initial data: who creates an organization's subscription and its first capacity period in the product (Platform Admin action, a bootstrap, or the payment flow)? Until payment exists, is a synthetic ACTIVE subscription with 10 base slots acceptable for local and seed use? | Without it nothing can be admitted |
| Q-L2-5 | Monthly included video quota amount: the SRS says it is fixed after a synthetic cost/latency benchmark. Use a configurable placeholder value now? | Grants cannot be issued without a number |
| Q-L2-6 | Who issues the monthly included grant (scheduled job at month start, or lazily on first admission in the month)? | Ledger correctness at month boundaries |
| Q-L2-7 | Payment interface: which Billing commands the payment teammate calls (for example "activate add-on slots for period" and "issue top-up grant"), with which idempotency key (the payment event ID)? | Agreed contract between the two owners |
| Q-L2-8 | Video generation does not exist yet in this backend: is the video-quota admission port built now (with contract tests only) or only when the video flow is built? | Order of L2 work |
| Q-L2-9 | `GET /v1/video-quota` path prefix (`/v1` per SRS, or `/api/...` like the current routers) — part of the conventions decision O-CONV | FE path |

## 2A. Owner answers (2026-11-18, selections in the coordinating session; not yet decision rows)

| ID | Owner selection | Meaning for the contract plan |
|---|---|---|
| Q-L2-1 | "Module mới trong backend" | New bounded `billing` module in the backend (own schema, ports, adapters); BE1 and Story call it only through ports and never read its tables |
| Q-L2-2 | "Port giữ chỗ (reservation)" | Class create: BE1 asks Billing to reserve one slot (versioned, short expiry, organization-level lock in Billing), inserts the class, then confirms; on failure the slot is released. Concurrent creates cannot exceed capacity |
| Q-L2-3 | "503 BILLING_UNAVAILABLE" | Billing unreachable or indeterminate: no class created; HTTP 503, new code `BILLING_UNAVAILABLE`, `retryable=true`, `Retry-After` when known; the code is to be added to the SRS §9.8 table in a later SRS revision |
| Q-L2-4 | "Platform Admin + seed" | Platform Admin creates an ACTIVE subscription with the 10 base slots when creating an organization; the seed creates them for local use; paid add-on slots are activated later by the payment flow |
| Q-L2-5 | "Cấu hình, giá trị tạm" | Monthly included video quota is a versioned configuration value with a temporary number, to be fixed after the benchmark; the temporary number is set in the implementation task |
| Q-L2-6 | "Lười, lần dùng đầu" | The monthly included grant is created lazily by Billing at the first admission (or read) of the month, idempotent per scope and month; no scheduler |
| Q-L2-7 | "2 lệnh, key = payment event" | Billing exposes two commands to the payment work: activate add-on slots for a period, and issue a top-up grant; idempotency key = the verified payment event ID; to be shared with the payment teammate for agreement |
| Q-L2-8 | "Làm sổ + đọc trước" | Build the grant/usage ledger, the admission port with contract tests, and the read API now; connect the admission to the Story saga when the video flow is built |
| Q-L2-9 | "Theo slice quy ước chung" | The quota API prefix follows the conventions slice (O-CONV) |

## 3. Next artifacts

With the answers above: a Billing contract plan (tables, ports, events, idempotency, errors), then a capacity-admission slice plan (MGR-2 rewrite against the adopted SRS) and a video-quota slice plan, each with its own review and Task Approval. Payment-side commands are specified only as the interface the payment teammate calls.
