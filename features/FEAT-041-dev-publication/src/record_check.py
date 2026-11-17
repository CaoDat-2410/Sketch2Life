"""Record publication checks without publishing machine-specific paths."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
CHECKS = {
    'srs': ['python', '-X', 'utf8', 'features/FEAT-039-collaborative-learning-scope/src/verify_documentation.py'],
    'tasks': ['python', '-X', 'utf8', 'features/FEAT-040-four-person-delivery-plan/src/verify_plan.py'],
    'architecture': ['python', '-X', 'utf8', 'tools/validate_architecture.py'],
    'harness': ['python', '-X', 'utf8', 'tools/validate_harness.py'],
    'skeleton': ['python', '-X', 'utf8', 'tools/validate_skeleton.py'],
    'team': ['python', '-X', 'utf8', 'tools/validate_team_allocation.py'],
    'security': ['python', '-X', 'utf8', 'tools/validate_repository_security.py'],
    'staged_diff': ['git', 'diff', '--cached', '--check'],
}

def main() -> int:
    label = sys.argv[1]
    args = CHECKS[label]
    check_env = os.environ.copy(); check_env['PYTHONUTF8'] = '1'
    result = subprocess.run(args, cwd=ROOT, env=check_env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    output = (result.stdout + result.stderr).replace(str(ROOT), '<workspace>').replace(ROOT.as_posix(), '<workspace>')
    (FEATURE / 'evidence/raw' / f'{label}.txt').write_text(output, encoding='utf-8')
    metric = {'check': label, 'command': args, 'exit_code': result.returncode,
              'output_lines': len(output.splitlines()), 'raw': f'evidence/raw/{label}.txt'}
    (FEATURE / 'evidence/metrics' / f'{label.upper()}_RESULT.json').write_text(json.dumps(metric, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metric))
    print('\n'.join(output.splitlines()[:8]))
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
