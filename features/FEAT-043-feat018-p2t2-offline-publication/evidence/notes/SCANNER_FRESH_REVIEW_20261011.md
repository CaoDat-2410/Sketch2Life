# Fresh review — repository-security scanner source and test (2026-10-11)

- Evidence ID: `EV-043-SCANNER-FRESH-REVIEW-20261011`
- Type: review. Related: FEAT-043 AC-043-03; PUB-P1 commit 1.
- Reviewer: the Claude Code session that also prepared this publication. It did not author the
  scanner. This is **not** an independent review. The earlier M1 handle-relative reports (which
  stopped as not reviewable) and older image-safe reviews are not reused as a current PASS.
- Reviewed identities (byte-equal to the PUB-P1 inventory and to commit 1):
  - `tools/validate_repository_security.py`: 24792 bytes, SHA-256
    `4c8733f65cf507c6c3276d03ad8bd530e982839d75605d72e292d4f1520cfb5c`
  - `backend/tests/unit/test_repository_security_validator.py`: 39828 bytes, SHA-256
    `a202c01969cfdc686c62efda0dae28922381a279216ff8d8b2ec30188bb8478e`

## Scope and method

1. Full read of both files and of the scanner diff against baseline `44af2e4`.
2. Synthetic test run from the repository root (Windows, Python 3.12.10, pytest 8.4.2): 22 passed,
   1 skipped. The skip is the OS no-follow symlink test: Windows refused unprivileged symlink
   creation (error 1314).
3. Two-path Ruff (`ruff check --no-cache` on both files, natural config discovery):
   `All checks passed!`. Two-path strict mypy (`--follow-imports=silent --explicit-package-bases
   --config-file backend/pyproject.toml`): `Success: no issues found in 2 source files`.
4. Actual runs on every exact publication tree (commits 1–4), plus an independent classifier.
   The classifier imports the tree's scanner module, does not call `main()` and opens no
   excluded file. Its per-category counts matched the scanner counters exactly in every tree.

## Behaviour confirmed

- Path rules (environment files, credential suffixes/names, seed-account paths) run on every
  publishable path (`git ls-files --cached --others --exclude-standard`).
- `_read_approved_text` is the only content-read boundary. Before opening it requires a
  repository-relative path, no path finding, no image suffix, an allowlisted text name and a
  regular file. It opens each ancestor handle-relative with no-follow semantics, compares
  (dev, ino, size, mtime_ns) identities before the open, at the open and after the read, and
  compares the handle's final path with the requested path. Any `OSError`, `UnicodeError` or
  `ValueError` is reported as an error (exit 1).
- Images, non-allowlisted names, symlinks/reparse points and non-regular files are counted and
  not content-read. On exit 0 the scanner prints
  `REPOSITORY_SECURITY_VALID_WITH_DECLARED_CONTENT_EXCLUSIONS` and
  `mandatory_gate=NOT_ESTABLISHED_WITHOUT_OWNER_SEMANTICS_ACCEPTANCE`. That line is reported
  unchanged; owner acceptance is recorded separately (D-043-03).

## Findings

| ID | Severity | Finding |
|---|---|---|
| SR-1 | Info | Semantics change from the baseline scanner. The baseline content-scanned every UTF-8-decodable file. The candidate scans only allowlisted text. On these trees, 14 `.svg`, 1 `.ipynb` and 211 `.gitkeep` files are no longer content-scanned. The 5 binaries (2 `.png`, 2 `.wav`, 1 `.jar`) were not effectively content-scanned by either version. |
| SR-2 | Low | On Windows, the pre-open leaf check uses a pathname `lstat`. Substitution between that check and the handle-relative open is detected by the identity and final-path checks and fails closed rather than being prevented. |
| SR-3 | Low | The test imports the root-level `tools` package, so it only collects when pytest runs from the repository root. Run from `backend/`, it fails with `ModuleNotFoundError: tools`. |
| SR-4 | Info | POSIX branches (`dir_fd`/`O_NOFOLLOW`, `/proc/self/fd`) were not exercised; POSIX remains UNVERIFIED. The OS symlink no-follow test was skipped for lack of privilege. |
| SR-5 | Info | Under the backend Ruff configuration (forced via `--config`), line 594 exceeds 100 characters (E501). Under the configuration Ruff discovers for `tools/`, the file passes. |

## Conclusion and limits

Within this scope no blocking defect was found. On the actual publication trees the read
boundary behaved as declared: 0 read failures and 0 symlink, non-regular or forbidden-path
skips, with exclusions exactly as listed in `../metrics/SCANNER_EXCLUSIONS_T1_T4.tsv`. This is
neither an independent review nor a repository-security PASS. The mandatory gate for this
checkpoint rests on owner decision A, which is scoped to the five PUB-P1 trees.
