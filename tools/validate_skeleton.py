from __future__ import annotations

import json
import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ".editorconfig",
    ".env.example",
    "compose.yaml",
    "package.json",
    "pnpm-workspace.yaml",
    "pnpm-lock.yaml",
    "tsconfig.base.json",
    "backend/pyproject.toml",
    "backend/src/sketch2life/main.py",
    "backend/src/sketch2life/application/ports/identity.py",
    "backend/src/sketch2life/interfaces/http/app.py",
    "apps/mobile/package.json",
    "apps/mobile/android/build.gradle",
    "apps/mobile/android/app/build.gradle",
    "apps/mobile/android/app/src/main/AndroidManifest.xml",
    "apps/mobile/android/app/src/main/java/com/sketch2life/mobile/MainActivity.kt",
    "apps/mobile/android/app/src/main/java/com/sketch2life/mobile/MainApplication.kt",
    "apps/mobile/src/app/AppRoot.tsx",
    "apps/mobile/src/bridge/pixi/protocol/messages.ts",
    "apps/mobile/src/infrastructure/auth/AuthSessionPort.ts",
    "packages/art-renderer/package.json",
    "docs/setup/LOCAL_DEVELOPMENT.md",
    "docs/SYSTEM_BASELINE.md",
    "tools/validate_repository_security.py",
    "tools/validate_team_allocation.py",
]


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"missing: {relative}")

    for relative in ("package.json", "apps/mobile/package.json", "packages/art-renderer/package.json"):
        try:
            json.loads((ROOT / relative).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {relative}: {exc}")

    try:
        with (ROOT / "backend/pyproject.toml").open("rb") as stream:
            tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"invalid TOML backend/pyproject.toml: {exc}")

    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    if "change-me" not in env_text:
        errors.append(".env.example must keep explicit placeholder secrets")
    if "FIREBASE_STORAGE" in env_text or "FIREBASE_DATABASE" in env_text:
        errors.append("Firebase storage/database configuration is forbidden")

    mobile_package = json.loads((ROOT / "apps/mobile/package.json").read_text(encoding="utf-8"))
    if "ios" in mobile_package.get("scripts", {}):
        errors.append("Android-only mobile package must not expose an iOS script")
    for script in ("android:apk:debug", "android:apk:release", "android:aab:release"):
        if script not in mobile_package.get("scripts", {}):
            errors.append(f"missing Android distribution script: {script}")

    forbidden_mobile_dependencies = {
        "@react-native-firebase/database",
        "@react-native-firebase/firestore",
        "@react-native-firebase/storage",
        "firebase-admin",
    }
    mobile_dependencies = set(mobile_package.get("dependencies", {})) | set(
        mobile_package.get("devDependencies", {})
    )
    for dependency in sorted(forbidden_mobile_dependencies & mobile_dependencies):
        errors.append(f"forbidden mobile data/provider dependency: {dependency}")

    android_root_gradle = (ROOT / "apps/mobile/android/build.gradle").read_text(encoding="utf-8")
    android_app_gradle = (ROOT / "apps/mobile/android/app/build.gradle").read_text(encoding="utf-8")
    android_manifest = (
        ROOT / "apps/mobile/android/app/src/main/AndroidManifest.xml"
    ).read_text(encoding="utf-8")
    for expected in (
        "minSdkVersion = 29",
        "compileSdkVersion = 37",
        "targetSdkVersion = 36",
    ):
        if expected not in android_root_gradle:
            errors.append(f"missing Android SDK baseline: {expected}")
    for expected in (
        'namespace "com.sketch2life.mobile"',
        'applicationId "com.sketch2life.mobile"',
    ):
        if expected not in android_app_gradle:
            errors.append(f"missing Android identity: {expected}")
    if 'android:usesCleartextTraffic="false"' not in android_manifest:
        errors.append("Android main manifest must disable cleartext traffic")
    if re.search(
        r"release\s*\{[^}]*signingConfig\s+signingConfigs\.debug",
        android_app_gradle,
        re.DOTALL,
    ):
        errors.append("Android release build must not use the debug signing key")

    # The runnable app is apps/ui-mobile; keep the older apps/mobile skeleton checks above
    # for the approved architecture scaffold, but validate the app used by the workspace too.
    active_app = ROOT / "apps/ui-mobile"
    active_android = active_app / "android"
    active_root_gradle = active_android / "build.gradle"
    active_app_gradle = active_android / "app/build.gradle"
    active_manifest = active_android / "app/src/main/AndroidManifest.xml"
    active_config = active_app / "app.json"
    for path in (active_root_gradle, active_app_gradle, active_manifest, active_config):
        if not path.is_file():
            errors.append(f"active Android app is missing: {path.relative_to(ROOT)}")

    if all(path.is_file() for path in (active_root_gradle, active_app_gradle, active_manifest, active_config)):
        active_gradle_text = active_root_gradle.read_text(encoding="utf-8")
        active_build_text = active_app_gradle.read_text(encoding="utf-8")
        active_manifest_text = active_manifest.read_text(encoding="utf-8")
        active_expo = json.loads(active_config.read_text(encoding="utf-8")).get("expo", {})
        for expected in (
            "?: '29'",
            "?: '37'",
            "?: '36'",
        ):
            if expected not in active_gradle_text:
                errors.append(f"active Android app does not match ADR-0004 SDK baseline: {expected}")
        if 'applicationId \'com.sketch2life.mobile\'' not in active_build_text:
            errors.append("active Android app must retain applicationId com.sketch2life.mobile")
        if 'android.permission.RECORD_AUDIO' not in active_manifest_text:
            errors.append("active Android manifest must declare RECORD_AUDIO for explicit narration")
        if re.search(
            r"release\s*\{[^}]*signingConfig\s+signingConfigs\.debug",
            active_build_text,
            re.DOTALL,
        ):
            errors.append("active Android release build must not use the debug signing key")
        if "ANDROID_RELEASE_STORE_FILE" not in active_build_text or "verifyReleaseSigning" not in active_build_text:
            errors.append("active Android release signing must be injected and fail closed")
        plugins = active_expo.get("plugins", [])
        if not any(
            (plugin == "expo-av")
            or (isinstance(plugin, list) and plugin and plugin[0] == "expo-av")
            for plugin in plugins
        ):
            errors.append("active Expo config must use the expo-av permission plugin")
        if "android.permission.RECORD_AUDIO" in active_expo.get("android", {}).get(
            "blockedPermissions", []
        ):
            errors.append("active Expo config must not block RECORD_AUDIO")

    ios_files = [path for path in (ROOT / "apps/mobile/ios").rglob("*") if path.is_file()]
    if ios_files:
        errors.append("Android-only project contains active iOS files")

    if errors:
        print("SKELETON_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SKELETON_VALID")
    print("backend=python-fastapi")
    print("frontend=react-native")
    print("mobile_target=android-only")
    print("android_sdk=min29-target36-compile37")
    print("auth=firebase-auth-only")
    print("ai=lightning-dev-runpod-production")
    print("workspace=pnpm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
