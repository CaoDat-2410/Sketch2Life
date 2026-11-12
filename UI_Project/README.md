# Sketch2Life UI Project

Thư mục này gom các source UI hiện có cho bốn role, các giao diện dùng chung và trải nghiệm riêng cho trẻ:

- `parent-ui` — Parent web preview.
- `parent-android/apps/ui-mobile` — giao diện mobile Expo/React Native cùng màn hình và assets.
- `parent-android/apps/mobile` — app React Native/Android native và luồng fixture hiện tại.
- `parent-android/packages/art-renderer` — package renderer nội bộ dùng bởi workspace mobile.
- `teacher-ui` — Teacher web.
- `school-manager-ui` — School Manager web.
- `platform-admin-ui` — Platform Admin web.
- `web-ui` — cổng web chung, gồm đăng nhập/kích hoạt cho ba role web.
- `shared` — shell, dashboard, role flows và style dùng chung.
- `design-references` — mockup màn hình và bảng component/motion Rev38 để tham khảo; không phải implementation/API contract.
- `child-experience` — ứng dụng UI dành riêng cho trải nghiệm của trẻ trong checkout dự án.

Hai thư mục `parent-android/apps/ui-mobile` và `parent-android/apps/mobile` là hai workspace mobile riêng biệt có sẵn trong source; chúng được giữ riêng, không gộp code vào nhau.

## Chạy các workspace web

Yêu cầu Node.js và npm tương thích với các phiên bản trong `package.json`.

Tại thư mục gốc:

```powershell
npm ci
npm run build
npm run dev
```

`npm run dev` mở các preview ở cổng 5171–5175. Có thể chạy riêng bằng `npm run dev:parent`, `npm run dev:teacher`, `npm run dev:manager`, `npm run dev:admin` hoặc `npm run dev:web`.

## Chạy Parent mobile

Tại `parent-android`:

```powershell
pnpm install
pnpm start
```

Lệnh này chạy app `@sketch2life/mobile`. Để chạy workspace Expo UI, dùng `pnpm start:ui-mobile`. Với Android SDK/emulator đã cấu hình, `pnpm android` chạy app native; `pnpm android:ui-mobile` chạy app Expo Android.

## Chạy Child experience

Tại `child-experience`:

```powershell
npm ci
npm start
```

Các source mobile và child được lấy từ working tree cục bộ của checkout `Sketch2Life-be-dev-2026-11-07`, nhánh `dev`, HEAD `1431ef81`, gồm cả thay đổi chưa commit tại máy. Đây không phải xác nhận phiên bản mới nhất trên GitHub. Cache dependency, output build/Gradle/CMake và thiết lập SDK theo máy đã được loại khỏi folder. UI preview/source không đồng nghĩa API/backend đã tích hợp đầy đủ.


