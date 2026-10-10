"""Capture reproducible redacted offline integration checks."""
from __future__ import annotations
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
def redact(value: str) -> str:
    for prefix in (str(ROOT), ROOT.as_posix()):
        value = value.replace(prefix.replace(chr(92), chr(92) * 2), '<worktree>')
        value = value.replace(prefix, '<worktree>')
    return re.sub(r"\b[A-Za-z]:[\\/]{1,2}(?:Users|Project)[\\/]{1,2}[^\\/:\r\n\s'\"]+", '<owner-local>', value)
def main() -> int:
    arguments = sys.argv[1:]
    cwd = ROOT
    if arguments[0].startswith('--cwd='):
        cwd = (ROOT / arguments.pop(0).split('=', 1)[1]).resolve()
        assert cwd.is_relative_to(ROOT)
    name, *command = arguments
    assert name.replace('_', '').replace('-', '').isalnum()
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    output = redact(result.stdout)
    output = '\n'.join(line.rstrip() for line in output.splitlines()).rstrip() + ('\n' if output.strip() else '')
    (FEATURE / 'evidence/raw' / (name + '.txt')).write_text(output, encoding='utf-8', newline='\n')
    record = {'command': [redact(x) for x in command], 'cwd': redact(str(cwd)), 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'exit_code': result.returncode, 'status': 'PASS' if result.returncode == 0 else 'FAIL'}
    (FEATURE / 'evidence/metrics' / (name + '.json')).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(output[-14000:])
    print(json.dumps(record))
    return result.returncode
if __name__ == '__main__':
    raise SystemExit(main())
