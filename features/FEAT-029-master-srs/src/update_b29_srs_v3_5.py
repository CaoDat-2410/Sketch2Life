"""Version the owner-directed B29 school package/quota update as SRS v3.5."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FEAT029 = ROOT / "features" / "FEAT-029-master-srs"
FEAT039 = ROOT / "features" / "FEAT-039-collaborative-learning-scope"
CANONICAL = FEAT029 / "artifacts" / "Sketch2Life_Master_SRS.md"
PRESERVED = FEAT029 / "artifacts" / "Sketch2Life_Master_SRS_v3.4_preserved_20261026.md"
CURRENT_COPY = FEAT039 / "artifacts" / "Collaborative_Learning_SRS_v3.5.md"
OLD_FEATURE_COPY = FEAT039 / "artifacts" / "Collaborative_Learning_SRS_v3.4.md"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"Expected one occurrence, got {count}: {old!r}")
    return text.replace(old, new, 1)


def main() -> None:
    original = CANONICAL.read_bytes()
    if PRESERVED.exists():
        raise FileExistsError(PRESERVED)
    if CURRENT_COPY.exists():
        raise FileExistsError(CURRENT_COPY)
    if original != OLD_FEATURE_COPY.read_bytes():
        raise ValueError("Current FEAT-029 and FEAT-039 v3.4 sources are not byte-identical")
    text = original.decode("utf-8")
    text = replace_once(
        text,
        "- Phiên bản: 3.4 — v3.3/B28 cộng B29 thanh toán cấp trường vào baseline ngày 2026-10-25; chỉ số tiền còn PROPOSED, implementation NOT IMPLEMENTED.",
        "- Phiên bản: 3.5 — cập nhật hạn mức gói trường học theo chỉ đạo ngày 2026-10-26; chỉ các số tiền còn PROPOSED, implementation NOT IMPLEMENTED.",
    )
    text = replace_once(
        text,
        "- Feature quản lý: FEAT-039; SRS v3.4 / revision 6 cập nhật baseline billing, phối hợp FEAT-058 cho bộ Review 2.",
        "- Feature quản lý: FEAT-039; SRS v3.5 / revision 7 cập nhật hạn mức B29, phối hợp FEAT-058 cho bộ Review 2.",
    )
    text = replace_once(
        text,
        "**Baseline status: OWNER_APPROVED in SRS v3.4. Implementation status: NOT IMPLEMENTED.**",
        "**Baseline status: OWNER_APPROVED in SRS v3.5. Implementation status: NOT IMPLEMENTED.**",
    )
    replacements = {
        "up to 2 active classes and 100 shared AI credits": "up to 1 active class and 3 shared AI credits",
        "Up to 10 active classes, 10 Teacher seats and 500 shared AI credits": "Up to 5 active classes, 10 Teacher seats and 100 shared AI credits",
        "100 credits shared by eligible Teachers in the school": "15 credits shared by eligible Teachers in the school",
        "300 credits shared by eligible Teachers in the school": "45 credits shared by eligible Teachers in the school",
        "700 credits shared by eligible Teachers in the school": "80 credits shared by eligible Teachers in the school",
    }
    for old, new in replacements.items():
        text = replace_once(text, old, new)
    text = replace_once(
        text,
        "## Change log — SRS v3.4\n\n2026-10-25:",
        "## Change log — SRS v3.5\n\n2026-10-26: Update baseline school entitlements to the owner's latest direction: Free Trial is 14 days with one active class and 3 shared AI credits; Plus has five active classes, ten Teacher seats and 100 shared AI credits; one-time school-shared AI top-ups contain 15, 45 and 80 credits. Keep all monetary amounts PROPOSED. Billing remains NOT IMPLEMENTED. Preserve v3.4 and earlier baselines.\n\n## Change log — SRS v3.4\n\n2026-10-25:",
    )
    v35 = text.encode("utf-8")
    PRESERVED.write_bytes(original)
    CANONICAL.write_bytes(v35)
    CURRENT_COPY.write_bytes(v35)
    if CANONICAL.read_bytes() != CURRENT_COPY.read_bytes():
        raise ValueError("SRS v3.5 outputs are not byte-identical")
    print({
        "prior_v3_4_sha256": sha256(original),
        "canonical_v3_5": str(CANONICAL),
        "feature_copy_v3_5": str(CURRENT_COPY),
        "v3_5_sha256": sha256(v35),
        "preserved_v3_4": str(PRESERVED),
    })


if __name__ == "__main__":
    main()
