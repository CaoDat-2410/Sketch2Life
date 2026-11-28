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
# package.json is always present, so the COPY works on a fresh clone; dist-demo (a git-ignored build
# output) is copied only when it exists. Without it the API simply does not mount /renderer.
COPY packages/art-renderer ./packages/art-renderer
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir '/app/backend[image-admission,modal]'

WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "sketch2life.main:app", "--host", "0.0.0.0", "--port", "8000"]
