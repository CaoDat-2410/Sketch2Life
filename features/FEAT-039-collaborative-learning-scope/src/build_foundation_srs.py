"""Compose documentation v3.1 from the preserved v3.0 and reviewed draft inputs."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features/FEAT-039-collaborative-learning-scope"
BASE = FEATURE / "artifacts/Sketch2Life_Master_SRS_v3.0_preserved_20261010.md"
EXPECTED_BASE = "c69fd96ba9e5cd0ec85fcaa516c67ad73aafa02a45768dc2d93e29b7a756e2cf"
CANONICAL = ROOT / "features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md"
OUTPUT = FEATURE / "artifacts/Collaborative_Learning_SRS_v3.1.md"


def main() -> None:
    if hashlib.sha256(BASE.read_bytes()).hexdigest() != EXPECTED_BASE:
        raise ValueError("Preserved v3.0 changed; refusing to compose")
    text = BASE.read_text(encoding="utf-8")

    def replace(old: str, new: str) -> None:
        nonlocal text
        if text.count(old) != 1:
            raise ValueError(f"Expected one source fragment: {old[:95]}")
        text = text.replace(old, new, 1)

    replace("- Phiên bản: 3.0 — thay thế scope v2.0 theo xác nhận owner ngày 2026-10-10.",
            "- Phiên bản: 3.1 — đặc tả nền tảng hệ thống, mở rộng scope replacement v3.0 ngày 2026-10-10.")
    replace("- Feature quản lý: FEAT-039; task approval revision 2, chỉ tài liệu/phân tích.",
            "- Feature quản lý: FEAT-039; task approval revision 3, chỉ tài liệu/phân tích; implementation chưa được thực hiện trong task này.")
    replace("| SRC-OLD | Bản SRS v2.0 được bảo toàn trong FEAT-039 | Lịch sử và phân tích chuyển đổi; không còn là scope mục tiêu mới |",
            "| SRC-ANS3 | Owner: một trường pilot, hồ sơ + QR/mã không tài khoản trẻ, trường thu consent và authorized Teacher/Admin ghi bằng chứng/phạm vi | Chốt hình thức tổ chức/child account/school consent; các thông số age/capacity/retention và quy trình chi tiết vẫn theo decision register |\n| SRC-OLD | Bản SRS v2.0 và v3.0 được bảo toàn trong FEAT-039 | Lịch sử và phân tích chuyển đổi; v3.1 là canonical mới |")
    replace("OWNER_CONFIRMED | Trả lời trực tiếp trong task này: thay scope, Android, FastAPI, React Native",
            "OWNER_CONFIRMED | Trả lời trực tiếp trong task này, gồm scope/Android/FastAPI/RN, per-Sketch review, turn attribution, video failure choice và organization/profile/school consent")
    replace("| Actor | PARENT/GUIDE/ADMIN, trẻ không role | Child/Teacher/Super Admin; phương thức cấp credential cho trẻ TBD |",
            "| Actor | PARENT/GUIDE/ADMIN, trẻ không role | Child/Teacher/Super Admin; hồ sơ trẻ do Teacher quản lý, QR/mã phiên, không child login; capability contract proposed |")
    replace("| Dữ liệu | Original/hash/provenance, retention cũ | Giữ provenance/an toàn; thời hạn cụ thể/consent process mới TBD |",
            "| Dữ liệu | Original/hash/provenance, retention cũ | Giữ provenance/an toàn; school-mediated consent được owner chọn; chi tiết verification/retention theo OD04/05/17 |")
    replace("### B4.3 Identity refinement proposed/TBD", "### B4.3 Identity baseline và refinement")
    replace("Đề xuất Teacher/Super Admin dùng adult authentication; Child dùng `ChildParticipant` và capability phiên ngắn hạn được giáo viên xác nhận qua QR/mã hoặc hồ sơ, không bắt buộc tài khoản Firebase của trẻ. Đây là phương án, chưa là câu trả lời cho child credential/account lifecycle. Vai trò Child là quyền tham gia thật; không bị xóa khỏi scope vì baseline cũ chỉ adult.",
            "OWNER_CONFIRMED: trẻ dùng hồ sơ do Teacher quản lý và QR/mã phiên; không có tài khoản đăng nhập riêng. Teacher/Super Admin dùng adult authentication theo repository constraint. ChildParticipant, pending device admission, scoped capability, possession/refresh/revoke là logical design PROPOSED ở B19/B21/B22; không coi QR là verified child identity. Vai trò Child là quyền tham gia thật; không bị xóa khỏi scope vì baseline cũ chỉ adult. Pilot một trường, chuẩn bị organization scoping cho mở rộng; schema cụ thể và multi-tenant launch chưa được chốt.")
    replace("DeviceParticipant binding, group canvas ownership và many-school schema cần refinement; ERD không bắt buộc một table/entity, không là SQL migration. Portfolio không được gán contribution của cả nhóm cho một trẻ nếu thiếu attribution.",
            "Pilot một trường đã OWNER_CONFIRMED; organization boundary chuẩn bị khả năng mở rộng. DeviceParticipant binding, group canvas ownership và topology khi multi-school cần refinement; ERD không bắt buộc một table/entity, không là SQL migration. Portfolio không được gán contribution của cả nhóm cho một trẻ nếu thiếu attribution. Field/nullable/validation chi tiết xem B21.")
    replace("Các tên state sau là `PROPOSED` từ nguồn V/IX, cần refinement/contract approval. Hành vi pause/recover/group independent progress là confirmed.",
            "Các tên state sau là display concepts `PROPOSED` từ nguồn V/IX; B19.4 định nghĩa lower_snake_case wire registry cho refinement/contract approval. Hành vi pause/recover/group independent progress là confirmed. Chi tiết transitions/epochs/ack ở B19 và contracts B22; tên hiển thị không tạo enum cạnh tranh.")
    replace("Super Admin administrative power không là consent hoặc lý do đọc toàn bộ child content. Teacher không tự đại diện hợp pháp chỉ vì quản lý lớp. Guardian consent có thể qua school-mediated record hoặc external consent flow; đây là candidates cho OD04, chưa chọn. Export/delete được yêu cầu dù không có Parent portal.",
            "Super Admin administrative power không là consent hoặc lý do đọc toàn bộ child content. Teacher không tự đại diện hợp pháp chỉ vì quản lý lớp. OWNER_CONFIRMED: nhà trường thu consent người đại diện hợp pháp; authorized Teacher/Admin ghi nhận bằng chứng và phạm vi. Verification authority/process, policy purposes/jurisdiction và data-class retention còn cần review; enrollment không tạo consent. Export/delete được yêu cầu dù không có Parent portal; workflow chi tiết ở B24.")
    replace("Endpoint naming ví dụ `/v2/classroom-sessions/{id}/commands` hoặc REST resource routes còn chưa chọn. Không tự bump old `/v1` payload semantics; coexistence/migration cần ADR và compatibility tests.",
            "B22 đề xuất namespace `/api/collaboration/v1` và route/DTO/HTTP semantics cụ thể, toàn bộ PROPOSED_UNADOPTED. Không tự bump old `/v1` payload semantics; coexistence/migration cần ADR và compatibility tests. B12 là family overview; B22 là candidate interface chi tiết.")
    replace("OD01–OD03 đã được owner trả lời ngày 2026-10-10, được giữ lại để truy vết. Các mục còn lại là TBD cho refinement/implementation gate của phần liên quan.",
            "OD01–OD03 và một phần OD04/06/14 đã được owner trả lời ngày 2026-10-10; giữ lại để truy vết, không hỏi lại các lựa chọn đã chốt. Những phần còn mở là refinement/implementation gate của phần liên quan; có thể chuẩn bị independent fixtures trước khi quyết định phần implementation.")
    replace("| OD04 | Guardian consent/verification khi không Parent portal | Cao | Thu thập/AI/durable child records |",
            "| OD04 | RESOLVED_OWNER hình thức: trường thu consent, authorized Teacher/Admin ghi evidence/purpose; verification authority/process còn TBD | Cao phần refinement | Thu thập/AI/durable child records, B21/B24 |")
    replace("| OD06 | Một trường hay nhiều tổ chức, isolation/teacher/admin scope | Trung bình | Tenancy/authorization |",
            "| OD06 | RESOLVED_OWNER: một trường pilot, chuẩn bị mở rộng; resource scoping/topology multi-school còn PROPOSED | Đã chốt phạm vi pilot | Tenancy/authorization; không full multi-tenant launch |")
    replace("| OD14 | Child credential, provisioning/revoke; Teacher offline/late join/co-teacher policy | Cao | Auth/session recovery |",
            "| OD14 | RESOLVED_OWNER child login: managed profiles + QR/mã, không account riêng; grant/provisioning/revoke/Teacher offline/late join/co-teacher policy còn PROPOSED/TBD | Cao phần refinement | Auth/session recovery, B19/B21/B22 |")
    replace("- Documentation gate: FEAT-039 approved rev2; source coverage, all M01–M14/AC01–AC18, link/provenance and repo checks.",
            "- Documentation gate: FEAT-039 approved rev3; source coverage, all M01–M14/AC01–AC18/FR001–FR066, detailed use cases/data/API/UI/NFR/traceability, preserved hashes and repo checks.")
    replace("| SRC-ANS3 | Owner: một trường pilot, hồ sơ + QR/mã không tài khoản trẻ, trường thu consent và authorized Teacher/Admin ghi bằng chứng/phạm vi | Chốt hình thức tổ chức/child account/school consent; các thông số age/capacity/retention và quy trình chi tiết vẫn theo decision register |",
            "| SRC-ANS3 | Owner: một trường pilot, hồ sơ + QR/mã không tài khoản trẻ, trường thu consent và authorized Teacher/Admin ghi bằng chứng/phạm vi | Chốt hình thức tổ chức/child account/school consent; verification và contract chi tiết còn refinement |\n| SRC-ANS4 | Owner: đủ 3 đến trước 13 tuổi; một lớp tối đa 40 trẻ; giữ dữ liệu phiên/tranh 90 ngày sau end | Chốt 36–155 tháng inclusive, pilot capacity target, default session/artwork retention; không phải benchmark hoặc TTL cho mọi data class |")
    replace("| Tuổi | 0–107 tháng, dưới 9 | 3–12; UX 3–5/6–8/9–12; biên tháng chính xác TBD |",
            "| Tuổi | 0–107 tháng, dưới 9 | Owner chọn 36–155 tháng inclusive, từ đủ 3 đến trước 13; UX 3–5/6–8/9–12 |")
    replace("| BR01 | Tuổi mục tiêu 3–12, UI bands 3–5/6–8/9–12; người lớn xác nhận tuổi, không suy từ ảnh | CONFIRMED + REPO_CONSTRAINT; exact month policy TBD |",
            "| BR01 | Từ đủ 3 đến trước 13: 36–155 completed months inclusive; UX 3–5/6–8/9–12; adult xác nhận tuổi, không suy từ ảnh | OWNER_CONFIRMED endpoint + CONFIRMED bands + REPO_CONSTRAINT; calculation fixtures/mixed-age refinement |")
    replace("| NFR07 | Data minimization, access/audit, retention/export/delete và consent lifecycle | CONFIRMED; retention duration/jurisdiction/guardian verification TBD |",
            "| NFR07 | Data minimization, access/audit, retention/export/delete và consent lifecycle | CONFIRMED; session/artwork default 90 ngày sau end OWNER_CONFIRMED; other data-class/copy durations, jurisdiction/guardian verification TBD |")
    replace("| OrganizationScope | id, name, policyRef, status | Isolation scope; single/multi organization OD06 |",
            "| OrganizationScope | id, name, policyRef, status | Pilot một trường OWNER_CONFIRMED; scope schema chuẩn bị expansion PROPOSED; full multi-school topology riêng |")
    replace("| ChildParticipant | id, studentRef?, sessionRef, alias, admissionState | StudentRef có thể TBD cho guest; không tự thu DOB đầy đủ |",
            "| ChildParticipant | id, studentRef, sessionRef, alias, admissionState | Pilot bắt buộc managed profile; không anonymous/guest participant; Android không tự thu DOB đầy đủ |")
    replace("Identity; classroom; session; artwork/operations/snapshot; AI requests/reviews; learning content; assessment/reflection; consent; audit. Retention/export/delete matrix phải chọn per-class policy/version, legal basis và allowed purpose. Không tự giữ 30/60/90 ngày từ scope cũ như value confirmed.",
            "Identity; classroom; session; artwork/operations/snapshot; AI requests/reviews; learning content; assessment/reflection; consent; audit. OWNER_CONFIRMED default: dữ liệu từng phiên và tranh giữ 90 ngày sau session end. Đây là câu trả lời mới, không giữ mặc định 30/60/90 của scope cũ. Portfolio/profile/audit/consent evidence/generic library có policy riêng; copy/provider/backup/shared-delete cần exact lifecycle và evidence B24. Không kéo dài raw source bởi portfolio link; expiry/delete sớm theo approved purpose/request policy.")
    replace("Performance/model tests require pinned versions, device/GPU, fixture manifest and reproducible metrics. Pilot 20–40 trẻ is source planning context, not a proven load result or a user-selected simultaneous-class target. Numeric acceptance thresholds stay OD12 until approved. This documentation task runs document/repository checks only; historical product test passes are not reclassified as current tests.",
            "Performance/model tests require pinned versions, device/GPU, fixture manifest and reproducible metrics. OWNER_CONFIRMED pilot target: một lớp, tối đa 40 trẻ chạy cùng lúc; đây chưa là năng lực đã đo. Device/network/groups/AI budget và candidate latency/quality targets B25 còn PROPOSED/TBD. This documentation task runs document/repository checks only; historical product test passes are not reclassified as current tests.")
    replace("| OD05 | Retention/export/delete data classes, shared artwork, copies/backups | Cao | Privacy schema/lifecycle |",
            "| OD05 | RESOLVED_OWNER default session/artwork: 90 ngày sau end; portfolio/profile/audit/consent/library TTL, shared-delete/copies/backups/authority còn TBD | Cao phần refinement | Privacy lifecycle B19.2/B24; không kéo dài raw source vô hạn |")
    replace("| OD12 | Pilot measurable thresholds, device set, simultaneous classes, model quality/budget | Trung bình | Load/model/device acceptance |",
            "| OD12 | RESOLVED_OWNER capacity target: một lớp tối đa 40 trẻ; device/network profile, latency/quality/model budget còn PROPOSED/TBD | Trung bình phần refinement | Load/model/device acceptance B25; chưa claim đạt tải |")
    replace("| OD13 | “12 tuổi” đến trước 13 hay endpoint khác; age-month policy và mixed-age groups | Cao | Age gates/curriculum |",
            "| OD13 | RESOLVED_OWNER: từ đủ 3 đến trước 13, 36–155 completed months inclusive; calculation/date fixtures và mixed-age/curriculum details còn refinement | Đã chốt endpoint | Age gates/curriculum migration B19/B21 |")
    replace("OD01–OD03 và một phần OD04/06/14 đã được owner trả lời ngày 2026-10-10; giữ lại để truy vết, không hỏi lại các lựa chọn đã chốt.",
            "OD01–OD03/06/13 và một phần OD04/05/12/14 đã được owner trả lời ngày 2026-10-10; giữ lại để truy vết, không hỏi lại các lựa chọn đã chốt.")
    text += "\n2026-10-10 v3.1: owner yêu cầu SRS làm nền tảng toàn hệ thống; bổ sung B19–B26 về policy/state/concurrency/recovery, 38 detailed use cases và AT, logical data/API contracts, UX/privacy/NFR measurement và per-FR verification. Chốt một trường pilot, managed profiles + QR/code không child login, trường thu consent với authorized Teacher/Admin ghi evidence/purpose. Giữ exact v3.0 bên cạnh exact v2.0; source runtime và full stack không thay đổi bởi tài liệu.\n"
    text += "Owner answers cùng increment v3.1: 36–155 completed months inclusive; pilot target một lớp tối đa 40 trẻ; default session/artwork retention 90 ngày sau end. Calculation/device/model/performance/copypurge và các data-class TTL khác còn refinement; không benchmark/legal compliance claim.\n"

    navigation = """### 0.4 Chỉ dẫn đọc bản nền tảng v3.1

| Người đọc / việc cần làm | Phần chính |
|---|---|
| Owner/BA duyệt scope và quyết định | [B1–B6](#b1), [FR và trạng thái](#b10), [decision register](#b17) |
| Thiết kế domain và orchestration | [Kiến trúc](#b8), [policy/state/consistency/recovery](#b19) |
| Backend/Android/Desktop thiết kế contracts | [Detailed use cases](#b20), [data dictionary](#b21), [API/WS/event/error examples](#b22) |
| UX và Teacher workflow | [Screens/age tools/accessibility](#b23), [privacy workflow](#b24) |
| QA, NFR và tích hợp | [Measurement profiles/fixtures](#b25), [traceability/gates](#b26) |
| Migration từ source hiện tại | [Maturity/migration](#b15), [phasing/allocation](#b16), báo cáo reuse đi kèm |

B1–B18 là scope và tổng quan; B19–B26 là refinement có actor/input/guard/error/outcome và verification. Các ID FR được giữ nguyên; UC01–UC13 là summary, UC-001–UC-038 là detailed cases. Chữ “phải” trong phần PROPOSED diễn tả candidate specification để review, không tự adopt stack hoặc cấp task implementation approval. Một quyết định owner-confirmed được ghi riêng và không trở lại TBD vì schema chi tiết chưa chốt.

"""
    replace("## B1. Mục tiêu và phạm vi sản phẩm", navigation + "## B1. Mục tiêu và phạm vi sản phẩm")

    for name in ("B19_STATE_AND_POLICY.md", "B20_DETAILED_USE_CASES.md", "B21_DATA_API_CONTRACTS.md", "B23_UX_PRIVACY_QUALITY.md", "B26_TRACEABILITY_AND_GATES.md"):
        fragment = (FEATURE / "artifacts/drafts" / name).read_text(encoding="utf-8")
        if "\ufffd" in fragment:
            raise ValueError(f"Encoding corruption in {name}")
        text += "\n" + fragment.strip() + "\n"
    text = re.sub(r"^## B(\d+)\.", lambda m: f'<a id="b{m.group(1)}"></a>\n\n{m.group(0)}', text, flags=re.M)
    text = text.rstrip() + "\n"
    for destination in (CANONICAL, OUTPUT):
        destination.write_text(text, encoding="utf-8", newline="\n")
    print(f"Composed v3.1: {len(text.splitlines())} lines, {len(text)} characters")


if __name__ == "__main__":
    main()
