# Báo cáo sửa assertion B2 T12 — 2026-11-05

## Cổng bắt đầu

- Nhánh: `feature/feat063-be-foundation`.
- HEAD trước và sau sửa: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`.
- Addendum append-only `B2 scope addendum — test_be1_postgres_api.py:305/309 contract assertions` có trong `approvals/TASK_APPROVAL.md` và ghi rõ owner/Person 2 đã duyệt.
- SHA-256 trước sửa khớp baseline yêu cầu: `EA34F05E03F8925B55542455660A34CE0E8EC1976FA6CA0170A78DB290FD576B`.

## Thay đổi

Trong file `backend/tests/integration/test_be1_postgres_api.py`, lượt này chỉ thay hai assertion response artifact. Assertion upload kiểm tra response `default`, media `application/json`, schema ref `Be1Error`, và cả ba mã 413, 415, 503 trong description của `default`. Assertion download kiểm tra cùng response shape và mã 410 trong description.

```diff
@@ upload response assertion @@
-    assert {"413", "415", "503"}.issubset(upload_response)
+    assert (
+        "default" in upload_response
+        and "application/json" in upload_response["default"]["content"]
+        and upload_response["default"]["content"]["application/json"]["schema"]
+        == {"$ref": "#/components/schemas/Be1Error"}
+        and all(
+            status_code in upload_response["default"]["description"]
+            for status_code in ("413", "415", "503")
+        )
+    )
@@ download response assertion @@
-    assert "410" in download_response
+    assert (
+        "default" in download_response
+        and "application/json" in download_response["default"]["content"]
+        and download_response["default"]["content"]["application/json"]["schema"]
+        == {"$ref": "#/components/schemas/Be1Error"}
+        and "410" in download_response["default"]["description"]
+    )
```

Nguồn hợp đồng là `backend/tests/contract/test_openapi_contract_catalog.py` khoảng dòng 309–323: operation BE1 giữ riêng response thành công/401/403/422, còn các mã khác được gộp trong `default`; description liệt kê các mã và JSON schema trỏ tới `Be1Error`. Đây là assertion test lệch hợp đồng đã công bố, không phải lỗi runtime. Các thay đổi local có sẵn ở assertion đếm 55/60 và khối import dirty được giữ nguyên.

## Hash

| Trạng thái file | SHA-256 |
| --- | --- |
| Trước sửa | `EA34F05E03F8925B55542455660A34CE0E8EC1976FA6CA0170A78DB290FD576B` |
| Sau sửa | `49F14546F4A3B6684466CAF7215CE35466548E90AF11E5F1604BE4C343033E0E` |

## Kiểm tra offline

- Ruff trước sửa: `backend/.venv/Scripts/ruff.exe check --no-cache tests/integration/test_be1_postgres_api.py` báo một `I001` ở khối import local có sẵn (dòng 315); exit 1. Lệnh dùng cache thông thường không tạo được file cache tạm vì `Access is denied`.
- Ruff sau sửa: cùng lệnh không cache báo đúng một `I001` ở khối import không đổi (dòng 330); exit 1. Không sửa I001.
- Mypy trước và sau: `backend/.venv/Scripts/mypy.exe --no-incremental tests/integration/test_be1_postgres_api.py` trả `INTERNAL ERROR`, exit 1 cả hai lần. Tool không xuất diagnostic của source nên không có số lỗi type trước/sau để đối chiếu; baseline không cho phép phân tích type.
- Test hợp đồng: `backend/.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-b2-t12-contract-20261105 tests/contract/test_openapi_contract_catalog.py` — `3 passed in 15.71s`, exit 0.
- `python tools/validate_harness.py` — `HARNESS_VALID`, approval gate và frontend asset gate bật, exit 0.
- `python tools/validate_repository_security.py` (chạy lại sau khi thêm report) — `REPOSITORY_SECURITY_VALID`; quét 6.424 publishable files; loại trừ environment files, seed accounts, credentials/signing keys và external reference documents; không có absolute machine paths; exit 0.
- `python tools/validate_architecture.py` — `ARCHITECTURE_VALID`; dependency direction, mobile feature isolation, frontend asset gate, mobile AI boundary hợp lệ; không có Firebase data products; exit 0.
- `git diff --check` — exit 0, không có lỗi whitespace. Git phát cảnh báo CRLF-to-LF cho các file dirty có sẵn thuộc context, decisions, source register, approval, ledger và status của FEAT-063/FEAT-064.

## Trạng thái dừng

PostgreSQL NOT RUN, owner-run required. `OWNER_MODAL_CALL_APPROVED` giữ `NO`. Trạng thái: **XONG-CHƯA REVIEW / WAITING_FOR_OWNER_T12_RERUN**. Không tuyên bố T12 hoặc B2 accepted; owner cần chạy lại T12, sau đó chờ independent review.
