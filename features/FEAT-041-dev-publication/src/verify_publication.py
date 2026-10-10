"""Record remote publication and unchanged protected local/source bytes."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main() -> None:
    manifest = json.loads((FEATURE / 'evidence/metrics/PUBLICATION_MANIFEST.json').read_text())
    head = git('rev-parse', 'HEAD').decode().strip()
    branch = git('branch', '--show-current').decode().strip()
    assert branch == manifest['source_branch']
    refs = [f'refs/heads/{branch}', 'refs/heads/dev']
    remote_output = git('ls-remote', '--heads', 'origin', *refs).decode()
    remote = dict(line.split()[::-1] for line in remote_output.splitlines())
    assert all(remote.get(ref) == head for ref in refs), remote
    subprocess.check_call(['git', 'merge-base', '--is-ancestor', manifest['initial_remote_dev'], head], cwd=ROOT)
    protected = manifest['protected_local_runtime_sha256']
    changed = set(git('diff', '--name-only', manifest['initial_head'], head).decode().splitlines())
    assert not changed.intersection(protected)
    for path, expected in protected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
        if path != 'backend/src/sketch2life/domain/child_age.py':
            assert git('show', ':' + path) == git('show', 'HEAD:' + path), path
    published_prose = {}
    for item in manifest['source_reference_changes']:
        assert hashlib.sha256((ROOT / item['backup']).read_bytes()).hexdigest() == item['original_prose_sha256'], item['backup']
        data = git('show', 'HEAD:' + item['path'])
        assert data == (ROOT / item['path']).read_bytes(), item['path']
        final_hash = hashlib.sha256(data).hexdigest()
        additions = []
        if item['path'] == 'docs/context/SOURCE_REGISTER.md':
            # The approval source row was added after the initial sanitation snapshot.
            # Keep the original snapshot hash immutable and verify this exact addition.
            row = '| `owner-dev-publication-20261010` | `features/FEAT-041-dev-publication/approvals/TASK_APPROVAL.md` | Direct owner push/dev request | Secure current-branch publication and dev integration | Git publication/hygiene authorized; pending historical runtime excluded by documented default, no new product/provider/deploy authorization |\n'
            assert data.decode().count(row) == 1
            baseline = data.decode().replace(row, '').encode()
            assert hashlib.sha256(baseline).hexdigest() == item['published_prose_sha256']
            additions.append('owner-dev-publication-20261010 approval row')
        else:
            assert final_hash == item['published_prose_sha256'], item['path']
        published_prose[item['path']] = {
            'normalized_snapshot_sha256': item['published_prose_sha256'],
            'actual_published_sha256': final_hash,
            'verified_post_snapshot_additions': additions,
        }
    review = json.loads((FEATURE / 'evidence/metrics/INDEX_REVIEW.json').read_text())
    hashes = {}
    for path, expected in review['protected_index_hashes'].items():
        data = git('show', 'HEAD:' + path)
        assert data == (ROOT / path).read_bytes(), path
        hashes[path] = hashlib.sha256(data).hexdigest()
        assert hashes[path] == expected, path
    assert not git('diff', '--cached', '--name-only').strip()
    report = {
        'status': 'REMOTE_PUBLICATION_VALID',
        'verified_commit': head,
        'source_branch': branch,
        'remote_refs': remote,
        'dev_fast_forward_from': manifest['initial_remote_dev'],
        'protected_runtime_count': len(protected),
        'protected_runtime_bytes_unchanged': True,
        'protected_runtime_not_committed': True,
        'source_prose_original_backups_unchanged': True,
        'published_source_prose_lineage_verified': True,
        'published_source_prose': published_prose,
        'protected_published_artifact_hashes': hashes,
        'index_empty': True,
    }
    (FEATURE / 'evidence/metrics/REMOTE_PUBLICATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    (FEATURE / 'evidence/raw/remote_publication.txt').write_text(remote_output, encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
