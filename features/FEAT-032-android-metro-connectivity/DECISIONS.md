# Decisions

- 2026-09-28: Use Expo LAN mode as the default physical-device path because it does not require
  ADB to be installed or a reverse port mapping to exist.
- 2026-09-28: Keep localhost mode as an explicit emulator/device option only when the launcher has
  successfully installed an ADB reverse mapping for Metro port 8081.
- 2026-09-28: Do not alter Android release cleartext policy or add host/provider endpoints to the
  mobile bundle. This is a development transport fix only.
