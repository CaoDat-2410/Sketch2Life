from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ENV_FILES = {".env.example"}
BANNED_SUFFIXES = {".jks", ".keystore", ".p12", ".pfx", ".pem", ".pdf", ".xls", ".xlsx"}
BANNED_NAMES = {
    "google-services.json",
    "id_rsa",
    "id_ed25519",
}

CONTENT_RULES = {
    "private key material": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "absolute Windows machine path": re.compile(
        r"\b[A-Za-z]:[\\/](?:Users|Project)[\\/]", re.IGNORECASE
    ),
    "absolute Unix home path": re.compile(r"(?:^|[\s'\"])/(?:Users|home)/[^/\s]+/"),
}

SENSITIVE_ASSIGNMENT = re.compile(
    r"^\s*[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API_KEY|PRIVATE_KEY)[A-Z0-9_]*\s*=\s*(.*?)\s*$",
    re.MULTILINE,
)
ALLOWED_EXAMPLE_VALUES = {"", "change-me", "minioadmin", "placeholder", "example"}
SYNTHETIC_FIXTURE_PATH = "backend/tests/unit/test_media_validation.py"
SYNTHETIC_FIXTURE_BEGIN = "# SECURITY_VALIDATOR_SYNTHETIC_FIXTURES: BEGIN"
SYNTHETIC_FIXTURE_END = "# SECURITY_VALIDATOR_SYNTHETIC_FIXTURES: END"
SENSITIVE_ASSIGNMENT_RULE = "non-placeholder secret assignment"
SYNTHETIC_FIXTURE_RULES = frozenset(
    {"private key material", SENSITIVE_ASSIGNMENT_RULE}
)
SYNTHETIC_FIXTURE_BLOCK = re.compile(
    rf"(?ms)^{re.escape(SYNTHETIC_FIXTURE_BEGIN)}\r?$.*?"
    rf"^{re.escape(SYNTHETIC_FIXTURE_END)}\r?$"
)


def _is_allowed_synthetic_fixture_finding(
    *,
    relative: str,
    rule: str,
    text: str,
    start: int,
    end: int,
) -> bool:
    if relative != SYNTHETIC_FIXTURE_PATH or rule not in SYNTHETIC_FIXTURE_RULES:
        return False
    blocks = tuple(SYNTHETIC_FIXTURE_BLOCK.finditer(text))
    if len(blocks) != 1 or end <= start:
        return False
    block = blocks[0]
    return block.start() <= start and end <= block.end()


def publishable_files() -> list[Path]:
    command = [
        "git",
        "-c",
        f"safe.directory={ROOT.as_posix()}",
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ]
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    errors: list[str] = []
    files = publishable_files()

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        lower_relative = relative.lower()
        lower_name = path.name.lower()

        if lower_name == ".env" or (
            lower_name.startswith(".env.") and lower_name not in ALLOWED_ENV_FILES
        ):
            errors.append(f"environment file is publishable: {relative}")
        if path.suffix.lower() in BANNED_SUFFIXES:
            errors.append(f"credential/external-document suffix is publishable: {relative}")
        if lower_name in BANNED_NAMES or "service-account" in lower_name:
            errors.append(f"credential-bearing file is publishable: {relative}")
        if "seed" in lower_relative and any(
            marker in lower_relative for marker in ("account", "credential", "user")
        ):
            errors.append(f"seed account/user material is publishable: {relative}")

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for label, pattern in CONTENT_RULES.items():
            for match in pattern.finditer(text):
                if not _is_allowed_synthetic_fixture_finding(
                    relative=relative,
                    rule=label,
                    text=text,
                    start=match.start(),
                    end=match.end(),
                ):
                    errors.append(f"{label} found in: {relative}")

        if lower_name not in ALLOWED_ENV_FILES:
            for match in SENSITIVE_ASSIGNMENT.finditer(text):
                value = match.group(1).strip().strip("'\"")
                if (
                    value.lower() not in ALLOWED_EXAMPLE_VALUES
                    and not value.startswith("${")
                    and not _is_allowed_synthetic_fixture_finding(
                        relative=relative,
                        rule=SENSITIVE_ASSIGNMENT_RULE,
                        text=text,
                        start=match.start(),
                        end=match.end(),
                    )
                ):
                    errors.append(
                        f"{SENSITIVE_ASSIGNMENT_RULE} found in: {relative}"
                    )

    required_ignores = (
        ".env",
        "*.jks",
        "*.keystore",
        "apps/mobile/android/app/google-services.json",
        "*-firebase-service-account.json",
        "data/seeds/",
    )
    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for required in required_ignores:
        if required not in ignore_text:
            errors.append(f"missing required ignore rule: {required}")

    if errors:
        print("REPOSITORY_SECURITY_INVALID")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1

    print("REPOSITORY_SECURITY_VALID")
    print(f"publishable_files_scanned={len(files)}")
    print("environment_files=excluded")
    print("seed_accounts=excluded")
    print("credentials_and_signing_keys=excluded")
    print("external_reference_documents=excluded")
    print("absolute_machine_paths=absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
