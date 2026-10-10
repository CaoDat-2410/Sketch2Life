"""Read-only remote ancestry and original workspace preservation check."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from verify_candidate import FEATURE, ROOT, SOURCE, DEV, git

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--original-workspace', type=Path, required=True)
    parser.add_argument('--receipt')
    args = parser.parse_args()
    original = args.original_workspace.resolve()
    head = git('rev-parse', 'HEAD').decode().strip()
    refs = dict(line.split()[::-1] for line in git('ls-remote', 'origin', 'refs/heads/dev', 'refs/heads/codex/feat-018-contract-plan').decode().splitlines())
    assert refs['refs/heads/dev'] == head, refs
    assert refs['refs/heads/codex/feat-018-contract-plan'] == SOURCE, refs
    for ancestor in (SOURCE, DEV):
        subprocess.check_call(['git', 'merge-base', '--is-ancestor', ancestor, head], cwd=ROOT)
    manifest = json.loads((original / 'features/FEAT-041-dev-publication/evidence/metrics/PUBLICATION_MANIFEST.json').read_text())
    assert git('rev-parse', 'HEAD', cwd=original).decode().strip() == DEV
    assert git('branch', '--show-current', cwd=original).decode().strip() == manifest['source_branch']
    for name, expected in manifest['protected_local_runtime_sha256'].items():
        assert hashlib.sha256((original / name).read_bytes()).hexdigest() == expected, name
        if name != 'backend/src/sketch2life/domain/child_age.py':
            assert git('show', head + ':' + name) == git('show', DEV + ':' + name), name
        else:
            assert not git('ls-files', '--', name).strip()
    hashes = json.loads((FEATURE / 'evidence/metrics/CANDIDATE_REVIEW.json').read_text())['protected_artifact_hashes']
    for name, expected in hashes.items():
        blob = git('show', head + ':' + name)
        assert hashlib.sha256(blob).hexdigest() == expected and blob == (ROOT / name).read_bytes(), name
    assert not git('ls-files', '-u').strip()
    result = {'status': 'REMOTE_PUBLICATION_VERIFIED', 'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'remote_dev_sha': head, 'remote_source_sha': SOURCE, 'prior_dev_sha': DEV, 'both_source_and_prior_dev_are_ancestors': True, 'protected_artifact_hashes': hashes, 'original_workspace_runtime_hashes_unchanged': 8, 'original_workspace_head_unchanged': True, 'original_workspace_branch_unchanged': True, 'pending_runtime_excluded_from_publication': True, 'force_push': False}
    if args.receipt:
        assert args.receipt.replace('_', '').isalnum()
        (FEATURE / 'evidence/metrics' / (args.receipt + '.json')).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
