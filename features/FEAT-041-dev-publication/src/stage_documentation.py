"""Stage an exact reviewed documentation candidate set, excluding dirty runtime."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]

def git_paths(*args: str) -> list[str]:
    raw = subprocess.check_output(['git', *args, '-z'], cwd=ROOT)
    return [p.decode('utf-8') for p in raw.split(b'\0') if p]

def main() -> None:
    manifest = json.loads((FEATURE / 'evidence/metrics/PUBLICATION_MANIFEST.json').read_text())
    protected = manifest['protected_local_runtime_sha256']
    for relative, expected in protected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, f'Local runtime changed: {relative}'
    assert not git_paths('diff', '--cached', '--name-only'), 'Existing staged work must be reviewed separately'
    modified = git_paths('diff', '--name-only', '--diff-filter=ACMR')
    new = git_paths('ls-files', '--others', '--exclude-standard')
    new_roots = ('docs/adr/ADR-0014-', 'docs/adr/ADR-0015-',
                 'features/FEAT-020-backend-ai-workflow-demo/status/',
                 'features/FEAT-036-ui-current-direction-alignment/',
                 'features/FEAT-037-registration-age-genai-payment-alignment/',
                 'features/FEAT-038-lightning-vision-startup/',
                 'features/FEAT-039-collaborative-learning-scope/',
                 'features/FEAT-040-four-person-delivery-plan/',
                 'features/FEAT-041-dev-publication/')
    allowed = {'.md', '.json', '.txt', '.py'}
    candidates = {p for p in modified if p not in protected and (p == '.gitignore' or Path(p).suffix in allowed)}
    candidates.update(p for p in new if p.startswith(new_roots) and (Path(p).suffix in allowed or Path(p).name == '.gitkeep'))
    assert not set(protected) & candidates
    assert 'features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md' in candidates
    assert 'features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md' in candidates
    assert not any(Path(p).suffix.lower() in {'.pdf', '.docx', '.png', '.zip', '.xlsx'} for p in candidates)
    stage_manifest = FEATURE / 'evidence/metrics/STAGED_CANDIDATES.json'
    stage_manifest.write_text(json.dumps({'candidate_count_before_manifest': len(candidates), 'paths': sorted(candidates), 'excluded_runtime': list(protected)}, indent=2) + '\n', encoding='utf-8')
    candidates.add(stage_manifest.relative_to(ROOT).as_posix())
    subprocess.check_call(['git', 'add', '--', *sorted(candidates)], cwd=ROOT)
    staged = git_paths('diff', '--cached', '--name-only')
    assert set(staged) == candidates, 'Unexpected staged paths'
    print(json.dumps({'staged_paths': len(staged), 'protected_runtime_paths': len(protected), 'binary_candidates': 0}, indent=2))

if __name__ == '__main__':
    main()
