# Project skeleton map

```text
CAPSTONE/
├─ apps/mobile/                   # Android-only React Native shell + native project
├─ backend/                       # Python/FastAPI modular monolith
├─ packages/art-renderer/         # isolated PixiJS/GSAP WebView package
├─ packages/contracts/            # schemas, generated types, fixtures
├─ services/                      # replaceable AI/domain worker boundaries
├─ data/fixtures/                 # synthetic test inputs only
├─ infra/                         # deploy/migration/container guidance
├─ tests/                         # cross-component test layers
├─ features/                      # context/plan/approval/evidence per feature
├─ docs/                          # architecture, context, governance, setup
├─ tools/                         # harness/skeleton/architecture validators
├─ compose.yaml                   # PostgreSQL, Redis, MinIO
├─ package.json                   # pnpm workspace commands
└─ .env.example                   # safe environment template
```

## Start-work rule

Create a feature folder, write the plan, obtain approval, then implement only within the approved scope. Update context and evidence before moving the feature to review.
