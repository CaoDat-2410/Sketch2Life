# Lộ trình BE2 theo 14 task

- Date: 2026-10-14, Asia/Saigon
- Status: PROPOSED; runtime NOT_STARTED in this change
- Source: FEAT-040 / Master SRS v3.1 / ADR-0015
- Starting branch: `feature/be2-01-ai-job-foundation`

BE2 là **P3**, người backend thứ hai: AI, Sketch, knowledge, video, activity, content/policy. BE1 là P2: identity/classroom/session/canvas/consent/data. P4 nối các module; BE2 giữ logic/adapters/workers/component tests. Không đưa lịch giao hàng hoặc ước lượng giờ vào lộ trình.

## Thứ tự nên làm

1. **BE2-01 trước**: fixture/contract foundation. Durable jobs/outbox/queue làm follow-on riêng sau runtime decisions/approval, vẫn thuộc BE2.
2. Sau foundation có ba hướng độc lập: **BE2-02 Vision**, **BE2-07 knowledge**, **BE2-12 publication**. Shared DATA-24 review và ProviderCopyLifecycle candidates được chuẩn bị từ foundation để tránh vòng chờ.
3. Khi chuẩn bị kích hoạt provider, ưu tiên governance **BE2-12 → BE2-14**: versioned policy/limits/kill switch. Policies chưa adopt vẫn dùng named fixtures để tiến component work.
4. Luồng trợ giúp: **02 → 03 → 04 → 05 → 06**. Generation thật và per-item Teacher review là acceptance riêng.
5. Luồng knowledge/video: **07 → 08 → 09**, thêm **10** cho exhausted failure. Reviewed-library/video review làm độc lập Sketch; toàn 08 vẫn cần actual-generation evidence theo scope được duyệt.
6. Luồng content/activity: **12 → 11 / 13 / 14**. Các component có thể làm bằng fake ports song song hai luồng trên.
7. Tích hợp từng luồng khi handoff sẵn: INTG-05 assistance; INTG-06 video; INTG-07 activity; INTG-08/10 governance/operations. BE2 giao adapters/test/fixes; P4 composition và coordination.

Đây là sequencing đề xuất, không là priority đã được owner chốt. Dependency table nguồn vẫn giữ; live BE1 không là prerequisite cho fixture runners. Task count không biểu thị effort bằng nhau.

## Danh sách đầy đủ

| Task | Việc cần làm / đầu ra | Runtime nội bộ trước | Điểm nghiệm thu |
|---|---|---|---|
| BE2-01 | Job/attempt domain, DATA-25, CMD-44, completion/queue/repository/fakes/runner; durable follow-on | Không | Dedup/bounded retry/cancel/stale/scoped progress; actual restart cho chặng durable |
| BE2-02 | Vision adapter với snapshot/topic/age/context; DATA-22; CMD-34 correction | 01 | Version/hash/source đúng; inference và corrections giữ provenance riêng |
| BE2-03 | Assistance request/cancel/dedup/budget; DATA-21; CMD-32/33 | 01, 02 | Scope/turn/purpose; payload conflict; trẻ tiếp tục vẽ khi chờ |
| BE2-04 | SketchGenerator + worker thật; DATA-23; separate derivative; provider-copy hooks | 01, 02, 03 | Actual generated Sketch đúng profile; original immutable; pending review |
| BE2-05 | Moderation/per-item Teacher review; shared DATA-24; CMD-35 | 01, 04 | Exact version/hash/audience; edit invalidates; Child fetch cũng gated |
| BE2-06 | CMD-36 Child view/hide/decline | 05 | Đúng turn/audience; không sửa original hoặc tự tạo request mới |
| BE2-07 | Knowledge/source claims và script versioning; DATA-26; CMD-38/39 | 01 | Facts có nguồn; imagination riêng; edits có version/invalidation |
| BE2-08 | LibraryResolver/VideoGenerator/MediaValidator/workers; DATA-27; CMD-40 | 01, 07 | Library + actual generation evidence; rights/encoding/safety; final review; truthful waiting/progress |
| BE2-09 | CMD-41/42 final Teacher video review + authorized playback | 08; shared DATA-24 fixtures | Exact video/script/hash/audience; old approval/URL không bypass edit/revoke |
| BE2-10 | DATA-28; CMD-43 exhausted failure retry/skip/end | 01, 08 | Teacher explicit action/reason/receipt; không auto-skip hoặc giả generated success |
| BE2-11 | DATA-29; CMD-45 activity discovery/adaptation/execution | 01, 12 | Published catalog; tuổi từng trẻ/safety/material/prerequisite; edits có lineage |
| BE2-12 | DATA-33; sole CMD-48 typed dispatcher; draft/review/publish/recall | 01; shared DATA-24 fixtures | Publication review khác session review; correct capabilities; recall chặn use |
| BE2-13 | Versioned preset, conditional automation, Teacher override; CMD-48 preset branch | 01, 12 | Pinned config/epochs; stale intents; automation không bypass review/consent |
| BE2-14 | AI config/limits/kill switch; CMD-48 AI branch; ProviderCopyLifecycle contract | 01, 12 | Backend-only secrets; version/cancel/redaction; actual purge cần verified receipt |

Số 01–14 trong dependency là BE2-xx. DATA-24 primary owner BE2-05, nhưng schema-only fixtures có từ foundation; BE2-09/12 không cần real Sketch runtime. ProviderCopyLifecycle primary owner BE2-14; BE2-01 fake support, BE2-04/08 provider-specific hooks.

## Handoff và ownership

BE2 primary 14 CMD contracts: CMD-32–36, CMD-38–45, CMD-48; 10 DTO: DATA-21–29 và DATA-33. BE2-04 không thêm public route; 13/14 là branches qua sole CMD-48 dispatcher BE2-12. Non-AI core-policy branch do BE1-15 qua port.

| Nhận từ BE1 | Nội dung |
|---|---|
| H-IDENTITY | Verified principal/device grant, organization/scope/capability |
| H-CLASS-CONSENT | Audience, tuổi 36–155 tháng, consent/purpose revisions và revoke |
| H-SESSION-CONTROL | Session/stage/config epochs, transitions/cancel/clock |
| H-CANVAS-SYNC | Immutable checkpoint/snapshot/version/hash, topic/region/context |
| H-GALLERY | Pinned artwork/meaning/contributors/audience cho knowledge |
| Generic artifact/audit/lifecycle | DATA-20 refs/access; DATA-35 audit; DATA-34 scoped data-request authority |

Phát H-AI-REVIEW, H-KNOWLEDGE-VIDEO, H-ACTIVITY, H-CONTENT-PRESET, AI H-ADMIN-POLICY, H-OPERATIONS và provider-copy H-DATA-REQUEST. Mỗi pack có schema/version, fixtures/hash, errors, consumer example, reports và compatibility/adoption note.

BE1 CMD-59/60 giữ read/delivery gateway; BE2 giao projection/exact-review eligibility. BE1 giữ data-request authority/core storage purge; BE2 giữ provider discovery/cancel/purge verification/adapters; P4 nối ports. Các module không đọc/ghi DB nhau để thay handoff.

## Tái sử dụng và phần còn thiếu

| Existing source | Có thể dùng | Cần bổ sung |
|---|---|---|
| Vision/Qwen transport + validated schemas | Provider mapping/error patterns | New snapshot/context/consent/age + quality benchmark |
| WorkflowJobV1 / StoryVideoJobService / whiteboard job | State/failure/cancel/dedup examples | DATA-25 general job/attempt/receipts/current eligibility/durable runtime |
| JobStore / InMemoryJobStore | Interface/copy isolation/fake CAS patterns | Specialized semantics/conformance/durable adapters |
| Legacy catalog/semantic/media/renderer | Source/library/recommendation/adapter references | Publication/mixed-age/per-session exact review và new generation evidence |

Chi tiết paths trong `../evidence/notes/SOURCE_AUDIT.md`. Legacy under-9/Parent/payment/fixed model/video assumptions không là target v3.1.

## Điểm bàn giao từng luồng

| Mốc | BE2 phải giao | Xác nhận được |
|---|---|---|
| Foundation | Runner, DATA-25/states/errors/receipts, schema pack, ports | Independent contract/component ready, chưa live/durable |
| Assistance | Vision→request→Sketch→moderation→review→Child response | Component faults + actual generation; INTG-05 nối FE/BE1 |
| Video | Knowledge/script→library/generation→review→play→retry/skip/end | Source/rights/final review/access/waiting + actual generation; INTG-06 |
| Activity/content | Published compatible catalog→Teacher adaptation/execution refs | H-ACTIVITY/content conformance; INTG-07 nối off-screen/reflection của owner khác |
| Governance/runtime | Policies/preset/kill switch, durable jobs, copy hooks/receipts | Actual adapters/recovery/load decisions/evidence; INTG-08/10/11 |

BE2 tự chạy component/adapter/fault tests. Fixture pass, LightningAI environment ready, real model pass và device/visual acceptance ghi riêng. Việc đầu tiên sau duyệt Phase A revision 1 là A1–A9 trong `PLAN.md`; các card sau lập plan/approval/evidence riêng.
