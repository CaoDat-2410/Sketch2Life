# C1 remaining-check inventory and existing Pillow verification —2026-10-16

Current code review remains CODE_REVIEW_PASS_WITH_NOTES; all six findings stay
CLOSED_C1_COMPONENT_SCOPE. No implementation or approval change in this step.

## Completed without installing dependencies

Pillow12.1.0 was already installed in the Python3.12.10 base interpreter and satisfies
the repository's `Pillow>=11,<13` requirement. A feature-local ignored runner loads
only that existing PIL package into the venv test process using importlib. It does
not add the full global site-packages directory, change the shared venv or install
anything. Pytest/dependencies remain from the existing venv; application imports
are pinned to this worktree. Synthetic image encode/decode also passed.

`backend/tests/unit/test_lightning_vision_v2_server.py`: **7 passed, 0 skipped**,
pytest exit0, real JUnit. Six tests exercise helpers; the Pixi test injects a fake
generation runner/config/catalog. No real model/provider/service call. Temporary
image writes are confined to ignored feature-local evidence. During test execution
the audit guard recorded no attempted socket connection/bind or subprocess launch.

The first wrapper attempt blocked pytest's Windows platform metadata subprocess
while writing JUnit (the test body output showed seven passes). It was not a test
failure or valid completed receipt. That log is preserved. The corrected wrapper
resolves read-only platform metadata before enabling the test audit guard; the
second attempt produced valid JUnit and exit0. No SUT/test was changed to pass.

Raw runner, attempt logs, environment/module provenance and JUnit are ignored under
`evidence/local/c1-existing-pillow-20261016/`. Source/approval hashes match the final
code-review snapshot before and after execution.

## Still NOT_RUN: production route walk

`test_v12_production_app_routes_do_not_mount_cmd34` needs `python-multipart` when
the production app imports File/Form routes. Neither the existing venv nor base
Python has `python_multipart`/`multipart`. This inventory did not run the route test
or pretend the earlier Pillow skip became PASS. PyAV and other inspected imports
are available; dependency sufficiency is only proven by actually running the test.

The package is already declared in `backend/pyproject.toml` as
`python-multipart>=0.0.20,<1`. No production dependency declaration is missing.
Actual C1 approval excludes dependency installation. No package was installed and
no new permission/owner acceptance was manufactured here.

Next concrete environment-only action, if the user authorizes it: install only
python-multipart within that declared constraint into an ignored feature-local
test-dependency target; keep the shared venv unchanged, reuse the existing Pillow,
then run the remaining route test (and confirm the complete focused suite has no
skip in that process). Redirect BE1 artifact paths/temp files into feature evidence.
Do not install the whole project, activate a provider, start a service or open C2.

After remaining verification, update evidence and obtain owner acceptance of C1.
Commit planning/publication is separate. Full BE2-02 remains IN_PROGRESS; real
owner/provider/persistence/runtime gates are unchanged. BE2-01 stays WAITING_STUDIO.
