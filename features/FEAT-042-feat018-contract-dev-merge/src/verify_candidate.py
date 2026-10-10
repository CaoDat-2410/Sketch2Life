"""Verify candidate identity, immutable artifacts and original dirty workspace."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
SOURCE = 'f9594268b22c026f6b8ba837e3f3f9e8831a7280'
DEV = '396b4f67ddcb413f1ae72fdc9ca0746419f449a4'
def git(*args: str, cwd: Path = ROOT) -> bytes:
    return subprocess.check_output(['git', *args], cwd=cwd)
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--original-workspace', type=Path, required=True)
    args = parser.parse_args()
    original = args.original_workspace.resolve()
    assert git('rev-parse', 'HEAD', cwd=original).decode().strip() == DEV
    manifest = json.loads((original / 'features/FEAT-041-dev-publication/evidence/metrics/PUBLICATION_MANIFEST.json').read_text())
    review = json.loads((ROOT / 'features/FEAT-041-dev-publication/evidence/metrics/INDEX_REVIEW.json').read_text())
    assert git('branch', '--show-current', cwd=original).decode().strip() == manifest['source_branch']
    assert not git('ls-files', '-u').strip()
    merge_head = git('rev-parse', 'MERGE_HEAD').decode().strip()
    assert merge_head == SOURCE
    protected_hashes = {}
    for name, expected in review['protected_index_hashes'].items():
        blob = git('show', ':' + name)
        actual = hashlib.sha256(blob).hexdigest()
        assert actual == expected and blob == (ROOT / name).read_bytes(), name
        protected_hashes[name] = actual
    for name, expected in manifest['protected_local_runtime_sha256'].items():
        assert hashlib.sha256((original / name).read_bytes()).hexdigest() == expected, name
        if name != 'backend/src/sketch2life/domain/child_age.py':
            assert git('show', ':' + name) == git('show', DEV + ':' + name), name
        else:
            assert not git('ls-files', '--', name).strip()
    subprocess.check_call(['git', 'diff', '--cached', '--check'], cwd=ROOT)
    result = {'status': 'CANDIDATE_INTEGRITY_VALID', 'source_sha': SOURCE, 'prior_dev_sha': DEV, 'plan_checkpoint': git('rev-parse', 'HEAD').decode().strip(), 'unmerged_paths': 0, 'protected_artifact_hashes': protected_hashes, 'original_workspace_runtime_hashes_unchanged': 8, 'original_workspace_branch_unchanged': True, 'pending_runtime_excluded_from_candidate': True}
    (FEATURE / 'evidence/metrics/CANDIDATE_REVIEW.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    main()
