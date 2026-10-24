"""Compose SRS v3.2 from the preserved v3.1 baseline and reviewed B27 amendment."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features/FEAT-039-collaborative-learning-scope"
BASE = FEATURE / "artifacts/Sketch2Life_Master_SRS_v3.1_preserved_20261023.md"
EXPECTED_BASE = "A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9"
AMENDMENT = FEATURE / "artifacts/drafts/B27_CLASSROOM_INTEGRATION_AMENDMENT_20261023.md"
CANONICAL = ROOT / "features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md"
OUTPUT = FEATURE / "artifacts/Collaborative_Learning_SRS_v3.2.md"


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"Expected one source fragment, found {text.count(old)}: {old[:100]}")
    return text.replace(old, new, 1)


def main() -> None:
    if hashlib.sha256(BASE.read_bytes()).hexdigest() != EXPECTED_BASE.lower():
        raise ValueError("Preserved v3.1 changed; refusing to compose")
    text = BASE.read_text(encoding="utf-8")

    replacements = (
        (
            "- Phiên bản: 3.1 — đặc tả nền tảng hệ thống, mở rộng scope replacement v3.0 ngày 2026-10-10.",
            "- Phiên bản: 3.2 — v3.1 cộng phụ lục sửa đổi tích hợp lớp ngày 2026-10-23; xem B27 và phân biệt OWNER_CONFIRMED / PROPOSED / OPEN_TBD.",
        ),
        (
            "- Feature quản lý: FEAT-039; task approval revision 3, chỉ tài liệu/phân tích; implementation chưa được thực hiện trong task này.",
            "- Feature quản lý: FEAT-039; SRS revision 4 là cập nhật tài liệu-only. Runtime implementation chưa được thực hiện theo phụ lục này.",
        ),
        (
            "Bản v2.0 nguyên trạng, bao gồm nội dung chưa commit trước task, được giữ trong FEAT-039.",
            "Bản v2.0 nguyên trạng, bao gồm nội dung chưa commit trước task, được giữ trong FEAT-039. Exact SRS v3.1 trước phụ lục này được bảo toàn tại `Sketch2Life_Master_SRS_v3.1_preserved_20261023.md`.",
        ),
        (
            "| SRC-ADR | ADR-0003/0006/0008–0013 cùng các feature records | Quyết định cũ cần giữ, thay hoặc rà soát theo ma trận chuyển đổi |",
            "| SRC-ADR | ADR-0003/0006/0008–0013 cùng các feature records | Quyết định cũ cần giữ, thay hoặc rà soát theo ma trận chuyển đổi |\n| SRC-ANS5 | Owner clarification ngày 2026-10-23: mã sáu số dùng chung; đóng cả QR và mã khi Teacher bắt đầu; phân biệt hoàn tất đủ quy trình với Teacher dừng sớm | Xác nhận hành vi admission và ý nghĩa outcome; fields/API/persistence cụ thể vẫn cần contract |",
        ),
        (
            "### 0.4 Chỉ dẫn đọc bản nền tảng v3.1",
            "### 0.4 Chỉ dẫn đọc bản nền tảng v3.2",
        ),
        (
            "| Migration từ source hiện tại | [Maturity/migration](#b15), [phasing/allocation](#b16), báo cáo reuse đi kèm |",
            "| Migration từ source hiện tại | [Maturity/migration](#b15), [phasing/allocation](#b16), báo cáo reuse đi kèm |\n| Quyết định tích hợp lớp mới | [SRS amendment và các contract còn mở](#b27), FEAT-060 API traceability |",
        ),
        (
            "B1–B18 là scope và tổng quan; B19–B26 là refinement có actor/input/guard/error/outcome và verification. Các ID FR được giữ nguyên; UC01–UC13 là summary, UC-001–UC-038 là detailed cases. Chữ “phải” trong phần PROPOSED diễn tả candidate specification để review, không tự adopt stack hoặc cấp task implementation approval. Một quyết định owner-confirmed được ghi riêng và không trở lại TBD vì schema chi tiết chưa chốt.",
            "B1–B18 là scope và tổng quan; B19–B26 là refinement có actor/input/guard/error/outcome và verification; B27 truy vết amendment ngày 2026-10-23. Các ID FR được giữ nguyên; UC01–UC13 là summary, UC-001–UC-038 là detailed cases. Chữ “phải” trong phần PROPOSED diễn tả candidate specification để review, không tự adopt stack hoặc cấp task implementation approval. Một quyết định owner-confirmed được ghi riêng và không trở lại TBD vì schema chi tiết chưa chốt.",
        ),
        (
            "| AdmitParticipant | Lobby/allowed late join, membership và consent policy | Participant admitted + scoped device binding |",
            "| AdmitParticipant | Chỉ khi admission đang mở trước khi Teacher start; xác minh membership và consent policy | Participant admitted + scoped device binding; OWNER_CONFIRMED: mọi admission mới qua QR/deep-link/mã bị đóng sau start |",
        ),
        (
            "| OD14 | RESOLVED_OWNER child login: managed profiles + QR/mã, không account riêng; grant/provisioning/revoke/Teacher offline/late join/co-teacher policy còn PROPOSED/TBD | Cao phần refinement | Auth/session recovery, B19/B21/B22 |",
            "| OD14 | RESOLVED_OWNER child login: managed profiles + QR/mã, không account riêng; no late admission by QR/code after start OWNER_CONFIRMED; grant/provisioning/revoke/Teacher offline/co-teacher policy còn PROPOSED/TBD | Cao phần refinement | Auth/session recovery, B19/B21/B22 |",
        ),
        (
            "| LateAdmit | active/paused → same lifecycle | PROPOSED Teacher explicit confirmation; policy allows late join | Child assigned group + checkpoint/resync; no old-content access outside grant |",
            "| LateAdmit | active/paused → same lifecycle | **OWNER_CONFIRMED: không nhận bất kỳ admission mới nào qua QR/deep-link hoặc mã 6 số sau khi Teacher start thành công.** Trạng thái request đang chờ tại thời điểm start và cách xử lý lỗi cụ thể vẫn cần contract | Trẻ đã admitted trước start tiếp tục dùng grant; không tạo membership mới khi phiên active/paused |",
        ),
        (
            "- **Preconditions:** Lobby mở hoặc late-join policy đã được duyệt; managed profile/enrollment/consent đủ cho purpose hiện hành, tuổi 36–155 completed months tại ngày phiên và còn quota admission tối đa 40 trẻ; device chưa bị revoke.",
            "- **Preconditions:** Admission đang mở trong Lobby trước khi Teacher start; managed profile/enrollment/consent đủ cho purpose hiện hành, tuổi 36–155 completed months tại ngày phiên và còn quota admission tối đa 40 trẻ; device chưa bị revoke.",
        ),
        (
            "- **Alternatives/errors:** mã sai/hết hạn/đóng admission cho thông báo an toàn, không lộ roster cả lớp. Duplicate join trả binding hiện có hoặc yêu cầu Teacher xử lý rebind theo policy. Late join chưa có policy không tự admit. Grant bị revoke không thể dùng QR cũ để lấy quyền lại.",
            "- **Alternatives/errors:** mã sai/hết hạn/đóng admission cho thông báo an toàn, không lộ roster cả lớp. Duplicate join trả binding hiện có hoặc yêu cầu Teacher xử lý rebind theo policy. Sau khi start thành công, mọi QR/deep-link hoặc mã sáu số mới bị từ chối; pending-at-start handling cần contract. Grant đã admitted trước start tiếp tục; revoked grant không thể dùng QR cũ để lấy quyền lại.",
        ),
        (
            "1. **Product/policy**: giữ owner decisions tuổi 36–155 inclusive, pilot một lớp tối đa 40 trẻ và retention tranh/phiên 90 ngày sau end. Chốt tiếp mixed-age, school authority/consent, retention các classes khác/export/delete/backups, screen time, Teacher offline/co-teacher/late join, tool imports, return-stage và device/AI-budget profile bằng attributable evidence. Các module không phụ thuộc quyết định có thể làm fixtures; real collection/production path phụ thuộc policy chưa chốt không tự mở.",
            "1. **Product/policy**: giữ owner decisions tuổi 36–155 inclusive, pilot một lớp tối đa 40 trẻ, retention tranh/phiên 90 ngày sau end, và đóng mọi admission mới sau Teacher start. Chốt tiếp mixed-age, school authority/consent, retention các classes khác/export/delete/backups, screen time, Teacher offline/co-teacher behavior, tool imports, return-stage và device/AI-budget profile bằng attributable evidence. Các module không phụ thuộc quyết định có thể làm fixtures; real collection/production path phụ thuộc policy chưa chốt không tự mở.",
        ),
    )
    for old, new in replacements:
        text = replace_once(text, old, new)

    fragment = AMENDMENT.read_text(encoding="utf-8").strip()
    if "## B27." not in fragment or "## B27." in text:
        raise ValueError("B27 amendment source is missing or already included")
    text = text.rstrip() + '\n\n<a id="b27"></a>\n\n' + fragment + "\n"

    for destination in (CANONICAL, OUTPUT):
        destination.write_text(text, encoding="utf-8", newline="\n")
    print(f"Composed SRS v3.2: {len(text.splitlines())} lines, {len(text)} characters")


if __name__ == "__main__":
    main()
