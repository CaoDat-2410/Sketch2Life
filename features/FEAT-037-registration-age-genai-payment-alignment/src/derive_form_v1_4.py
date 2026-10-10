from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from docx import Document

SOURCE_SHA256 = "588E602A9EA1614C205EF696439C44CA5B5FAC089818C4239AB709077979CCAE"

REPLACEMENTS = {
    "VERSION 1.3 — REVIEW DRAFT": "VERSION 1.4 | CAPSTONE TRIAL PACKAGES, CREDITS AND PAYMENT",
    "Proposed packages and payment are described separately and remain subject to owner approval.": (
        "Build Sketch2Life as an adult-supervised flow in which a drawing and the child's own description "
        "are transformed into a Montessori activity. The system validates the media, combines image and "
        "narration, opens an adult understanding review, and returns the complete reviewed activity set "
        "matching the confirmed topic and exact product age. It enforces active catalog status, safety/policy "
        "and required-supervision constraints; adult-confirmed interests may order or explain eligible matches. "
        "Readiness, prior work, prerequisite sequence and material availability do not hide an eligible match. "
        "An adult approves the selected activity and learning objective. The flow then provides source-derived "
        "PixiJS exploration and an age-aware illustrated story experience before handing the child off to the "
        "approved physical activity. The capstone trial includes Free, Gia đình, and Lớp học packages, "
        "one-time credit top-ups, and adult-managed payment and credit accounting."
    ),
    "Proposed for review: let the adult Owner Caregiver compare package price, profile limits and monthly credit allowance and manage purchase/entitlement for the household. Final terms require owner approval.": (
        "•\tLet the Owner Caregiver compare the Free, Gia đình, and Lớp học packages, see prices, profile limits "
        "and monthly credit allowances, make a manual monthly payment or buy a one-time top-up, and manage "
        "household entitlement and balance."
    ),
    "Proposed payment and credit flow are described in section 3.2(h); they are not approved product requirements.": (
        "•\tPayment and credit behavior follow section 3.2(h)."
    ),
    "Proposed for review: after approval, administer versioned package prices, monthly credit allowances, top-up terms and time-bounded entitlements, with payment status visible without exposing provider credentials or raw card data.": (
        "•\tAdmin can manage time-bounded package entitlements and view payment status. Authorized adults can see "
        "their credit balance without exposing provider credentials or raw card data."
    ),
    "(Proposed, subject to owner approval) Package and Credit Rules: adult-facing package comparison, profile limits, monthly credit allowances, payment verification and time-bounded entitlement concept; provider, top-up size/price, rollover, billing, tax, renewal, cancellation and refund rules remain open.": (
        "-\tPackage and Credit Rules: adult-facing package comparison, profile limits, monthly credit allowances, "
        "the listed one-time top-up packs, backend-verified payment, time-bounded entitlements, and auditable "
        "credit reservation and settlement."
    ),
    "Package/payment and entitlement rules are proposed for owner review and are not approved implementation scope.": (
        "-\tWP2 - Backend, Identity, Curriculum Services and Recommender: Adult authentication, ChildProfile "
        "ownership, Guide assignments, consent, contracts, complete-set topic-and-age activity discovery with "
        "interest-based ordering, retention, deletion and operations. Defines the capstone-trial package, "
        "payment-verification, and credit-entitlement requirements."
    ),
    "h) Proposed Packages and Payment (Owner Review Draft)": (
        "h) Capstone Trial Packages, Credits and Payment"
    ),
    "The options below are provisional hypotheses for owner review, not approved prices, monthly credit allowances, entitlements or a decision to launch payments. They require validation against operating cost and feedback from families and Montessori Guides.": (
        "The following package prices, monthly allowances, and top-up packs are the assumptions used in the "
        "capstone trial. An adult is the purchaser; child experiences remain supervised under the same safety, "
        "privacy, and adult-approval rules."
    ),
    "Proposed credit mechanic: one credit covers one complete drawing/story experience, including its standard required AI outputs and normal adult-approved off-screen handoff. Reserve one credit when a session starts and debit it only after the approved experience completes its handoff. Release the reservation for a failed or cancelled session; retries within the same session do not consume extra credits. Included credits are pooled within a household or class and allocated monthly. Optional one-time top-ups may be offered after the balance is exhausted, but pack sizes/prices, unused-credit rollover/expiry and detailed balance rules remain open; no automatic top-up is proposed.": (
        "Credit rule: one credit covers one complete adult-approved drawing/story experience, its standard AI "
        "outputs, and the off-screen activity handoff. Reserve one credit at session start and debit it only "
        "after successful handoff; release it after failure or cancellation. Retries within the same session do "
        "not consume another credit. Monthly credits are pooled within a household or class. Adults may buy "
        "one-time top-ups: 10 credits for 49,000 VND, 30 for 129,000 VND, or 60 for 239,000 VND."
    ),
    "Proposed payment flow: an adult purchaser reviews the price, billing period, profile limit, monthly included credits, current balance and renewal terms. The backend verifies payment before granting a time-bounded package entitlement. It reserves/commits/releases credits idempotently with session outcome. Monthly manual renewal is the starting proposal. Auto-renewal, provider/method, cancellation, failed payments, refunds/chargebacks, taxes, optional top-up packs, rollover/expiry, and final entitlement behavior remain open decisions.": (
        "Payment flow: an adult sees the package price, billing period, profile limit, included monthly credits, "
        "and current balance before checkout. Paid monthly plans renew only when the adult makes the next "
        "manual payment. The backend verifies payment before granting a time-bounded package entitlement or "
        "top-up credits, and records credit reservations and settlement idempotently. Children cannot purchase "
        "packages or top-ups. Mobile does not store raw card data or payment-provider credentials."
    ),
    "Candidate package prices and monthly credit allowances in section 3.2(h) are review proposals only; provider, top-up, billing, rollover and entitlement terms require owner decisions.": (
        "-\tThe current product age target is under 9 years (0–107 completed months); 9–12 catalog records "
        "remain outside current product-session scope. The target includes the knowledge base, multimodal "
        "understanding, topic-and-age activity discovery, activity delivery, Guide Console, Parent Web, PixiJS "
        "exploration and age-aware illustrated story/video flow. Section 3.2(h) specifies the capstone-trial "
        "package prices, monthly credits, one-time top-ups, and payment/credit flow. The project uses manual "
        "monthly renewal and server-side payment confirmation; provider integration and commercial rollout "
        "are outside this capstone trial scope."
    ),
    "-\tProposed Payment Safety: Any future payment uses an adult purchaser and a backend-verified entitlement; provider credentials and raw card data are not stored in the mobile app. Provider, payment method and billing rules remain undecided.": (
        "-\tPayment Safety: Every purchase is initiated by an adult and verified by the backend. The mobile "
        "app never stores provider credentials or raw card data."
    ),
    "All packages retain the same under-9 eligibility, adult approval, content/activity safety, consent, access, retention and deletion protections. A higher tier changes only the proposed profile/session limits; it does not relax child-safety or privacy requirements.": (
        "All packages retain the same under-9 eligibility, adult approval, content/activity safety, consent, "
        "access, retention and deletion protections. Higher tiers change only profile limits and credit "
        "allowances; they do not relax child-safety or privacy requirements."
    ),
    "Illustrative comparison anchors checked 6 October 2026 (not validation of Sketch2Life cost or willingness to pay): eKids public pricing lists VND 100,000/month; Montessori Classroom (Vietnam App Store) lists monthly options of VND 129,000, 199,000 and 259,000.": (
        "Pricing references, checked 6 October 2026: eKids public pricing lists VND 100,000/month; Montessori "
        "Classroom (Vietnam App Store) lists monthly options of VND 129,000, 199,000 and 259,000."
    ),
}


def set_paragraph_text(paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def set_pricing_reference_paragraph(paragraph) -> None:
    hyperlinks = [child for child in paragraph._p if child.tag.endswith("}hyperlink")]
    if len(hyperlinks) != 2:
        raise SystemExit(f"Expected two source hyperlinks in the pricing paragraph; found {len(hyperlinks)}")
    paragraph.clear()
    paragraph.add_run("Pricing references (checked 6 October 2026): ")
    paragraph._p.append(hyperlinks[0])
    paragraph.add_run(" lists VND 100,000/month; ")
    paragraph._p.append(hyperlinks[1])
    paragraph.add_run(" lists monthly options of VND 129,000, 199,000 and 259,000.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    input_hash = hashlib.sha256(args.input.read_bytes()).hexdigest().upper()
    if input_hash != SOURCE_SHA256:
        raise SystemExit(f"Unexpected v1.3 input SHA-256: {input_hash}")

    document = Document(args.input)
    for needle, replacement in REPLACEMENTS.items():
        matches = [p for p in document.paragraphs if needle in p.text]
        if len(matches) != 1:
            raise SystemExit(f"Expected one paragraph containing {needle!r}; found {len(matches)}")
        if needle.startswith("Illustrative comparison anchors"):
            set_pricing_reference_paragraph(matches[0])
        else:
            set_paragraph_text(matches[0], replacement)

    if len(document.tables) != 4:
        raise SystemExit(f"Expected 4 source tables; found {len(document.tables)}")
    packages = document.tables[2]
    values = [
        ["Package", "Trial price", "Audience and profiles", "Monthly credits included"],
        ["Khám phá", "0 VND", "1 child profile; adult-managed use", "10 credits/month"],
        ["Gia đình", "99,000 VND/month", "Up to 3 child profiles; pooled across household", "30 credits/month"],
        ["Lớp học", "499,000 VND / class / month", "1 Guide/class; up to 25 assigned child profiles; shared class pool", "120 credits/class/month"],
    ]
    if len(packages.rows) != len(values):
        raise SystemExit(f"Unexpected package table row count: {len(packages.rows)}")
    for row, row_values in zip(packages.rows, values, strict=True):
        for cell, value in zip(row.cells, row_values, strict=True):
            cell.text = value

    document.core_properties.title = "Sketch2Life Capstone Registration Form Version 1.4"
    document.core_properties.subject = "Capstone trial package, payment and credit requirements"
    document.core_properties.comments = ""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document.save(args.output)

    updated = Document(args.output)
    body = "\n".join(p.text for p in updated.paragraphs)
    package_text = "\n".join(" | ".join(c.text for c in row.cells) for row in updated.tables[2].rows)
    visible = body + "\n" + package_text
    for forbidden in (
        "REVIEW DRAFT",
        "Owner Review Draft",
        "subject to owner approval",
        "requires owner approval",
        "provisional hypotheses",
        "not approved product requirements",
        "Proposed for review",
        "review proposals only",
        "remain open decisions",
    ):
        if forbidden.casefold() in visible.casefold():
            raise SystemExit(f"Internal review marker remains: {forbidden}")
    for expected in (
        "VERSION 1.4",
        "0–107 completed months",
        "49,000 VND",
        "129,000 VND",
        "239,000 VND",
        "10 credits/month",
        "30 credits/month",
        "120 credits/class/month",
    ):
        if expected.casefold() not in visible.casefold():
            raise SystemExit(f"Expected final content missing: {expected}")

    print(f"Output: {args.output}")
    print(f"Input SHA-256: {input_hash}")
    print(f"Output SHA-256: {hashlib.sha256(args.output.read_bytes()).hexdigest().upper()}")
    print(f"Paragraphs: {len(updated.paragraphs)}; tables: {len(updated.tables)}")


if __name__ == "__main__":
    main()
