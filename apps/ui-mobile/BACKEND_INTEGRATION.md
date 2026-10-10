# HƯỚNG DẪN KẾT NỐI BACKEND (BACKEND INTEGRATION GUIDE)
### Dành cho Technical Leader & Backend Engineers — Dự Án Sketch2Life

Tài liệu này hướng dẫn chi tiết cách kết nối hệ thống **Backend (BE)** vào ứng dụng di động **Sketch2Life Mobile (FE)** theo chuẩn RESTful API, khớp 100% với **Sơ đồ Workflow 8 bước (Image 3)**.

---

## 1. Cấu Hình Nhanh (Quick Setup)

File cấu hình tập trung nằm tại:
📁 `src/config/apiConfig.ts`

```typescript
export const API_CONFIG = {
  // 1. Địa chỉ máy chủ Backend của bạn:
  // - Khi test cùng máy tính: 'http://localhost:8000/api'
  // - Khi test trên Android Emulator: 'http://10.0.2.2:8000/api'
  // - Khi test qua điện thoại thật (cùng mạng Wi-Fi): 'http://<IP_MÁY_BẠN>:8000/api' (ví dụ: 'http://192.168.1.15:8000/api')
  BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api',

  // 2. Cờ chuyển đổi Mock / Real API:
  // - USE_MOCK_API: true  --> Sử dụng Mock Data nội bộ (FE tự chạy mượt mà ngay cả khi chưa bật BE)
  // - USE_MOCK_API: false --> GỌI TRỰC TIẾP VÀO BACKEND CỦA BẠN!
  USE_MOCK_API: false,

  // 3. Thời gian chờ tối đa (timeout):
  TIMEOUT_MS: 15000,
};
```

> **💡 Lưu ý:** Chỉ cần đổi `USE_MOCK_API: false` và điền `BASE_URL`, toàn bộ các màn hình trên ứng dụng sẽ tự động gửi request HTTP thật đến Backend của bạn. Nếu Backend gặp sự cố hoặc timeout, ứng dụng có cơ chế tự động fallback thông minh để không làm gián đoạn trải nghiệm người dùng.

---

## 2. Danh Sách API Endpoints (Theo Workflow 8 Bước)

| Bước | Endpoint | Method | Chức Năng | Screen Tương Ứng |
| :--- | :--- | :---: | :--- | :--- |
| **Bước 1** | `/api/children` | `GET` | Lấy danh sách hồ sơ bé (`An`, `Bảo`) | 4. Child Profile |
| **Bước 1** | `/api/drawings/upload` | `POST` | Tải lên ảnh tranh vẽ của bé | 5. Capture / Upload |
| **Bước 1** | `/api/voice/transcribe` | `POST` | Nhận diện giọng nói thành văn bản (Whisper ASR) | 6. Voice Recording |
| **Bước 2** | `/api/story/scene-understanding` | `GET` | Phân tích tranh + lời kể (Human Gate A) | 8. Scene Understanding |
| **Bước 5 & 6**| `/api/story/video` | `GET` | Lấy danh sách phân đoạn cảnh và video câu chuyện | 9. Story & 10. Video |
| **Bước 3** | `/api/activities/recommend` | `GET` | Gợi ý hoạt động Montessori theo độ tuổi (Human Gate B) | 11. Activity Recommend |
| **Bước 7** | `/api/activities/:id` | `GET` | Chi tiết nguyên liệu & các bước thực hành ngoài đời | 12. Activity Detail |
| **Bước 8** | `/api/activities/:id/feedback`| `POST` | Lưu đánh giá phụ huynh, cập nhật lịch sử học tập | 13. Feedback Loop |

---

## 3. Đặc Tả Request & Response JSON Chi Tiết

### 1. Lấy Danh Sách Trẻ Em
- **Endpoint:** `GET /api/children`
- **Response `200 OK`:**
```json
[
  {
    "id": "child-1",
    "name": "An",
    "age": 5,
    "ageGroup": "5-6",
    "avatar": "👧",
    "recentStoriesCount": 4
  },
  {
    "id": "child-2",
    "name": "Bảo",
    "age": 7,
    "ageGroup": "7-8",
    "avatar": "👦",
    "recentStoriesCount": 2
  }
]
```

---

### 2. Tải Lên Tranh Vẽ (Upload Drawing)
- **Endpoint:** `POST /api/drawings/upload`
- **Content-Type:** `application/json` hoặc `multipart/form-data`
- **Request Body:**
```json
{
  "childId": "child-1",
  "imageBase64": "data:image/jpeg;base64,...",
  "title": "Bức vẽ chú bướm của bé An"
}
```
- **Response `200 OK`:**
```json
{
  "drawingId": "draw-178955",
  "imageUrl": "https://storage.sketch2life.vn/drawings/draw-178955.png",
  "uploadedAt": "2026-09-16T09:30:00Z",
  "detectedLabels": ["butterfly", "flower", "sun", "meadow"]
}
```

---

### 3. Nhận Diện Giọng Nói Kể Chuyện (Whisper ASR)
- **Endpoint:** `POST /api/voice/transcribe`
- **Request Body:**
```json
{
  "drawingId": "draw-178955",
  "audioUri": "file:///path/to/record.m4a",
  "durationSeconds": 14
}
```
- **Response `200 OK`:**
```json
{
  "audioId": "audio-88912",
  "transcript": "Chú bướm bay đến bông hoa, ở một khu vườn đầy nắng. Chúng mình cùng chơi và khám phá thế giới xung quanh nhé!",
  "durationSeconds": 14,
  "confidence": 0.985
}
```

---

### 4. Hiểu Tranh & Kiểm Duyệt An Toàn (Human Gate A)
- **Endpoint:** `GET /api/story/scene-understanding?storyId={id}`
- **Response `200 OK`:**
```json
{
  "storyId": "story-butterfly-01",
  "storyTitle": "Giấc mơ của chú bướm",
  "storySubtitle": "Một câu chuyện từ bức vẽ của bé An",
  "entities": [
    { "id": "e1", "name": "Con bướm", "count": 1, "icon": "🦋", "category": "animal" },
    { "id": "e2", "name": "Bông hoa", "count": 2, "icon": "🌷", "category": "plant" },
    { "id": "e3", "name": "Mặt trời", "count": 1, "icon": "☀️", "category": "nature" },
    { "id": "e4", "name": "Bãi cỏ", "count": 1, "icon": "🌿", "category": "nature" }
  ],
  "voiceTranscript": "Chú bướm bay đến bông hoa, ở một khu vườn đầy nắng. Chúng mình cùng chơi và khám phá thế giới xung quanh nhé!",
  "complimentTitle": "Thật tuyệt vời!",
  "complimentSub": "Bé An có một câu chuyện rất sống động và đầy cảm xúc! ♡"
}
```

---

### 5. Gợi Ý Hoạt Động Montessori Ngoài Đời (Human Gate B)
- **Endpoint:** `GET /api/activities/recommend?age=5-6`
- **Response `200 OK`:**
```json
[
  {
    "id": "act-butterfly-craft",
    "title": "Tự làm bướm sắc màu",
    "subtitle": "Khéo tay tạo nên những cánh bướm đầy sắc màu như trong câu chuyện!",
    "ageGroup": "5–6 tuổi",
    "durationMinutes": 30,
    "category": "Sáng tạo & Khéo léo",
    "materials": [
      { "id": "m1", "name": "Giấy màu", "type": "paper", "isReady": true },
      { "id": "m2", "name": "Kéo an toàn", "type": "scissors", "isReady": true },
      { "id": "m3", "name": "Bút màu", "type": "crayon", "isReady": true },
      { "id": "m4", "name": "Keo dán", "type": "glue", "isReady": true }
    ],
    "steps": [
      { "stepNumber": 1, "title": "Cắt cánh bướm theo mẫu hoặc tự vẽ", "isDone": true },
      { "stepNumber": 2, "title": "Trang trí cánh bướm bằng màu sắc yêu thích", "isDone": true },
      { "stepNumber": 3, "title": "Gắn thân bướm và râu", "isDone": false },
      { "stepNumber": 4, "title": "Hoàn thiện và cùng nhau trưng bày!", "isDone": false }
    ],
    "safetyNotes": [
      "Nên có sự đồng hành của người lớn",
      "Sử dụng kéo an toàn, góc tròn cho trẻ mầm non"
    ],
    "parentTips": "Hãy cùng con trò chuyện về màu sắc, thiên nhiên và những loài côn trùng xung quanh nhé! ♡"
  }
]
```

---

### 6. Lưu Đánh Giá Phụ Huynh (Step 8 Feedback Loop)
- **Endpoint:** `POST /api/activities/:id/feedback`
- **Request Body:**
```json
{
  "activityId": "act-butterfly-craft",
  "childId": "child-1",
  "completionStatus": "completed",
  "interestScore": 5,
  "independenceScore": 4,
  "selectedObservationTags": [
    "Nhớ vòi bướm hút mật",
    "Tự tay dán cánh"
  ],
  "parentNotes": "Bé An rất vui khi cầm chú bướm giấy tự làm đi quanh nhà vờ như bướm bay hút mật hoa!"
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "message": "Cập nhật nhật ký học tập thành công!",
  "feedbackId": "fb-992182",
  "savedAt": "2026-09-16T10:15:00Z"
}
```

---

## 4. Lệnh cURL Mẫu Để Leader Kiểm Thử Độc Lập

```bash
# 1. Test API Trẻ em
curl -X GET http://localhost:8000/api/children

# 2. Test Phân tích tranh & lời kể
curl -X GET "http://localhost:8000/api/story/scene-understanding?storyId=story-butterfly-01"

# 3. Test Gợi ý hoạt động Montessori
curl -X GET "http://localhost:8000/api/activities/recommend?age=5-6"

# 4. Test Gửi Feedback Loop
curl -X POST http://localhost:8000/api/activities/act-butterfly-craft/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "activityId": "act-butterfly-craft",
    "childId": "child-1",
    "completionStatus": "completed",
    "interestScore": 5,
    "independenceScore": 4,
    "selectedObservationTags": ["Nhớ vòi bướm hút mật", "Tự tay dán cánh"],
    "parentNotes": "Bé An rất hào hứng!"
  }'
```

---

## 5. Tổ Chức Mã Nguồn Frontend Liên Quan

- `src/config/apiConfig.ts`: Cấu hình URL và cờ Mock/Real.
- `src/services/api.types.ts`: Toàn bộ TypeScript Data Contracts.
- `src/services/api.ts`: API Client sử dụng `fetch` hỗ trợ Timeout, AbortController và Fallback.
- `src/services/mockData.ts`: Dữ liệu mock đạt chuẩn cho toàn bộ app.
- `src/context/AppContext.tsx`: State Provider gắn kết dữ liệu người dùng với giao diện.
