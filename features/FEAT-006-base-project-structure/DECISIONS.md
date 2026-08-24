# FEAT-006 decisions

1. Use `apps/mobile` as the only active client boundary.
2. Keep `apps/api` thin and place business logic under `backend/src/sketch2life`.
3. Separate domain, application, contracts, interfaces, and infrastructure in the backend.
4. Keep existing `apps/parent-web` and `apps/child-app` docs as historical references, but do not add code there.
5. Keep the visual asset gate inside the mobile app and feature folders.
