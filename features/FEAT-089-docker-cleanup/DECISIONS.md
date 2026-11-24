# FEAT-089 decisions

## D1 — Preserve Docker volumes and shared build cache

- **Decision:** Do not prune named or anonymous volumes, and do not prune BuildKit cache.
- **Reason:** Volumes contain PostgreSQL, MinIO, Firebase Auth emulator, Redis, or ClamAV data. Build cache is shared across CAPSTONE worktrees and another local project, so ownership cannot be isolated safely.
- **Effect:** Cleanup is limited to six old stopped test containers and 24 old, unused Sketch2Life images. Docker may still report unused volume space and reclaimable build cache.
