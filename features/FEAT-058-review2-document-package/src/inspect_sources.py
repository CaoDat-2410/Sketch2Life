"""Read pinned repository objects without changing the working tree."""
from __future__ import annotations
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'evidence' / 'local'
METRICS = ROOT / 'evidence' / 'metrics'
REFS = {
    'be2': 'origin/feature/be2-backend-ai-integration',
    'admin': 'origin/FE_UI_Admin',
    'p2t5': 'origin/feature/feat018-p2t5-evaluation-harness',
    'lightning': 'origin/feature/feat018-p2t2-live-lightning',
}

def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args])

def wanted(lane: str, p: str) -> bool:
    if lane == 'be2':
        return (
            (p.startswith('backend/src/') and p.endswith('.py'))
            or ('versions/' in p and p.startswith('backend/') and p.endswith('.py'))
            or (p.startswith('docs/adr/') and p.endswith('.md'))
            or p in ['backend/pyproject.toml', 'apps/ui-mobile/package.json', 'apps/mobile/package.json']
            or (p.startswith('features/FEAT-057') and (p.endswith('/STATUS.md') or p.endswith('/CONTEXT.md')
                or any(t in p for t in ['RUNTIME_READINESS_20261020', 'BE2_01_07_08_POSTGRESQL17_FLOW_TEST_20261022',
                'APPROVED_SCOPE_EXECUTION_MANIFEST_20261021', 'CROSS_LANE_X01_MODAL_RUN_20261020',
                'CROSS_LANE_UOW_OWNER_DECISION_D3_20261021'])))
            or (p.startswith('docs/contracts/') and p.endswith('.md'))
        )
    if lane == 'admin':
        return p.startswith('apps/admin-ui/') and p.endswith(('.ts', '.tsx', '.json', '.md')) and not p.endswith('package-lock.json')
    if lane == 'p2t5':
        return p.endswith('STATUS.md') and 'FEAT-018' in p or (p.startswith('backend/src/') and ('evaluation' in p or 'diagnostic' in p))
    return (p.startswith('backend/src/') and any(t in p.lower() for t in ['modal', 'lightning', 'vision'])) or (p.endswith('.md') and ('P2_T2' in p or 'W2_' in p) and '/notes/' in p)

manifest = []
for lane, ref in REFS.items():
    sha = git('rev-parse', ref).decode().strip()
    paths = git('ls-tree', '-r', '--name-only', sha).decode().splitlines()
    selected = [p for p in paths if wanted(lane, p)]
    for p in selected:
        data = git('show', f'{sha}:{p}')
        target = LOCAL / 'branches' / lane / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest.append({'lane': lane, 'sha': sha, 'path': p, 'sha256': hashlib.sha256(data).hexdigest()})
    print(lane, sha[:8], len(selected), 'files captured')
METRICS.mkdir(parents=True, exist_ok=True)
(METRICS / 'inspected_objects.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

routes = []
base = LOCAL / 'branches' / 'be2' / 'backend' / 'src'
for p in base.rglob('*.py'):
    if 'interfaces' not in p.parts:
        continue
    try:
        tree = ast.parse(p.read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeError):
        continue
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                continue
            if dec.func.attr not in ['get', 'post', 'put', 'patch', 'delete'] or not dec.args:
                continue
            if isinstance(dec.args[0], ast.Constant):
                routes.append({'method': dec.func.attr.upper(), 'path': dec.args[0].value,
                               'function': node.name, 'source': str(p.relative_to(LOCAL / 'branches' / 'be2'))})
(METRICS / 'be2_route_inventory.json').write_text(json.dumps(routes, indent=2), encoding='utf-8')
print('HTTP route declarations', len(routes))
