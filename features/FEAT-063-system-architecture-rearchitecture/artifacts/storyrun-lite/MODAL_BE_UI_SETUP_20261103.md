# Chạy lại demo Parent: BE chính → PostgreSQL → Modal Vision

Tài liệu cho người ghép UI. Đọc cùng `MAIN_BE_UI_HANDOFF_20261103.md` và `README.md` trong thư mục này. Bản này mô tả môi trường **Windows local**, ảnh synthetic và actor Parent giả lập. Demo mặc định tắt, chỉ nhận kết nối loopback; chưa có đăng nhập Parent thật và chưa hỗ trợ UI ở máy khác. UI chạy trên browser cần cùng origin với BE; chưa cấu hình CORS cho origin khác.

Ngày 03/11, một lượt dùng BE chính và DB `sketch2life` đã đạt: upload `READY` → một POST `/v2/vision` của Modal trả 200 → `SUBJECT_REVIEW` → xác nhận 202 → `PREPARATION_REVIEW`; ledger `SUCCEEDED`. Đây là kết quả của một lượt synthetic, không phải xác nhận toàn bộ BE đã hoàn thiện. App Modal và các process tạm đã dừng; cần khởi động lại để demo.

## 1. Chuẩn bị

- Lấy bản code chứa phần tích hợp đã bàn giao; kiểm tra branch/commit với người phụ trách. Các thay đổi tại thời điểm viết còn local, chưa được push, nên checkout cũ có thể thiếu file.
- Windows, Python 3.12, PostgreSQL 17, Git, PowerShell thường và Bruno. Máy local không cần GPU để chạy model: Modal chạy GPU.
- Một DB demo `sketch2life` trên `127.0.0.1:5433` hoặc DB task `storyrun_lite_*` được cấu hình hợp lệ, user kết nối là owner. Hai URL của BE và StoryRun phải cùng host, port và tên DB. Port 5433 là cấu hình chạy thử được kiểm chứng; không mặc định máy khác dùng cùng port. Đường `sketch2life` hiện bị guard yêu cầu đúng `127.0.0.1:5433`.
- ClamAV daemon thật có database chữ ký, lắng nghe loopback; Modal CLI đã đăng nhập workspace được cấp quyền, có Volume model và Secret bên dưới. Xin người quản lý workspace cấp quyền và chuyển bearer qua kênh bí mật; không gửi token vào chat hoặc đặt trong UI/Git.
- Ảnh synthetic JPEG/PNG/WebP được phép thay đổi giữa các lượt. Bruno mẫu gửi một part tối đa 4 MiB; giới hạn đầy đủ và SHA-256 xem `README.md`.

## 2. Cài BE và chuẩn bị database

Trong PowerShell tại thư mục gốc repo, cài môi trường local:

```powershell
py -3.12 -m venv backend\.venv
Set-Location backend
.\.venv\Scripts\python.exe -m pip install -e ".[image-admission]"
```

Kiểm tra PostgreSQL đã chạy và kết nối đúng phiên bản, DB, user và owner. Đối với DB trống mới, sau khi xác nhận trạng thái và backup phù hợp, áp migration bằng cấu hình DB đã được kiểm tra; dùng `upgrade heads`, không dùng `upgrade head` khi có nhiều nhánh. Các đường cài mới, Lesson trước và StoryRun trước đã được kiểm thử có điều kiện; DB có dữ liệu hoặc schema không khớp cần kiểm tra trước, không reset/xóa để làm theo demo. Xem báo cáo `../../evidence/STORYRUN_LITE_MAIN_BE_INTEGRATION_20261103.md` và plan tương ứng để biết phạm vi migration đã kiểm chứng.

Khi đang ở `backend`, sau khi đã đặt `SKETCH2LIFE_DATABASE_URL` cho đúng DB trong session:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade heads
```

Không đưa mật khẩu trực tiếp vào lệnh hay ảnh chụp. Hai URL được tạo bằng prompt ẩn ở mục 5. Nếu DB đích không trống hoặc chưa rõ schema, dừng và nhờ người phụ trách kiểm tra trước khi chạy migration.

## 3. Cài và chạy ClamAV thật

1. Tải bản Windows portable từ [release chính thức ClamAV](https://github.com/Cisco-Talos/clamav/releases), xác minh SHA-256 theo release rồi giải nén **ngoài repo**. Lượt trước dùng 1.5.4; không sao chép chữ ký hay executable vào Git.
2. Tạo thư mục database chữ ký và file cấu hình `freshclam.conf`, `clamd.conf` theo mẫu đi kèm bản tải. Bỏ dòng `Example`, đặt `DatabaseDirectory` đến thư mục chữ ký; trong `freshclam.conf` cấu hình mirror chính thức `database.clamav.net`. Trong `clamd.conf` đặt `TCPSocket 3310`, `TCPAddr 127.0.0.1` và cùng `DatabaseDirectory`. Dùng đường dẫn tuyệt đối của máy đang cài.
3. Chạy `freshclam.exe --config-file=<đường-dẫn-freshclam.conf>` để tải chữ ký, sau đó chạy `clamd.exe --config-file=<đường-dẫn-clamd.conf>` và giữ process này mở. Kiểm tra listener `127.0.0.1:3310`; đổi port nếu bị chiếm và đặt đúng port đó ở mục 5.
4. Trước flow, xác minh daemon trả CLEAN cho ảnh synthetic. Việc kiểm tra EICAR phải theo quy trình bảo mật của môi trường; lượt đã ghi nhận CLEAN và INFECTED trong báo cáo local. Nếu scanner hoặc worker không sẵn sàng, upload không được coi là READY.

Các bước cài này là hướng dẫn vận hành; cấu hình và chữ ký cần được kiểm tra lại trên máy người nhận.

## 4. Chuẩn bị endpoint Modal

Từ repo root, tạo venv CLI riêng ngoài repo hoặc trong thư mục local bỏ qua, cài Modal và đăng nhập bằng tài khoản được cấp quyền:

```powershell
$modalVenv = Join-Path $env:LOCALAPPDATA 'Sketch2Life\modal-cli'
py -3.12 -m venv $modalVenv
& "$modalVenv\Scripts\python.exe" -m pip install "modal==1.6.3"
& "$modalVenv\Scripts\modal.exe" setup
& "$modalVenv\Scripts\modal.exe" volume list --env main
& "$modalVenv\Scripts\modal.exe" volume ls --env main sketch2life-qwen3-vl-8b-v1 /qwen3-vl-8b-instruct
& "$modalVenv\Scripts\modal.exe" secret list --env main
```

Xác nhận Volume `sketch2life-qwen3-vl-8b-v1` có model và Secret `sketch2life-modal-qwen-auth` có key `LIGHTNING_DEV_AUTH`; bearer dùng ở BE phải khớp Secret. Không tạo đè Secret hoặc tải lại model nếu chưa kiểm tra workspace. Nếu thiếu model/Secret, làm theo `features/FEAT-061-modal-qwen-vl-endpoint/evidence/MODAL_QWEN_SETUP_20261028.md` cùng người quản lý workspace. Đó là các thao tác cloud và cần quyền tương ứng.

### Tải model về máy và đưa lên Volume khi workspace chưa có

Bỏ qua phần này nếu Volume trong đúng workspace đã có đủ model. Nếu đã có bản model đúng revision trên ổ ngoài repo thì dùng lại, không cần tải. Bản cần dùng là `Qwen/Qwen3-VL-8B-Instruct`, revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`; snapshot khoảng 17,5 GB, cần thêm dung lượng cho cache và quá trình tải. Trước khi tạo Volume hay upload, xác nhận workspace và quyền với người quản lý Modal.

Trong PowerShell đã đặt `$modalVenv` ở trên:

```powershell
& "$modalVenv\Scripts\python.exe" -m pip install "huggingface_hub==2.3.0"
Get-PSDrive -PSProvider FileSystem | Select-Object Name,Root,@{Name='FreeGB';Expression={[math]::Round($_.Free / 1GB, 1)}}
$qwenModelDir = Read-Host 'Duong dan tuyet doi luu model ngoai repo'
& "$modalVenv\Scripts\hf.exe" download Qwen/Qwen3-VL-8B-Instruct --revision 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b --local-dir "$qwenModelDir"
Get-ChildItem -LiteralPath "$qwenModelDir" -Force | Select-Object Name,Length,Mode
```

Sau khi tải xong, kiểm tra `config.json`, tokenizer, processor, `model.safetensors.index.json` và đủ bốn file `model-00001-of-00004.safetensors` đến `model-00004-of-00004.safetensors`. Việc thấy đủ tên file chưa chứng minh checksum của toàn bộ model. Nếu Hugging Face yêu cầu đăng nhập, dùng cơ chế chính thức; không đưa token vào chat hoặc Git.

Chỉ tạo Volume nếu đã xác nhận Volume này chưa có trong workspace. Không tạo mới để che lỗi chọn sai workspace:

```powershell
& "$modalVenv\Scripts\modal.exe" volume create --version=2 --env main sketch2life-qwen3-vl-8b-v1
```

Upload snapshot lên Volume được phép sử dụng, rồi kiểm tra lại:

```powershell
& "$modalVenv\Scripts\modal.exe" volume put --env main sketch2life-qwen3-vl-8b-v1 "$qwenModelDir" /qwen3-vl-8b-instruct
& "$modalVenv\Scripts\modal.exe" volume ls --env main sketch2life-qwen3-vl-8b-v1 /qwen3-vl-8b-instruct
```

Đích upload không có dấu `/` cuối; kiểm tra `config.json` và các shard nằm trực tiếp dưới `/qwen3-vl-8b-instruct`. Nếu bị lồng thêm thư mục hoặc thiếu file thì dừng và kiểm tra, không upload đè tùy tiện. Model nằm trên Volume; repo không chứa weights. Endpoint đọc Volume và không tự tải model khi khởi động.

### Khởi động endpoint

Từ repo root, mở một PowerShell riêng và giữ nó chạy:

```powershell
$modalVenv = Join-Path $env:LOCALAPPDATA 'Sketch2Life\modal-cli'
& "$modalVenv\Scripts\modal.exe" serve deployment/modal/qwen_vision_v2.py
```

Lấy base URL HTTPS **mới được in ra**; URL của `serve` tạm trước không còn dùng được. Trên PowerShell khác, kiểm tra:

```powershell
$modalBase = (Read-Host 'Nhap base URL HTTPS vua duoc in').Trim().TrimEnd('/')
Invoke-RestMethod -Uri "$modalBase/health" -TimeoutSec 120
```

Kỳ vọng `status: ok`. Health có thể chờ khởi tạo container; nếu timeout, kiểm tra log/trạng thái app và quota trước khi tiếp tục. Chạy Modal có thể phát sinh chi phí GPU. Giữ cửa sổ `serve` mở trong suốt lượt demo.

## 5. Cấu hình BE và tạo run

Trên PowerShell mới, tại thư mục `backend`, đặt biến môi trường **cho process hiện tại**. Dùng user/port đúng với máy; ví dụ dưới đây áp dụng DB `sketch2life` tại `127.0.0.1:5433`. Nhập mật khẩu ở prompt ẩn; URL được escape nếu mật khẩu có ký tự đặc biệt. Không in URL sau khi tạo.

```powershell
$dbPassSecure = Read-Host 'Mat khau PostgreSQL postgres' -AsSecureString
$dbPassPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPassSecure)
try {
  $dbPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($dbPassPtr)
  $dbPassEncoded = [Uri]::EscapeDataString($dbPassPlain)
  $dbUrl = "postgresql+psycopg://postgres:${dbPassEncoded}@127.0.0.1:5433/sketch2life"
  $env:SKETCH2LIFE_DATABASE_URL = $dbUrl
  $env:STORYRUN_LITE_DATABASE_URL = $dbUrl
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($dbPassPtr)
  Remove-Variable dbPassPlain,dbPassEncoded,dbUrl,dbPassSecure,dbPassPtr -ErrorAction SilentlyContinue
}
$env:SKETCH2LIFE_ENV = 'local'
$env:STORYRUN_LITE_MAIN_DEMO_ENABLED = '1'
$env:STORYRUN_LITE_CLAMAV_HOST = '127.0.0.1'
$env:STORYRUN_LITE_CLAMAV_PORT = '3310'
$env:STORYRUN_LITE_VISION_MODE = 'loopback'
Remove-Item Env:STORYRUN_LITE_VISION_LOOPBACK_URL,Env:STORYRUN_LITE_MODAL_BASE_URL,Env:STORYRUN_LITE_MODAL_TOKEN,Env:STORYRUN_LITE_MODAL_RUN_ID -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn sketch2life.main:app --host 127.0.0.1 --port 8778
```

Nếu DB chưa migrate, dừng Uvicorn và áp migration sau preflight mục 2, rồi chạy lại. Mở `http://127.0.0.1:8778/docs` hoặc `/openapi.json` để kiểm tra routes. Import `bruno/` và chọn environment `local`. Chạy 01–05 theo `README.md` để tạo run và upload; lưu `run_ref`, ETag, revision và `asset_ref` sau khi upload `READY`. Với dữ liệu cũ có thể gặp `ACTIVE_RUN_EXISTS`; xử lý qua lifecycle đúng contract, không tự xóa DB.

**Dừng trước request 06 attach.** Mode `loopback` ở bước này chưa trỏ tới Vision stub nên chưa thực hiện inference. Dừng BE bằng Ctrl+C; giữ DB và ClamAV chạy.

Sau mỗi lần khởi động BE, kiểm tra `GET /v1/story-runs/readiness` hoặc Bruno `12-get-readiness` trước khi tiếp tục. Kỳ vọng `200` với `status: ready`; `503 SERVICE_NOT_READY` nghĩa runtime chưa cấu hình hoặc đã mất quyền giữ singleton. `/health` của BE chỉ là liveness và có thể vẫn `ok` khi StoryRun không sẵn sàng. Sau mất lock cần khởi động lại process; probe không tự reconnect hoặc lấy lại lock.

## 6. Ghim run, khởi động lại BE và gọi Modal

Trong cùng PowerShell BE, chọn đúng `run_ref` vừa tạo, base URL vừa kiểm tra và nhập bearer khớp Secret Modal bằng prompt ẩn. Không đặt URL/bearer vào code UI. Biến token tồn tại trong bộ nhớ process trong thời gian demo.

```powershell
$env:STORYRUN_LITE_VISION_MODE = 'modal_live'
$env:STORYRUN_LITE_MODAL_BASE_URL = (Read-Host 'Modal base URL HTTPS hien tai').Trim().TrimEnd('/')
$env:STORYRUN_LITE_MODAL_RUN_ID = (Read-Host 'run_ref vua tao').Trim()
$modalBearerSecure = Read-Host 'Bearer khop Modal Secret' -AsSecureString
$modalBearerPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($modalBearerSecure)
try {
  $env:STORYRUN_LITE_MODAL_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($modalBearerPtr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($modalBearerPtr)
  Remove-Variable modalBearerSecure,modalBearerPtr -ErrorAction SilentlyContinue
}
Remove-Item Env:STORYRUN_LITE_VISION_LOOPBACK_URL -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn sketch2life.main:app --host 127.0.0.1 --port 8778
```

Chạy Bruno request 06 **một lần**, rồi 07 để đọc run, 08 để xác nhận, sau đó chạy **`11-get-run-after-confirm`**. Request 11 assert `PREPARATION_REVIEW` và cập nhật ETag/revision; request 07 assert `SUBJECT_REVIEW` nên không dùng lại nó để kiểm tra sau confirm. Xác nhận phải dùng understanding revision/ETag hiện tại. `PREPARATION_REVIEW` là mốc cuối demo, chưa phải sinh truyện/video. Nếu timeout/reset hoặc kết quả không rõ sau khi đã gửi, kiểm tra run và ledger; không tự gửi lại attach hay tạo retry cho cùng attempt.

Để demo ảnh thứ hai trên cùng DB, sau request 11 hãy chạy **`09-cancel-run`** với ETag/revision hiện tại và key cancel riêng. Kỳ vọng `202`, `DELETE_PENDING`: hệ thống đóng lượt demo, nhả active-owner slot và giữ run, ảnh đã admission, kết quả, receipt cũ. Sau đó dùng các idempotency key mới để tạo run/upload mới, gửi bytes bằng request 03, complete/poll tới READY. Dừng trước request 06, khởi động lại BE với UUID của run mới tại `STORYRUN_LITE_MODAL_RUN_ID`, rồi mới attach một lần. Không xóa DB, marker hay tái sử dụng attempt cũ. Cancel không chứng minh request đã SENT ở provider được dừng.

Các bước Bruno mẫu được kiểm chứng với Vision stub; lượt Modal thật đã dùng HTTP helper tương đương, chưa chứng minh một lần chạy Bruno toàn bộ với Modal. Kiểm tra từng response thực tế thay vì suy ra kết quả từ log Modal. `repair_attempted=True` có thể xuất hiện dù chỉ có một HTTP request.

## 7. Kết thúc và bàn giao UI

Dừng BE, ClamAV và cửa sổ `modal serve`; kiểm tra app tạm đã dừng. Trong PowerShell BE xóa `STORYRUN_LITE_MODAL_TOKEN`, hai biến DB URL và đóng cửa sổ. Không commit `.env`, token, ảnh hoặc dữ liệu thật. Gửi người ghép UI `MAIN_BE_UI_HANDOFF_20261103.md`, `openapi.json` và collection Bruno; contract của main app được xem tại `/openapi.json` khi bật demo. Ghi kết quả thực tế, trạng thái ledger và những bước chưa chạy; không chụp credential.
