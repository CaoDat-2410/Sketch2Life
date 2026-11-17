"""Verify the prospective publication tree and preservation of local runtime."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]

def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)

def main() -> None:
    source = json.loads((FEATURE / 'evidence/metrics/PUBLICATION_MANIFEST.json').read_text())
    staged = [p.decode() for p in git_bytes('diff', '--cached', '--name-only', '-z').split(b'\0') if p]
    protected = source['protected_local_runtime_sha256']
    assert not set(staged) & set(protected)
    for p, expected in protected.items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == expected
        if p != 'backend/src/sketch2life/domain/child_age.py':
            assert git_bytes('show', ':' + p) == git_bytes('show', 'HEAD:' + p)
    selected = [
        'features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md',
        'features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.1.md',
        'features/FEAT-039-collaborative-learning-scope/artifacts/Sketch2Life_Master_SRS_v2.0_preserved_20261010.md',
        'features/FEAT-039-collaborative-learning-scope/artifacts/Sketch2Life_Master_SRS_v3.0_preserved_20261010.md',
        'features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md',
    ]
    hashes = {}
    for p in selected:
        blob = git_bytes('show', ':' + p)
        assert blob == (ROOT / p).read_bytes(), f'Git normalization changed protected bytes {p}'
        hashes[p] = hashlib.sha256(blob).hexdigest()
    assert source['canonical_srs_sha256'] == hashes[selected[0]]
    assert not any(Path(p).suffix.lower() in {'.png', '.jpg', '.pdf', '.docx', '.zip', '.xls', '.xlsx', '.pem', '.jks'} for p in staged)
    assert all(not p.startswith(('.tmp/', '.pytest-tmp-')) for p in staged)
    diff = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout
    report = {'status': 'PUBLICATION_INDEX_VALID', 'staged_paths_at_review': len(staged),
              'runtime_local_sha256_unchanged': True, 'runtime_index_equals_head': True,
              'protected_index_hashes': hashes, 'binary_candidates': 0, 'staged_paths': staged}
    (FEATURE / 'evidence/metrics/INDEX_REVIEW.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'staged_paths'}, indent=2))

if __name__ == '__main__':
    main()
