# BE2-12 final offline baseline — 2026-10-20

Candidate: `feature/be2-backend-ai-integration` at `d35f035f87fddfc87b0d72d8929f5b1b843fce0e`.
Environment: CPython 3.12.10; pytest 8.4.2; Ruff 0.16.4; mypy 1.20.2; Pydantic 2.13.4; SQLAlchemy 2.0.52; Alembic 1.19.1; Pillow 12.3.0; python-multipart 0.0.32; AV 18.1.0.
Runner: `features/FEAT-048-be2-content-publication/src/run_component_checks.py`.
Result: **PASS**; runner hash check: `source_unchanged=true`; 540 source files in its source hash map.
Inventory: `477` of `477` expected.

## Environment mismatch captured and resolved

The first approved-profile resolution selected Pydantic 2.14.1, and BE2-12 strict mypy failed at `CONTENT_COMMAND_ADAPTER`; pytest still passed 477/477. The exact mypy failure was reproduced. The pre-run FEAT-057 environment inventory records Pydantic 2.13.4, and the exact command passed under that version. The same compatibility pinning also restored recorded Ruff, SQLAlchemy, and Alembic versions. No source or case inventory changed. The first failure and intermediate pass are retained in sibling evidence directories.
Checks: `{"architecture": 0, "collection": 0, "harness": 0, "mypy": 0, "pytest": 0, "ruff": 0, "security": 0, "whitespace": 0}`.
Summary SHA-256: `727b8c976612670d4836b83d2a1ec7b51f27629e158e82909f7eeb91543fbf9d`.
Evidence manifest SHA-256: `0a1897bd622a0898a367456fe8f31f5889e9e41df42d026a80f3565fa4a4805d`.
PostgreSQL, external owners/adapters, provider generation, service/server startup, HTTP calls, Lightning/Studio, and runtime integration remain `NOT_RUN`. Task approval, acceptance, and status records are unchanged; this is local offline evidence, not full-card completion.

Final summary hash: `727b8c976612670d4836b83d2a1ec7b51f27629e158e82909f7eeb91543fbf9d`.
Final evidence manifest hash: `0a1897bd622a0898a367456fe8f31f5889e9e41df42d026a80f3565fa4a4805d`.
