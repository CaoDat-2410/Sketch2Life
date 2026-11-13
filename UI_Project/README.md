# Sketch2Life UI Project

Đây là workspace UIUX chính dùng cho review và bàn giao. Parent được đóng gói vào app Android; Teacher, School Manager và Platform Admin là các portal web.

- `parent-ui` — source giao diện Parent; được bundling thành asset cục bộ trong app Android. Vite preview chỉ để xem nhanh trên web.
- `parent-android/apps/mobile` — app Android native là entry point Parent trên máy ảo/thiết bị.
- `parent-android/apps/ui-mobile` — workspace mobile Expo riêng, không phải entry point Parent được bàn giao trong flow này.
- `parent-android/packages/art-renderer` — package renderer nội bộ dùng bởi workspace mobile.
- `teacher-ui` — Teacher web.
- `school-manager-ui` — School Manager web.
- `platform-admin-ui` — Platform Admin web.
- `web-ui` — cổng web chung, gồm đăng nhập/kích hoạt cho ba role web.
- `shared` — shell, dashboard, role flows và style dùng chung.
- `design-references` — mockup màn hình và bảng component/motion Rev38 để tham khảo; không phải implementation/API contract.

Parent Android dùng bundle từ `parent-ui`, không cần gọi Parent dev server ở cổng 5171 khi mở APK. Không dùng các giao diện Expo/Child cũ làm entry point cho lần bàn giao này.

## Chạy các workspace web

Yêu cầu Node.js và npm tương thích với các phiên bản trong `package.json`.

Tại thư mục gốc:

```powershell
npm ci
npm run build
npm run dev
```

`npm run dev` mở web preview ở cổng 5171–5175: Parent preview ở 5171, Teacher ở 5172, School Manager ở 5173, Platform Admin ở 5174 và web portal chung ở 5175. Có thể chạy riêng bằng `npm run dev:parent`, `npm run dev:teacher`, `npm run dev:manager`, `npm run dev:admin` hoặc `npm run dev:web`.

Để kiểm tra ba role web, dùng các địa chỉ Teacher, School Manager và Platform Admin sau khi chạy `npm run dev`. Parent preview ở 5171 là cùng UI source được đóng gói vào Android, không thay cho kiểm tra APK trên máy ảo.

## Chạy Parent mobile

Tại `parent-android`, cài dependency rồi mở Metro:

```powershell
pnpm install
pnpm start
```

Trong terminal khác, chạy app Parent trên emulator Android đã mở:

```powershell
pnpm android
```

Lệnh này chạy app `@sketch2life/mobile`, đóng gói `parent-ui` vào WebView cục bộ. Không dùng `pnpm android:ui-mobile` cho Parent APK.

Để tạo APK debug để cài trực tiếp hoặc lưu làm artifact:

```powershell
pnpm --dir apps/mobile android:apk:debug
```

Sau khi clone, cài dependency web bằng `npm ci` tại `UI_Project`, rồi cài dependency Android bằng `pnpm install` tại `UI_Project/parent-android`. Cần Android SDK, JDK và emulator theo cấu hình React Native của workspace. Gradle tự build bundle Parent từ `parent-ui`; APK debug chứa UI mới nhất của checkout, không cần kết nối máy chủ Vite.

Các portal và app hiện vẫn có màn hình fixture/preview. UI preview/source không đồng nghĩa API/backend đã được tích hợp đầy đủ.


