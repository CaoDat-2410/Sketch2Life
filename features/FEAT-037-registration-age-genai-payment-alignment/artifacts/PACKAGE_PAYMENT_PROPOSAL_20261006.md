# Capstone-trial packages, payment and credits

- Status: OWNER_APPROVED_CAPSTONE_TRIAL_ASSUMPTION
- Prepared: 2026-10-06
- Currency: Vietnamese đồng (VND)
- Audience: children younger than 9 years; an adult is the purchaser and account holder
- Scope: product-documentation assumption for the capstone trial; no commercial launch or live payment integration is claimed

## Pricing comparison

Public prices are comparison points only; they do not establish Sketch2Life's costs or willingness to pay:

| Service | Publicly listed price observed on 2026-10-06 | Relevance |
|---|---:|---|
| eKids | 100,000 VND/month for an eKids monthly mobile package; its website also lists 250,000 VND for a one-month all-content package | Vietnamese children's learning app with free and paid tiers |
| Montessori Classroom, Vietnam App Store | Monthly options displayed at 129,000, 199,000 and 259,000 VND | Montessori-oriented mobile app in the same broad category |

Prices may change and features differ. These figures support only a capstone price comparison; they do not validate conversion, AI cost, taxes, payment fees, or classroom purchasing behavior.

## Approved capstone-trial packages

| Package | Trial price | Audience and limits | Monthly allowance |
|---|---:|---|---:|
| **Khám phá (Free)** | 0 VND | 1 child profile | 10 credits |
| **Gia đình** | 99,000 VND/month | Up to 3 child profiles; credits pooled across the household | 30 credits |
| **Lớp học** | 499,000 VND/class/month | 1 Guide/class; up to 25 assigned child profiles; credits pooled across the class | 120 credits |

## Approved one-time top-ups

| Pack | Trial price |
|---|---:|
| 10 credits | 49,000 VND |
| 30 credits | 129,000 VND |
| 60 credits | 239,000 VND |

Top-up credits are purchased separately from monthly allowances after a verified payment. The trial documents do not define expiration or rollover for unused monthly or top-up credits.

## Credit unit and lifecycle

One credit covers one complete adult-approved drawing/story experience, including standard AI outputs and the normal adult-approved off-screen activity handoff. Reserve one credit when the session starts; debit it once the experience reaches successful handoff. Release the reservation if the session fails or is cancelled. A retry within the same session is idempotent and does not consume another credit. Credit use is tied to the whole experience, not charged separately for each ASR, VLM, story, image, TTS, or video provider call.

Monthly credits are pooled only within the listed household or assigned-class scope. A backend-owned ledger records grants, reservations, commits, releases, top-ups, and idempotency references. Concurrent sessions must not spend the same balance twice.

## Payment and entitlement flow

1. An adult chooses a package or one-time top-up and sees the price, profile limit, included monthly credits, and current balance before checkout.
2. Paid monthly plans are renewed manually. The backend verifies a successful payment before activating the time-bounded entitlement and granting the monthly allowance or top-up credits.
3. The backend reserves, commits, or releases credits according to the session outcome. Duplicate payment notifications or session retries cannot grant or debit twice.
4. Mobile does not store raw card data or payment-provider credentials. The backend owns payment verification and credit accounting.

The payment provider and specific payment instrument have not been selected. This document does not authorize live billing. Cancellation, refunds/chargebacks, taxes, and provider transaction-state handling need a separate implementation specification. The trial prices have not been costed against a deployed model profile; measure cost per completed experience and payment fees before considering a commercial launch.

## Price rationale and product safeguards

- The 99,000 VND family price sits near the observed 100,000 VND eKids monthly tier and below the 129,000–259,000 VND Montessori Classroom monthly listings.
- The 499,000 VND classroom price and 120 credits/class/month model a single Guide with a bounded 25-child class. The reviewed sources offer no direct like-for-like comparator.
- The 49,000/129,000/239,000 VND top-up prices create a descending per-credit rate across the three pack sizes: 4,900; 4,300; and about 3,983 VND per credit. This is a capstone trial assumption, not validated unit economics.
- Safety rules, adult approval gates, child-data access, retention choices, and the off-screen activity handoff are the same across every package. A paid tier does not weaken child safety or privacy.

## Sources

- [eKids official pricing page](https://ekidsvn.edu.vn/pricing), accessed 2026-10-06.
- [Montessori Classroom listing on the Vietnam App Store](https://apps.apple.com/vn/app/montessori-classroom-ages-2-8/id1523888532), accessed 2026-10-06.
