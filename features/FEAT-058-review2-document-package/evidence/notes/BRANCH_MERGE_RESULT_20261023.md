# Branch merge result and final document baseline

- Date: 2026-10-23 Asia/Saigon
- Target: local `dev`, BE1-ready base `f220781876472950093856e97bbdaaec5170a7c1`.
- Final source: `dev@0a7ce768c153f2104cff930569c3eda6e484532c`; local `dev` is 726 commits ahead of `origin/dev` and has not been pushed.
- The refreshed `origin/FE_UI_Child` tip is `ca3779869dfc1385cbbc7b8ca730f780386af7b2`. Its merge commit is `0a7ce768c153f2104cff930569c3eda6e484532c`. It adds `apps/child-ui`: 166 files, 11,112 insertions. The earlier remote Child ref at the BE1 base was a no-op; it was superseded after the owner reported the new push.
- `feature/be2-backend-ai-integration`: source `aa41ed6f481a6d4a797609e588137c94a7c778d7`; integrated as a fast-forward in the isolated worktree.
- `FE_UI_Teacher`: source `a5c7fa84c9d05f66f6278954d2fc6b5bb4fc8f62`; merge commit `a392059be0fd601ad09f0c5d4e62b26602106c71`.
- `FE_UI_Admin`: source `2bb2ab4bb7d1d09b93e566e9b519cd006984ca85`; merge commit `32d8bc7ac153d8333e5624126b6ce18ad352b1cb`.
- Combined delta from the BE1 base to final `dev`: 2,505 files changed, 322,976 insertions, 4 deletions. The Child source head is an ancestor of final `dev`.
- The merge worktree had no Child path overlap with the calling checkout's pre-existing dirty paths. The dirty checkout was preserved; a local stash backup `b881880442fbef6bf86772f9681692172fbbcfe6` remains.
- A repository security scan passed on the merge tree before the final Child refresh (prior scan records remain historical). This document continuation does not run application builds/tests. No push, PR, deployment or provider call was made.

## Document implications

- `apps/child-ui` is the Child UI source baseline: Expo SDK 55, React Native 0.83.10, React 19. It contains local fixtures and many test source files, but its package scripts expose `start`, `android`, `ios`, and `typecheck` only. No child app build/test/typecheck was run after merge.
- Its `childApiFetch` returns an empty success response and its session PIN verifier uses local fixture values. The UI therefore demonstrates screen flow, not a connected classroom service. Teacher UI uses service modules and fixtures; Admin login returns a mock token. Branch inclusion does not prove backend integration.
- Existing `apps/ui-mobile` (Expo 52 / RN 0.76.9) and `apps/mobile` (bare RN 0.87) remain separate scaffolds. They are not chosen as the current Child surface.
- Durable BE1 runtime routes and local demo/legacy routers coexist in `backend/src/sketch2life/interfaces/http/app.py`. The report treats classroom runtime as the target primary composition and the current split as a cleanup/integration gap, per ADR-0019.
- PostgreSQL Alembic revisions have independent schema roots/heads; see `backend/alembic/README.md`. A complete release migration order is not assumed.
- The required `review-2` tag does not exist; owner directed the report to record it as TBD. Owner selected Modal, but app/environment, model/GPU, endpoint, scaling, timeout, secrets and measured latency are TBD. No live Modal endpoint or performance is claimed.
- `FA26SE225` appears in the registration filename but not in its form body; class is blank. Documents label the identifier as inferred and class as TBD.

