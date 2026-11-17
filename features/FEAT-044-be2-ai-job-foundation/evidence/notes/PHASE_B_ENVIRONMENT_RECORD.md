# BE2 Phase B — environment progress

- Date: 2026-10-15, Asia/Saigon. Target: new CPU Studio `sketch2life-backend-test`, separate
  from FEAT-018. No direct Lightning connector/session access from this Codex environment.
- Current state: **AUTHORIZED_COMPONENT_TEST_ENVIRONMENT / BASELINE_READY_USER_REPORTED**.
  Actual O-09 separately authorizes named Studio synthetic use and Phase B planrev3 B1–B6;
  see approvals/PHASE_B_TASK_APPROVAL.md and recordrev9. First code turn B2 only/review before B3.
  No migration/durability/fault result is inferred from approval. Earlier entries retain their
  checkpoint state; observed baseline facts are in O-08 below.

## O-04 — creation and initial inventory reported by user

The user reported "Ok tạo r g làm gì tiếp ?" after the Studio creation instructions, then pasted:

| Item | User-supplied observation | Limit |
|---|---|---|
| OS | Linux6.8.0-110-generic x86_64 | No direct remote query by Codex |
| Python | 3.14.7 | Backend requires >=3.12,<3.14; not a supported backend interpreter |
| Git | /commands/git | No BE2 checkout/commit verified yet |
| Docker | client/server28.0.1, API1.48, linux/amd64 | Engine availability only, not application/service readiness |
| Running containers | No rows in supplied docker ps output | Stopped containers/images not inventoried |
| PostgreSQL/Redis | No client paths returned | Actual servers not provisioned/verified |

## Next concrete setup step

1. Clone the already-published `feature/be2-01-ai-job-foundation` from the repository remote;
   verify branch and commit. Local uncommitted planning records are not included in a Git clone.
2. Verify `python:3.12-slim` runner with Docker; this reuses backend/Dockerfile's baseline and
   does not replace host Python. First run may download the official image.
3. After source/runner are available, use a dedicated Docker network and PostgreSQL17/Redis8
   containers for synthetic tests, with separate volumes/runtime secrets and no unnecessary
   host port publication. Check existing stopped containers before selecting names.
4. Install backend[dev] in the isolated runner environment, capture versions and run the missing
   Phase A test. Do not invoke the FEAT-018 GPU/Wan verification/setup path as BE2 readiness proof.

No container/image download, provisioning, dependency installation, migration or test was executed
by Codex in this remote target. Phase B code approval and remaining gate inputs stay pending.

## O-05 — Python runner verified by user output

User reports the official python:3.12-slim image downloaded and `Python 3.12.15` printed.
Reported image digest: sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1.
No container rows followed the supplied docker ps -a command. Source checkout/branch/commit output
has not been supplied, so source and backend dependencies are still unverified.

## Prepared first-run PostgreSQL/Redis bootstrap (not executed by Codex)

This is for the selected new backend-test Studio. It creates two labelled services on a dedicated
bridge without host port publication. Private random password file stays outside Git. Named
volumes retain service data across container restarts. First-run guards stop on any existing
resource name; they do not delete/adopt it. A partial failure requires inspection before retry.
No application migrations, business rows, model/provider or Phase B implementation is included.

```bash
bash <<'BE2_SETUP'
set -euo pipefail

for item in "container sketch2life-be2-pg" "container sketch2life-be2-redis" "volume sketch2life-be2-pgdata" "volume sketch2life-be2-redisdata" "network sketch2life-be2-net"; do
  read -r kind name <<< "$item"
  if docker "$kind" inspect "$name" >/dev/null 2>&1; then
    printf 'STOP: %s already exists; keep it and report this output.\n' "$name"
    exit 1
  fi
done

BE2_CONFIG_DIR="$HOME/.local/share/sketch2life-be2"
mkdir -p "$BE2_CONFIG_DIR"
chmod 700 "$BE2_CONFIG_DIR"
if [ ! -s "$BE2_CONFIG_DIR/pg-password" ]; then
  (umask 077; python3 -c 'import secrets; print(secrets.token_hex(32))' > "$BE2_CONFIG_DIR/pg-password")
fi

docker network create --label io.sketch2life.scope=be2-synthetic sketch2life-be2-net
docker volume create --label io.sketch2life.scope=be2-synthetic sketch2life-be2-pgdata
docker volume create --label io.sketch2life.scope=be2-synthetic sketch2life-be2-redisdata

docker run -d --name sketch2life-be2-pg \
  --label io.sketch2life.scope=be2-synthetic \
  --network sketch2life-be2-net --network-alias be2-postgres \
  -e POSTGRES_DB=be2_synthetic -e POSTGRES_USER=be2_test \
  -e POSTGRES_PASSWORD_FILE=/run/secrets/pg-password \
  --mount "type=bind,src=$BE2_CONFIG_DIR/pg-password,dst=/run/secrets/pg-password,readonly" \
  -v sketch2life-be2-pgdata:/var/lib/postgresql/data \
  --health-cmd="pg_isready -U be2_test -d be2_synthetic" \
  --health-interval=2s --health-timeout=3s --health-retries=20 \
  postgres:17-alpine

docker run -d --name sketch2life-be2-redis \
  --label io.sketch2life.scope=be2-synthetic \
  --network sketch2life-be2-net --network-alias be2-redis \
  -v sketch2life-be2-redisdata:/data \
  --health-cmd="redis-cli ping" \
  --health-interval=2s --health-timeout=3s --health-retries=20 \
  redis:8-alpine redis-server --appendonly yes

for attempt in {1..20}; do
  pg_state="$(docker inspect -f '{{.State.Health.Status}}' sketch2life-be2-pg)"
  redis_state="$(docker inspect -f '{{.State.Health.Status}}' sketch2life-be2-redis)"
  if [ "$pg_state" = healthy ] && [ "$redis_state" = healthy ]; then break; fi
  sleep 2
done
test "$pg_state" = healthy
test "$redis_state" = healthy

docker exec sketch2life-be2-pg psql -U be2_test -d be2_synthetic -Atc "SHOW server_version"
docker exec sketch2life-be2-redis redis-cli PING
docker ps --filter label=io.sketch2life.scope=be2-synthetic --format '{{.Names}}\t{{.Status}}'
BE2_SETUP
```

Health/version output verifies local service readiness only. Password-authenticated connection
from the Python runner, repository/commit verification, dependency inventory and Phase A test are
still required. Official image behavior checked against Docker Library postgres/redis docs.

## O-06 — services healthy, source checkout still unresolved

User reports PostgreSQL server17.11, Redis PONG and both dedicated containers healthy after
running the prepared bootstrap. Reported image digests:

- postgres:17-alpine: sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24
- redis:8-alpine: sha256:3811787313eba226a2ef38658c6ccb91cd5e110edc89c37767de373120a0e5a0

Git branch/log failed with not-a-git-repository while the prompt was at ~. This shows only that
the current directory is outside a checkout; it does not prove the repository was never cloned.
Next inspect/reuse $HOME/Sketch2Life or clone the published BE2 branch into that absent path, then
use explicit git -C commands to verify branch/commit. Never overwrite an existing directory or
change its branch silently. Existing healthy services stay running. Runner-to-service password
authentication, installed backend packages, source/commit and Phase A test are not verified yet.

## O-07 — published source verified by user

User supplies branch feature/be2-01-ai-job-foundation and shallow HEAD993a26c, matching the
published local tracking ref. Grafted means shallow history, not source failure. Local uncommitted
ADR/decision records are not part of this remote checkout. Backend packages/test are still pending.

Minimal live-app dependency scan: backend[dev] also needs the declared image-admission extra
(av==18.1.0) because app.py imports AvImageDecoder eagerly. Renderer/model/GPU extras are not
required for this route-only check. Independent persistence review traced150 local modules.

Prepared runner installs backend[dev,image-admission] in a persistent Docker Python3.12 venv volume,
checks password-authenticated PostgreSQL and Redis over the dedicated network, then runs only the
existing missing Phase A route test. Runtime secret is read from the readonly-mounted private file
and is not printed. Existing services/data remain unchanged; no application migrations.

### Prepared runner command (not executed by Codex)

```bash
bash <<'BE2_ENV'
set -euo pipefail
BE2_REPO_DIR="$HOME/Sketch2Life"
test "$(git -C "$BE2_REPO_DIR" branch --show-current)" = feature/be2-01-ai-job-foundation
test "$(git -C "$BE2_REPO_DIR" rev-parse --short=7 HEAD)" = 993a26c
test -s "$HOME/.local/share/sketch2life-be2/pg-password"

docker volume create --label io.sketch2life.scope=be2-synthetic sketch2life-be2-venv312

docker run --rm -i --network sketch2life-be2-net \
  --mount "type=bind,src=$BE2_REPO_DIR,dst=/workspace" \
  --mount "type=bind,src=$HOME/.local/share/sketch2life-be2/pg-password,dst=/run/secrets/pg-password,readonly" \
  --mount type=volume,src=sketch2life-be2-venv312,dst=/opt/be2-venv \
  -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/workspace/backend/src \
  -e PIP_DISABLE_PIP_VERSION_CHECK=1 \
  -e SKETCH2LIFE_ENV=test -e SKETCH2LIFE_AI_PROVIDER=disabled \
  -e SKETCH2LIFE_BE1_ARTIFACT_ROOT=/tmp/be2-artifacts \
  -w /workspace python:3.12-slim bash -s <<'BE2_RUNNER'
set -euo pipefail
test -f backend/pyproject.toml
if [ ! -x /opt/be2-venv/bin/python ]; then
  python -m venv /opt/be2-venv
fi
source /opt/be2-venv/bin/activate
OUT=features/FEAT-044-be2-ai-job-foundation/evidence/local/lightning-bootstrap-20261015
mkdir -p "$OUT"

python -m pip install --no-input -e './backend[dev,image-admission]' 2>&1 | tee "$OUT/install.txt"
python -m pip check 2>&1 | tee "$OUT/pip-check.txt"

python - <<'PY' | tee "$OUT/inventory.txt"
import importlib.metadata as metadata
import json
import platform
from pathlib import Path
import psycopg
import redis

packages = ("sqlalchemy", "psycopg", "alembic", "redis", "rq", "pytest", "fastapi", "pydantic", "Pillow", "av")
report = {"python": platform.python_version(),
          "packages": {name: metadata.version(name) for name in packages}}
with psycopg.connect(host="be2-postgres", dbname="be2_synthetic", user="be2_test",
                     password=Path("/run/secrets/pg-password").read_text().strip(),
                     connect_timeout=5) as connection:
    report["postgres"] = connection.execute("SHOW server_version").fetchone()[0]
assert report["postgres"].startswith("17."), "Expected PostgreSQL 17"
client = redis.Redis(host="be2-redis", socket_connect_timeout=5, socket_timeout=5)
assert client.ping(), "Redis did not answer PING"
report["redis"] = client.info("server")["redis_version"]
report["authenticated_postgres_connection"] = "PASS"
report["redis_connection"] = "PASS"
print(json.dumps(report, indent=2))
PY

python -B -m pytest -c backend/pyproject.toml \
  backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route \
  -p no:cacheprovider -rs 2>&1 | tee "$OUT/live-route.txt"
BE2_RUNNER
BE2_ENV
```

## O-08 — installed inventory, authenticated connections and live-route PASS

User supplies the inventory in metrics/PHASE_B_LIGHTNING_ENVIRONMENT_20261015.json: Python3.12.15,
SQLAlchemy2.1.4, psycopg3.3.6, Alembic1.20.0, redis-py6.4.0, RQ2.12.0, pytest8.4.2, FastAPI0.143.1,
Pydantic2.14.1, Pillow12.3.0, av18.1.0; PostgreSQL17.11, Redis server8.10.2. These observed package
versions match the declared ranges/exact av pin; no dependency change or extra pin is required.
Authenticated runner-to-PostgreSQL connection and Redis ping/info pass. The exact missing route
test gives1 passed,0 skipped in2.72s. No direct Codex remote execution or separate shell-exit
receipt is claimed. Original remote install/pip-check/inventory/test receipts stay in ignored
evidence/local/lightning-bootstrap-20261015; no secret value is copied to evidence.

Baseline environment/test dependency is ready. Separate remaining component contract decisions,
Phase A candidate acceptance and Phase B approval are the next gate; do not repeat inventory.
Migration/restart/concurrency/fault and real owner integration evidence remain unproven.

## O-09 authorization follow-up —2026-10-15

User explicitly approves planrev3 B1–B6 on sketch2life-backend-test and accepts rev8 §13, including
synthetic-only environment/source-test synchronization and private-file DB/per-run shared HMAC
mechanisms. Current code remains NOT_STARTED; baseline output is USER_REPORTED, not independently
executed by Codex. B2 tests must name their actual new source snapshot, not old published993a26c.
No new setup or alteration of existing healthy services is required by this documentation handoff.
