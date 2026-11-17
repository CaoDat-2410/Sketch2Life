"""Reversible publication hygiene; preserve local source/runtime bytes."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
RUNTIME = [
    'apps/ui-mobile/src/demo/childAge.mjs',
    'apps/ui-mobile/src/screens/Flow1Screens.tsx',
    'backend/src/sketch2life/application/services/backend_ai_workflow.py',
    'backend/src/sketch2life/application/services/supervised_flow.py',
    'backend/src/sketch2life/contracts/schemas/workflow_demo.py',
    'backend/src/sketch2life/interfaces/cli/workflow_demo.py',
    'backend/tests/e2e/test_lightning_backend_workflow.py',
    'backend/src/sketch2life/domain/child_age.py',
]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()

def main() -> None:
    manifest = FEATURE / 'evidence/metrics/PUBLICATION_MANIFEST.json'
    if manifest.exists():
        raise SystemExit('Preparation already recorded; do not overwrite initial hashes')
    assert git('branch', '--show-current') == 'codex/pixi-ai-show-20261001'
    protected = {p: digest(ROOT / p) for p in RUNTIME}
    source_files = [ROOT / 'docs/context/SOURCE_REGISTER.md', *(ROOT / 'features/FEAT-037-registration-age-genai-payment-alignment').rglob('*.md')]
    changes = []
    backup_root = ROOT / '.tmp/feat041-publication/source-reference-originals'
    for path in source_files:
        if 'rendered' in path.parts:
            continue
        raw = path.read_bytes()
        text = raw.decode('utf-8').replace('\r\n', '\n')
        def sanitize(match: re.Match[str]) -> str:
            basename = re.split(r'[\\/]+', match[0].strip('`'))[-1]
            return f'`owner-local attachment {basename}`'
        published = re.sub(r'`[A-Za-z]:[\\/][^`]*`', sanitize, text)
        if published == text:
            continue
        relative = path.relative_to(ROOT)
        backup = backup_root / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        assert not backup.exists(), 'Never overwrite preserved source prose'
        backup.write_bytes(raw)
        # Source SHA/version/authority text remains untouched; only locator is derived.
        path.write_text(published, encoding='utf-8', newline='\n')
        changes.append({'path': relative.as_posix(), 'original_prose_sha256': hashlib.sha256(raw).hexdigest(), 'published_prose_sha256': digest(path), 'backup': backup.relative_to(ROOT).as_posix()})
    result = {'source_branch': git('branch', '--show-current'), 'initial_head': git('rev-parse', 'HEAD'),
              'initial_remote_source': git('rev-parse', 'origin/codex/pixi-ai-show-20261001'),
              'initial_remote_dev': git('rev-parse', 'origin/dev'),
              'committed_ahead_of_dev': int(git('rev-list', '--count', 'origin/dev..HEAD')),
              'dev_is_ancestor': subprocess.run(['git', 'merge-base', '--is-ancestor', 'origin/dev', 'HEAD'], cwd=ROOT).returncode == 0,
              'protected_local_runtime_sha256': protected, 'source_reference_changes': changes,
              'publication_scope': 'reviewed documentation and repository hygiene; pending runtime excluded',
              'canonical_srs_sha256': digest(ROOT / 'features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md')}
    manifest.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'normalized_prose_files': len(changes), 'protected_runtime_files': len(protected), 'committed_ahead_of_dev': result['committed_ahead_of_dev'], 'dev_is_ancestor': result['dev_is_ancestor']}, indent=2))

if __name__ == '__main__':
    main()
