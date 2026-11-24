"""Synchronize the reviewed B29 proposal into both current SRS documents."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "features/FEAT-029-master-srs/artifacts/B29_TEACHER_WEB_BILLING_PROPOSAL.md"
TARGETS = [
    ROOT / "features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md",
    ROOT / "features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.3.md",
]
START = "# B29 — Proposed School-level Billing Change Request"
END = "## Change log — SRS v3.3"
CHANGE_LOG = (
    "## Change log — SRS v3.3\n\n"
    "2026-10-25: Add B29 as a segregated PROPOSED school-level billing change request using the existing Teacher Desktop and Super Admin Portal. Preserve the v3.3/B28 policy baseline and existing requirement IDs. All package prices, add-on amounts and quota values are proposal candidates only; 999,000 VND/month is the owner-selected Plus candidate for this proposal, not adopted product pricing. School entitlement, permissions, provider, legal and platform decisions remain subject to review and separate implementation approval. No billing implementation is claimed.\n\n"
)


def main() -> None:
    proposal = SOURCE.read_text(encoding="utf-8").strip() + "\n\n"
    if not proposal.startswith(START):
        raise ValueError(f"Unexpected proposal heading: {proposal.splitlines()[0]}")
    for target in TARGETS:
        body = target.read_text(encoding="utf-8")
        begin = body.index(START)
        end = body.index(END, begin)
        updated = body[:begin] + proposal + CHANGE_LOG + body[end + len(END):]
        updated = updated.replace(
            "2026-10-25: Add B29 as a segregated PROPOSED Teacher Web billing change request; preserve v3.3/B28 policy baseline and existing requirement IDs. All prices, quotas, provider/consumer/legal/platform decisions require owner review and separate implementation approval. No billing implementation is claimed.\n\n",
            "",
        )
        updated = updated.replace(
            "2026-10-25: Add B29 as a segregated PROPOSED school-level billing change request using the existing Teacher Desktop and Super Admin Portal. Preserve the v3.3/B28 policy baseline and existing requirement IDs. Prices, quotas, school entitlement, permissions, provider, legal and platform decisions require owner review and separate implementation approval. No billing implementation is claimed.\n\n",
            "",
        )
        updated = updated.replace(
            "2026-10-25: Add B29 as a segregated PROPOSED school-level billing change request using the existing Teacher Desktop and Super Admin Portal. Preserve the v3.3/B28 policy baseline and existing requirement IDs. Price options await owner selection; quotas, school entitlement, permissions, provider, legal and platform decisions require owner review and separate implementation approval. No billing implementation is claimed.\n\n",
            "",
        )
        lines = updated.splitlines()
        seen_change = False
        deduplicated = []
        for line in lines:
            if line.startswith("2026-10-25: Add B29 as a segregated"):
                if seen_change:
                    continue
                seen_change = True
                line = CHANGE_LOG.splitlines()[2]
            deduplicated.append(line)
        updated = "\n".join(deduplicated) + "\n"
        target.write_text(updated, encoding="utf-8", newline="\n")
        print(f"Updated {target}")
    if TARGETS[0].read_bytes() != TARGETS[1].read_bytes():
        raise ValueError("The current SRS copies are not byte-identical")


if __name__ == "__main__":
    main()
