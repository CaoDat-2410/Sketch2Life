"""Capture repository checks as feature-local, machine-path-redacted evidence."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
CHECKS = {
    'architecture': ['tools/validate_architecture.py'],
    'harness': ['tools/validate_harness.py', '--feature', 'features/FEAT-040-four-person-delivery-plan'],
    'security': ['tools/validate_repository_security.py'],
    'plan': ['features/FEAT-040-four-person-delivery-plan/src/verify_plan.py'],
}

def main() -> int:
    label = sys.argv[1]
    args = [sys.executable, '-X', 'utf8', *CHECKS[label]]
    check_env = os.environ.copy()
    check_env['PYTHONUTF8'] = '1'
    result = subprocess.run(args, cwd=ROOT, env=check_env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    output = result.stdout + result.stderr
    output = output.replace(str(ROOT), '<workspace>').replace(ROOT.as_posix(), '<workspace>')
    output = re.sub(r'\b[A-Za-z]:[\\/](?:Users|Project)[\\/][^\r\n]*', '<local-machine-path>', output, flags=re.I)
    raw = FEATURE / 'evidence/raw' / f'{label}.txt'
    raw.write_text(output, encoding='utf-8')
    metric = {'check': label, 'command': ['python', '-X', 'utf8', *CHECKS[label]],
              'exit_code': result.returncode, 'output_lines': len(output.splitlines()),
              'raw': raw.relative_to(ROOT).as_posix(), 'machine_paths_redacted': True}
    (FEATURE / 'evidence/metrics' / f'{label.upper()}_RESULT.json').write_text(json.dumps(metric, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metric, indent=2))
    print('\n'.join(output.splitlines()[:12]))
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
