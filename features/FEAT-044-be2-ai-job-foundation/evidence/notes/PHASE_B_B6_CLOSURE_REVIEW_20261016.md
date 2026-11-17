# Phase B B6 — independent closure review — 2026-10-16

- **Verdict: CLOSE_WITH_NOTES.** B6 đóng ở phạm vi component, gắn với source manifest
  `90724453b77b0cbf3a5843f1e78165a27155a8f76eb832ca0324e6a753a9dfec` (46 file). Phase B B1–B6
  đóng ở phạm vi component; B-12 là HANDOFF, không phải PASS. **BE2-01 vẫn IN_PROGRESS, không DONE.**
- Findings: 0 H / 1 M / 4 L. Không finding nào làm mất hiệu lực bằng chứng runtime b6fix01.
- Reviewer: Claude, một phiên review riêng (side session, khởi chạy từ phiên
  `local_a8250e46-35a7-493d-91c2-6237b57a6c2c` chỉ với brief). Phiên này không viết code B6, không
  viết fix01, không làm pre-run review. Kết luận dưới đây lấy từ code, package và bằng chứng, không
  lấy từ kết luận của tác giả. **Giới hạn độc lập:** tách phiên, không tách nhà cung cấp/model —
  cùng họ model với tác giả.
- Thời điểm: 2026-10-16 ~02:10 Asia/Saigon. Thực thi: direct local, Windows, root venv Python 3.12.10,
  `PYTHONPATH`/`MYPYPATH` trỏ `backend/src` của worktree (import origin đã kiểm). Không có PostgreSQL/
  Redis local ⇒ mọi case PG/Redis là **NOT_RUN** (skip không phải PASS).
- Authority: plan rev3 `plan/PHASE_B_PLAN.md` sha256 `bb20d5be…` (khớp), approval
  `approvals/PHASE_B_TASK_APPROVAL.md` (không sửa). Receipts (ignored):
  `evidence/local/b6-closure-review-20261016/`.

## 1. Phạm vi và đầu vào

Đã đọc: AGENTS.md; plan rev3 §4, §7.1, §8; `PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md` (toàn bộ);
`PHASE_B_B6_HANDOFF_20261016.md`; DECISIONS 116–121; STATUS; metrics
`PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.json`; bảng crash-window B1
(`PHASE_B_B1_PROPOSED_SEQUENCES.md` §8); bảng A-01..A-20 của `plan/PLAN.md`.

Code đã review đầy đủ:

| File | sha256 (worktree = manifest 90724453) |
|---|---|
| `features/FEAT-044-be2-ai-job-foundation/src/run_durable_conformance.py` | `c89595b3…710f97` |
| `backend/tests/integration/ai_jobs/test_restart_recovery.py` | `6e616cb6…f4e35b0` |
| `backend/tests/unit/test_ai_job_b6_conformance.py` | `b9065ff5…72f3defd` |

Cùng với: script Studio `evidence/local/b6fix01-studio-package-20261016/run_b6fix01_on_studio.sh`
(`55695aef…`), hồ sơ Codex `evidence/local/b6-codex-review-20261016/`, hai bản output Studio do user
dán lại trong `evidence/local/b6-fix01-20261016/`.

## 2. Code B6 và mapping (mục kiểm 1)

**A-01..A-20** khớp bảng `plan/PLAN.md` A-01..A-20: A-03..A-17 chạy trên SQL adapter thật (DB clone
từ template đã migrate, RQ queue riêng, HMAC thật, owner fixture ASSUMED_CONTRACT), assert đọc lại từ
SQL; A-01 = provenance (import origin, PG 17, Redis, nhãn fence, manifest); A-02/A-19/A-20 =
contract_only (NOT_APPLICABLE, do fixture runner sở hữu và B-11 tiêu thụ); A-18 = DEFERRED (BE2-14,
khớp loại trừ plan §3); A-17-http = optional (FAIL vẫn làm exit 1). Phân loại hợp lý.

**W01–W10** khớp đúng 10 dòng plan §7.1. W11 (completion write boundary) và W12 (crash mid-notice) là
bổ sung của B6 — xem B6-CR02 về W11. W07 được đánh dấu bounded (không claim journal), đúng plan.

**B-01..B-12** khớp plan §8; mọi pattern trỏ tới test có thật (unit test
`test_every_mapped_pattern_names_an_existing_integration_test` kiểm điều này; tôi kiểm lại bằng tay
toàn bộ 85 hàm test integration). B-06 lấy từ ma trận W; B-10 cần các durable scenario; B-11 cần
migrations + Phase A JUnit + fixture report.

**Có báo PASS giả không?**
- Bên trong runner: không có fallback sang fake; không có service ⇒ NOT_RUN, exit 2 (đã chạy lại:
  exit 2, 40 NOT_RUN, 0 FAIL); scenario ném exception ⇒ check FAIL; skip của test được map ⇒
  NOT_RUN; FAIL bất kỳ item nào (kể cả optional) ⇒ exit 1; required ≠ PASS ⇒ exit 2
  (`run_durable_conformance.py:137-144`). **B-12 luôn HANDOFF** (`:406-408`, không có nhánh nào khác).
- Nhưng runner **đứng một mình** không phải là gate tự đủ — xem **B6-CR01 (M)**. Trong run b6fix01,
  các khe hở này được script package bù hoàn toàn, nên RUNNER_RESULT=PASS là hợp lệ.

## 3. B6-RT01 và bản sửa (mục kiểm 2)

- Nguyên nhân xác nhận: child gửi object `Attempt` qua pipe (`test_restart_recovery.py:136` bản cũ),
  parent dùng nó làm tham số SQL ở `:156` ⇒ psycopg `cannot adapt type 'Attempt'`.
- Delta `b6fix01_delta.patch` (`11e238c7…`) đúng một dòng: `"attempt": attempt` →
  `"attempt": attempt.attempt_id`. `b6fix01_previous` và `b6fix01_source` chỉ khác nhau ở đúng file
  này.
- Probe độc lập của phiên này (P5, decision logic): cho đúng test đó FAIL ⇒ tập FAIL là
  {B-01, B-06, W02, W08}, **trùng khớp** run 1. Một test lỗi giải thích cả bốn dòng FAIL.
- Lỗi tương tự còn không: không. Payload child giờ toàn `str` (checksum, job id, attempt id,
  receipt id, `fingerprint: str` theo `application/ports/ai_jobs.py:160`, artifact ref). Đối số
  spawn (URL, `CapabilityKey`, `Connection`) không đi vào SQL. W01/W06 không gửi object domain nào.
  Fixture `rq_queue` skip đúng khi thiếu Redis (`b4_support.py:38`). Cả 3 test restart đã PASS trên
  PostgreSQL ở run b6fix01.

## 4. Bằng chứng runtime (mục kiểm 3)

**Hash manifest:** `sha256sum -c evidence/local/b6fix01-studio-package-20261016/b6fix01_source.sha256`
từ gốc worktree: **46/46 OK, exit 0**. 46 file này đúng bằng 14 file tracked đã sửa + 32 file
untracked trong `backend/` và `src/`, `fixtures/` của FEAT-044 (không có code thay đổi ngoài manifest).
Hash package khớp evidence §9.4: delta `11e238c7`, previous `3940e529`, source `90724453`, runner
`55695aef`, ZIP `e813a48b`.

**Run 1 (USER_REPORTED_REMOTE, FAIL):** 201 passed / 1 failed / 0 skipped; durable exit 1, FAIL
W02/W08/B-01/B-06; RUNNER_RESULT=FAIL. Ghi nhận là FAIL, không ghi đè. (Về độ trung thực của bản
ghi, xem B6-CR03.)

**Run b6fix01 (USER_REPORTED_REMOTE, PASS):** đối chiếu nội bộ output được dán:
- source_state `b6_snapshot` → apply delta → manifest 90724453, `source_files_ok=46` trước mỗi suite;
- 202 passed / 0 failed / 0 skipped; số test theo từng file khớp số hàm/param ở worktree (integration
  107 = 2+11+6+8+6+11+18+7+4+10+3+21; unit 95 = 14+18+29+28+6) — run local của tôi cho cùng số theo
  từng module (chỉ khác: PG/Redis skip);
- Phase A 224 / 0 skipped; fixture 20 PASS / 215, `d17f58a3`;
- durable: 45 item, required 39/39 PASS, 127 checks = tổng checks của A-01, A-03..A-17, A-17-http
  (5+10+4+3+4+4+6+5+5+10+3+13+27+13+4+7+4); B-12 HANDOFF;
- mọi exit 0, skips 0, `RUNNER_RESULT=PASS`, `studio_command_exit=0`.

Giới hạn: đây là output user dán lại; receipts Studio (`junit-b2-b6.xml`, `durable-conformance.json`)
**không có ở local** nên hash `afe8b512…`/`205d2017…` chỉ là "as reported", không tính lại được.
Studio đã tắt sau run — Docker services/network/venv volume có thể mất; mọi runtime sau phải bắt đầu
bằng inventory.

**Gate bên ngoài bù cho runner** (`run_b6fix01_on_studio.sh`): pin hash manifest/delta/previous và
`sha256sum -c` trước B2–B6, Phase A, durable (`:34-36`, `:76-80`); lệnh pytest cố định toàn bộ suite
(`:96-100`, `:107-111`); bắt exit pytest ≠ 0 (`:153-155`); bắt dòng "N skipped" (`:81`, `:103`,
`:114`); fixture report sinh trong cùng run (`:117-118`); durable runner nhận đúng manifest package
(`:124-127`). Vì vậy kết luận PASS đứng trên **RUNNER_RESULT của package**, không chỉ trên
`durable_runner_exit=0`.

## 5. Hòa giải hồ sơ review B6 của Codex (mục kiểm 4)

| File (ignored, `evidence/local/b6-codex-review-20261016/`) | mtime (+07) | Nội dung |
|---|---|---|
| `restart/probe_restart_payload.json` | 01:21:54 | Tái hiện đúng B6-RT01 (`:136,156`, "cannot adapt type 'Attempt'") |
| `report/report_probe_results.json` | 01:23:34 | Chứng minh runner đứng một mình nhận JUnit thiếu, JUnit Phase A không liên quan, fixture 0 check, manifest rỗng; ghi `expected_any_failure_exit_code: 1` |
| `package/review_summary.json` | 01:24:49 | `result: PASS`, `actionable_findings: []`, `actual_b6_pg_redis: NOT_RUN` |

**Kết luận:** hồ sơ Codex **INCONSISTENT / INCOMPLETE**. Summary được ghi *sau* cả hai probe nhưng
không mang theo finding nào của chúng; phạm vi của summary là package/host-simulation và guard của
pipeline, không phải logic runner hay PostgreSQL. Không thể xác định từ hồ sơ Codex có thấy output run
1 (bắt đầu 01:19:36 giờ Studio) hay không. Do đó:
- Hồ sơ này **không được tính là Codex PASS cho B6** và không dùng làm bằng chứng closure.
- Hai probe của Codex là chẩn đoán hợp lệ, tái lập được: RT01 → đã sửa ở b6fix01 và được run b6fix01
  chứng minh trên PostgreSQL ⇒ **B6-RT01 CLOSED**; khe hở runner → mang sang **B6-CR01** dưới đây
  (phiên này tự tái lập bằng probe riêng, không dùng file của Codex).

## 6. Tính độc lập (mục kiểm 5)

Pre-run review b6fix01 (DECISIONS 121, evidence §10) là **AUTHOR_SELF_REVIEW** và không được tính là
review độc lập ở đây. Review này không dựa vào verdict §10/§11 của tác giả; các khẳng định §10.2/§10.3
(trace dòng 142–173, probe in-memory) chỉ được xác nhận gián tiếp qua run b6fix01 trên PostgreSQL.

## 7. Findings

### B6-CR01 (M) — Runner durable đứng một mình không phải gate tự đủ

- Vị trí: `run_durable_conformance.py:192-215` (`resolve_tests`: một case khớp là đủ cho pattern
  wildcard), `:412-422` (`phase_a_status`: JUnit bất kỳ có ≥1 case pass là PASS), `:425-433`
  (`fixture_status`: report 0 check là PASS), `:838-847` (A-01: manifest rỗng/thiếu file vẫn PASS, hash
  manifest không được pin), `:1540-1551` (không có điều kiện "JUnit toàn bộ pass, 0 skip").
- Tình huống hỏng cụ thể (probe phiên này, `b6_closure_probe.json`, giả định durable scenario PASS):
  - P1: test B-06(d) `test_rolled_back_round_and_foreign_lineage_produce_no_quarantine` FAIL, còn lại
    pass ⇒ **exit 0**, không item nào FAIL. 16/85 test integration và toàn bộ unit B3–B6 không được
    pattern nào tham chiếu.
  - P2: JUnit thiếu 3 test `test_dispatch_recovery` (chạy `-k` hoặc suite crash giữa chừng) ⇒ B-04
    PASS, **exit 0**.
  - P3/P4: fixture report 0 check ⇒ PASS; JUnit Phase A 1 test bất kỳ ⇒ PASS.
  - P7: manifest rỗng ⇒ check A-01 "every source manifest hash matches" PASS.
  - Hệ quả: nếu runner được dùng lại ngoài package (dev, CI, Studio khác) với suite bị thu hẹp hoặc
    input nhầm, nó in "B-0x PASS" và exit 0 dù có test fail/thiếu.
- Vì sao không chặn closure B6: run b6fix01 được bọc bởi guard package (§4), và output cho thấy suite
  đầy đủ 202/0/0. Evidence §4 nói "a skipped **mapped** test" — đúng về mặt chữ, nhưng DECISIONS 117
  ("resolved only from this run's own JUnit") và câu "Exit 1 if anything fails" dễ bị đọc là runner tự
  đảm bảo điều đó.
- Điều kiện còn lại: không hồ sơ nào được trích `durable_runner_exit=0` hay dòng B-xx của runner làm
  bằng chứng nếu không kèm `RUNNER_RESULT` của package bao quanh. Trước khi runner thành gate dùng lại
  (card review/dev/CI), owner chọn: (a) giữ nguyên, ghi nhận giới hạn; hoặc (b) làm cứng runner (JUnit
  phải 0 fail/0 skip trên mọi case + inventory test kỳ vọng; pin hash manifest và cấm rỗng; inventory
  Phase A; fixture checks > 0) — (b) đổi file trong manifest nên cần package và run Studio mới.

### B6-CR02 (L) — Truy vết mapping chưa khớp hoàn toàn với plan/B1

- B-06(d) ("no quarantine delivery from loser/rolled-back work; owned-lineage refs") không có test chính
  trong mapping: `test_audit_durability.py:239` không thuộc W nào, còn B-06 (`:307`) chỉ lấy từ W01–W12.
- W11 của B6 (`:276-278`, completion write boundary) khác dòng 11 của bảng crash-window B1 đã review
  (`PHASE_B_B1_PROPOSED_SEQUENCES.md:390`: create race, loser rollback/restart giữa các round, B-03a–f).
  Dòng B1 #11 vẫn được phủ qua B-03 `test_b03*` (gồm `test_b03f_restart_between_rounds…`), nhưng việc
  đánh số lại không được ghi. Evidence §3 gọi W01–W12 là "plan §7.1", trong khi §7.1 chỉ có 10 dòng.
- B-05(e) phần log dispatcher (`test_outbox_dispatch.py:110`) không được map vào B-05 (A-17 có kiểm log
  toàn bộ luồng dispatch+worker nên phần lớn được phủ).
- Không mất phủ trong run này: mọi test trên đều chạy và PASS trong 202/0/0.

### B6-CR03 (L) — Bản ghi run 1 ghi "verbatim" nhưng đã bị rút gọn và chú thích

`evidence/local/b6-fix01-20261016/studio_b6_run1_user_report.txt:2` ghi "Verbatim summary", nhưng
dòng `:42-45` gộp các dòng W/B (runner in mỗi item một dòng), `:54-57` mất đường dẫn file, và đoạn
`:61-68` có chú thích của người ghi ("child sent the Attempt object…", "Earlier assertions… passed").
Nội dung thực chất nhất quán (probe P5 và probe Codex tái lập đúng), nên không ảnh hưởng verdict; nhãn
nên là "condensed/annotated". Bản ghi run b6fix01 đã ghi rõ phần bị lược (dòng 1–5) — đúng chuẩn.

### B6-CR04 (L) — Docstring/usage và lý do NOT_RUN của runner gây hiểu nhầm

- `run_durable_conformance.py:5` hướng dẫn `[--junit B2_B6.xml] [--junit PHASE_A.xml]`, nhưng Phase A
  phải dùng `--phase-a-junit` (`:1517`). Làm theo docstring sẽ trộn Phase A vào B2–B6 và B-11 NOT_RUN
  (exit 2) — fail-closed, nhưng sai hướng dẫn.
- `:362`: W bị NOT_RUN vì skip vẫn có lý do "mapped tests did not all pass", dễ đọc thành FAIL.

### B6-CR05 (L) — Đầu CONTEXT.md đã cũ

`CONTEXT.md:4-9` vẫn ghi `Q01/B6_READY_FOR_HANDOFF`, "B6 NOT_STARTED", manifest `3930046b`. Phiên này
thêm trạng thái hiện tại lên đầu và đánh dấu khối cũ là superseded (không xóa lịch sử).

### Quan sát (không phải finding)

- O-1 của tác giả xác nhận: `backend/pyproject.toml:85` `addopts = "-q"` triệt `-v`.
- ruff trên 3 file B6: PASS với `--config backend/pyproject.toml` từ gốc repo; chạy từ `backend/` cho
  8 I001 do nhận diện first-party phụ thuộc cwd — chỉ là ngữ cảnh gọi, không phải lỗi code.
- Nửa "client completion" của A-17 chỉ nằm ở A-17-http (optional) trong runner durable; trên Studio
  A-17-http PASS, và fixture runner Phase A vẫn phủ trên fakes.

## 8. Kiểm tra phiên này đã chạy (local, NOT_RUN cho PG/Redis)

| Kiểm tra | Kết quả |
|---|---|
| Import origin | `backend/src/sketch2life/__init__.py` của worktree |
| Manifest 90724453 `sha256sum -c` | 46/46 OK, exit 0 |
| B2–B6 pytest (`-o addopts=`) | exit 0: 103 passed, 99 skipped — 99 là PG/Redis **NOT_RUN** (gồm 3 test restart); B6 unit 6/6 PASS |
| Phase A suites | exit 0: 223 passed, 1 skipped (Pillow) |
| Fixture runner | exit 0, 20 PASS / 215, `d17f58a3` |
| Durable runner, không service, với JUnit local | exit **2**: 40 NOT_RUN, 0 FAIL, A-18 DEFERRED, 3 NOT_APPLICABLE, B-12 HANDOFF |
| Probe decision logic (P1–P8) | xem B6-CR01; P5 = tập FAIL run 1; P8 exit 2, B-12 HANDOFF |
| mypy 3 file B6 | 0 issue |
| ruff 3 file B6 (`--config backend/pyproject.toml`) | PASS |
| validate_harness / architecture / skeleton / repository_security | exit 0 / 0 / 0 / 0 |
| `git diff --check`; staged | sạch; 0 file staged |

## 9. Giới hạn (giữ nguyên, không ẩn)

- OwnerFence, audit sink, artifact sink là **ASSUMED_CONTRACT**; tích hợp owner thật là B-12 (P2/BE1).
- **B-12 HANDOFF**, không PASS: live router, provider, xóa copy thật, chính sách production, deploy,
  ký duyệt vai trò P1/P2/P4.
- W07 bounded: không claim journal, provider có thể chạy hai lần.
- Bằng chứng runtime là USER_REPORTED_REMOTE; receipts Studio không có ở local; Studio đã tắt.
- Closure gắn với bytes manifest 90724453 đang **chưa commit**. Bất kỳ thay đổi nào trước khi commit
  làm closure mất hiệu lực cho file đó; nên `sha256sum -c` lại ngay trước commit.

## 10. Bước tiếp theo

1. Recorder/owner ghi quyết định closure B6 (DECISIONS) nếu chấp nhận verdict này; owner chọn (a)/(b)
   cho B6-CR01. Phiên này không sửa DECISIONS, metrics, approvals, plan hay code.
2. Review card BE2-01 (toàn card, không chỉ B6), rồi tích hợp vào `dev` theo decision 116 (một nhánh
   đã review cho mỗi card; nhánh card tiếp theo tạo từ `dev` mới). Kế hoạch publication
   (COMMIT_PLAN_V2) vẫn chờ user.
3. Không đánh dấu BE2-01 DONE. Không staging, commit, push hay deploy trong phiên này.
