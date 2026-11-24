# B29 — Proposed School-level Billing Change Request

**Status: PROPOSED — every package price, quota and add-on value below is a proposal candidate, not approved product pricing.** This addendum is separate from the owner-approved SRS v3.3/B28 baseline. The owner's selection of 999,000 VND/month authorizes recording that candidate in the Review 2 materials only; it does not adopt billing or any amount into the product baseline, or authorize implementation, merchant onboarding, a live transaction, or release.

## B29.1 Product context and boundary

Sketch2Life is a collaborative creative learning platform for children aged 3–12, inspired by Montessori, Reggio Emilia, and social constructivist learning. This is the owner's English product-positioning statement. The registration v1.2 and SRS v3.3/B28 target is 36–155 completed months inclusive. The repository currently contains conflicting backend age guards: `validate_age_months` accepts 36–155, while `supported_child_age_band` caps at 107 months. Full 9–12 implementation support is therefore not claimed; the age-policy mismatch needs cross-feature reconciliation and evidence.

The owner chose to reuse the **existing Teacher Desktop** and **Super Admin Portal**. No new role, separate portal, or standalone UI is proposed. Teacher Desktop gains a Subscription & Billing section for current plan, upgrade/renewal, add-ons, payment and transaction history. The Super Admin Portal gains Billing Management for plans, add-ons, school subscriptions, transactions and revenue views. A proposed `billing:manage` permission lets designated Teachers manage billing for their school; other Teachers can see plan and usage read-only. Candidate payment routes are MoMo, VNPay and VietQR. Child Android must not initiate checkout, show a payment button, link to an alternate payment method, or use payment prompts targeted at a child.

**School-level ownership:** Subscription, payment, add-on, entitlement and shared credit balance records attach to `school_id`, not an individual Teacher. A Teacher with `billing:manage` acts for the school; the permission is not a new role. All of this is proposed and depends on confirming the current school/membership contract.

**Baseline boundary:** B28 remains the active product policy baseline. Billing, credits, Teacher Desktop/Super Admin billing surfaces, provider integrations and numeric price/quota options below are not part of that baseline. This change request awaits owner approval, platform-policy review and a separately approved implementation feature/ADR.

## B29.2 Proposed package and add-on pricing

The owner selected Option B's school-level scope and chose 999,000 VND/month as the Plus price candidate to carry in this proposal. The previous 499,000 VND candidate is superseded. Every Sketch2Life amount and quota in the table remains PROPOSED and must be reviewed before baseline adoption or checkout; no amount is approved for sale.

| Item | Proposed price and included quantity | Billing scope | Status |
|---|---|---|---|
| Free Trial | 14 days, up to 2 classes, 100 shared AI credits, no payment method; one trial per `school_id` | School | PROPOSED candidate; trial duration and eligibility are TBD |
| Plus | 999,000 VND/month; up to 10 active classes, 10 Teacher seats, 500 shared AI credits | School | PROPOSED price and entitlement candidate; not approved for sale |
| Additional class | +1 active class for 99,000 VND/month | School | PROPOSED price candidate; monthly recurring while active |
| Additional Teacher seat | +1 active Teacher account for 49,000 VND/month | School | PROPOSED price candidate; `billing:manage` remains a permission, not a paid role |
| AI credit top-up S | 100 shared credits / 149,000 VND, one-time | School | PROPOSED price and quota candidate; expiry TBD |
| AI credit top-up M | 300 shared credits / 399,000 VND, one-time | School | PROPOSED price and quota candidate; expiry TBD |
| AI credit top-up L | 700 shared credits / 799,000 VND, one-time | School | PROPOSED price and quota candidate; expiry TBD |

One Teacher seat means one active Teacher account assigned to the school; Super Admin is not a purchased school seat. Class and Teacher add-ons are recurring school entitlements. AI-credit top-ups are one-time school-shared purchases. Mid-cycle proration, add-on expiry, whether monthly credits roll over, renewal/cancellation and school eligibility remain OPEN_TBD. Additional storage/video quota is not priced in this proposal because storage/provider costs and corresponding product limits have not been validated.

Pricing comparison checked 2026-10-25: Klassi lists a free one-class option, a Solo offer around 250,000 VND/month, and an AI offer around 500,000 VND/month; its Solo plan add-on is about 85,000 VND per extra class slot/month (up to three extra slots). eKids lists a monthly content plan at 250,000 VND. The App Store listing for Draw to Life describes USD 9.99/month for 40 credits and USD 3.99 credit packs. These are observed third-party reference prices, not Sketch2Life pricing. The products differ in buyer, channel, AI operation, credit definition and included services; they do not establish Sketch2Life unit economics. The 99,000 VND/class add-on is a proposed candidate near Klassi's public class-slot price; Teacher-seat and AI top-up amounts remain internal proposal hypotheses without a direct comparable. [Klassi pricing](https://klassi.vn/pricing), [Klassi extra class slot](https://klassi.vn/help/vi/giao-vien/25-mua-them-slot-lop), [eKids pricing](https://ekidsvn.edu.vn/pricing), [Draw to Life App Store listing](https://apps.apple.com/vn/app/draw-to-life-ai-art-for-kids/id6752760587?platform=ipad).

### Proposed credit unit

For the pricing proposal, one credit covers one successful AI creation request; a technical failure/retry must not be charged twice. The exact billable action and treatment of Teacher-rejected outputs remain OPEN_TBD and must match the current AI workflow and measured provider cost. The school owns the shared monthly and top-up pools; authorized Teachers may use them within that school's classes under approved controls. Reservation, commit, release, expiry, rollover and refund/reversal rules still require owner decision.

## B29.3 Proposed architecture and technology fit

Proposed flow: Teacher Desktop authenticates the adult. The API verifies school membership and `billing:manage` before permitting purchase, renewal or add-on actions. It validates the school-level plan and idempotency key, then creates a payment attempt. Application-owned `PaymentGatewayPort` adapters encapsulate MoMo/VNPay integrations and a bank/acquirer or gateway route for VietQR. The backend alone stores provider credentials in an approved runtime secret manager. The browser receives only a hosted payment URL or short-lived QR/payment instructions; it never receives a provider secret. Super Admin uses the existing administrative portal to manage catalogs and reconcile school accounts under separate privileged authorization.

After payment, a provider server callback/IPN is signature/hash-verified, matched to the server's partner account, order, amount and currency, and processed idempotently. An atomic PostgreSQL transaction records the verified payment result and grants the associated Teacher/class entitlement and credit-ledger entry exactly once. Redirect/browser state is informational; it cannot grant quota. A scheduled reconciliation/worker may query pending transactions and resolve missing callbacks under a separately approved operational profile. Proposed persistence can use the existing PostgreSQL/SQLAlchemy/Alembic family after the migration-owner and lineage gates are closed. No new framework, payment library, queue or storage vendor is selected here.

VietQR is treated as a QR-based payment initiation/confirmation route provided through a participating bank, acquirer or gateway. A static QR image or screenshot of a bank transfer is not proof of payment. The chosen partner must provide a trustworthy transaction notification or reconciliation interface before automatic entitlement grant is designed.

| Layer | Proposed responsibility | Current status |
|---|---|---|
| Existing Teacher Desktop | Subscription & Billing section for plan, upgrade/renewal, add-ons, checkout status and history; `billing:manage` gates actions | Reuse existing surface category; proposed screens and permission are not implemented |
| Existing Super Admin Portal | Billing Management for plan catalog, add-ons, school subscriptions, transactions and revenue views | Reuse existing surface category; billing module is not implemented |
| FastAPI application | Verify school membership and billing permission; plan catalog, checkout intent, payment status, school entitlement and shared usage/credit ledger | Proposed B29 capability; no billing routes or service are accepted |
| Payment adapter port | Normalize create/callback/query/refund outcomes without provider leakage into domain rules | Proposed only |
| Provider/bank adapters | MoMo, VNPay and one participating VietQR bank/acquirer route; verify signatures and reconciliation results | No merchant account, credentials or provider implementation selected |
| PostgreSQL ledger | Append-only payment/credit journal; school-keyed subscription/entitlement and shared balances; transactional idempotent grant/reservation/commit/release | No B29 migration/model or approved migration root exists |
| Child Android | Consume only existing entitled, Teacher-approved classroom experiences; no purchase entry point or payment prompts | No payment feature is implemented |

Billing records should reference `school_id`, authorized adult actor, school membership and order metadata. Every subscription, add-on and shared entitlement/credit balance is school-owned even when a Teacher initiated the transaction. Do not send child names, artwork, audio, prompts, transcripts, age, consent evidence or session content to payment providers. Entitlement and credit history are separate from child session/artwork history and follow a separately approved retention/accounting policy.

### Proposed sequence / payment states

Candidate payment-attempt states are `CREATED → PENDING → PAID_VERIFIED` or `FAILED`, `CANCELLED`, `EXPIRED`, and `RECONCILIATION_REQUIRED`. `PAID_VERIFIED` is a server-side state only, reached after validated provider evidence; the entitlement/credit grant is a separate idempotent ledger effect. Duplicate callback: no second grant. Browser return before callback: remain Pending and poll/query safely. Callback with mismatched signature/order/amount/currency: reject or quarantine for review; never grant. Unknown QR transfer: remain Pending until bank/gateway reconciliation confirms it.

## B29.4 Proposed functional requirements

All IDs below use the `PFR-B29-*` namespace and remain `PROPOSED`.

| ID | Proposed requirement | State / verification candidate |
|---|---|---|
| PFR-B29-01 | Teacher Desktop shall display Free Trial, Plus and add-on quota options with currency, school-level included quota, billing interval, expiry, renewal and cancellation terms before confirmation. | PROPOSED; review terms before adult confirmation |
| PFR-B29-02 | Only an authenticated adult Teacher with `billing:manage` and verified membership in the target `school_id` may create or manage a school checkout; other Teachers are read-only. | PROPOSED; deny missing permission, school mismatch and cross-school IDs |
| PFR-B29-03 | The service shall create an idempotent checkout/payment attempt for the selected offer and return only a safe provider redirect or payment instruction. | PROPOSED; retry same key creates no duplicate order |
| PFR-B29-04 | Teacher Desktop shall offer only provider routes enabled for the school: MoMo, VNPay, or the approved participating-bank/acquirer VietQR route. | PROPOSED; unavailable routes are not shown as usable |
| PFR-B29-05 | The backend shall verify callback signature/hash, merchant/account, order reference, amount, currency, state and transaction uniqueness before marking payment as paid. | PROPOSED; tampered/mismatched callbacks never grant |
| PFR-B29-06 | A verified successful payment shall atomically create the entitlement/credit ledger grant at most once; a redirect alone shall never grant value. | PROPOSED; duplicate/reordered callback and race tests |
| PFR-B29-07 | The Teacher shall be able to refresh/query a payment attempt and view a safe receipt, including Pending/reconciliation status when outcome is uncertain. | PROPOSED; browser closure does not lose server status |
| PFR-B29-08 | The system shall preserve payment/credit audit history and provide an authorized reconciliation view without exposing child content. | PROPOSED; role, purpose and access audit checks |
| PFR-B29-08A | Super Admin shall manage the plan/add-on catalog and review school subscriptions, transactions and reconciliation status through the existing Super Admin Portal. | PROPOSED; privileged actions audited |
| PFR-B29-08B | Subscription, add-on purchase, entitlement and shared credit-balance records shall attach to `school_id`, not to an individual Teacher account. | PROPOSED; verify school ownership across lifecycle and teacher changes |
| PFR-B29-08C | A Teacher with `billing:manage` may purchase school-scoped add-ons for active classes, Teacher seats and shared AI credits; the system shall show price, billing cycle and new limit before confirmation. | PROPOSED; no child-facing checkout and no silent auto-purchase |
| PFR-B29-09 | Child Android shall not provide checkout, external payment links, paywall prompts or child-directed upsell; paid access cannot bypass Teacher review or child-safety rules. | PROPOSED non-negotiable safeguard; negative UI/route tests |
| PFR-B29-10 | When credits are consumed, the service shall apply the owner-approved usage unit and reserve/commit/release/refund policy with idempotent results. | PROPOSED; usage unit and exception policy remain owner TBD |

## B29.5 Proposed non-functional requirements

All IDs below use `PNFR-B29-*`; acceptance thresholds must be set after an implementation design and business review.

- **Security:** TLS in transit; provider credentials and signing keys only in server-side secret management; validate callbacks using the exact provider-signed canonical input; rotate credentials; restrict callback routes; enforce authorization server-side; protect against replay and request forgery. Never log secrets, full callback signatures or unnecessary payer identifiers.
- **Integrity/idempotency:** duplicate, delayed, reordered or concurrent callbacks must not double-grant entitlement or credits. Payment state, ledger entry and entitlement change must be atomic or recoverable through an idempotent outbox/worker. Return success to the provider only when its callback acknowledgement contract is satisfied.
- **Privacy/child safety:** collect the minimum adult purchaser and billing data required; keep child media/session data out of payment requests, receipts, support logs and analytics. No behavioral advertising, child-targeted purchasing prompt, ranking, diagnosis, or purchase-based bypass of age/content/safety gates. Teacher review and child hide/decline controls remain unchanged across every plan.
- **Transparency and control:** show total price and currency, quota, plan scope, billing period, renewal mode, trial end/expiry, top-up expiry, cancellation/refund rules, and any restrictions before the adult confirms. Provide accessible Vietnamese-first, keyboard/screen-reader-friendly controls and a clear pending state.
- **Availability/recovery:** a provider timeout or lost redirect must not misstate success/failure; provide a safe Pending state, bounded retries, status query/reconciliation and support reference. Define recovery targets and provider-specific timeouts before implementation.
- **Audit/retention:** record adult actor, class/organization scope, offer version, order ID, verified status, ledger grant and reconciliation/refund actions; redact IP/device fields as policy requires. Retention, accounting evidence, data subject requests and backup copies remain subject to a documented policy and qualified review.
- **Performance/cost:** latency, callback acknowledgement, reconciliation interval, uptime, cost ceiling, model-use budget and max concurrent purchases are OPEN_TBD; do not claim measured capacity from the 40-child pilot target.

## B29.6 Business rules and exception handling

| Rule / exception | Required proposed behavior | Current status |
|---|---|---|
| Adult purchaser | Teacher with `billing:manage` only; verify school membership and `school_id` server-side. Other Teachers may view plan/usage but cannot buy or change billing. | Proposed; permission assignment and school identity contract not reviewed |
| School-wide entitlement | Subscription and shared quota belong to one `school_id`; eligible classes in that school draw from its governed balance. | Proposed; multiple-school membership, cross-school use and school-transfer rules OPEN_TBD |
| Super Admin action | Plan catalog, add-ons, subscriptions and reconciliation use the existing Super Admin Portal with separate privileged authorization and audit. | Proposed; no additional role or standalone admin UI |
| Offer/price changed after checkout | Persist offer/price/currency snapshot on the order; callback must match stored order amount | Proposed |
| Duplicate checkout request | Idempotency key returns the same order while valid; no second charge intent | Proposed |
| Provider timeout / browser closed | Keep `PENDING`; do not grant; query/reconcile server-side and let Teacher refresh status | Proposed |
| Invalid signature/hash | Reject callback, keep value ungranted, emit redacted security event and reconciliation alert | Proposed |
| Order, amount, currency or merchant mismatch | Quarantine/mark `RECONCILIATION_REQUIRED`; do not grant or silently rewrite the order | Proposed |
| Duplicate callback / replay | Return provider-appropriate acknowledgement after idempotent no-op; grant once | Proposed |
| Late callback after cancellation/expiry | Reconcile against provider transaction state; do not auto-grant or discard a real captured payment; create operator case | Proposed; recovery/refund policy TBD |
| Payment paid but ledger grant failed | Durable retry/outbox or reconciliation repairs the grant once; receipt shows pending fulfillment until repaired | Proposed |
| Failed, declined or cancelled payment | No entitlement/credit grant; preserve safe reason category and retry option | Proposed |
| QR expired, wrong amount or unmatchable transfer | No screenshot-based credit; remain pending or require manual reconciliation and documented refund path | Proposed |
| Refund, reversal or chargeback | Keep payment, refund and consumed-credit entries immutable; apply approved compensation policy; never silently delete history or claw back active child work | Policy OPEN_TBD |
| Insufficient credits / concurrent use | Reserve/debit under an atomic balance guard; reject safely without partial work or negative balance | Proposed |
| School resource limit reached | Block creation/activation beyond the paid class or Teacher-seat limit; show the upgrade/add-on action only to an authorized adult with `billing:manage`. Never block a child's in-progress work solely to prompt an upgrade. | Proposed; show read-only limit to other Teachers |
| Plan expires or is cancelled | Show entitlement and renewal state to adult Teacher; never interrupt a running child safety/review gate; downgrade timing and access grace are OPEN_TBD | Proposed |
| Provider unavailable | Hide/disable only that route; retain offer and other safe options; do not say payment succeeded | Proposed |

## B29.7 Child, AI, privacy and platform-policy review gates

This is a source-based issue checklist, not a legal opinion or compliance statement. Before implementation or sale, qualified counsel and platform-policy review must determine whether the service, child-data flows, web checkout, billing model and payment roles trigger specific obligations. The official National Assembly law records list the Vietnam Personal Data Protection Law 91/2025/QH15 (effective 2026-01-01), AI Law 134/2025/QH15 (effective 2026-03-01), and E-commerce Law 122/2025/QH15 (effective 2026-07-01); the National Assembly's consolidated Consumer Protection law text 47/VBHN-VPQH is dated 2026-03-17. Applicability, notices, records, consent, consumer terms, invoicing/tax and dispute duties require qualified review against the complete statutes and actual service model. [PDP Law](https://vanban.chinhphu.vn/?docid=214590&pageid=27160), [AI Law](https://vanban.chinhphu.vn/?classid=1&docid=216334&pageid=27160), [E-commerce Law](https://vanban.chinhphu.vn/?classid=1&docid=216503&orggroupid=1&pageid=27160), [Consumer Protection consolidated text](https://vanban.chinhphu.vn/?classid=2629&docid=217232&pageid=27160).

The UNICEF Guidance on AI and Children v3.0 is non-binding guidance; use it to review child safety, privacy, fairness, transparency/accountability, best interests, development, well-being and inclusion. Payment must not become an incentive to increase AI use, weaken teacher review, collect more child data or target a child's behavior. [UNICEF Guidance v3.0](https://www.unicef.org/innocenti/reports/policy-guidance-ai-children).

Google Play policy says Play-distributed apps generally must use Google Play Billing for in-app digital goods/services, subscriptions and virtual currency unless a stated exception/program applies. Because school-level credits could be consumed in Child Android after an adult Teacher purchases through Teacher Desktop, the team must receive a written platform-policy assessment for the exact app distribution, buyer and consumption model before enabling this design. No payment link or alternate-purchase prompt is to be shown in Child Android while that review is open. [Google Play Payments policy](https://support.google.com/googleplay/android-developer/answer/9858738?hl=en), [Understanding Payments policy](https://support.google.com/googleplay/android-developer/answer/10281818?hl=en).

Provider references establish technical verification duties, not merchant readiness: MoMo's notification guide requires signature validation and recommends matching partner code, order ID and amount against the merchant database; VNPay documentation describes secure-hash/IPN processing; NAPAS describes VietQRPay as a participant-institution service. The team must contract with an approved provider/acquirer, obtain official current integration/fee/refund specs, and perform sandbox reconciliation before selecting an adapter. [MoMo IPN](https://developers.momo.vn/v3/docs/payment/api/result-handling/notification/), [VNPay secure-hash/IPN docs](https://sandbox.vnpayment.vn/apis/docs/chuyen-doi-thuat-toan/changeTypeHash.html), [NAPAS VietQRPay](https://developer.napas.com.vn/vi/product/introduce/viet-qr-pay).

## B29.8 Owner decisions required before baseline adoption

1. Are the proposed additional class (99,000 VND/month) and Teacher seat (49,000 VND/month) prices acceptable?
2. Are the top-ups 100/149k, 300/399k and 700/799k acceptable? What are the expiry and monthly rollover rules?
3. Are the shared-school Free Trial terms (one per school, 14 days, up to 2 classes, 100 credits) and included 10 Teacher seats acceptable, or what should change?
4. Is one credit one successful AI creation request? How should Teacher-rejected outputs, failed generation, reservation, release and refund be handled?
5. Who assigns/revokes `billing:manage`; how should one school be identified when a Teacher belongs to multiple schools or has no school membership?
6. What are renewal, cancellation, trial-end, upgrade/downgrade, refund, payment dispute and chargeback policies?
7. Which merchant/provider/acquirer will contract for MoMo/VNPay/VietQR; what are current fees, transaction limits, refund APIs, settlement/reconciliation and data-processing terms?
8. Is a Teacher Desktop purchase that unlocks school-shared credits consumed in a Play-distributed Child Android app permissible under the exact Google Play policy/exception, or must the product use a different billing design/distribution model?
9. Which legal entity, tax/VAT, invoice, e-commerce notices, consumer service and dispute processes apply? Obtain counsel/accounting determination.
10. What privacy impact, adult verification, retention/accounting record and access/audit review is required before payment or child data is processed?

## B29.9 Proposed verification and adoption gates

Before product-baseline adoption: owner resolves the commercial decisions; legal/accounting counsel reviews applicable laws and consumer terms; the distribution/platform owner signs off on Google Play treatment; provider/acquirer terms and fees are available; security reviews key custody/callback/IPN; finance confirms refund/reconciliation policy; cost-per-experience and quota behavior are measured without real child data. Only then should a separate ADR and implementation plan define versioned contracts, schema/migrations, UI and release criteria. No B29 requirement is currently implemented or verified.
