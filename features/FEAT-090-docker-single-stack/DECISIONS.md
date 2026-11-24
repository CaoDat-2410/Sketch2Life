# FEAT-090 decisions

## D1 — Keep `fe085-parent-api` as the only active local stack

- **Decision:** Keep the five-service `fe085-parent-api` stack on host port 18001.
- **Evidence:** The shared `.env` points the Android emulator to `http://10.0.2.2:18001`; this API was healthy and is built from the active mobile worktree.
- **Stopped:** Duplicate project stacks on ports 8000, 18000, and 58000, plus the redundant Firebase Auth emulator and their duplicate ClamAV/database/cache/object-store services.
- **Data handling:** Stop only. Preserve stopped containers and all named/anonymous volumes.

## D2 — Do not change service replica counts in Compose YAML

- **Decision:** Keep the Compose service definitions as one instance per service; no `container_name` or replica override is needed.
- **Reason:** The YAML already starts one container for each service. The excess containers came from starting additional Compose projects. The fixed startup script stops Compose containers rooted anywhere under CAPSTONE except the canonical project, then starts dependencies in that canonical project.

## D3 — Retain one ClamAV instance

- **Decision:** Keep ClamAV in the canonical stack.
- **Reason:** It is the backend's upload-scanning service. One instance used about 953 MiB; the RAM problem came from three duplicate ClamAV containers, not from the single required service.
