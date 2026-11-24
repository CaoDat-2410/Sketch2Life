"""Create an English-only derivative of the current-system SRS form."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path
from unicodedata import category, name

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.text.paragraph import Paragraph
from lxml import etree


FEATURE = Path(__file__).resolve().parents[1]
SOURCE = FEATURE / "artifacts" / "Sketch2Life_SRS_Form.docx"
OUTPUT = FEATURE / "artifacts" / "Sketch2Life_SRS_Form_English.docx"

TRANSLATIONS = {
    "FEAT-016 contracts; backend session chưa persist": "FEAT-016 contracts; backend session persistence is not implemented",
    "Backend modular monolith theo clean architecture: application/domain/contracts/interfaces/infrastructure.": "The backend is a modular monolith that follows clean architecture: application/domain/contracts/interfaces/infrastructure.",
    "Firebase Authentication cho parent/guide; backend verify token": "Firebase Authentication for Parent/Guide; the backend verifies the token",
    "Lightning dev/fixture; Runpod production target qua AiGateway": "Lightning for development/fixtures; Runpod production target through AiGateway",
    "Exact model profiles / revisions / compute profiles sau benchmark.": "Exact model profiles/revisions/compute profiles after benchmarking.",
    "Session init": "Session initialization",
    "Đặc tả yêu cầu phần mềm Sketch2Life": "Sketch2Life: Collaborative Creative Learning\nwith AI for Children",
    "Biểu mẫu SRS hiện trạng hệ thống": "Current System Software Requirements Specification",
    "Tài liệu này chuyển snapshot hiện trạng Sketch2Life thành một biểu mẫu SRS có thể chỉnh sửa. Nó mô tả product boundary, requirements, contract, flow và tiêu chí nghiệm thu theo những gì repository hiện có; các phần chưa được nối thành production vertical slice được gắn trạng thái rõ ràng.": "This document turns the current Sketch2Life snapshot into an editable software requirements specification. It describes the product boundary, requirements, contracts, workflows, and acceptance criteria supported by the repository. Capabilities not connected in a production vertical slice are clearly labeled by maturity.",
    "Mục đích sử dụng: dùng làm baseline để review phạm vi, phân biệt evidence fixture với production readiness, và ghi nhận các quyết định cần phê duyệt trước khi triển khai tiếp.": "Purpose: Use this as the scope review baseline, distinguish fixture evidence from production readiness, and record decisions that require approval before further implementation.",
    "1 Tóm tắt và mục đích": "1 Summary and Purpose",
    "Sketch2Life biến bản vẽ và lời kể của trẻ thành một trải nghiệm học tập ngắn, sau đó chuyển trẻ sang một hoạt động Montessori ngoài màn hình và thu feedback từ người lớn. Hệ thống không phải generic image generator: bản vẽ gốc phải được bảo toàn, suy luận AI phải có human review, activity phải qua các luật xác định, và Gate B phải khóa identity/version trước khi nội dung số hoặc activity vật lý được sử dụng.": "Sketch2Life turns children's drawings and narration into a short learning experience, then guides them into an off-screen Montessori activity and records adult feedback. It is not a generic image generator: the original drawing must be preserved, AI reasoning must receive human review, activities must pass deterministic rules, and Gate B must lock identity/version before digital content or physical activities are used.",
    "Kết luận hiện trạng: repository đang ở giai đoạn foundation với nhiều boundary, contract, fixture và standalone workstream đã được harden; chưa phải sản phẩm end-to-end production-ready.": "Current state: The repository is at the foundation stage. Several boundaries, contracts, fixtures, and standalone workstreams have been hardened, but the product is not end-to-end production-ready.",
    "2 Phạm vi sản phẩm và tác nhân": "2 Product Scope and Actors",
    "2.1 Trong phạm vi": "2.1 In Scope",
    "Android-only React Native app với child, parent và guide modes trong một application.": "An Android-only React Native application with Child, Parent, and Guide modes.",
    "Multimodal understanding, Gate A, P1 deterministic filter, Gate B, original-art renderer, learning-media cache/fallback, handoff và feedback.": "Multimodal understanding, Gate A, the deterministic P1 filter, Gate B, the original-art renderer, learning-media cache/fallback, activity handoff, and feedback.",
    "Versioned contracts, immutable source/derived artifact lineage, stale-version và idempotency semantics.": "Versioned contracts, immutable source/derived artifact lineage, stale-version handling, and idempotency semantics.",
    "Fixture/contract-driven evidence làm baseline cho Integration Sprint.": "Fixture- and contract-driven evidence as the baseline for the Integration Sprint.",
    "2.2 Ngoài phạm vi hoặc chưa sẵn sàng production": "2.2 Out of Scope or Not Production-Ready",
    "Firebase ID-token verification middleware, role/authorization persistence và parent/guide sign-in UI.": "Firebase ID-token verification middleware, persistent role/authorization data, and Parent/Guide sign-in UI.",
    "Camera/image picker/microphone capture, consent UX, backend session repository, migrations và persistence adapter.": "Camera/image-picker/microphone capture, consent UX, a backend session repository, migrations, and persistence adapters.",
    "S3/MinIO adapter, Redis/RQ worker, job resource API, retention/deletion job và observability production.": "S3/MinIO adapters, a Redis/RQ worker, a job resource API, retention/deletion jobs, and production observability.",
    "Runpod production adapter, model-profile freeze, live video generation, signed APK/AAB và Play Console release.": "A Runpod production adapter, frozen model profiles, live video generation, signed APK/AAB packages, and Play Console release.",
    "Qualified Montessori catalog: records hiện là synthetic/provisional và production_eligible=false.": "Qualified Montessori catalog: current records are synthetic/provisional and production_eligible=false.",
    "3 Hiện trạng hệ thống": "3 Current System State",
    "Các nhãn trong bảng dưới đây phản ánh snapshot hiện tại, không phải cam kết tiến độ. Những workstream đã pass test offline vẫn cần integration evidence trước khi được xem là production capability.": "The labels below describe the current snapshot, not delivery commitments. Workstreams that pass offline tests still require integration evidence before they can be considered production capabilities.",
    "Hình 1. Ma trận hiện trạng theo vùng hệ thống": "Figure 1. Current Maturity by System Area",
    "apps/mobile: presentation và device adapters; không giữ business truth.": "apps/mobile: presentation and device adapters; does not own business truth.",
    "backend/src/sketch2life: Python modular monolith gồm domain, application, contracts, interfaces và infrastructure.": "backend/src/sketch2life: a Python modular monolith with domain, application, contracts, interfaces, and infrastructure layers.",
    "packages/contracts: language-neutral versioned schemas và fixtures.": "packages/contracts: language-neutral, versioned schemas and fixtures.",
    "packages/domain-montessori và packages/domain-experience: domain/spec boundary và catalog fixtures.": "packages/domain-montessori and packages/domain-experience: domain/spec boundaries and catalog fixtures.",
    "packages/art-renderer: PixiJS/GSAP original-art renderer độc lập.": "packages/art-renderer: a standalone PixiJS/GSAP original-art renderer.",
    "features/: plan, approval, context, evidence và fixture isolation.": "features/: plans, approvals, context, evidence, and fixture isolation.",
    "4 Kiến trúc và topology": "4 Architecture and Topology",
    "Kiến trúc được tổ chức theo dependency direction: interface adapters đi vào application use cases và ports; application phụ thuộc domain; infrastructure implement ports; contracts được version hóa ở boundary. Modular monolith là boundary đầu tiên, chỉ tách service khi có evidence về scale, ownership hoặc reliability.": "The architecture follows inward dependency direction: interface adapters call application use cases and ports; the application depends on the domain; infrastructure implements ports; and contracts are versioned at boundaries. The modular monolith is the initial boundary. Services should be separated only when evidence supports a need for scale, ownership, or reliability.",
    "Hình 2. Topology boundary hiện tại và mục tiêu đã được chấp nhận": "Figure 2. Current Boundaries and Accepted Target Topology",
    "Đường mobile chỉ đi qua backend HTTPS. Mobile không gọi Lightning, Runpod, S3 hoặc database trực tiếp. Firebase chỉ cung cấp Authentication; backend mới là nơi verify identity và quyết định authorization.": "Mobile communicates only with the backend over HTTPS. Mobile does not call Lightning, Runpod, S3, or a database directly. Firebase provides Authentication only; the backend verifies identity and makes authorization decisions.",
    "5 Luồng nghiệp vụ chính": "5 Main Business Flows",
    "Hình 3. Luồng end-to-end từ capture đến feedback": "Figure 3. End-to-End Flow from Capture to Feedback",
    "Route hiện có: POST /v1/live-understanding. Mobile synthetic client gửi mode=live-lightning, fixture_id, session_id, expected_session_version và request_id tùy chọn. Route parse request với extra=forbid, reject provider khác lightning_dev, reject expected version khác 1 bằng STALE_SESSION_VERSION, load synthetic fixture, chạy media validation rồi tạo ASR/vision proposal.": "Current route: POST /v1/live-understanding. The mobile synthetic client sends mode=live-lightning, fixture_id, session_id, expected_session_version, and an optional request_id. The route parses the request with extra=forbid, rejects providers other than lightning_dev, rejects expected versions other than 1 with STALE_SESSION_VERSION, loads a synthetic fixture, validates media, and creates an ASR/vision proposal.",
    "Route này chưa tạo backend session aggregate, chưa persist artifact, chưa gọi P1/Gate B, chưa queue job và chưa verify Firebase trong router. Vì vậy đây là dev smoke boundary, không phải public production API.": "This route does not create a backend session aggregate, persist artifacts, invoke P1/Gate B, queue a job, or verify Firebase in the router. It is therefore a development smoke-test boundary, not a public production API.",
    "6 State machine và version semantics": "6 State Machines and Version Semantics",
    "Hình 4. Session state model trong FEAT-016 runtime fixture": "Figure 4. Session State Model in the FEAT-016 Runtime Fixture",
    "Cùng command_id replay -> trả lại snapshot tương ứng, không tăng version lần hai.": "Replaying the same command_id returns its corresponding snapshot without incrementing the version a second time.",
    "Expected session version cũ -> reject STALE_SESSION_VERSION.": "An outdated expected session version is rejected with STALE_SESSION_VERSION.",
    "Job completion/cancellation lệch version -> reject; terminal job không bị ghi đè.": "Job completion or cancellation with a mismatched version is rejected; terminal jobs are not overwritten.",
    "Renderer sequence không tăng đơn điệu -> bỏ qua; Gate A/B không được bypass bằng local flag.": "Non-monotonic renderer sequences are ignored; Gate A/B cannot be bypassed with a local flag.",
    "6.1 Contract và provenance envelope": "6.1 Contract and Provenance Envelope",
    "Các requirement dưới đây được tách thành capability đã có evidence, capability fixture/offline, và target cần integration. Reviewer nên cập nhật cột status khi có approval hoặc evidence mới.": "The requirements below distinguish capabilities with evidence, fixture/offline capabilities, and targets requiring integration. Reviewers should update the status column when new approval or evidence becomes available.",
    "9 Security privacy và data handling": "9 Security, Privacy, and Data Handling",
    "Đây là các scenario hiện có trong fixture/evidence. Cột review result là phần nhóm có thể cập nhật khi nối production vertical slice.": "These scenarios exist in fixtures/evidence. The team may update the review-result column when a production vertical slice is integrated.",
    "11 Traceability và roadmap": "11 Traceability and Roadmap",
    "Freeze shared contract registry V1, resolve ASR/vision generation split và reconcile Pixi bridge event registry.": "Freeze shared contract registry V1, resolve the ASR/vision generation split, and reconcile the Pixi bridge event registry.",
    "Wire PostgreSQL, S3-compatible storage và Redis/RQ through ports/provenance rules.": "Connect PostgreSQL, S3-compatible storage, and Redis/RQ through the defined ports and provenance rules.",
    "12 Open decisions và review form": "12 Open Decisions and Review Form",
    "Ghi chú review: ____________________________________________________________________________________": "Review notes: ____________________________________________________________________________________",
    "Phụ lục A Form cập nhật requirement": "Appendix A. Requirement Update Form",
    "Dùng mẫu này khi thêm hoặc thay đổi requirement. Mọi thay đổi behavior phải đi kèm source/contract, approval, evidence và status cập nhật.": "Use this form when adding or changing a requirement. Every behavior change must include an updated source/contract, approval, evidence, and status.",
    "Phụ lục B Nguyên tắc đọc tài liệu": "Appendix B. Reading Guide",
    "Current/implemented không đồng nghĩa production-ready.": "Current/implemented does not mean production-ready.",
    "Fixture-only là evidence có thể tái lập, không phải live provider hoặc production infrastructure.": "Fixture-only is reproducible evidence, not a live provider or production infrastructure.",
    "Accepted architecture là quyết định định hướng; implementation vẫn cần feature plan và approval riêng.": "Accepted architecture is directional; implementation still requires a separate feature plan and approval.",
    "Mọi derived artifact phải giữ provenance; original child media không bị thay thế âm thầm.": "Every derived artifact must preserve provenance; original child media is never silently replaced.",
    "Khi có mâu thuẫn, ưu tiên direct task, ADR/decision đã approved, source/evidence hiện tại, rồi mới đến external reference.": "When sources conflict, prioritize the direct task, approved ADRs/decisions, current source/evidence, and then external references.",
    "Trường": "Field", "Giá trị": "Value", "Mã tài liệu": "Document ID",
    "Phiên bản": "Version", "Ngày lập": "Prepared on", "Trạng thái": "Status",
    "Cần review và xác nhận phạm vi": "Scope review and confirmation required",
    "Snapshot nguồn": "Source snapshot", "Checkout tham chiếu": "Reference checkout",
    "Đối tượng đọc": "Audience", "Project owner, team, reviewer, người tích hợp": "Project owner, team, reviewer, and integrator",
    "Phân loại": "Classification", "Tài liệu nội bộ  |  synthetic và fixture data only": "Internal project document  |  synthetic and fixture data only",
    "Trạng thái": "Status", "Ý nghĩa trong tài liệu": "Meaning in this document",
    "Có code hoặc boundary đang chạy local; chưa mặc định là production.": "Code or a boundary runs locally; production readiness is not implied.",
    "Có harness, fixture, in-memory hoặc standalone package để kiểm thử.": "A harness, fixture, in-memory implementation, or standalone package is available for testing.",
    "Đã là quyết định kiến trúc nhưng cần integration/evidence trước khi triển khai.": "Accepted as an architectural decision, but integration/evidence is required before implementation.",
    "Chưa wire, còn phụ thuộc approval, benchmark, môi trường hoặc quyết định tiếp theo.": "Not wired; depends on approval, benchmarking, environment, or a follow-up decision.",
    "Tác nhân": "Actor", "Trách nhiệm": "Responsibility", "Trạng thái": "Status",
    "Không có account độc lập; dùng supervised session để vẽ, kể, xem experience và bắt đầu activity.": "No independent account; uses a supervised session to draw, narrate, view an experience, and start an activity.",
    "Trong fixture flow": "In fixture flow",
    "Xác thực, consent/supervision, xác nhận hoặc sửa Gate A, duyệt Gate B và gửi feedback.": "Authenticates, handles consent/supervision, confirms or corrects Gate A, approves Gate B, and submits feedback.",
    "Account model đã quyết định; UI/auth chưa wire": "Account model decided; UI/auth not wired",
    "Review Montessori, activity/objective identity/version, supervision và feedback.": "Reviews Montessori content, activity/objective identity/version, supervision, and feedback.",
    "Giữ business truth, session/artifact/job state, validation, authorization, provenance và provider adapters.": "Owns business truth, session/artifact/job state, validation, authorization, provenance, and provider adapters.",
    "Boundary/fixture hiện có; persistence còn mở": "Boundary/fixture exists; persistence remains open",
    "Lightning cho dev/fixture; Runpod là production target qua AiGateway.": "Lightning for development/fixtures; Runpod is the production target through AiGateway.",
    "Provider boundary; model profile còn benchmark-gated": "Provider boundary exists; model profile is benchmark-gated",
    "Vùng hệ thống": "System area", "Bằng chứng hiện có": "Current evidence", "Maturity": "Maturity",
    "Validators và context harness chạy local": "Validators and context harness run locally",
    "FastAPI health/live-fixture route, typed contracts, P1 admission/compiler và provider guard": "FastAPI health/live-fixture route, typed contracts, P1 admission/compiler, and provider guard",
    "Media validation, ASR/VLM contracts, fixtures và Lightning synthetic route": "Media validation, ASR/VLM contracts, fixtures, and Lightning synthetic route",
    "PixiJS + GSAP package, closed Motion DSL, provenance và fallback": "PixiJS + GSAP package, closed Motion DSL, provenance, and fallback",
    "FEAT-015 fixture flow và FEAT-016 in-memory session/job semantics": "FEAT-015 fixture flow and FEAT-016 in-memory session/job semantics",
    "Compose và Android skeleton; chưa wire auth/DB/storage/worker/signing": "Compose and Android skeleton; auth/DB/storage/worker/signing are not wired",
    "Chưa wire": "Not wired", "Hạng mục": "Item", "Baseline": "Baseline",
    "Bounded HTTP polling; bắt đầu khoảng 2 giây, backoff tối đa 10 giây, dừng ở terminal state": "Bounded HTTP polling; starts at about 2 seconds, backs off to at most 10 seconds, and stops at a terminal state",
    "PostgreSQL + S3-compatible storage + Redis/RQ là target adapters": "PostgreSQL + S3-compatible storage + Redis/RQ are target adapters",
    "Bước": "Step", "Behavior và rule": "Behavior and rule", "Maturity": "Maturity",
    "Nhận drawing và narration trong supervised session; current capture UI/device path chưa hoàn chỉnh.": "Receives drawing and narration in a supervised session; the current capture UI/device path is incomplete.",
    "Đọc bounded snapshot, hash source, inspect PNG/WAV, trả PASS hoặc RECAPTURE với reason ổn định.": "Reads a bounded snapshot, hashes the source, inspects PNG/WAV, and returns PASS or RECAPTURE with a stable reason.",
    "ASR + vision tạo proposal; live route hiện dừng trước Gate A.": "ASR + vision create a proposal; the live route currently stops before Gate A.",
    "Adult xác nhận hoặc sửa meaning; semantic anchors phải có claim provenance.": "An adult confirms or corrects the meaning; semantic anchors must include claim provenance.",
    "Deterministic safety, age/readiness, prerequisite, material, supervision và policy chạy trước model selector.": "Deterministic safety, age/readiness, prerequisite, material, supervision, and policy checks run before model selection.",
    "Adult/guide duyệt activity identity/version và learning-objective identity/version đồng thời.": "An adult/Guide approves the activity identity/version and learning-objective identity/version together.",
    "P3 original-art animation và P4 reviewed media/cache/fallback; hai artifact giữ riêng.": "P3 original-art animation and P4 reviewed media/cache/fallback; the two artifacts remain separate.",
    "Ready session phải dẫn đến off-screen activity và feedback; failure media không được xóa handoff.": "A ready session must lead to an off-screen activity and feedback; media failure must not remove the handoff.",
    "Chờ adult confirmation/correction": "Awaiting adult confirmation/correction",
    "Proposal đủ context -> Gate B; thiếu context -> CONTEXT_REQUIRED": "Sufficient proposal context -> Gate B; insufficient context -> CONTEXT_REQUIRED",
    "Chờ activity/objective identity/version approval": "Awaiting activity/objective identity/version approval",
    "Compile immutable ExperienceSpec và prepare media/renderer": "Compile immutable ExperienceSpec and prepare media/renderer",
    "ActivityHandoff READY hoặc typed blocked state": "ActivityHandoff READY or a typed blocked state",
    "Feedback đã được ghi nhận; terminal state": "Feedback recorded; terminal state",
    "Nhóm": "Group", "Field / contract": "Field / contract", "Rule": "Rule",
    "Yêu cầu": "Requirement", "Traceability": "Traceability", "Maturity": "Maturity",
    "Hệ thống phải mở supervised session cho child và giữ session version để chống stale command.": "The system must open a supervised session for the Child and retain the session version to prevent stale commands.",
    "Hệ thống phải validate image/audio trước AI; invalid media phải trả recapture reason và không gọi AI.": "The system must validate image/audio before AI processing; invalid media must return a recapture reason and must not call AI.",
    "Hệ thống phải lưu original child media immutable và gắn SHA-256 khi source AVAILABLE.": "The system must store original child media immutably and attach a SHA-256 hash when the source is AVAILABLE.",
    "Hệ thống phải tạo ASR/vision proposal từ source đã PASS và trả typed failure khi provider/schema lỗi.": "The system must create an ASR/vision proposal from a source that passed validation and return a typed failure when the provider/schema fails.",
    "Hệ thống phải yêu cầu Gate A xác nhận/correct semantic meaning trước P1.": "The system must require Gate A to confirm/correct semantic meaning before P1.",
    "P1 phải chạy hard rules về safety, age/readiness, prerequisite, material, supervision và policy trước model selection.": "P1 must apply hard rules for safety, age/readiness, prerequisites, materials, supervision, and policy before model selection.",
    "Gate B phải khóa đồng thời activity identity/version và learning-objective identity/version.": "Gate B must lock both the activity identity/version and learning-objective identity/version together.",
    "ExperienceSpec phải immutable, có canonical hash, fit evaluation và strict continuity.": "ExperienceSpec must be immutable and include a canonical hash, fit evaluation, and strict continuity.",
    "Original-art animation phải dùng source artifact/provenance và fallback whole-drawing khi extraction/mask lỗi.": "Original-art animation must use source-artifact provenance and fall back to the whole drawing if extraction/masking fails.",
    "Learning media phải resolve exact cache key và reviewed identity; miss/stale/corrupt/unsafe trả typed fallback/block.": "Learning media must resolve the exact cache key and reviewed identity; a miss/stale/corrupt/unsafe result returns a typed fallback/block.",
    "Media/provider failure không được loại bỏ off-screen activity handoff.": "Media/provider failure must not remove the off-screen activity handoff.",
    "Ready session phải đi qua Activity Bridge, start activity và feedback trước terminal completion.": "A ready session must pass through the Activity Bridge, start the activity, and record feedback before terminal completion.",
    "Backend phải verify Firebase ID token và map role/relationship trước authorization.": "The backend must verify the Firebase ID token and map the role/relationship before authorization.",
    "ADR-0005; auth adapter chưa wire": "ADR-0005; auth adapter not wired",
    "Mobile phải chỉ gọi backend HTTPS và poll backend job resource với bounded backoff.": "Mobile must call only the backend over HTTPS and poll the backend job resource with bounded backoff.",
    "Backend phải sở hữu storage, retention/deletion và artifact access; mobile không nhận S3/provider credentials.": "The backend must own storage, retention/deletion, and artifact access; mobile receives no S3/provider credentials.",
    "Runpod production provider phải được nối sau benchmark/profile freeze qua AiGateway, không thay đổi domain/application.": "The Runpod production provider must be connected through AiGateway after benchmarking/profile freeze, without changing the domain/application layers.",
    "Domain không import UI/framework/ORM/queue/provider SDK; infrastructure implement ports.": "The domain must not import UI/framework/ORM/queue/provider SDKs; infrastructure implements ports.",
    "Boundary schemas versioned; mobile types generated/derived, không tự định nghĩa business truth.": "Boundary schemas are versioned; mobile types are generated/derived and do not define business truth.",
    "Derived/generated artifact phải tham chiếu source IDs, version, hash, config, actor/reason.": "A derived/generated artifact must reference source IDs, version, hash, config, and actor/reason.",
    "Duplicate command không tăng version; stale async result không mutate state mới.": "A duplicate command does not increment the version; a stale async result does not mutate newer state.",
    "Typed failure/fallback; media failure không phá handoff.": "Typed failure/fallback; media failure does not break the handoff.",
    "Polling bắt đầu khoảng 2 giây, backoff tối đa 10 giây, dừng terminal/background; SSE/WebSocket cần ADR.": "Polling starts at about 2 seconds, backs off to at most 10 seconds, and stops at terminal/background; SSE/WebSocket requires an ADR.",
    "Mỗi workstream chạy bằng synthetic fixture/versioned contract; evidence lưu trong feature folder.": "Each workstream runs against synthetic fixtures/versioned contracts; evidence is stored in its feature folder.",
    "Catalog/activity/objective/asset chỉ dùng production sau review/benchmark/approval; current records provisional.": "Catalog/activity/objective/asset may be used in production only after review/benchmark/approval; current records are provisional.",
    "Không commit .env, token, service account, signing key, seed account hoặc real child data.": "Do not commit .env files, tokens, service accounts, signing keys, seed accounts, or real child data.",
    "Firebase chỉ dùng Authentication; cấm Storage, Firestore và Realtime Database.": "Use Firebase Authentication only; Firebase Storage, Firestore, and Realtime Database are prohibited.",
    "Mobile không chứa endpoint/credential của S3, Lightning, Runpod hoặc database.": "Mobile contains no S3, Lightning, Runpod, or database endpoint/credential.",
    "Object storage do backend ports sở hữu; mobile dùng short-lived backend-controlled references.": "Object storage is owned by backend ports; mobile uses short-lived backend-controlled references.",
    "Handbook/workbook originals và rendered extracts ở local external reference, không publish.": "External handbook/workbook originals and rendered extracts stay local and are not published.",
    "Evidence chỉ lưu hash/metadata bounded; không lưu raw image, prompt, model output, token, signed URL hoặc provider headers.": "Evidence stores only bounded hashes/metadata; it does not store raw images, prompts, model output, tokens, signed URLs, or provider headers.",
    "Consent, least privilege, retention và deletion phải được thể hiện trong session/artifact design trước production.": "Consent, least privilege, retention, and deletion must be covered in session/artifact design before production.",
    "Giữ claims; GATE_A_REQUIRED": "Preserve claims; GATE_A_REQUIRED",
    "Câu hỏi cần quyết định": "Decision question", "Người / evidence": "Owner / evidence",
    "Contract registry V1: chọn generation ASR/vision nào làm shared authority?": "Contract registry V1: which ASR/vision generation is the shared authority?",
    "Pixi bridge event registry: reconcile protocol messages với fixture lifecycle.": "Pixi bridge event registry: reconcile protocol messages with the fixture lifecycle.",
    "PostgreSQL/S3/Redis/RQ migration và persistence boundary cho Integration Sprint.": "PostgreSQL/S3/Redis/RQ migration and persistence boundary for the Integration Sprint.",
    "Consent, retention, deletion và privacy UX trước khi nhận real child data.": "Consent, retention, deletion, and privacy UX before receiving real child data.",
    "Catalog/activity/objective qualification để chuyển production_eligible=true.": "Catalog/activity/objective qualification required to set production_eligible=true.",
    "Vai trò": "Role", "Tên / chữ ký": "Name / signature", "Ngày": "Date", "Kết quả": "Result",
    "Tên: ______________________________": "Name: ______________________________",
    "Ngày: __________": "Date: __________",
    "Nội dung điền": "Entry",
    "Tên requirement": "Requirement title", "Mô tả": "Description",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def all_paragraphs(document):
    seen = set()

    def add(paragraph):
        element = paragraph._p
        if element not in seen:
            seen.add(element)
            yield paragraph

    def table_paragraphs(table):
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    yield from add(paragraph)
                for table in cell.tables:
                    yield from table_paragraphs(table)

    for paragraph in document.paragraphs:
        yield from add(paragraph)
    for table in document.tables:
        yield from table_paragraphs(table)
    for section in document.sections:
        for part in (
            section.header, section.footer, section.first_page_header,
            section.first_page_footer, section.even_page_header, section.even_page_footer,
        ):
            for paragraph in part.paragraphs:
                yield from add(paragraph)
            for table in part.tables:
                yield from table_paragraphs(table)


def replace_text(paragraph, new_text: str) -> None:
    runs = paragraph.runs
    if runs:
        runs[0].text = new_text
        for run in runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(new_text)


def set_font(run, size: float, family: str = "Arial") -> None:
    run.font.name = family
    run.font.size = Pt(size)
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(f"w:{key}"), family)
    language = rpr.find(qn("w:lang"))
    if language is None:
        language = OxmlElement("w:lang")
        rpr.append(language)
    language.set(qn("w:val"), "en-US")
    language.set(qn("w:eastAsia"), "en-US")
    language.set(qn("w:bidi"), "en-US")


def set_table_widths(table, widths) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    grid = table._tbl.tblGrid.gridCol_lst
    for column_index, width in enumerate(widths):
        twips = int(round(width.inches * 1440))
        grid[column_index].set(qn("w:w"), str(twips))
        table.columns[column_index].width = width
        for row in table.rows:
            row.cells[column_index].width = width
    table_width = table._tbl.tblPr.find(qn("w:tblW"))
    table_width.set(qn("w:type"), "dxa")
    table_width.set(qn("w:w"), str(sum(int(round(width.inches * 1440)) for width in widths)))


def add_team_section(document) -> None:
    existing = next((p for p in document.paragraphs if p.text.strip() == "1.1 Project Team"), None)
    if existing:
        return
    scope_heading = next(
        (p for p in document.paragraphs if p.text.strip() == "2 Product Scope and Actors"), None
    )
    if scope_heading is None:
        raise ValueError("Project Scope heading was not found for team insertion")
    anchor = scope_heading._p.getprevious()
    while anchor is not None and anchor.tag != qn("w:tbl"):
        anchor = anchor.getprevious()
    if anchor is None:
        anchor = scope_heading._p

    entries = [
        ("1.1 Project Team", "Heading 2"),
        ("Supervisor: Lam Huu Khanh Phuong.", "Normal"),
        ("Project members:", "Normal"),
        ("Do Cao Dat - Project Leader and Full-stack Development", "List Bullet"),
        ("Pham Tan Hieu - Backend 2", "List Bullet"),
        ("Vu Chi Bao - Frontend", "List Bullet"),
        ("Ly Anh Khoa - Backend 1", "List Bullet"),
    ]
    for text, style_name in entries:
        element = OxmlElement("w:p")
        anchor.addnext(element)
        paragraph = Paragraph(element, scope_heading._parent)
        paragraph.style = document.styles[style_name]
        paragraph.add_run(text)
        paragraph.paragraph_format.keep_together = True
        anchor = element


def add_page_number_fields(document) -> None:
    seen_parts = set()
    for section in document.sections:
        for part in (section.footer, section.first_page_footer, section.even_page_footer):
            part_name = str(part.part.partname)
            if part_name in seen_parts:
                continue
            seen_parts.add(part_name)
            paragraph = part.paragraphs[0] if part.paragraphs else part.add_paragraph()
            if any("PAGE" in (item.text or "").upper() for item in paragraph._p.xpath(".//w:instrText")):
                continue
            begin_run = paragraph.add_run()
            begin = OxmlElement("w:fldChar")
            begin.set(qn("w:fldCharType"), "begin")
            begin_run._r.append(begin)
            instruction_run = paragraph.add_run()
            instruction = OxmlElement("w:instrText")
            instruction.set(qn("xml:space"), "preserve")
            instruction.text = " PAGE "
            instruction_run._r.append(instruction)
            separator_run = paragraph.add_run()
            separator = OxmlElement("w:fldChar")
            separator.set(qn("w:fldCharType"), "separate")
            separator_run._r.append(separator)
            paragraph.add_run("1")
            end_run = paragraph.add_run()
            end = OxmlElement("w:fldChar")
            end.set(qn("w:fldCharType"), "end")
            end_run._r.append(end)


def remove_manual_page_break_before(document, heading_text: str) -> None:
    heading = next((p for p in document.paragraphs if p.text.strip() == heading_text), None)
    if heading is None:
        return
    previous = heading._p.getprevious()
    if previous is not None and previous.tag == qn("w:p") and previous.xpath('.//w:br[@w:type="page"]'):
        previous.getparent().remove(previous)


def set_all_xml_fonts(path: Path) -> None:
    temporary = path.with_suffix(".normalized.docx")
    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
        temporary, "w", zipfile.ZIP_DEFLATED
    ) as target:
        for item in source.infolist():
            content = source.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                root = etree.fromstring(content)
                changed = False
                if item.filename == "word/numbering.xml":
                    for bullet in root.iter(qn("w:lvlText")):
                        if bullet.get(qn("w:val")) == "\uf0b7":
                            bullet.set(qn("w:val"), "•")
                            changed = True
                for fonts in root.iter(qn("w:rFonts")):
                    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
                        attr = qn(f"w:{key}")
                        if fonts.get(attr) != "Arial":
                            fonts.set(attr, "Arial")
                            changed = True
                for language in root.iter(qn("w:lang")):
                    for key in ("val", "eastAsia", "bidi"):
                        attr = qn(f"w:{key}")
                        if language.get(attr) != "en-US":
                            language.set(attr, "en-US")
                            changed = True
                if changed:
                    content = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            target.writestr(item, content)
    temporary.replace(path)


def main() -> None:
    source_hash = sha256(SOURCE)
    shutil.copy2(SOURCE, OUTPUT)
    document = Document(OUTPUT)

    translated = {}
    for paragraph in all_paragraphs(document):
        original = paragraph.text
        if original in TRANSLATIONS:
            replace_text(paragraph, TRANSLATIONS[original])
            translated[original] = translated.get(original, 0) + 1
        elif original.startswith("Mục đích sử dụng:"):
            paragraph.clear()
            lead = paragraph.add_run("Purpose:")
            lead.bold = True
            paragraph.add_run(" Use this as the scope review baseline, distinguish fixture evidence from production readiness, and record decisions that require approval before further implementation.")
            translated[original] = translated.get(original, 0) + 1
        elif original.startswith("Kết luận hiện trạng:"):
            paragraph.clear()
            lead = paragraph.add_run("Current state:")
            lead.bold = True
            paragraph.add_run(" The repository is at the foundation stage. Several boundaries, contracts, fixtures, and standalone workstreams have been hardened, but the product is not end-to-end production-ready.")
            translated[original] = translated.get(original, 0) + 1
        elif original.startswith("Route này chưa"):
            paragraph.clear()
            lead = paragraph.add_run("This route does not")
            lead.bold = True
            paragraph.add_run(" create a backend session aggregate, persist artifacts, invoke P1/Gate B, queue a job, or verify Firebase in the router. It is therefore a development smoke-test boundary, not a public production API.")
            translated[original] = translated.get(original, 0) + 1
        elif original.startswith("Ghi chú review:"):
            replace_text(paragraph, original.replace("Ghi chú review:", "Review notes:"))
            translated[original] = translated.get(original, 0) + 1

    # Translate any labels with accents that were split across distinct runs or
    # that appear in headers/footers outside the body map.
    for paragraph in all_paragraphs(document):
        if "Trang " in paragraph.text:
            for run in paragraph.runs:
                run.text = run.text.replace("Trang ", "Page ")
    add_team_section(document)
    add_page_number_fields(document)
    remove_manual_page_break_before(document, "2.2 Out of Scope or Not Production-Ready")
    remove_manual_page_break_before(document, "11 Traceability and Roadmap")
    remove_manual_page_break_before(document, "9 Security, Privacy, and Data Handling")
    remove_manual_page_break_before(document, "7 Functional requirements")
    remove_manual_page_break_before(document, "Appendix A. Requirement Update Form")
    out_of_scope = next((p for p in document.paragraphs if p.text.strip() == "2.2 Out of Scope or Not Production-Ready"), None)
    if out_of_scope is not None:
        out_of_scope.paragraph_format.page_break_before = True
    live_route = next((p for p in document.paragraphs if p.text.strip() == "5.1 Live understanding dev boundary"), None)
    if live_route is not None:
        live_route.paragraph_format.page_break_before = True

    for paragraph in all_paragraphs(document):
        for run in paragraph.runs:
            original_run_text = run.text
            normalized_run_text = original_run_text
            for dash in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
                normalized_run_text = normalized_run_text.replace(dash, "-")
            if normalized_run_text != original_run_text:
                run.text = normalized_run_text
        if paragraph.text.strip().startswith("[ ]"):
            paragraph.style = document.styles["Normal"]
            paragraph.paragraph_format.left_indent = Pt(0)
            paragraph.paragraph_format.first_line_indent = Pt(0)

    for style in document.styles:
        if style.type in (WD_STYLE_TYPE.PARAGRAPH, WD_STYLE_TYPE.CHARACTER):
            size = 10
            style.font.name = "Arial"
            style.font.size = Pt(size)
            rpr = style._element.get_or_add_rPr()
            fonts = rpr.rFonts
            if fonts is None:
                fonts = OxmlElement("w:rFonts")
                rpr.insert(0, fonts)
            for key in ("ascii", "hAnsi", "eastAsia", "cs"):
                fonts.set(qn(f"w:{key}"), "Arial")

    document.styles["Normal"].font.size = Pt(10)
    for paragraph in all_paragraphs(document):
        text = paragraph.text.strip()
        if text.startswith("Figure "):
            size = 10
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(3)
            paragraph.paragraph_format.line_spacing = 1.0
        elif paragraph.style.name.startswith("Heading"):
            size = 10
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(3)
            paragraph.paragraph_format.line_spacing = 1.0
        elif paragraph.style.name == "Title":
            size = 10
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(6)
            paragraph.paragraph_format.line_spacing = 1.0
        elif paragraph.style.name in {"Header", "Footer", "Caption"}:
            size = 10
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.paragraph_format.line_spacing = 1.0
        else:
            size = 10
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(1 if paragraph.style.name.startswith("List") else 3)
            paragraph.paragraph_format.line_spacing = 1.0
            if paragraph.style.name.startswith("List"):
                paragraph.paragraph_format.keep_together = True
            if text.startswith("Current route:"):
                paragraph.paragraph_format.keep_together = True
        for run in paragraph.runs:
            set_font(run, size)
            if paragraph.style.name.startswith("Heading"):
                run.bold = True
        if paragraph.style.name == "Title":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor(24, 52, 82)

    status_table = document.tables[1]
    status_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    status_table.autofit = False
    status_widths = (Inches(1.85), Inches(5.25))
    status_grid = status_table._tbl.tblGrid.gridCol_lst
    for column_index, width in enumerate(status_widths):
        twips = int(round(width.inches * 1440))
        status_grid[column_index].set(qn("w:w"), str(twips))
        status_table.columns[column_index].width = width
        for row in status_table.rows:
            row.cells[column_index].width = width
    table_width = status_table._tbl.tblPr.find(qn("w:tblW"))
    table_width.set(qn("w:type"), "dxa")
    table_width.set(qn("w:w"), str(sum(int(round(w.inches * 1440)) for w in status_widths)))

    state_table = document.tables[6]
    state_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    state_table.autofit = False
    state_widths = (Inches(2.3), Inches(3.2), Inches(1.4))
    state_grid = state_table._tbl.tblGrid.gridCol_lst
    for column_index, width in enumerate(state_widths):
        twips = int(round(width.inches * 1440))
        state_grid[column_index].set(qn("w:w"), str(twips))
        state_table.columns[column_index].width = width
        for row in state_table.rows:
            row.cells[column_index].width = width
    state_width = state_table._tbl.tblPr.find(qn("w:tblW"))
    state_width.set(qn("w:type"), "dxa")
    state_width.set(qn("w:w"), str(sum(int(round(w.inches * 1440)) for w in state_widths)))

    set_table_widths(document.tables[3], (Inches(1.75), Inches(3.85), Inches(1.3)))
    set_table_widths(document.tables[5], (Inches(1.35), Inches(4.15), Inches(1.4)))
    set_table_widths(document.tables[8], (Inches(0.8), Inches(3.3), Inches(1.4), Inches(1.4)))
    set_table_widths(document.tables[9], (Inches(0.9), Inches(1.25), Inches(3.3), Inches(1.45)))
    set_table_widths(document.tables[11], (Inches(2.8), Inches(2.2), Inches(1.9)))
    signoff_table = document.tables[14]
    for row in signoff_table.rows[1:]:
        row.cells[1].text = "Name: ________________________"
        row.cells[2].text = "Date: _______"
    set_table_widths(signoff_table, (Inches(1.25), Inches(2.5), Inches(1.0), Inches(2.15)))
    notes_row = signoff_table.add_row()
    notes_cell = notes_row.cells[0].merge(notes_row.cells[-1])
    notes_cell.text = "Review notes: ______________________________________________"
    document_paragraphs = document.paragraphs
    notes_index = next((i for i, paragraph in enumerate(document_paragraphs) if paragraph.text.startswith("Review notes:")), None)
    if notes_index is not None:
        for paragraph in document_paragraphs[notes_index:notes_index + 3]:
            paragraph.text = ""

    for table in document.tables:
        for row_index, row in enumerate(table.rows):
            row_properties = row._tr.get_or_add_trPr()
            if row_properties.find(qn("w:cantSplit")) is None:
                row_properties.append(OxmlElement("w:cantSplit"))
            if row_index == 0 and row_properties.find(qn("w:tblHeader")) is None:
                header_flag = OxmlElement("w:tblHeader")
                header_flag.set(qn("w:val"), "true")
                row_properties.append(header_flag)
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before = Pt(0)
                    paragraph.paragraph_format.space_after = Pt(0)
                    paragraph.paragraph_format.line_spacing = 1.0
                    for run in paragraph.runs:
                        set_font(run, 10)
                        if row_index == 0:
                            run.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)
                            paragraph.paragraph_format.keep_with_next = True

    for section in document.sections:
        for part in (section.header, section.footer, section.first_page_header, section.first_page_footer):
            for paragraph in part.paragraphs:
                for run in paragraph.runs:
                    set_font(run, 10)

    document.core_properties.title = "Sketch2Life: Collaborative Creative Learning with AI for Children - Current System SRS"
    document.core_properties.subject = "English-only current-system Software Requirements Specification"
    document.save(OUTPUT)
    set_all_xml_fonts(OUTPUT)

    check = Document(OUTPUT)
    visible = "\n".join(p.text for p in all_paragraphs(check))
    remaining = sorted({
        ch for ch in visible
        if ord(ch) > 127 and "LATIN" in name(ch, "") and category(ch).startswith("L")
    })
    if remaining:
        examples = [p.text for p in all_paragraphs(check) if any(ch in p.text for ch in remaining)]
        raise ValueError(f"Non-ASCII Latin text remains: {remaining}: {examples[:8]}")
    for name_text in ("Do Cao Dat", "Pham Tan Hieu", "Vu Chi Bao", "Ly Anh Khoa", "Lam Huu Khanh Phuong"):
        if name_text not in visible:
            raise ValueError(f"Missing expected team/supervisor name: {name_text}")
    if "AI for Children" not in visible:
        raise ValueError("The English SRS title is missing AI for Children")
    if sha256(SOURCE) != source_hash:
        raise ValueError("The Vietnamese source SRS was modified")

    print({
        "source_docx": str(SOURCE),
        "source_sha256": source_hash,
        "english_docx": str(OUTPUT),
        "english_docx_sha256": sha256(OUTPUT),
        "translated_string_instances": sum(translated.values()),
        "distinct_source_strings_translated": len(translated),
        "team_members_added": 4,
        "english_text_audit": "pass",
        "font_policy": "Arial 10 pt for all editable text, including body, headings, tables, captions, header/footer and cover title",
    })


if __name__ == "__main__":
    main()
