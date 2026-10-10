"""Assemble reviewed documentation fragments; never edits the product or SRS."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
SRS = ROOT / 'features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md'
PIN = 'a95c89589843e3555e967c5e486f3bcaf4bbdf9446cb3bc9c49ed16f672964d9'

H = [
    ('H-IDENTITY', 'BE1-03, BE1-04', 'DATA-01/04/12/35; CMD-07/17/18/51/52/53; verified adult + scoped device context', 'FE-02/03/13; BE2-03/05/09; INTG-03'),
    ('H-CLASS-CONSENT', 'BE1-04, BE1-05', 'DATA-02–05; CMD-01–09/54–56; age, enrollment, purpose eligibility/revoke', 'FE-03/15; BE2-02/03/04/08/14; INTG-03/08'),
    ('H-SESSION-ADMISSION', 'BE1-06, BE1-07, BE1-03, BE1-08', 'DATA-06–14; CMD-10/12–19/24–27; pending/admit/grant/turn scope', 'FE-02/03/04; INTG-03/04'),
    ('H-CANVAS-SYNC', 'BE1-09, BE1-10, BE1-02', 'DATA-14–20; CMD-27–31/61; operation receipt, checkpoint, snapshot, epoch', 'FE-01/04/05/06; BE2-02/03/07; INTG-04/05'),
    ('H-SESSION-CONTROL', 'BE1-06, BE1-08, BE1-11', 'DATA-06/07/08/19; CMD-19–26/66; scoped transition/finish + clock/warning/policy events', 'FE-05/08/09; BE2-03/10/11/13; INTG-04/06/07/11'),
    ('H-AI-REVIEW', 'BE2-02, BE2-03, BE2-04, BE2-05, BE2-06', 'DATA-21–24; CMD-32–36; source/context/meaning/proposal/exact review/child response', 'FE-06/14; BE1-11/12/14; BE2-09/12 shared DATA-24 contract only; INTG-05'),
    ('H-GALLERY', 'BE1-13, BE1-10', 'DATA-20/32; CMD-37/65; pinned artwork/meaning/contributor/audience', 'FE-07; BE2-07; INTG-06'),
    ('H-KNOWLEDGE-VIDEO', 'BE2-07, BE2-08, BE2-09, BE2-10', 'DATA-24/26–28; CMD-38–43; source/script/job/review/play/disposition', 'FE-08; BE1-11/12; INTG-06'),
    ('H-ACTIVITY', 'BE2-11, BE2-12', 'DATA-29/33; CMD-45/48; published discovery/assignment/preparation/evidence refs', 'FE-09; BE1-11/14; INTG-07'),
    ('H-ASSESSMENT-PORTFOLIO', 'BE1-14', 'DATA-30/31; CMD-46/47/62/64; observation/reflection/judgement/progress/source expiry', 'FE-10/11; INTG-07'),
    ('H-CONTENT-PRESET', 'BE2-12, BE2-13', 'DATA-24/33; CMD-48 typed content/preset branches; publication/recall/effective version', 'FE-03/12; BE1-06/11/12; INTG-08'),
    ('H-ADMIN-POLICY', 'BE1-15, BE2-14, BE2-12', 'DATA-33 envelope maintained by BE2-12; CMD-48 sole dispatcher. Core policy implementation BE1-15; AI policy implementation BE2-14', 'FE-14/15; BE1-06/12; BE2-03/04/08; INTG-08/10'),
    ('H-OPERATIONS', 'BE2-01, BE2-03, BE2-14, BE1-02, BE1-03, BE1-11, BE1-12', 'P3 job/policy projections DATA-25/33 CMD-44; P2 durable audit/session/auth projections DATA-07/35 CMD-11/59. Gateway BE1-12 calls producer ports', 'FE-05/14; INTG-05/10/11'),
    ('H-DATA-REQUEST', 'BE1-15, BE2-14, BE2-04, BE2-08', 'DATA-34 lifecycle authority/export/core-copy purge BE1-15; ProviderCopyLifecycle schema BE2-14, provider hooks BE2-04/08; CMD-49/50/63 sole P2', 'FE-11/15; INTG-08; BE1-15 consumes provider receipts; BE2-14/04/08 consume scoped authority/cancel-purge commands'),
]

DEPENDENCIES = {
    'FE-01': [], 'FE-02': ['FE-01'], 'FE-03': ['FE-01'],
    'FE-04': ['FE-01', 'FE-02'], 'FE-05': ['FE-03', 'FE-04'],
    'FE-06': ['FE-04', 'FE-05'], 'FE-07': ['FE-04', 'FE-05'],
    'FE-08': ['FE-05', 'FE-07'], 'FE-09': ['FE-05', 'FE-08'],
    'FE-10': ['FE-09'], 'FE-11': ['FE-07', 'FE-10'],
    'FE-12': ['FE-01'], 'FE-13': ['FE-01'], 'FE-14': ['FE-01'], 'FE-15': ['FE-01'],
    'BE1-01': [], 'BE1-02': ['BE1-01'], 'BE1-03': ['BE1-01', 'BE1-02'],
    'BE1-04': ['BE1-01', 'BE1-02', 'BE1-03'], 'BE1-05': ['BE1-02', 'BE1-03', 'BE1-04'],
    'BE1-06': ['BE1-02', 'BE1-03', 'BE1-04', 'BE1-05'],
    'BE1-07': ['BE1-03', 'BE1-04', 'BE1-05', 'BE1-06'],
    'BE1-08': ['BE1-03', 'BE1-06', 'BE1-07'],
    'BE1-09': ['BE1-01', 'BE1-02', 'BE1-03', 'BE1-05', 'BE1-08'],
    'BE1-10': ['BE1-02', 'BE1-03', 'BE1-09'], 'BE1-11': ['BE1-06', 'BE1-08', 'BE1-10'],
    'BE1-12': ['BE1-02', 'BE1-03', 'BE1-05', 'BE1-06'],
    'BE1-13': ['BE1-05', 'BE1-09', 'BE1-10', 'BE1-12'],
    'BE1-14': ['BE1-03', 'BE1-05', 'BE1-10', 'BE1-11', 'BE1-13'],
    'BE1-15': ['BE1-02', 'BE1-03', 'BE1-05', 'BE1-10', 'BE1-13', 'BE1-14'],
    'BE1-16': ['BE1-04', 'BE1-06', 'BE1-08'],
    'BE2-01': [], 'BE2-02': ['BE2-01'], 'BE2-03': ['BE2-01', 'BE2-02'],
    'BE2-04': ['BE2-01', 'BE2-02', 'BE2-03'], 'BE2-05': ['BE2-01', 'BE2-04'],
    'BE2-06': ['BE2-05'], 'BE2-07': ['BE2-01'], 'BE2-08': ['BE2-01', 'BE2-07'],
    'BE2-09': ['BE2-08'], 'BE2-10': ['BE2-01', 'BE2-08'],
    'BE2-11': ['BE2-01', 'BE2-12'], 'BE2-12': ['BE2-01'],
    'BE2-13': ['BE2-01', 'BE2-12'], 'BE2-14': ['BE2-01', 'BE2-12'],
    'INTG-01': [], 'INTG-02': ['INTG-01'], 'INTG-03': ['INTG-02'],
    'INTG-04': ['INTG-03'], 'INTG-05': ['INTG-04'], 'INTG-06': ['INTG-03', 'INTG-04'],
    'INTG-07': ['INTG-06'], 'INTG-08': ['INTG-03', 'INTG-05', 'INTG-07'],
    'INTG-09': ['INTG-04', 'INTG-05', 'INTG-06', 'INTG-07', 'INTG-08'],
    'INTG-10': ['INTG-02'], 'INTG-11': ['INTG-09', 'INTG-10'],
    'INTG-12': ['INTG-09', 'INTG-10', 'INTG-11'],
}

MODULES = [
    ('M01', 'FE-02/03/13', 'BE1-03/07/12', 'INTG-03/08'),
    ('M02', 'FE-03/13', 'BE1-04/05', 'INTG-03'),
    ('M03', 'FE-03/05/08/09', 'BE1-06/11; BE2-10', 'INTG-03/04/06/07'),
    ('M04', 'FE-03/04/05', 'BE1-08/16', 'INTG-04/09'),
    ('M05', 'FE-01/04', 'BE1-09/10/02', 'INTG-04'),
    ('M06', 'FE-06', 'BE2-02/03/04/05/06', 'INTG-05'),
    ('M07', 'FE-07', 'BE1-13', 'INTG-06'),
    ('M08', 'FE-08', 'BE2-07/08/09/10', 'INTG-06'),
    ('M09', 'FE-09/12', 'BE2-11/12', 'INTG-07'),
    ('M10', 'FE-10/11', 'BE1-14/15', 'INTG-07'),
    ('M11', 'FE-03/05/06', 'BE1-11/12; BE2-01/03/13', 'INTG-04/05/10'),
    ('M12', 'FE-12/13/14/15', 'BE1-03/04/12/15; BE2-12/14', 'INTG-08/10'),
    ('M13', 'FE-11/14/15', 'BE1-02/03/05/12/15; BE2-14', 'INTG-08/09'),
    ('M14', 'FE-02/04/05/06/08/15', 'BE1-03/10/11/15; BE2-01/03/10/14', 'INTG-04/05/06/08/09'),
]

HEADER = '''# Phân công task cho 4 người — Sketch2Life scope mới

Bản này chia công việc theo task, không gắn ngày, thời lượng hoặc lịch sprint. Vai trò do bạn xác nhận: **1 FE, 2 BE, 1 người nối tất cả các phần**. Chưa có tên thành viên nên dùng P1–P4. Tổng cộng **57 task**, bao phủ 14 module của SRS v3.1; số task không phải thước đo khối lượng bằng nhau.

Nguồn yêu cầu: [Master SRS v3.1](../../FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md), [reuse/architecture audit](../../FEAT-039-collaborative-learning-scope/artifacts/REUSE_AND_ARCHITECTURE.md), [quyết định phân công mới](../../../docs/adr/ADR-0015-four-person-role-and-integration-allocation.md). Bản phân công chi tiết là backlog đề xuất để nhận việc và lập feature implementation; yêu cầu chia vai trò đã được xác nhận, các task runtime chưa được phê duyệt triển khai.

## 1. Ai chịu trách nhiệm phần nào

| Người | Vai trò | Primary ownership | Số task |
|---|---|---|---|
| P1 — Người 1 | FE | React Native Android cho Child; UI Teacher/Admin; canvas/input/UX và component tests | 15 |
| P2 — Người 2 | BE1: hệ thống lõi | Auth/scope; trường/lớp/hồ sơ/consent; session/group/canvas/sync; gallery; assessment/portfolio; core persistence/privacy | 16 |
| P3 — Người 3 | BE2: AI và nội dung | Vision/Sketch; async jobs; knowledge/video; exact-content review; activities/content/preset/AI policy; provider adapters/copies | 14 |
| P4 — Người 4 | Tổng hợp kỹ thuật | Contract registry; composition/API connectors; nối FE–BE/worker; luồng xuyên module; môi trường chung; phối hợp E2E, đo và bàn giao | 12 |

P4 có trách nhiệm tích hợp code và tạo bản chạy chung, bao gồm các connector/entrypoint/wiring cần thiết. Lỗi logic/canvas/provider/durable adapter vẫn do owner P1/P2/P3 sửa. P4 điều phối suite xuyên hệ thống; mỗi người phải bàn giao component tests/evidence của mình. Chọn framework Teacher/Admin, DB/queue/canvas/model/provider phải theo ADR phù hợp; P4 không tự chốt stack để lấp chỗ thiếu.

Một FE sở hữu cả Android và Teacher/Admin là điểm nghẽn thực tế. Nên nhận từng tập giao diện có luồng hoàn chỉnh để nối sớm; không mở cả 34 UI responsibilities đồng thời. Các card lớn như canvas, core storage và media có thể tách subtask khi lập feature, giữ nguyên primary owner và truy vết. Độ khó của real Sketch/video/authorization không tương đương một màn hình CRUD.

## 2. Những gì đã chốt và những gate còn mở

- Giữ **FastAPI, React Native, Android tablet/điện thoại**. Pilot một trường, một lớp đồng thời tối đa 40 trẻ là mục tiêu kiểm thử. Độ tuổi 36–155 tháng đủ; hồ sơ do giáo viên quản lý, QR/mã phiên, không child login riêng.
- Nhà trường thu consent; người có thẩm quyền ghi nhận/xác minh evidence và purpose. Teacher duyệt từng Sketch trước Child access. Tablet chung chọn active child theo lượt; selected contributor không thay thế identity xác thực.
- Video đang generating phải chờ. Hết retries được phép: Teacher chọn retry/skip/end, có history; không tự fallback/skip. Mặc định session/artwork giữ 90 ngày sau session end; portfolio/profile/audit/provider/backup/device copies có policy riêng.
- OD07/08/09/10/11/14/15/16/17/18 và phần còn mở của consent/retention/capacity cần quyết định tương ứng: quay lại stage, advanced tools/imports, rubric, screen-time values, admission/offline, RN runtime/canvas/sync, models/media/retry budget, privacy jurisdiction, automatic grouping. Giữ đúng trạng thái CONFIRMED/PROPOSED/TBD của từng FR trong bảng truy vết.
- Firebase chỉ Authentication. Domain độc lập framework/provider/storage/queue/UI; cross-module qua versioned ports/contracts. Mobile không chứa credentials/endpoints S3/Lightning/Runpod. Original artwork và provenance luôn giữ riêng với derivatives.

Không đưa billing, Parent portal, social/chat, thời lượng video hoặc model cũ trở lại làm prerequisite. Replay/advanced-age UX và automatic grouping Phase 2 vẫn có task/owner; import/text/sticker TBD vẫn có refinement gate. Chưa làm extension không được ghi requirement đã hoàn thành chỉ vì feature flag tắt.

## 3. Bắt đầu độc lập, rồi nối theo đầu ra

| Người | Task có thể bắt đầu độc lập | Bàn giao đầu tiên |
|---|---|---|
| P1 | FE-01 | UI/canvas fixture runner, state/error/operation examples, Android prototype/benchmark plan |
| P2 | BE1-01 | Core domain/command/permission fixtures, ports, standalone validation runner |
| P3 | BE2-01 | AI/job/review/media fixtures, state machine và fake provider runner |
| P4 | INTG-01 | Contract/fixture registry, fake-boundary integration runner, compatibility/error map |

Bốn runner dùng synthetic data và tự chạy khi không có backend/database/provider thật hoặc output của người khác. Sau đó review chéo payload/error/version/hash, ghi những candidate được adopt và unresolved gaps. Việc review là checkpoint đầu ra, không là lịch sprint hoặc prerequisite khiến ba người phải chờ P4. Đây là nguyên tắc độc lập của ADR-0006; phân vai mới theo ADR-0015 thay nhãn discipline lịch sử.

Khi đủ các output cần cho một luồng, P4 nối ngay luồng đó theo task tích hợp tương ứng. Không phải chờ xong cả 57 task mới bắt đầu nối. Đường kỹ thuật chính: lớp/consent/join → canvas/control/recovery → gallery/knowledge/video → off-screen/reflection/portfolio. **Trợ giúp Sketch là nhánh tùy chọn**; gallery/video vẫn chạy khi trẻ không yêu cầu Sketch, với meaning được Teacher xác nhận. Admin/data lifecycle đi kèm các phạm vi tương ứng trước khi tuyên bố pilot hoàn chỉnh.

Task ID INTG-01–12 thuộc backlog này; SRS INT-01–12 là scenario kiểm thử khác. H-* là sổ bàn giao bên dưới, không phải endpoint mới hoặc một task thứ 58.

## 4. Danh mục task để nhận việc

Tất cả task cards có trạng thái **PROPOSED / NOT_STARTED (runtime)**. Bộ tài liệu phân công được hoàn thành không làm các cards thành DONE. Khi nhận card, tạo hoặc dùng owning feature, chốt plan/acceptance/approval và lưu evidence tại feature đó.

'''

FOOTER = '''
## 10. Quy tắc bàn giao và Done

Mỗi owner giao source/contract revision, versioned payload/error examples, fixture manifest/hash, hướng dẫn chạy, component positive/negative tests và evidence có thể chạy lại. Các thao tác write/retry phải có observed revision/idempotency semantics phù hợp; reject do scope/consent/stale không được UI coi là success. P4 review kết nối và đưa lỗi về đúng owner.

Các mức hoàn thành phải tách rõ: (1) contract/fixture ready; (2) component runtime verified; (3) integrated verified; (4) measured/pilot evidence theo profile được adopt. Một runner pass, screenshot hoặc stub video không chứng minh durable saves, permissions, real generation hoặc tải 40 trẻ. Chỉ ghi FR VERIFIED khi đủ evidence của chính FR đó; feature/policy còn TBD không được tuyên bố toàn bộ sản phẩm complete.

Mỗi card cần plan/acceptance và task approval trong owning feature trước implementation. Visual assets mới phải qua generated → provenance/review/approval → approved/applied. Dùng synthetic data; không commit child data thật, .env, credentials, seed users, external handbook/workbook originals hoặc rendered extracts. Trước commit/push phải chạy repository security validator; kế hoạch này không yêu cầu hoặc cấp phép commit/push/deploy.

Đầu ra cuối của P4 là bản chạy nối được các module đã bàn giao, hồ sơ contract/architecture/API khớp code và verification report. Các component owner xác nhận phần mình; pending policy/module/adapter vẫn hiển thị trong báo cáo. Các blockers ngoài feature được ghi riêng, không dùng để hạ tiêu chí nghiệm thu task đang nhận.
'''

def main() -> None:
    assert hashlib.sha256(SRS.read_bytes()).hexdigest() == PIN, 'SRS baseline changed'
    srs = SRS.read_text(encoding='utf-8')
    names = [('P1 — FE', 'FE_TASKS.md'), ('P2 — BE1 lõi', 'BE_CORE_TASKS.md'),
             ('P3 — BE2 AI/nội dung', 'BE_AI_TASKS.md'), ('P4 — tích hợp', 'INTEGRATION_TASKS.md')]
    cards: dict[str, tuple[str, str, str]] = {}
    fragments = {}
    for owner, filename in names:
        fragment = (FEATURE / 'artifacts/drafts' / filename).read_text(encoding='utf-8')
        fragments[filename] = fragment
        for m in re.finditer(r'^## ((?:FE|BE1|BE2|INTG)-\d{2}) — (.+)\n([\s\S]*?)(?=^## |\Z)', fragment, re.M):
            ident, title, body = m.groups()
            assert ident not in cards, ident
            cards[ident] = (owner, title, body.strip())
    assert set(cards) == set(DEPENDENCIES)
    ui = dict(re.findall(r'^\| ([CTA]\d{2}) \| (FE-\d{2}) \|', fragments['FE_TASKS.md'], re.M))
    cmds = dict(re.findall(r'^\| (CMD-\d{2}) \| (BE1-\d{2}) \|', fragments['BE_CORE_TASKS.md'], re.M))
    data = dict(re.findall(r'^\| (DATA-\d{2}) \| (BE1-\d{2})', fragments['BE_CORE_TASKS.md'], re.M))
    for line in fragments['BE_AI_TASKS.md'].splitlines():
        if not re.match(r'^\| BE2-\d{2} \|', line):
            continue
        cells = [x.strip() for x in line.strip('|').split('|')]
        task, route, _data, _h = cells
        if route.startswith('CMD-'):
            for cmd in re.findall(r'CMD-\d{2}', route):
                assert cmd not in cmds, cmd
                cmds[cmd] = task
    ai_data = {21: 3, 22: 2, 23: 4, 24: 5, 25: 1, 26: 7, 27: 8, 28: 10, 29: 11, 33: 12}
    data.update({f'DATA-{k:02}': f'BE2-{v:02}' for k, v in ai_data.items()})
    assert len(cards) == 57 and len(ui) == 34 and len(cmds) == 66 and len(data) == 35
    fr_meta, fr_contracts, module_meta = {}, {}, {}
    for line in srs.splitlines():
        cells = [x.strip().strip('`') for x in line.strip('|').split('|')]
        if len(cells) >= 4 and re.fullmatch(r'FR\d{3}', cells[0]):
            if not cells[1].startswith('UC-'):
                fr_meta.setdefault(cells[0], (cells[1], cells[2]))
            if len(cells) == 6 and 'CMD-' in cells[3]:
                fr_contracts[cells[0]] = cells
        if len(cells) == 3 and re.fullmatch(r'M(?:0[1-9]|1[0-4])', cells[0]):
            module_meta[cells[0]] = cells[1]
    assert len(fr_meta) == len(fr_contracts) == 66
    parts = [HEADER]
    for owner, _ in names:
        parts += [f'### {owner}\n\n| Task | Công việc |\n|---|---|\n']
        parts += [f'| {ident} | {title} |\n' for ident, (o, title, _) in cards.items() if o == owner]
        parts += ['\n']
    parts += ['## 5. Sổ bàn giao H-*\n\nHandoff gồm schema/port **candidate có version**, closed payload/errors, synthetic fixtures/hash, scope/purpose/provenance, conformance results và release note. Chỉ version đã adopt trong owning feature/ADR được dùng runtime. P4 giữ registry; producer sở hữu semantics và adapters; consumer không đọc DB producer. Contract fixtures có thể bàn giao trước live implementation, tránh vòng chờ giữa BE.\n\n| Handoff | Producer tasks | Payload/ownership boundary | Consumers |\n|---|---|---|---|\n']
    parts += [f'| {ident} | {producer} | {payload} | {consumer} |\n' for ident, producer, payload, consumer in H]
    parts += ['\nCMD-48 chỉ có một router/closed union primary ở BE2-12; content → BE2-12, preset → BE2-13, AI policy → BE2-14, non-AI organization/purpose/retention policy → BE1-15 qua versioned application port. DATA-33 envelope schema do BE2-12 duy trì, không trao quyền ghi DB của policy owner khác. CMD-59/60 primary BE1-12: query/delivery gateway gọi P3 projection/exact-review eligibility ports, không sao chép review rules hoặc truy cập DB P3. Provider-copy outcomes chưa có verified receipt phải Pending/Exception/Unsupported theo contract, không reported Deleted.\n\n']
    parts += ['## 6. Phụ thuộc để nghiệm thu implementation\n\nBảng này ghi dependency nội bộ của **chặng runtime đầy đủ**, không bắt các fixture đầu tiên chờ runtime. Cross-role producer outputs ở sổ H-* là điều kiện riêng để nối thật; UI/domain có thể dùng fake port trước đó. Gate ADR/authority/model/policy trong từng card vẫn áp dụng. Shared DATA-24 schema/review fixtures BE2-05 có từ foundation: BE2-09/12 chỉ cần phần contract này, không phụ thuộc real Sketch BE2-04/05. ProviderCopyLifecycle schema BE2-14 được review từ foundation, không phải đợi policy activation rồi mới viết adapters.\n\n<!-- DEPENDENCIES-BEGIN -->\n| Task | Task runtime nội bộ cần trước |\n|---|---|\n']
    parts += [f'| {ident} | {", ".join(deps) if deps else "Không; foundation độc lập"} |\n' for ident, deps in DEPENDENCIES.items()]
    parts += ['<!-- DEPENDENCIES-END -->\n\n## 7. Task cards chi tiết\n\n']
    for owner, _ in names:
        parts += [f'### {owner}\n\n']
        for ident, (o, title, body) in cards.items():
            if o == owner:
                parts += [f'#### {ident} — {title}\n\n{body}\n\n']
    parts += ['## 8. Ownership API, logical data và UI\n\nCác CMD/DATA/UI dưới đây là logical contract/responsibility IDs của SRS, không khẳng định đã có physical endpoint/table/screen. Mỗi ID có **một primary maintainer**; task khác consume/version-review behavior.\n\n### 8.1. 66 CMD — primary route owner\n\n<!-- CMD-OWNERS-BEGIN -->\n| CMD | Primary task | Người |\n|---|---|---|\n']
    parts += [f'| {cmd} | {task} | {"P2" if task.startswith("BE1") else "P3"} |\n' for cmd, task in sorted(cmds.items())]
    parts += ['<!-- CMD-OWNERS-END -->\n\n### 8.2. 35 DATA — primary schema/semantics maintainer\n\nDATA-04 assignment behavior thuộc BE1-03 nhưng schema BE1-04; DATA-07 lifecycle BE1-11 nhưng schema BE1-06; DATA-12 admission producer BE1-07 nhưng schema BE1-03. DATA-20 generic asset/snapshot schema BE1-10, core storage adapter BE1-02; P3 giữ derived-artifact provenance/eligibility. DATA-24 BE2-05 là shared exact review contract, publication/teaching có purpose riêng. DATA-25 durable AI jobs/adapters BE2-01 do P3 giao, không đẩy sang P2/P4. DATA-35 audit schema BE1-03, append persistence BE1-02; mọi producer emit qua versioned port.\n\n<!-- DATA-OWNERS-BEGIN -->\n| DATA | Primary task | Người |\n|---|---|---|\n']
    parts += [f'| {d} | {task} | {"P2" if task.startswith("BE1") else "P3"} |\n' for d, task in sorted(data.items())]
    parts += ['<!-- DATA-OWNERS-END -->\n\n### 8.3. 34 UI responsibilities — P1 primary\n\nC03/C05/C10 có thể là states của cùng workspace; 34 IDs không bắt buộc 34 routes độc lập. P4 nối connector nhưng P1 vẫn sở hữu UI/component behavior.\n\n<!-- UI-OWNERS-BEGIN -->\n| UI | Primary task |\n|---|---|\n']
    parts += [f'| {u} | {task} |\n' for u, task in sorted(ui.items())]
    parts += ['<!-- UI-OWNERS-END -->\n\n## 9. Truy vết toàn scope\n\n### 9.1. 14 module\n\n<!-- MODULE-TRACE-BEGIN -->\n| Module | Tên | FE | BE | Tích hợp |\n|---|---|---|---|---|\n']
    parts += [f'| {m} | {module_meta[m]} | {fe} | {be} | {integ} |\n' for m, fe, be, integ in MODULES]
    parts += ['<!-- MODULE-TRACE-END -->\n\n### 9.2. 66 FR\n\nGiữ nguyên trạng thái yêu cầu từ SRS. FE/BE tasks trong bảng được truy từ CMD/UI mapping B26.2 và semantic participants đã review, là implementation participants; cards foundation/durable/policy bổ trợ vẫn áp dụng. Truy vết không cấp approval cho FR PROPOSED/TBD. Nghiệm thu theo UC/AT cụ thể ở SRS và positive/negative trong card; tích hợp chung INTG-09/12 không thay component evidence.\n\n<!-- FR-TRACE-BEGIN -->\n| FR | Yêu cầu | Trạng thái SRS | FE | BE | Tích hợp |\n|---|---|---|---|---|---|\n']
    extra_be = {19: ['BE2-04'], 25: ['BE2-04'], 28: ['BE2-04'], 52: ['BE2-13', 'BE1-11'], 53: ['BE2-13'], 54: ['BE2-03', 'BE2-13', 'BE2-14', 'BE1-11'], 56: ['BE2-13', 'BE2-14', 'BE1-15'], 64: ['BE2-14', 'BE2-04', 'BE2-08']}
    extra_fe = {21: ['FE-04'], 28: ['FE-04'], 56: ['FE-14', 'FE-15']}
    for fr, cells in sorted(fr_contracts.items()):
        n = int(fr[2:])
        fe_tasks = {ui[u] for u in re.findall(r'\b[CTA]\d{2}\b', cells[4])}
        be_tasks = {cmds[c] for c in re.findall(r'CMD-\d{2}', cells[3])}
        fe_tasks.update(extra_fe.get(n, [])); be_tasks.update(extra_be.get(n, []))
        if n in (65,):
            integ = 'INTG-04/09; Phase 2 allocation'
        elif n <= 7 or n == 55:
            integ = 'INTG-03/08'
        elif n <= 21 or n in (60, 63, 66):
            integ = 'INTG-04/07'
        elif n <= 30 or n == 61:
            integ = 'INTG-05'
        elif n <= 40:
            integ = 'INTG-06'
        elif n <= 50:
            integ = 'INTG-07/08'
        elif n in (51, 52, 53, 54):
            integ = 'INTG-04/05/10'
        else:
            integ = 'INTG-08/10'
        desc, status = fr_meta[fr]
        parts += [f'| {fr} | {desc} | {status} | {", ".join(sorted(fe_tasks))} | {", ".join(sorted(be_tasks))} | {integ} |\n']
    parts += ['<!-- FR-TRACE-END -->\n', FOOTER]
    out = FEATURE / 'artifacts/TEAM_TASK_BREAKDOWN.md'
    out.write_text(''.join(parts), encoding='utf-8')
    manifest = {
        'artifact': out.relative_to(ROOT).as_posix(), 'srs_sha256': PIN,
        'task_counts': {prefix: sum(i.startswith(prefix + '-') for i in cards) for prefix in ('FE', 'BE1', 'BE2', 'INTG')},
        'cmd_owners': cmds, 'data_owners': data, 'ui_owners': ui,
        'dependencies': DEPENDENCIES, 'handoffs': [x[0] for x in H],
        'reviewed_fragment_sha256': {f: hashlib.sha256((FEATURE / 'artifacts/drafts' / f).read_bytes()).hexdigest() for f in fragments},
    }
    (FEATURE / 'evidence/metrics').mkdir(parents=True, exist_ok=True)
    (FEATURE / 'evidence/metrics/PLAN_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PLAN_BUILT task_count=57 CMD=66 DATA=35 UI=34 M=14 FR=66')

if __name__ == '__main__':
    main()
