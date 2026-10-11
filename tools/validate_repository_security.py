from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_SAMPLE_PATHS = frozenset(
    {"backend/.asr.env.example", "backend/.vision.env.example"}
)
ENV_ASSIGNMENT_EXEMPT_BASENAMES = frozenset({".env.example"})
BANNED_SUFFIXES = {".jks", ".keystore", ".p12", ".pfx", ".pem", ".pdf", ".xls", ".xlsx"}
BANNED_NAMES = {
    "google-services.json",
    "id_rsa",
    "id_ed25519",
}
TEXT_SUFFIXES = frozenset(
    {
        ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
        ".kt", ".kts", ".gradle", ".properties", ".toml", ".json",
        ".jsonl", ".yaml", ".yml", ".xml", ".html", ".htm",
        ".css", ".scss", ".sh", ".ps1", ".bat", ".cmd", ".md",
        ".txt", ".rst", ".csv", ".tsv", ".patch", ".diff",
        ".ini", ".cfg", ".conf",
    }
)
TEXT_BASENAMES = frozenset(
    {
        ".gitignore", ".gitattributes", ".gitmodules", ".editorconfig",
        ".env.example", "dockerfile", "makefile", "license", "codeowners", "gradlew",
    }
)
TEXT_RELATIVE_PATHS = frozenset(
    {
        "backend/.asr.env.example",
        "backend/.vision.env.example",
        "apps/mobile/android/app/proguard-rules.pro",
    }
)
IMAGE_SUFFIXES = frozenset(
    {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif",
        ".tiff", ".heic", ".heif", ".avif", ".apng", ".ico",
        ".jxl", ".svg",
    }
)
REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

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


def _path_findings(path: Path, relative: str) -> list[str]:
    lower_relative = relative.lower()
    lower_name = path.name.lower()
    findings = []
    is_approved_env_example = (
        lower_name == ".env.example" or lower_relative in ENV_SAMPLE_PATHS
    )
    is_environment_file = lower_name == ".env" or lower_name.endswith(".env") or (
        ".env." in lower_name and not is_approved_env_example
    )
    if is_environment_file:
        findings.append(f"environment file is publishable: {relative}")
    if path.suffix.lower() in BANNED_SUFFIXES:
        findings.append(f"credential/external-document suffix is publishable: {relative}")
    if lower_name in BANNED_NAMES or "service-account" in lower_name:
        findings.append(f"credential-bearing file is publishable: {relative}")
    if "seed" in lower_relative and any(
        marker in lower_relative for marker in ("account", "credential", "user")
    ):
        findings.append(f"seed account/user material is publishable: {relative}")
    return findings


def _is_allowlisted_text(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix().lower()
    return (
        path.suffix.lower() in TEXT_SUFFIXES
        or path.name.lower() in TEXT_BASENAMES
        or relative in TEXT_RELATIVE_PATHS
    )


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & REPARSE_POINT_ATTRIBUTE
    )


def _same_identity(before: os.stat_result, after: os.stat_result) -> bool:
    return bool(before.st_ino and after.st_ino) and (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) == (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )


def _same_object(before: os.stat_result, after: os.stat_result) -> bool:
    return bool(before.st_ino and after.st_ino) and (
        before.st_dev,
        before.st_ino,
    ) == (after.st_dev, after.st_ino)


def _windows_open_descriptor(
    path: Path, *, access: int, share: int, flags: int
) -> int:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    handle = create_file(str(path), access, share, None, 3, flags, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY | os.O_NOINHERIT)
    except BaseException:
        kernel32.CloseHandle(wintypes.HANDLE(handle))
        raise


def _windows_open_relative(parent_descriptor: int, name: str, *, directory: bool) -> int:
    """Open one component from a verified directory handle without path traversal."""
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class UnicodeString(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        ]

    class ObjectAttributes(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        ]

    class IoStatusBlock(ctypes.Structure):
        _fields_ = [("Status", ctypes.c_void_p), ("Information", ctypes.c_void_p)]

    if name in {"", ".", ".."} or "\\" in name or "/" in name:
        raise OSError("unsafe relative path component")
    name_buffer = ctypes.create_unicode_buffer(name)
    name_bytes = len(name.encode("utf-16-le"))
    if name_bytes > 0xFFFC:
        raise OSError("relative path component is too long")
    object_name = UnicodeString(
        name_bytes, name_bytes + 2, ctypes.cast(name_buffer, wintypes.LPWSTR)
    )
    attributes = ObjectAttributes(
        ctypes.sizeof(ObjectAttributes),
        wintypes.HANDLE(msvcrt.get_osfhandle(parent_descriptor)),
        ctypes.pointer(object_name),
        0x00000040,
        None,
        None,
    )
    io_status = IoStatusBlock()
    handle = wintypes.HANDLE()
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    create_file = ntdll.NtCreateFile
    create_file.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(ObjectAttributes),
        ctypes.POINTER(IoStatusBlock),
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    create_file.restype = ctypes.c_long
    # SYNCHRONIZE | READ_ATTRIBUTES plus TRAVERSE for directories or READ_DATA
    # for files; synchronous no-follow opens require exactly one component.
    access = 0x00100080 | (0x00000020 if directory else 0x00000001)
    options = 0x00200020 | (0x00000001 if directory else 0x00000040)
    status = create_file(
        ctypes.byref(handle),
        access,
        ctypes.byref(attributes),
        ctypes.byref(io_status),
        None,
        0,
        0x00000007 if directory else 0x00000001,
        1,
        options,
        None,
        0,
    )
    if status < 0:
        to_dos_error = ntdll.RtlNtStatusToDosError
        to_dos_error.argtypes = [ctypes.c_long]
        to_dos_error.restype = wintypes.DWORD
        raise ctypes.WinError(to_dos_error(status))
    if handle.value is None:
        raise OSError("relative open returned no handle")
    try:
        return msvcrt.open_osfhandle(handle.value, os.O_RDONLY | os.O_BINARY | os.O_NOINHERIT)
    except BaseException:
        ctypes.WinDLL("kernel32").CloseHandle(handle)
        raise


def _open_no_follow(path: Path, *, parent_descriptor: int | None = None) -> int:
    """Open a text candidate without following a link at the leaf."""
    if os.name != "nt":
        no_follow = getattr(os, "O_NOFOLLOW", None)
        if no_follow is None:
            raise OSError("no-follow file open is unavailable")
        target: str | Path = path if parent_descriptor is None else path.name
        return os.open(
            target,
            os.O_RDONLY | no_follow | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_descriptor,
        )

    if parent_descriptor is not None:
        descriptor = _windows_open_relative(parent_descriptor, path.name, directory=False)
        try:
            parent_metadata = path.parent.lstat()
            if (
                _is_link_or_reparse(parent_metadata)
                or not _same_object(parent_metadata, os.fstat(parent_descriptor))
            ):
                raise OSError("parent directory changed during file open")
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    # Direct callers without a verified parent still get a no-follow leaf open.
    return _windows_open_descriptor(
        path,
        access=0x80000000,
        share=0x00000001,
        flags=0x00200000,
    )


def _open_windows_directory(path: Path) -> int:
    return _windows_open_descriptor(
        path,
        access=0x00000080,
        share=0x00000007,
        flags=0x02200000,
    )


def _open_verified_parent_handles(path: Path, relative: Path) -> list[int]:
    """Open and retain each checked ancestor, failing closed on identity uncertainty."""
    descriptors: list[int] = []
    try:
        if os.name == "nt":
            anchor = Path(path.anchor)
            if not anchor.anchor or Path(ROOT.anchor) != anchor:
                raise OSError("Windows path anchor cannot be safely verified")
            directories = [anchor]
            current = anchor
            for part in path.parts[1:-1]:
                current /= part
                directories.append(current)
            for index, directory in enumerate(directories):
                metadata = directory.lstat()
                if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
                    raise OSError("unsafe parent directory")
                descriptor = (
                    _open_windows_directory(directory)
                    if index == 0
                    else _windows_open_relative(
                        descriptors[-1], directory.name, directory=True
                    )
                )
                try:
                    opened = os.fstat(descriptor)
                    if (
                        _is_link_or_reparse(opened)
                        or not stat.S_ISDIR(opened.st_mode)
                        or not _same_object(metadata, opened)
                        or _normalized_path(_descriptor_path(descriptor))
                        != _normalized_path(directory)
                    ):
                        raise OSError("parent directory changed while opening")
                except BaseException:
                    os.close(descriptor)
                    raise
                descriptors.append(descriptor)
            return descriptors

        no_follow = getattr(os, "O_NOFOLLOW", None)
        if (
            os.open not in os.supports_dir_fd
            or os.stat not in os.supports_dir_fd
            or not hasattr(os, "O_DIRECTORY")
            or no_follow is None
            or not ROOT.is_absolute()
            or ROOT.anchor != os.path.sep
        ):
            raise OSError("verified directory-relative open is unavailable")

        directory_flags = (
            os.O_RDONLY
            | os.O_DIRECTORY
            | no_follow
            | getattr(os, "O_CLOEXEC", 0)
        )
        root_descriptor = os.open(os.path.sep, directory_flags)
        descriptors.append(root_descriptor)
        current_descriptor = root_descriptor
        components = (*ROOT.parts[1:], *relative.parts[:-1])
        for component in components:
            metadata = os.stat(
                component, dir_fd=current_descriptor, follow_symlinks=False
            )
            if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
                raise OSError("unsafe parent directory")
            descriptor = os.open(
                component, directory_flags, dir_fd=current_descriptor
            )
            try:
                opened = os.fstat(descriptor)
                if (
                    _is_link_or_reparse(opened)
                    or not stat.S_ISDIR(opened.st_mode)
                    or not _same_object(metadata, opened)
                ):
                    raise OSError("parent directory changed while opening")
            except BaseException:
                os.close(descriptor)
                raise
            descriptors.append(descriptor)
            current_descriptor = descriptor
        return descriptors
    except BaseException:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise


def _descriptor_path(descriptor: int) -> Path:
    """Return the resolved path of an open handle, failing closed if unavailable."""
    if os.name == "nt":
        import ctypes
        import msvcrt
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_final_path = kernel32.GetFinalPathNameByHandleW
        get_final_path.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        get_final_path.restype = wintypes.DWORD
        handle = wintypes.HANDLE(msvcrt.get_osfhandle(descriptor))
        buffer = ctypes.create_unicode_buffer(260)
        length = get_final_path(handle, buffer, len(buffer), 0)
        if length == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        if length >= len(buffer):
            buffer = ctypes.create_unicode_buffer(length + 1)
            length = get_final_path(handle, buffer, len(buffer), 0)
            if length == 0 or length >= len(buffer):
                raise OSError("opened file path could not be verified")
        resolved = buffer.value
        if resolved.startswith("\\\\?\\UNC\\"):
            resolved = "\\\\" + resolved[8:]
        elif resolved.startswith("\\\\?\\"):
            resolved = resolved[4:]
        return Path(resolved)

    if sys.platform.startswith("linux"):
        return Path(os.readlink(f"/proc/self/fd/{descriptor}"))

    raise OSError("opened file path verification is unavailable")


def _normalized_path(path: Path) -> str:
    value = os.fspath(path)
    if os.name == "nt":
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
    return os.path.normcase(os.path.normpath(os.path.abspath(value)))


def _stat_leaf_without_follow(path: Path, parent_descriptor: int) -> os.stat_result:
    if os.name == "nt":
        # This pathname snapshot is compared with the subsequent handle-relative
        # leaf open; retained directory handles need not prevent rename/delete.
        return path.lstat()
    return os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)


def _read_approved_text(path: Path, expected: os.stat_result) -> str:
    """The sole content-read boundary; fail before reading on identity uncertainty."""
    relative = path.relative_to(ROOT)
    if ".." in relative.parts or not relative.parts:
        raise OSError("path is outside the repository")
    if _path_findings(path, relative.as_posix()) or path.suffix.lower() in IMAGE_SUFFIXES:
        raise OSError("path is forbidden for text reading")
    if not _is_allowlisted_text(path) or not stat.S_ISREG(expected.st_mode):
        raise OSError("path is not an approved regular text file")

    parent_handles = _open_verified_parent_handles(path, relative)
    try:
        parent_descriptor = parent_handles[-1]
        current = _stat_leaf_without_follow(path, parent_descriptor)
        if _is_link_or_reparse(current) or not _same_identity(expected, current):
            raise OSError("file identity changed before open")

        descriptor = _open_no_follow(path, parent_descriptor=parent_descriptor)
        try:
            stream = os.fdopen(descriptor, "r", encoding="utf-8")
        except BaseException:
            os.close(descriptor)
            raise
        with stream:
            opened = os.fstat(stream.fileno())
            # Do this before path resolution: a replaced ancestor may be restored
            # before GetFinalPathNameByHandleW observes the leaf's current path.
            if (
                _is_link_or_reparse(opened)
                or not stat.S_ISREG(opened.st_mode)
                or not _same_identity(expected, opened)
            ):
                raise OSError("file identity changed at open")
            if (
                _normalized_path(_descriptor_path(stream.fileno()))
                != _normalized_path(path)
            ):
                raise OSError("opened file path differs from requested path")
            text = stream.read()
            if not _same_identity(expected, os.fstat(stream.fileno())):
                raise OSError("file identity changed during read")
            return text
    finally:
        for parent_handle in reversed(parent_handles):
            os.close(parent_handle)


def main() -> int:
    errors: list[str] = []
    files = publishable_files()
    counts = {
        "allowlisted_text_content_scanned": 0,
        "skipped_image_content": 0,
        "skipped_non_allowlisted_content": 0,
        "skipped_symlink_content": 0,
        "skipped_nonregular_content": 0,
        "skipped_forbidden_path_content": 0,
        "text_read_failures": 0,
        "root_gitignore_rule_only_reads": 0,
    }
    ignore_text: str | None = None
    root_ignore = ROOT / ".gitignore"
    root_ignore_seen = False

    for path in files:
        try:
            relative_path = path.relative_to(ROOT)
        except ValueError:
            errors.append("publishable path is outside the repository")
            counts["skipped_nonregular_content"] += 1
            continue
        if not relative_path.parts or ".." in relative_path.parts:
            errors.append("publishable path has unsafe components")
            counts["skipped_nonregular_content"] += 1
            continue
        relative = relative_path.as_posix()
        findings = _path_findings(path, relative)
        errors.extend(findings)
        if path == root_ignore:
            root_ignore_seen = True

        try:
            metadata = path.lstat()
        except OSError:
            counts["skipped_nonregular_content"] += 1
            if _is_allowlisted_text(path) and not findings:
                errors.append(f"approved text path unavailable: {relative}")
            continue

        if _is_link_or_reparse(metadata):
            counts["skipped_symlink_content"] += 1
            if path == root_ignore:
                errors.append("repository-root .gitignore is a symlink/reparse point")
            continue
        if not stat.S_ISREG(metadata.st_mode):
            counts["skipped_nonregular_content"] += 1
            if _is_allowlisted_text(path) and not findings:
                errors.append(f"approved text path is not regular: {relative}")
            continue
        if findings:
            counts["skipped_forbidden_path_content"] += 1
            continue
        if path.suffix.lower() in IMAGE_SUFFIXES:
            counts["skipped_image_content"] += 1
            continue
        if not _is_allowlisted_text(path):
            counts["skipped_non_allowlisted_content"] += 1
            continue

        try:
            text = _read_approved_text(path, metadata)
        except (OSError, UnicodeError, ValueError) as exc:
            counts["text_read_failures"] += 1
            errors.append(f"approved text content not safely scanned: {relative} ({type(exc).__name__})")
            continue
        counts["allowlisted_text_content_scanned"] += 1
        if path == root_ignore:
            ignore_text = text

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

        if path.name.lower() not in ENV_ASSIGNMENT_EXEMPT_BASENAMES:
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
    if not root_ignore_seen:
        try:
            ignore_text = _read_approved_text(root_ignore, root_ignore.lstat())
        except (OSError, UnicodeError, ValueError) as exc:
            counts["text_read_failures"] += 1
            errors.append(f"repository-root .gitignore not safely scanned ({type(exc).__name__})")
        else:
            counts["root_gitignore_rule_only_reads"] += 1
    if ignore_text is not None:
        for required in required_ignores:
            if required not in ignore_text:
                errors.append(f"missing required ignore rule: {required}")

    if errors:
        print("REPOSITORY_SECURITY_INVALID")
        for error in sorted(set(errors)):
            print(f"- {error}")
    else:
        print("REPOSITORY_SECURITY_VALID_WITH_DECLARED_CONTENT_EXCLUSIONS")
        print("scope=path rules on all publishable paths; content rules on allowlisted text only")
        print("mandatory_gate=NOT_ESTABLISHED_WITHOUT_OWNER_SEMANTICS_ACCEPTANCE")
    print(f"publishable_paths_checked={len(files)}")
    for label, count in counts.items():
        print(f"{label}={count}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
