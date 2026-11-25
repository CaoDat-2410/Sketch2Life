"""One-shot local bootstrap: migrate a fresh dev database and seed the demo Parent identity.

Run by the ``bootstrap`` compose service (``docker compose up`` needs nothing else). Local only.

The committed migration graph holds two incompatible Parent schema lines. The legacy line
(``20261110_parent_profiles`` and everything built on it) cannot be applied next to the live
``20261109_m2_parent_profiles`` line, so a local database applies only the live heads.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

LEGACY_PARENT_ROOTS = frozenset({"20261110_parent_profiles"})


def _down(revision) -> list[str]:
    down = revision.down_revision
    if down is None:
        return []
    return [down] if isinstance(down, str) else list(down)


def bootstrap_revisions(script: ScriptDirectory) -> list[str]:
    """Heads of the migration graph with the legacy Parent line and its descendants removed."""
    revisions = {r.revision: r for r in script.walk_revisions()}
    legacy = set(LEGACY_PARENT_ROOTS)
    grew = True
    while grew:
        grew = False
        for key, revision in revisions.items():
            if key not in legacy and any(parent in legacy for parent in _down(revision)):
                legacy.add(key)
                grew = True
    kept = {key for key in revisions if key not in legacy}
    parents = {parent for key in kept for parent in _down(revisions[key])}
    return sorted(kept - parents)


def identity_upsert(subject: str, issuer: str) -> tuple[str, dict[str, str]]:
    sql = (
        "INSERT INTO be1_adult_identities "
        "(subject, account_id, issuer, state, account_role, email_verification_required, "
        "role_revision) "
        "VALUES (:subject, gen_random_uuid()::text, :issuer, 'active', 'parent', false, 1) "
        "ON CONFLICT (subject) DO UPDATE SET state = 'active', account_role = 'parent', "
        "email_verification_required = false, issuer = EXCLUDED.issuer"
    )
    return sql, {"subject": subject, "issuer": issuer}


def _firebase_uid(api_key: str, email: str, password: str) -> str:
    request = urllib.request.Request(
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + api_key,
        data=json.dumps({"email": email, "password": password, "returnSecureToken": True}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - fixed https URL
        return str(json.load(response)["localId"])


def _migrate() -> None:
    config = Config("alembic.ini")
    for revision in bootstrap_revisions(ScriptDirectory.from_config(config)):
        print(f"bootstrap: alembic upgrade {revision}", flush=True)
        command.upgrade(config, revision)


def _seed_parent() -> None:
    email = os.environ.get("SKETCH2LIFE_LOCAL_SEED_PARENT_EMAIL", "")
    password = os.environ.get("SKETCH2LIFE_LOCAL_SEED_PARENT_PASSWORD", "")
    api_key = os.environ.get("SKETCH2LIFE_FIREBASE_API_KEY", "")
    project = os.environ.get("SKETCH2LIFE_FIREBASE_PROJECT_ID", "")
    if not (email and password and api_key and project):
        print("bootstrap: demo parent seed skipped (seed email/password/api key not set)")
        return
    uid = _firebase_uid(api_key, email, password)
    sql, params = identity_upsert(uid, f"https://securetoken.google.com/{project}")
    engine = create_engine(os.environ["SKETCH2LIFE_DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(text(sql), params)
    print(f"bootstrap: seeded parent identity for {email}")


def main() -> int:
    if os.environ.get("SKETCH2LIFE_ENV") != "local":
        print("bootstrap: refused, SKETCH2LIFE_ENV is not 'local'", file=sys.stderr)
        return 2
    _migrate()
    try:
        _seed_parent()
    except Exception as error:  # seeding must not block the stack from starting
        print(f"bootstrap: demo parent seed failed: {type(error).__name__}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
