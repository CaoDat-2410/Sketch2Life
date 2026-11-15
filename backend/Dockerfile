FROM node:22-bookworm-slim AS renderer-build

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
WORKDIR /workspace
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY patches/expo-av@15.0.2.patch ./patches/expo-av@15.0.2.patch
COPY apps/mobile/package.json ./apps/mobile/package.json
COPY apps/ui-mobile/package.json ./apps/ui-mobile/package.json
COPY packages/art-renderer/package.json ./packages/art-renderer/package.json
RUN corepack enable \
    && corepack prepare pnpm@11.19.0 --activate \
    && pnpm install --frozen-lockfile --filter @sketch2life/art-renderer
COPY packages/art-renderer/demo.html ./packages/art-renderer/demo.html
COPY packages/art-renderer/mobile.html ./packages/art-renderer/mobile.html
COPY packages/art-renderer/vite.config.ts ./packages/art-renderer/vite.config.ts
COPY packages/art-renderer/tsconfig.json ./packages/art-renderer/tsconfig.json
COPY packages/art-renderer/src ./packages/art-renderer/src
COPY packages/art-renderer/demo ./packages/art-renderer/demo
COPY packages/art-renderer/fixtures ./packages/art-renderer/fixtures
RUN pnpm --filter @sketch2life/art-renderer build:demo

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend/src

WORKDIR /app
COPY backend/pyproject.toml backend/README.md ./backend/
COPY backend/alembic.ini ./backend/alembic.ini
COPY backend/alembic ./backend/alembic
COPY backend/src ./backend/src
COPY data/activity-catalog ./data/activity-catalog
COPY features/FEAT-028-pixi-topic-asset-library/assets/generated ./features/FEAT-028-pixi-topic-asset-library/assets/generated
COPY --from=renderer-build /workspace/packages/art-renderer/dist-demo ./packages/art-renderer/dist-demo
RUN pip install --no-cache-dir '/app/backend[image-admission,modal]'

WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "sketch2life.main:app", "--host", "0.0.0.0", "--port", "8000"]
