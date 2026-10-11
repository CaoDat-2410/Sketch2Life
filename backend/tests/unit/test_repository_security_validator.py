"""Synthetic-only checks for the repository security validator's read boundary."""

from __future__ import annotations

import ctypes
import os
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace, TracebackType
from typing import Any, Self

import pytest
from tools import validate_repository_security as security

REQUIRED_IGNORES = (
    ".env\n"
    "*.jks\n"
    "*.keystore\n"
    "apps/mobile/android/app/google-services.json\n"
    "*-firebase-service-account.json\n"
    "data/seeds/"
)
APPROVED_SUFFIXES = frozenset(
    {
        ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
        ".kt", ".kts", ".gradle", ".properties", ".toml", ".json",
        ".jsonl", ".yaml", ".yml", ".xml", ".html", ".htm",
        ".css", ".scss", ".sh", ".ps1", ".bat", ".cmd", ".md",
        ".txt", ".rst", ".csv", ".tsv", ".patch", ".diff",
        ".ini", ".cfg", ".conf",
    }
)
APPROVED_BASENAMES = frozenset(
    {
        ".gitignore", ".gitattributes", ".gitmodules", ".editorconfig",
        ".env.example", "dockerfile", "makefile", "license", "codeowners", "gradlew",
    }
)
APPROVED_RELATIVE_PATHS = frozenset(
    {
        "backend/.asr.env.example",
        "backend/.vision.env.example",
        "apps/mobile/android/app/proguard-rules.pro",
    }
)


def test_allowlist_is_exact_and_excludes_known_images() -> None:
    assert security.TEXT_SUFFIXES == APPROVED_SUFFIXES
    assert security.TEXT_BASENAMES == APPROVED_BASENAMES
    assert security.TEXT_RELATIVE_PATHS == APPROVED_RELATIVE_PATHS
    assert frozenset(
        {"backend/.asr.env.example", "backend/.vision.env.example"}
    ) == security.ENV_SAMPLE_PATHS
    assert frozenset({".env.example"}) == security.ENV_ASSIGNMENT_EXEMPT_BASENAMES
    assert security.TEXT_SUFFIXES.isdisjoint(security.IMAGE_SUFFIXES)
    assert ".svg" in security.IMAGE_SUFFIXES
    assert not security._is_allowlisted_text(security.ROOT / "live_ai_smoke_test.ipynb")
    assert not security._is_allowlisted_text(
        security.ROOT / "other" / "proguard-rules.pro"
    )


def test_environment_name_rules_cover_nested_variants_without_opening_them(
    synthetic_root: Path,
) -> None:
    forbidden_paths = (
        "backend/.asr.env",
        "backend/.vision.env",
        "backend/service.env",
        "backend/.env.local",
        "other/.asr.env.example",
    )
    for relative in forbidden_paths:
        path = synthetic_root / relative
        assert security._path_findings(path, relative) == [
            f"environment file is publishable: {relative}"
        ]

    allowed_examples = (
        ".env.example",
        "backend/.asr.env.example",
        "backend/.vision.env.example",
    )
    for relative in allowed_examples:
        assert security._path_findings(synthetic_root / relative, relative) == []


@pytest.fixture
def synthetic_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / ".gitignore").write_text(REQUIRED_IGNORES, encoding="utf-8")
    monkeypatch.setattr(security, "ROOT", tmp_path)
    return tmp_path


def run_inventory(
    root: Path,
    paths: list[Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, list[str]]:
    monkeypatch.setattr(security, "publishable_files", lambda: [root / ".gitignore", *paths])
    monkeypatch.setattr(
        Path, "read_text", lambda *_args, **_kwargs: pytest.fail("unguarded text read")
    )
    monkeypatch.setattr(
        Path, "read_bytes", lambda *_args, **_kwargs: pytest.fail("unguarded byte read")
    )
    opened: list[str] = []
    reader_attempts: list[str] = []
    original_reader = security._read_approved_text

    def tracked_reader(path: Path, expected: os.stat_result) -> str:
        reader_attempts.append(path.relative_to(root).as_posix())
        return original_reader(path, expected)

    monkeypatch.setattr(security, "_read_approved_text", tracked_reader)
    if os.name == "nt":
        original_windll = ctypes.WinDLL
        original_relative_open = security._windows_open_relative

        def tracked_relative_open(
            parent_descriptor: int, name: str, *, directory: bool
        ) -> int:
            if not directory:
                candidate = security._descriptor_path(parent_descriptor) / name
                opened.append(candidate.relative_to(root).as_posix())
            return original_relative_open(parent_descriptor, name, directory=directory)

        monkeypatch.setattr(security, "_windows_open_relative", tracked_relative_open)

        class ObservedCreateFile:
            def __init__(self, function: Any) -> None:
                self.function = function

            @property
            def argtypes(self) -> Any:
                return self.function.argtypes

            @argtypes.setter
            def argtypes(self, value: Any) -> None:
                self.function.argtypes = value

            @property
            def restype(self) -> Any:
                return self.function.restype

            @restype.setter
            def restype(self, value: Any) -> None:
                self.function.restype = value

            def __call__(self, *args: Any) -> Any:
                if len(args) < 6 or not (int(args[5]) & 0x02000000):
                    opened.append(Path(str(args[0])).relative_to(root).as_posix())
                return self.function(*args)

        class ObservedKernel32:
            def __init__(self, library: Any) -> None:
                self.library = library
                self.CreateFileW = ObservedCreateFile(library.CreateFileW)

            def __getattr__(self, name: str) -> Any:
                if name == "CreateFileW":
                    return self.CreateFileW
                return getattr(self.library, name)

        def tracked_windll(name: str, **kwargs: Any) -> Any:
            library = original_windll(name, **kwargs)
            if name.lower() == "kernel32":
                return ObservedKernel32(library)
            return library

        monkeypatch.setattr(ctypes, "WinDLL", tracked_windll)
    else:
        original_os_open = os.open

        def tracked_os_open(
            path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
            *args: Any,
            **kwargs: Any,
        ) -> int:
            flags = int(args[0]) if args else 0
            descriptor = kwargs.get("dir_fd")
            if not flags & getattr(os, "O_DIRECTORY", 0):
                candidate = Path(os.fsdecode(path))
                if descriptor is not None:
                    parent = Path(os.readlink(f"/proc/self/fd/{descriptor}"))
                    candidate = parent / candidate
                opened.append(candidate.relative_to(root).as_posix())
            return original_os_open(path, *args, **kwargs)

        monkeypatch.setattr(os, "open", tracked_os_open)
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {tracked_os_open})
    result = security.main()
    output = capsys.readouterr().out
    trace = [f"reader:{item}" for item in reader_attempts] + [
        f"system-open:{item}" for item in opened
    ]
    return result, output, trace


def assert_open_trace(trace: list[str], expected: set[str]) -> None:
    readers = {item.removeprefix("reader:") for item in trace if item.startswith("reader:")}
    system_opens = {
        item.removeprefix("system-open:")
        for item in trace
        if item.startswith("system-open:")
    }
    assert readers == expected
    assert system_opens == expected


def test_default_deny_never_opens_excluded_content(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    names = ["picture.png", "picture.JpG", "icon.svg", "unknown.blob", "archive.zip", "README"]
    paths = [synthetic_root / name for name in names]
    for path in paths:
        path.write_text("synthetic harmless text", encoding="utf-8")

    result, output, opened = run_inventory(synthetic_root, paths, monkeypatch, capsys)

    assert result == 0
    assert_open_trace(opened, {".gitignore"})
    assert "REPOSITORY_SECURITY_VALID_WITH_DECLARED_CONTENT_EXCLUSIONS" in output
    assert "mandatory_gate=NOT_ESTABLISHED_WITHOUT_OWNER_SEMANTICS_ACCEPTANCE" in output
    assert "publishable_paths_checked=7" in output
    assert "allowlisted_text_content_scanned=1" in output
    assert "skipped_image_content=3" in output
    assert "skipped_non_allowlisted_content=3" in output


def test_added_security_text_paths_are_scanned_and_other_files_are_denied(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    asr_example = synthetic_root / "backend" / ".asr.env.example"
    asr_example.parent.mkdir(parents=True)
    asr_example.write_text(
        "API_" + "TOKEN" + "=" + "synthetic-value", encoding="utf-8"
    )
    vision_example = synthetic_root / "backend" / ".vision.env.example"
    vision_example.write_text(
        "VISION_TOKEN=placeholder", encoding="utf-8"
    )
    proguard = synthetic_root / "apps" / "mobile" / "android" / "app" / "proguard-rules.pro"
    proguard.parent.mkdir(parents=True)
    proguard.write_text("ghp_" + "A" * 32, encoding="utf-8")

    unapproved_proguard = synthetic_root / "elsewhere" / "proguard-rules.pro"
    unapproved_proguard.parent.mkdir()
    unapproved_proguard.write_text("synthetic harmless text", encoding="utf-8")

    notebook = synthetic_root / "live_ai_smoke_test.ipynb"
    notebook.write_text('{"image/png":"synthetic-encoded-image"}', encoding="utf-8")
    wav = synthetic_root / "sample.wav"
    wav.write_text("synthetic binary placeholder", encoding="utf-8")
    jar = synthetic_root / "gradle-wrapper.jar"
    jar.write_text("synthetic binary placeholder", encoding="utf-8")
    unapproved_env_files = [
        synthetic_root / "backend" / ".asr.env",
        synthetic_root / "backend" / ".vision.env",
    ]
    for path in unapproved_env_files:
        path.write_text("TOKEN=" + "synthetic-unread-value", encoding="utf-8")

    result, output, opened = run_inventory(
        synthetic_root,
        [
            asr_example,
            vision_example,
            proguard,
            notebook,
            wav,
            jar,
            unapproved_proguard,
            *unapproved_env_files,
        ],
        monkeypatch,
        capsys,
    )

    assert result == 1
    assert_open_trace(
        opened,
        {
            ".gitignore",
            "backend/.asr.env.example",
            "backend/.vision.env.example",
            "apps/mobile/android/app/proguard-rules.pro",
        },
    )
    assert "non-placeholder secret assignment found in: backend/.asr.env.example" in output
    assert "non-placeholder secret assignment found in: backend/.vision.env.example" not in output
    assert "GitHub token found in: apps/mobile/android/app/proguard-rules.pro" in output
    assert "environment file is publishable: backend/.asr.env" in output
    assert "environment file is publishable: backend/.vision.env" in output
    assert "publishable_paths_checked=10" in output
    assert "allowlisted_text_content_scanned=4" in output
    assert "skipped_non_allowlisted_content=4" in output
    assert "skipped_forbidden_path_content=2" in output


def test_forbidden_paths_keep_findings_without_content_opens(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    names = [".env", "signing.pem", "google-services.json", "seed-accounts.json"]
    paths = [synthetic_root / name for name in names]
    for path in paths:
        path.write_text("synthetic harmless text", encoding="utf-8")

    result, output, opened = run_inventory(synthetic_root, paths, monkeypatch, capsys)

    assert result == 1
    assert_open_trace(opened, {".gitignore"})
    assert "environment file is publishable: .env" in output
    assert "credential/external-document suffix is publishable: signing.pem" in output
    assert "credential-bearing file is publishable: google-services.json" in output
    assert "seed account/user material is publishable: seed-accounts.json" in output
    assert "skipped_forbidden_path_content=4" in output


def test_allowed_text_still_receives_content_rules_and_placeholder_exception(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = synthetic_root / "source.py"
    marker = "-----BEGIN " + "PRIVATE KEY-----"
    token = "ghp_" + "A" * 32
    source.write_text(
        "\n".join((marker, token, "TOKEN=" + "not-a-placeholder")), encoding="utf-8"
    )
    document = synthetic_root / "document.md"
    document.write_text("C:" + "\\Users\\Example\\file", encoding="utf-8")
    data = synthetic_root / "data.json"
    data.write_text('"token": "' + "AKIA" + "A" * 16 + '"', encoding="utf-8")
    example = synthetic_root / ".env.example"
    example.write_text("TOKEN=placeholder", encoding="utf-8")

    result, output, opened = run_inventory(
        synthetic_root, [source, document, data, example], monkeypatch, capsys
    )

    assert result == 1
    assert_open_trace(
        opened, {".gitignore", "source.py", "document.md", "data.json", ".env.example"}
    )
    assert "private key material found in: source.py" in output
    assert "GitHub token found in: source.py" in output
    assert "non-placeholder secret assignment found in: source.py" in output
    assert "absolute Windows machine path found in: document.md" in output
    assert "AWS access key found in: data.json" in output
    assert "non-placeholder secret assignment found in: .env.example" not in output
    assert "allowlisted_text_content_scanned=5" in output


def test_marked_synthetic_fixture_exception_stays_narrow(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = synthetic_root / security.SYNTHETIC_FIXTURE_PATH
    fixture.parent.mkdir(parents=True)
    marker = "-----BEGIN " + "PRIVATE KEY-----"
    fixture.write_text(
        f"{security.SYNTHETIC_FIXTURE_BEGIN}\n{marker}\nTOKEN=synthetic-value\n{security.SYNTHETIC_FIXTURE_END}",
        encoding="utf-8",
    )

    result, output, opened = run_inventory(synthetic_root, [fixture], monkeypatch, capsys)

    assert result == 0
    assert_open_trace(opened, {".gitignore", security.SYNTHETIC_FIXTURE_PATH})
    assert "REPOSITORY_SECURITY_VALID_WITH_DECLARED_CONTENT_EXCLUSIONS" in output
    assert "allowlisted_text_content_scanned=2" in output


def test_root_and_nested_gitignore_use_guarded_reader(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    nested = synthetic_root / "nested" / ".gitignore"
    nested.parent.mkdir()
    nested.write_text("*.cache", encoding="utf-8")
    (synthetic_root / ".gitignore").write_text(".env", encoding="utf-8")

    result, output, opened = run_inventory(synthetic_root, [nested], monkeypatch, capsys)

    assert result == 1
    assert_open_trace(opened, {".gitignore", "nested/.gitignore"})
    assert "missing required ignore rule: *.jks" in output
    assert "allowlisted_text_content_scanned=2" in output


def test_out_of_inventory_gitignore_has_separate_rule_only_count(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker = "-----BEGIN " + "PRIVATE KEY-----"
    (synthetic_root / ".gitignore").write_text(marker, encoding="utf-8")
    monkeypatch.setattr(security, "publishable_files", list)
    opened: list[str] = []
    original_open = security._open_no_follow

    def tracked_open(path: Path, *, parent_descriptor: int | None = None) -> int:
        opened.append(path.name)
        return original_open(path, parent_descriptor=parent_descriptor)

    monkeypatch.setattr(security, "_open_no_follow", tracked_open)

    result = security.main()
    output = capsys.readouterr().out

    assert result == 1
    assert opened == [".gitignore"]
    assert "publishable_paths_checked=0" in output
    assert "allowlisted_text_content_scanned=0" in output
    assert "root_gitignore_rule_only_reads=1" in output
    assert "private key material found in: .gitignore" not in output


def test_missing_root_gitignore_is_invalid_without_unchecked_read(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (synthetic_root / ".gitignore").unlink()
    result, output, opened = run_inventory(synthetic_root, [], monkeypatch, capsys)

    assert result == 1
    assert opened == []
    assert "approved text path unavailable: .gitignore" in output


@pytest.mark.parametrize("case", ["missing", "directory", "undecodable", "unreadable"])
def test_approved_text_failure_is_invalid(
    case: str,
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = synthetic_root / "candidate.txt"
    if case == "directory":
        path.mkdir()
    elif case == "undecodable":
        path.write_bytes(bytes((0xFF,)))
    elif case == "unreadable":
        path.write_text("synthetic harmless text", encoding="utf-8")
        original_open = security._open_no_follow

        def refused_open(
            candidate: Path, *, parent_descriptor: int | None = None
        ) -> int:
            if candidate == path:
                raise PermissionError("synthetic refusal")
            return original_open(candidate, parent_descriptor=parent_descriptor)

        monkeypatch.setattr(security, "_open_no_follow", refused_open)

    result, output, opened = run_inventory(synthetic_root, [path], monkeypatch, capsys)

    assert result == 1
    if case in {"missing", "directory"}:
        readers = {item.removeprefix("reader:") for item in opened if item.startswith("reader:")}
        system_opens = {
            item.removeprefix("system-open:")
            for item in opened
            if item.startswith("system-open:")
        }
        assert readers == {".gitignore"}
        assert system_opens == {".gitignore"}
    else:
        readers = {item.removeprefix("reader:") for item in opened if item.startswith("reader:")}
        system_opens = {
            item.removeprefix("system-open:")
            for item in opened
            if item.startswith("system-open:")
        }
        assert readers == {".gitignore", "candidate.txt"}
        expected_opens = {".gitignore"} if case == "unreadable" else readers
        assert system_opens == expected_opens
    assert "REPOSITORY_SECURITY_INVALID" in output
    if case in {"missing", "directory"}:
        assert "approved text path" in output
    else:
        assert "approved text content not safely scanned: candidate.txt" in output


def test_symlink_and_reparse_metadata_skip_before_content_open(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    allowed = synthetic_root / "linked.py"
    forbidden = synthetic_root / "google-services.json"
    for path in (allowed, forbidden):
        path.write_text("synthetic harmless text", encoding="utf-8")
    original_lstat = Path.lstat

    def fake_lstat(path: Path) -> os.stat_result | SimpleNamespace:
        if path in (allowed, forbidden):
            return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    result, output, opened = run_inventory(
        synthetic_root, [allowed, forbidden], monkeypatch, capsys
    )

    assert result == 1
    assert_open_trace(opened, {".gitignore"})
    assert "skipped_symlink_content=2" in output
    assert "credential-bearing file is publishable: google-services.json" in output


def test_open_identity_mismatch_refuses_read_before_bytes(
    synthetic_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    approved = synthetic_root / "approved.md"
    substitute = synthetic_root / "substitute.md"
    approved.write_text("approved synthetic text", encoding="utf-8")
    substitute.write_text("different synthetic text", encoding="utf-8")
    expected = approved.lstat()
    reads = 0

    class TrackedStream:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            os.close(self.descriptor)

        def fileno(self) -> int:
            return self.descriptor

        def read(self) -> str:
            nonlocal reads
            reads += 1
            return "should never be read"

    monkeypatch.setattr(
        security,
        "_open_no_follow",
        lambda _path, **_kwargs: os.open(substitute, os.O_RDONLY),
    )
    monkeypatch.setattr(
        os,
        "fdopen",
        lambda descriptor, *_args, **_kwargs: TrackedStream(descriptor),
    )

    with pytest.raises(OSError, match="identity changed at open"):
        security._read_approved_text(approved, expected)
    assert reads == 0


def test_reader_rejects_image_name_even_with_regular_metadata(
    synthetic_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = synthetic_root / "icon.svg"
    path.write_text("synthetic harmless text", encoding="utf-8")
    monkeypatch.setattr(
        security,
        "_open_no_follow",
        lambda _path, **_kwargs: pytest.fail("excluded file was opened"),
    )
    with pytest.raises(OSError, match="forbidden for text reading"):
        security._read_approved_text(path, path.lstat())


def test_substituted_symlink_is_rejected_before_open(
    synthetic_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = synthetic_root / "approved.py"
    path.write_text("synthetic harmless text", encoding="utf-8")
    expected = path.lstat()
    if os.name == "nt":
        original_lstat = Path.lstat

        def swapped_lstat(candidate: Path) -> os.stat_result | SimpleNamespace:
            if candidate == path:
                return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
            return original_lstat(candidate)

        monkeypatch.setattr(Path, "lstat", swapped_lstat)
    else:
        original_stat = os.stat

        def swapped_stat(
            candidate: str | bytes | os.PathLike[str] | os.PathLike[bytes],
            *args: Any,
            **kwargs: Any,
        ) -> os.stat_result | SimpleNamespace:
            if candidate == path.name and kwargs.get("dir_fd") is not None:
                return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
            return original_stat(candidate, *args, **kwargs)

        monkeypatch.setattr(os, "stat", swapped_stat)
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {swapped_stat})
    monkeypatch.setattr(
        security,
        "_open_no_follow",
        lambda _path, **_kwargs: pytest.fail("substitute was opened"),
    )

    with pytest.raises(OSError, match="identity changed before open"):
        security._read_approved_text(path, expected)


def test_reparse_parent_is_rejected_before_content_open(
    synthetic_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = synthetic_root / "nested"
    parent.mkdir()
    path = parent / "approved.py"
    path.write_text("synthetic harmless text", encoding="utf-8")
    expected = path.lstat()
    if os.name == "nt":
        original_lstat = Path.lstat

        def substituted_windows_parent(candidate: Path) -> os.stat_result | SimpleNamespace:
            if candidate == parent:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
            return original_lstat(candidate)

        monkeypatch.setattr(Path, "lstat", substituted_windows_parent)
    else:
        original_stat = os.stat

        def substituted_posix_parent(
            candidate: str | bytes | os.PathLike[str] | os.PathLike[bytes],
            *args: Any,
            **kwargs: Any,
        ) -> os.stat_result | SimpleNamespace:
            if candidate == parent.name and kwargs.get("dir_fd") is not None:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
            return original_stat(candidate, *args, **kwargs)

        monkeypatch.setattr(os, "stat", substituted_posix_parent)
        monkeypatch.setattr(
            os, "supports_dir_fd", os.supports_dir_fd | {substituted_posix_parent}
        )
    monkeypatch.setattr(
        security,
        "_open_no_follow",
        lambda _path, **_kwargs: pytest.fail("parent target was opened"),
    )

    with pytest.raises(OSError, match="unsafe parent directory"):
        security._read_approved_text(path, expected)


def test_parent_substitution_and_restoration_never_reads_attacker_text(
    synthetic_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = synthetic_root / "nested"
    parent.mkdir()
    path = parent / "approved.py"
    path.write_text("approved synthetic text", encoding="utf-8")
    expected = path.lstat()
    attacker = synthetic_root / "attacker"
    original_open = security._open_no_follow

    if os.name == "nt":
        attacker.mkdir()
        attacker_file = attacker / path.name
        attacker_file.write_text("attacker synthetic text", encoding="utf-8")
        attacker_metadata = attacker_file.lstat()
        moved = synthetic_root / "nested-moved"
        # Demonstrate that the operating system can open through a junction and
        # restore the name before the real handle-path lookup.
        descriptor: int | None = None
        parent.rename(moved)
        try:
            created = subprocess.run(
                f'cmd.exe /d /c mklink /J "{parent}" "{attacker}"',
                capture_output=True,
                text=True,
                check=False,
            )
            assert created.returncode == 0, created.stderr
            assert _is_reparse_for_test(parent)
            descriptor = original_open(path)
            parent.rmdir()
            moved.rename(parent)
            assert security._same_identity(attacker_metadata, os.fstat(descriptor))
            assert not security._same_object(expected, os.fstat(descriptor))
            assert security._normalized_path(security._descriptor_path(descriptor)) == (
                security._normalized_path(attacker_file)
            )
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if parent.exists() and _is_reparse_for_test(parent):
                parent.rmdir()
            if moved.exists():
                moved.rename(parent)

        leaf_open_attempts = 0
        substitution_completed = False
        opened_leaf_identity: os.stat_result | None = None
        original_relative_open = security._windows_open_relative

        def observe_relative_open(
            parent_descriptor: int, name: str, *, directory: bool
        ) -> int:
            nonlocal opened_leaf_identity
            descriptor = original_relative_open(parent_descriptor, name, directory=directory)
            if not directory and name == path.name:
                opened_leaf_identity = os.fstat(descriptor)
            return descriptor

        def attempt_parent_replacement(
            candidate: Path, *, parent_descriptor: int | None = None
        ) -> int:
            nonlocal leaf_open_attempts, substitution_completed
            leaf_open_attempts += 1
            assert candidate == path
            assert parent_descriptor is not None
            parent.rename(moved)
            try:
                created = subprocess.run(
                    f'cmd.exe /d /c mklink /J "{parent}" "{attacker}"',
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert created.returncode == 0, created.stderr
                assert _is_reparse_for_test(parent)
                return original_open(candidate, parent_descriptor=parent_descriptor)
            finally:
                if parent.exists() and _is_reparse_for_test(parent):
                    parent.rmdir()
                moved.rename(parent)
                substitution_completed = True

        monkeypatch.setattr(security, "_windows_open_relative", observe_relative_open)
        monkeypatch.setattr(security, "_open_no_follow", attempt_parent_replacement)
        monkeypatch.setattr(
            os, "fdopen", lambda *_args, **_kwargs: pytest.fail("content was opened")
        )
        with pytest.raises(OSError, match="parent directory changed during file open"):
            security._read_approved_text(path, expected)
        assert leaf_open_attempts == 1
        assert substitution_completed
        assert opened_leaf_identity is not None
        assert security._same_identity(expected, opened_leaf_identity)
        assert not security._same_object(attacker_metadata, opened_leaf_identity)
        assert parent.is_dir()
        assert attacker.is_dir()
        assert not moved.exists()
    else:
        attacker.mkdir()
        attacker_file = attacker / path.name
        attacker_file.write_text("attacker synthetic text", encoding="utf-8")
        attacker_metadata = attacker_file.lstat()
        moved = synthetic_root / "nested-moved"
        substitution_and_restoration_completed = False
        opened_file_identity: os.stat_result | None = None

        def substitute_then_restore_before_final_path_check(
            candidate: Path, *, parent_descriptor: int | None = None
        ) -> int:
            nonlocal substitution_and_restoration_completed, opened_file_identity
            assert parent_descriptor is not None
            parent.rename(moved)
            parent.symlink_to(attacker, target_is_directory=True)
            try:
                assert parent.is_symlink()
                descriptor = original_open(
                    candidate, parent_descriptor=parent_descriptor
                )
                opened_file_identity = os.fstat(descriptor)
            finally:
                parent.unlink()
                moved.rename(parent)
                substitution_and_restoration_completed = True
            return descriptor

        monkeypatch.setattr(
            security, "_open_no_follow", substitute_then_restore_before_final_path_check
        )
        assert security._read_approved_text(path, expected) == "approved synthetic text"
        assert substitution_and_restoration_completed
        assert opened_file_identity is not None
        assert security._same_identity(expected, opened_file_identity)
        assert not security._same_object(attacker_metadata, opened_file_identity)


def _is_reparse_for_test(path: Path) -> bool:
    return bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


class _InjectedAncestorFailure(PermissionError):
    """Synthetic ancestor-open denial raised before the parent swap is reached."""


@dataclass
class _SameObjectJunctionSwap:
    """Synthetic parent swap that records each completed step for exact cleanup."""

    root: Path
    path: Path
    expected: os.stat_result
    parent_before: os.stat_result
    # Captured before patching: cleanup must never call the swapping hook.
    original_lstat: Callable[[Path], os.stat_result]
    armed: bool = True
    pending_at_cleanup: bool | None = None
    parent_hook_calls: int = 0
    parent_moved: bool = False
    junction_created: bool = False
    junction_removed: bool = False
    parent_restored: bool = False
    opened_junction: bool = False
    restored_before_verification: bool = False
    cleanup_errors: list[Exception] = field(default_factory=list)

    @property
    def parent(self) -> Path:
        return self.path.parent

    @property
    def attacker(self) -> Path:
        return self.root / "attacker"

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        _type: type[BaseException] | None,
        failure: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.undo()
        if not self.cleanup_errors:
            return
        if failure is None:
            raise AssertionError("synthetic swap cleanup failed") from self.cleanup_errors[0]
        # The original failure stays primary; cleanup problems are only annotated.
        for error in self.cleanup_errors:
            failure.add_note(f"synthetic swap cleanup also failed: {error!r}")

    def undo(self) -> None:
        """Reverse only completed steps: the junction first, then the moved parent."""
        self.pending_at_cleanup = self.armed
        self.armed = False
        try:
            if self.junction_created and not self.junction_removed:
                if not security._is_link_or_reparse(self.original_lstat(self.parent)):
                    raise AssertionError(f"expected synthetic junction at {self.parent}")
                self.parent.rmdir()
                self.junction_removed = True
            if self.parent_moved and not self.parent_restored:
                self.attacker.rename(self.parent)
                self.parent_restored = True
        except Exception as error:
            self.cleanup_errors.append(error)

    def assert_original_tree_only(self) -> None:
        assert sorted(os.listdir(self.root)) == [".gitignore", "nested"]
        restored = self.original_lstat(self.parent)
        assert stat.S_ISDIR(restored.st_mode)
        assert not security._is_link_or_reparse(restored)
        assert security._same_object(self.parent_before, restored)
        assert os.listdir(self.parent) == [self.path.name]
        assert security._same_identity(self.expected, self.original_lstat(self.path))


def _install_same_object_junction_swap(
    synthetic_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    ancestor_failure: OSError | None = None,
) -> _SameObjectJunctionSwap:
    parent = synthetic_root / "nested"
    parent.mkdir()
    path = parent / "approved.py"
    path.write_text("approved synthetic text", encoding="utf-8")
    swap = _SameObjectJunctionSwap(
        root=synthetic_root,
        path=path,
        expected=path.lstat(),
        parent_before=parent.lstat(),
        original_lstat=Path.lstat,
    )
    original_relative_open = security._windows_open_relative

    def substitute_after_parent_stat(candidate: Path) -> os.stat_result:
        metadata = swap.original_lstat(candidate)
        if candidate != swap.parent:
            return metadata
        swap.parent_hook_calls += 1
        if swap.armed:
            swap.armed = False
            swap.parent.rename(swap.attacker)
            swap.parent_moved = True
            moved_leaf = swap.original_lstat(swap.attacker / swap.path.name)
            assert security._same_identity(swap.expected, moved_leaf)
            created = subprocess.run(
                f'cmd.exe /d /c mklink /J "{swap.parent}" "{swap.attacker}"',
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode != 0:
                raise AssertionError(f"could not create synthetic junction: {created.stderr}")
            swap.junction_created = True
        return metadata

    def observe_directory_open(
        parent_descriptor: int, name: str, *, directory: bool
    ) -> int:
        if directory and ancestor_failure is not None:
            raise ancestor_failure
        descriptor = original_relative_open(parent_descriptor, name, directory=directory)
        try:
            if (
                directory
                and swap.junction_created
                and not swap.junction_removed
                and security._descriptor_path(parent_descriptor) / name == swap.parent
            ):
                swap.opened_junction = security._is_link_or_reparse(os.fstat(descriptor))
                swap.parent.rmdir()
                swap.junction_removed = True
                swap.attacker.rename(swap.parent)
                swap.parent_restored = True
                swap.restored_before_verification = True
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    monkeypatch.setattr(Path, "lstat", substitute_after_parent_stat)
    monkeypatch.setattr(security, "_windows_open_relative", observe_directory_open)
    monkeypatch.setattr(
        security,
        "_open_no_follow",
        lambda *_args, **_kwargs: pytest.fail("attacker leaf was opened"),
    )
    monkeypatch.setattr(
        os, "fdopen", lambda *_args, **_kwargs: pytest.fail("content was opened")
    )
    return swap


@pytest.mark.skipif(os.name != "nt", reason="Windows junction substitution")
def test_real_same_object_junction_swap_rejects_before_leaf_read(
    synthetic_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    swap = _install_same_object_junction_swap(synthetic_root, monkeypatch)

    with pytest.raises(OSError, match="parent directory changed while opening"), swap:
        security._read_approved_text(swap.path, swap.expected)

    assert swap.junction_created
    assert swap.opened_junction
    assert swap.restored_before_verification
    assert swap.parent_hook_calls == 1
    assert swap.cleanup_errors == []
    swap.assert_original_tree_only()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction substitution")
def test_same_object_swap_cleanup_after_earlier_failure_never_starts_pending_swap(
    synthetic_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    injected = _InjectedAncestorFailure("synthetic ancestor open denied before parent swap")
    swap = _install_same_object_junction_swap(
        synthetic_root, monkeypatch, ancestor_failure=injected
    )

    with pytest.raises(_InjectedAncestorFailure) as failure, swap:
        security._read_approved_text(swap.path, swap.expected)

    # Cleanup ran while the swapping lstat hook was still installed and armed.
    assert Path.lstat is not swap.original_lstat
    assert swap.pending_at_cleanup is True
    assert swap.parent_hook_calls == 0
    assert not (swap.parent_moved or swap.junction_created)
    assert failure.value is injected
    assert not getattr(failure.value, "__notes__", [])
    assert swap.cleanup_errors == []
    swap.assert_original_tree_only()


def test_operating_system_no_follow_guard_on_synthetic_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    link = tmp_path / "link.txt"
    target.write_text("synthetic harmless text", encoding="utf-8")
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError) as python_error:
        if os.name != "nt":
            pytest.skip(f"symlink creation is unavailable: {python_error}")
        create_link = ctypes.WinDLL("kernel32", use_last_error=True).CreateSymbolicLinkW
        create_link.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        create_link.restype = ctypes.c_ubyte
        # Windows 10+ permits this flag when Developer Mode or policy enables it.
        if not create_link(str(link), str(target), 0x2):
            win_error = ctypes.get_last_error()
            pytest.skip(
                "Windows denied unprivileged symlink creation "
                f"(error {win_error}; Python error was {python_error})"
            )

    try:
        descriptor = security._open_no_follow(link)
    except OSError:
        return  # Refusing the link at open is also fail-closed.
    try:
        assert security._is_link_or_reparse(os.fstat(descriptor))
    finally:
        os.close(descriptor)
