# FEAT-010 validation evidence

- Date: 2026-08-24
- Environment: Windows, Python 3.12 project environment, Node 24.18.1, pnpm 11.19.0
- External state: no Firebase/Lightning/Runpod/Google Play account was accessed or changed
- Credentials/data: none; fixture policy remains active

## Harness and architecture

Commands:

```powershell
python tools/validate_harness.py
python tools/validate_skeleton.py
python tools/validate_architecture.py
```

Result: PASS.

```text
HARNESS_VALID
SKELETON_VALID
auth=firebase-auth-only
ai=lightning-dev-runpod-production
ARCHITECTURE_VALID
mobile_ai_boundary=valid
firebase_data_products=absent
```

The skeleton validator also confirmed Android-only min29/target36/compile37 and all APK/AAB scripts. The scripts use a Node wrapper that selects `gradlew.bat` on Windows and `./gradlew` on Linux/macOS CI.

## Python

Commands:

```powershell
backend/.venv/Scripts/python -m ruff check backend/src backend/tests tools
backend/.venv/Scripts/python -m mypy backend/src
backend/.venv/Scripts/python -m pytest backend/tests
```

Result: PASS. Ruff passed; Mypy found no issues in 25 source files; Pytest passed 5/5 tests. The three new settings tests prove that production rejects development authentication, rejects Lightning as production AI, and accepts configured Firebase + Runpod runtime references.

## JavaScript/TypeScript

Commands:

```powershell
$env:CI='true'
pnpm install --frozen-lockfile
pnpm typecheck
pnpm test
pnpm --dir apps/mobile lint
```

Result: PASS. Frozen lockfile was already current; both workspace typechecks passed; Jest passed 2/2; ESLint exited 0.

## Secret/provider scan

No `google-services.json`, Firebase service-account file, Firebase Storage/Firestore/Realtime Database package/configuration, obsolete Lightning-private setting, or real provider credential was found. `.gitignore` explicitly excludes Firebase project/service credentials, release keystores, and local secret directories.

## Android artifact limitation

No APK/AAB was produced because this machine still has no Android SDK/`ANDROID_HOME`. The project now exposes reproducible Gradle commands and signing guidance. Producing an artifact is a later environment/release task, not silently claimed as complete here.
