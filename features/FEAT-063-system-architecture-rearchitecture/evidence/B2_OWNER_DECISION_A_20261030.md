# B2 — Owner decision A: Parent activity ordering (2026-10-30)

> Quyết định sản phẩm hẹp: **Q1=A đã chốt**. **Q2–Q8 chỉ là GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận**. Tài liệu này ghi quyết định, không sửa các nguồn hiện có, không sign-off SRS/register, không cấp quyền implementation/runtime.

## 1. Nguồn và thời điểm ghi nhận

- Người quyết định: **project owner**, chỉ thị trực tiếp ngày **2026-10-30**, source ID `owner-b2-option-a-directive-20261030`.
- Nguyên văn lựa chọn: “Parent không chọn hoạt động trước video; danh sách hoạt động của lesson hiện sau khi video xem được; Teacher vẫn ghim đúng một hoạt động đã duyệt trước video mẫu.”
- Thời điểm ghi nhận từ đồng hồ máy: **2026-10-30T23:59:14+07:00** (offset +07:00). Đây là lúc ghi nhận, không khẳng định là thời điểm chính xác owner gửi chỉ thị; nguồn chỉ cho biết ngày của chỉ thị.
- Chỉ thị hiện tại cho phép tạo đúng bản ghi này và plan B2A. Chưa có approval riêng cho bước followup này; owner yêu cầu không chờ và không sửa TASK_APPROVAL, sẽ ghi sau theo hash báo cuối.
- Đã đọc AGENTS Commit boundary và .codex/sketch2life-harness; nhánh `feature/feat063-be-foundation`. Thực thi hiện tại chỉ tạo tài liệu; không stage/commit/push/stash.

## 2. Preflight S0 và nguồn ghim

Ba hash B2 khớp giá trị owner cung cấp; tám file local khớp prefix. Các thay đổi có sẵn trong AGENTS/.codex/approval/B2 plan/B2 outputs và local owner được giữ nguyên.

| Tài liệu được giữ nguyên | SHA-256 thực tế khớp S0 |
| --- | --- |
| features/FEAT-063-system-architecture-rearchitecture/plan/B2_PARENT_ACTIVITY_ORDER_PLAN_20261030.md | AAD0459FAA7FE7BF053198FEC41CA13CB713F3D5774AC83546B3793862E47A1F |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B2_PARENT_ACTIVITY_ORDER_CROSSWALK_20261030.md | A17246115412A2413BE646F9DB8F16E8BC21B12950F792851322E913E3308514 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B2_PARENT_ACTIVITY_ORDER_INVENTORY_20261030.csv | F88D11E3F3348B646D7D1C3399A7555A5E64A3B67C71D083E3606C8C819A4A02 |

| File | S0 SHA-256 (16 đầu) | Cuối task |
| --- | --- | --- |
| docs/context/SOURCE_REGISTER.md | 26990af90db093ea | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | 98040aa6871048f6 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md | c67f37133de35ded | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/DEV_REMOTE_HISTORY_COMPARISON_20261030.md | adcc6724ebc3c642 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md | 8bbfd0edaa7cd6a2 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md | b61b06074665ba71 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md | 93374e9643649b67 | KHỚP (giữ nguyên) |
| features/FEAT-063-system-architecture-rearchitecture/plan/S1_DECISION_CARD_20261030.md | 4d95d3031f8af163 | KHỚP (giữ nguyên) |

Căn cứ dưới đây được đối chiếu lại tại source trước khi trích. Đây là căn cứ và lịch sử đã cân nhắc, không phải thay thế nguồn quyết định trực tiếp ở §1.

| Căn cứ | Nguồn repo-relative:dòng | Nội dung/giới hạn |
| --- | --- | --- |
| Rev25 | features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md:35–44 (scope :42) | Scope documentation-only đã ghi outdoor activities sau video; approval lịch sử giữ nguyên. |
| Q151 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2628 | \| Q151 \| Vẽ, sketch optional khi bật, chụp, video theo pipeline, rồi activities. \| §31.5; FR-PL-15–16 \| |
| D-99 | features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:104 | \| D-99 \| Parent sequence is drawing, optional line-sketch while the child draws, capture, child-specific video pipeline, then the lesson activity list. Teacher line-sketch is also generated only when enabled in session; this supersedes D-91/D-92’s assumption that the Teacher deck is a required main-flow step. Keep the Teacher occurrence/sample flow with one randomly selected eligible child and one pinned activity. \| Owner answers Q151/Q155/Q167/Q184–Q186; Q167 supersedes the Teacher-deck status in D-91/D-92 \| |
| ADR22 | docs/adr/ADR-0022-platform-lesson-library-and-sharing.md:41–42 | - Parent flow remains: child draws; while drawing an adult may enable a line-sketch guide; after drawing, capture the child artwork; run the existing VLM/story/storyboard/review/image-to-video/safety pipeline; then show the lesson outdoor activity list. |
| BR-08/09/15 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:215/216/222 | Parent lesson list sau video; Teacher sample vẫn pin đúng một activity đã duyệt. |
| FR-P-05 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:455 | \| FR-P-05 \| M \| Sau video, hiển thị một hoặc nhiều hoạt động ngoài trời gắn với lesson version, gồm vật liệu/cách làm/ghi chú; activity catalog thêm có thể được đề xuất bởi AI nhưng cần review. Không yêu cầu Parent chọn activity trước khi tạo video. \| |
| FR-PL-16 / AC-05/52 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:2541/1041/2589 | Đã mở lại các dòng, Parent draw/capture/video rồi lesson list; Teacher sample pin trước. |
| Lý do ngược đã cân nhắc | features/FEAT-063-system-architecture-rearchitecture/evidence/B2_PARENT_ACTIVITY_ORDER_CROSSWALK_20261030.md §S4 | UC-02/pipeline v2.2 có input activity cụ thể; A cần role split và lesson binding chưa đủ. C thêm nhánh hint; chưa chọn C. |

D-99 và UC-02 (:1321) từng mâu thuẫn; lựa chọn A của owner nay chốt hướng ordering. Nguồn chưa được sửa và các chi tiết vẫn chờ Q2–Q8. D-99 cite Q155 không được dùng làm bằng chứng ordering: Q151 nói ordering, Q155 (:2632) vẫn là tiếng Việt trước. Không viết lại D-99 hay approval lịch sử.

## 3. Q1–Q8: quyết định và giả định tách rõ

| Câu | Trạng thái | Nội dung hiện tại | Ranh giới / còn chờ |
| --- | --- | --- | --- |
| Q1 | ĐÃ CHỐT | A: Parent không chọn activity trước video; list lesson hiện sau video xem được; Teacher pin đúng một activity đã duyệt trước video mẫu. | Chỉ thị trực tiếp owner ngày 2026-10-30. |
| Q2 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Typed opaque lesson-version ref tùy chọn qua owner port; không dùng org/class/Teacher occurrence cho Parent. Vị trí lưu chưa chốt. Run không lesson không tự sinh list hoặc fallback catalog. | Chờ owner: có no-lesson không; lesson source/version/hash, nơi lưu ref và nghĩa câu cấm Parent lesson ref. |
| Q3 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Theo A, Parent không cần scalar activity làm tiền điều kiện; Teacher vẫn pin. Không tự xác định field removal, NULL/CHECK hoặc thời điểm/vị trí ghi ref. | Nhánh B trong S6 không áp dụng vì đã chọn A; role representation và schema contract vẫn chờ owner. |
| Q4 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Tách quyền read catalog/lesson preview với bước chọn activity làm điều kiện video; A không có bước chọn, list của run chỉ lộ hậu video. | Chờ owner xác nhận read/preview/projection; giả định này không cấp quyền mới. |
| Q5 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Dùng VIDEO_READY sau technical/safety, không cần xem hết; current video còn được phép playback. Complete giữ read hợp lệ; hide/cancel/delete thu hồi projection theo contract. | Chờ owner: exact ready/viewed/complete/replacement behavior; 'video xem được' trong Q1 không tự chốt các chi tiết này. |
| Q6 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Giữ version/lineage metadata nhưng kiểm quyền hiện hành trước nội dung; không fallback public catalog hoặc trả nội dung đã revoke. Policy media/list tách riêng. | Chờ owner: unpublish/revoke khi đang render và sau pin/playback. |
| Q7 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Role-specific input: Parent không buộc activity, Teacher đúng một approved activity. Prompt/input/stale semantics và lesson direction Parent chưa freeze. | Không nhập optional hint của C vào A. Mặc định role split là giả định; chỉ việc không có bước chọn Parent thuộc Q1 đã chốt. |
| Q8 | GIẢ ĐỊNH LÀM VIỆC - chưa xác nhận | Lập kế hoạch/approval riêng để hòa giải nguồn, giữ history và Q155 nghĩa tiếng Việt, dùng Q151 cho ordering; cập nhật B1 cần quyền riêng. | Chỉ thị lượt này chỉ cho tạo hai tài liệu: đã cho phép lập plan nhưng chưa xác nhận toàn bộ mặc định Q8 hoặc quyền sửa nguồn/B1. |

Quyết định A không đưa optional activity/hint trước video của C vào flow. Một giả định trong bảng không trở thành quyết định vì được dùng để soạn plan. Approval cho plan sau này cũng không tự xác nhận Q2–Q8 nếu owner không nói rõ từng nội dung.

## 4. Hiệu lực theo bảy nhóm

Lấy từ cột A của crosswalk B2 §S3; phần chi tiết vượt Q1 luôn được giữ ở mức giả định.

| Nhóm | Hiệu lực ordering đã chọn | Chi tiết chưa chốt / chưa được làm |
| --- | --- | --- |
| API | Không có bước chọn/xác nhận activity Parent trước video; Teacher pin giữ. | Payload, lesson-version/ref và projection chờ Q2/Q3/Q4/Q5/Q6; không freeze endpoint/DTO. |
| Schema | A không cho dùng activity đã chọn làm precondition Parent. | Đề xuất scalar trống/theo role chỉ là Q3; NULL/CHECK, ref lesson, cột/bảng/FK chưa được chọn (Q2/Q3). |
| State | Bỏ activity-selection prerequisite của Parent trước story/video; Teacher sample giữ activity đã duyệt. | Trigger/state representation theo role chờ Q3/Q7; không tự mở hoặc chạy state machine. |
| UI | Bỏ selector activity trước video Parent, list lesson hiện khi video xem được; Teacher trước sample. | Quyền preview và behavior ready/complete/hide/revoke chờ Q4/Q5/Q6. |
| AC/UC | UC/AC phải thể hiện thứ tự A và Teacher pin riêng. | Các ca lesson/no-lesson/quyền/projection/role contract chờ Q2–Q7; đây chưa là test đã chạy. |
| Pipeline stage 4 | Không có bước chọn activity của Parent để làm điều kiện lập story; Teacher pin giữ. | Mặc định role-specific payload/prompt và lesson direction chờ Q2/Q7; không tự lấy activity đầu tiên. |
| B1 | 16 dòng tiếp tục blocked_by=B2. | Chỉ cập nhật sau hòa giải nguồn/contract cần thiết, chốt câu hỏi chặn và approval B1 riêng; không coi A tự mở khóa API. |

## 5. Trạng thái B1 và pilot

| Dòng B1 | Trạng thái hiện tại | Điều kiện để xem xét cập nhật |
| --- | --- | --- |
| T018 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T019 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T020 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T021 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T022 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T023 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T024 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T025 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T026 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T027 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T028 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T029 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T030 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T031 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T046 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |
| T047 | VẪN blocked_by=B2; E0; pilot=N | Hòa giải source/contract, chốt câu hỏi chặn của dòng và có approval mới cho B1. |

Không sửa B1 CSV/MD hoặc tự gỡ bất kỳ blocker nào. Q1=A chỉ quyết định hướng; chưa chứng minh API/contract đã hoàn thiện. FEAT-064 loại Parent/Teacher mới và StoryRun tại `features/FEAT-064-current-flow-modal-vision-dev/plan/PLAN.md:34`; quyết định này không mở rộng, chặn hoặc cấp quyền pilot. Rev36:60–61/71 vẫn là bản kế hoạch lịch sử được giữ nguyên.

## 6. Giới hạn và việc tiếp theo

Không sửa SRS/register/ADR/DECISIONS/approval/plan cũ/B0/B1/B2 hoặc code; không cấp quyền đọc mới; không chọn NULL/CHECK/FK/provider; không chứng minh runtime/quality. Giữ Rev25/Q151, Teacher pin, Q155 nghĩa tiếng Việt, preserved v2.2 và các diagram/PDF cũ là snapshot lịch sử. Không tự cập nhật diagram/PDF cho có vẻ đồng bộ.

Bước tài liệu kế tiếp là owner rà plan `plan/B2A_SRS_REGISTER_AMENDMENT_PLAN_20261030.md` (DRAFT / AWAITING_APPROVAL), xác nhận các câu hỏi chặn, rồi ghi approval pin đúng hash nếu muốn áp dụng. Cập nhật B1 là một bước khác cần approval riêng.

## 7. Kiểm tra của lượt tạo tài liệu

Kết quả thật của lượt tạo hai tài liệu:

| Lệnh | Output/verdict thật | Exit |
| --- | --- | --- |
| python tools/validate_harness.py | HARNESS_VALID; approval_gate=enabled; frontend_asset_gate=enabled | 0 |
| python tools/validate_repository_security.py | REPOSITORY_SECURITY_VALID; publishable_files_scanned=5930; absolute_machine_paths=absent | 0 |
| python tools/validate_architecture.py | ARCHITECTURE_VALID; python_dependency_direction/mobile_feature_isolation/frontend_asset_gate/mobile_ai_boundary valid; firebase_data_products=absent | 0 |
| git diff --check | stdout rỗng | 0 |

Không chép root máy từ stdout vào file. git diff --check không quét untracked; hai file mới được kiểm riêng UTF-8/LF, 0 dòng trailing whitespace, không có mẫu absolute path hoặc secret. Kiểm nguồn: 45/45 clause context khớp source đã mở; coverage 36/36 PRE/AMB (35 có đề xuất, R36:61 giữ lịch sử). 3 thao tác chỉ Q1, 42 thao tác chờ Q2–Q8; không áp dụng thao tác nào vào nguồn.

So lại baseline: **143/145 file giữ nguyên hash**; hai file hướng dẫn `AGENTS.md` và `.claude/sketch2life-harness.md` đổi trong lúc task chạy. Phiên này không ghi hai file đó; chưa xác minh tiến trình nào đã ghi. Đồng thời owner cung cấp AGENTS mới trong chat; đã đọc lại `.codex/*harness*.md` trước, rồi AGENTS và harness Claude. Không khôi phục hoặc ghi đè thay đổi bên ngoài. **8/8 local và mọi source sản phẩm/B0/B1/B2/plan/approval giữ nguyên hash.** Phiên này chỉ ghi hai đầu ra mới; working tree còn drift hướng dẫn ngoài task. Không stage/commit/push/stash hoặc test/dịch vụ. Đây là kiểm tài liệu, không nghiệm thu amendment/runtime; Q2–Q8 và approval áp dụng plan vẫn chưa được xác minh.

