"""Validate scope coverage, ownership and dependency semantics of the plan."""
from __future__ import annotations

import hashlib
import json
import re
import runpy
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
PIN = 'a95c89589843e3555e967c5e486f3bcaf4bbdf9446cb3bc9c49ed16f672964d9'
errors: list[str] = []

def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)

def block(text: str, label: str) -> str:
    match = re.search(rf'<!-- {label}-BEGIN -->(.*?)<!-- {label}-END -->', text, re.S)
    check(match is not None, f'missing marked table: {label}')
    return match.group(1) if match else ''

def rows(text: str) -> list[list[str]]:
    return [[x.strip() for x in line.strip('|').split('|')]
            for line in text.splitlines() if line.startswith('|')]

def table(text: str, label: str, pattern: str) -> dict[str, list[str]]:
    selected = [r for r in rows(block(text, label)) if re.fullmatch(pattern, r[0])]
    result = {r[0]: r[1:] for r in selected}
    check(len(result) == len(selected), f'duplicate primary IDs: {label}')
    return result

def compact_tasks(text: str) -> set[str]:
    result = set()
    for m in re.finditer(r'\b(FE|BE1|BE2|INTG)-(\d{2})((?:/\d{2})*)', text):
        prefix, first, suffix = m.groups()
        result.add(f'{prefix}-{first}')
        result.update(f'{prefix}-{n}' for n in suffix.split('/') if n)
    return result

def main() -> int:
    doc = FEATURE / 'artifacts/TEAM_TASK_BREAKDOWN.md'
    text = doc.read_text(encoding='utf-8')
    srs_path = ROOT / 'features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md'
    mirror = ROOT / 'features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.1.md'
    check(hashlib.sha256(srs_path.read_bytes()).hexdigest() == PIN, 'canonical SRS changed')
    check(srs_path.read_bytes() == mirror.read_bytes(), 'SRS mirror differs')
    expected = {f'{prefix}-{n:02}' for prefix, count in [('FE', 15), ('BE1', 16), ('BE2', 14), ('INTG', 12)] for n in range(1, count + 1)}
    cards = list(re.finditer(r'^#### ((?:FE|BE1|BE2|INTG)-\d{2}) — (.+)\n([\s\S]*?)(?=^#{1,4} |\Z)', text, re.M))
    check(len(cards) == 57 and {m[1] for m in cards} == expected, '57 unique detailed task cards required')
    for m in cards:
        ident, title, body = m.groups()
        check(bool(title.strip()), f'missing title {ident}')
        if ident.startswith('FE-'):
            required = ['Chủ trì / review:', 'Phạm vi / bàn giao:', 'Prerequisites / gate:', 'SRS:', 'Nghiệm thu dương:', 'Nghiệm thu âm:', 'Evidence / DoD riêng:']
        elif ident.startswith('BE1-'):
            required = ['Đầu ra:', 'Phụ thuộc/gate:', 'Truy vết:', 'Nghiệm thu:', 'positive:', 'Negative:', 'Evidence/reviewer:']
        elif ident.startswith('BE2-'):
            required = ['Reviewer:', 'Phạm vi:', 'Giao:', 'Điều kiện trước:', 'Handoff:', 'Truy vết:', 'Nghiệm thu dương:', 'Nghiệm thu âm:', 'Evidence:']
        else:
            required = ['Owner/reviewer:', 'Đầu ra:', 'Phụ thuộc:', 'SRS:', 'Đạt:', 'Evidence:']
        for field in required:
            check(field in body, f'{ident} missing card field {field}')
        if ident.startswith('INTG-'):
            check('không' in body or 'Missing' in body, f'{ident} needs negative branch')
    unknown = compact_tasks(text) - expected
    check(not unknown, f'unknown task references: {sorted(unknown)}')

    cmd = table(text, 'CMD-OWNERS', r'CMD-\d{2}')
    data = table(text, 'DATA-OWNERS', r'DATA-\d{2}')
    ui = table(text, 'UI-OWNERS', r'[CTA]\d{2}')
    fr = table(text, 'FR-TRACE', r'FR\d{3}')
    modules = table(text, 'MODULE-TRACE', r'M\d{2}')
    check(set(cmd) == {f'CMD-{n:02}' for n in range(1, 67)}, 'CMD 01–66 coverage')
    check(set(data) == {f'DATA-{n:02}' for n in range(1, 36)}, 'DATA 01–35 coverage')
    check(set(ui) == {f'{p}{n:02}' for p, count in [('C', 10), ('T', 14), ('A', 10)] for n in range(1, count + 1)}, '34 UI coverage')
    check(set(fr) == {f'FR{n:03}' for n in range(1, 67)}, 'FR001–066 coverage')
    check(set(modules) == {f'M{n:02}' for n in range(1, 15)}, 'M01–14 coverage')
    for group, prefix in [(cmd, ('BE1-', 'BE2-')), (data, ('BE1-', 'BE2-')), (ui, ('FE-',))]:
        for ident, values in group.items():
            check(values[0] in expected and values[0].startswith(prefix), f'invalid primary {ident}: {values[0]}')
    check(sum(v[0].startswith('BE1-') for v in cmd.values()) == 52, 'P2 CMD partition 52')
    check(sum(v[0].startswith('BE2-') for v in cmd.values()) == 14, 'P3 CMD partition 14')
    check(sum(v[0].startswith('BE1-') for v in data.values()) == 25, 'P2 DATA partition 25')
    check(cmd.get('CMD-48', [None])[0] == 'BE2-12', 'sole CMD48 dispatcher')
    check(all(cmd.get(f'CMD-{n}', [None])[0] == 'BE1-12' for n in (59, 60)), 'sole read/delivery gateway')
    check(data.get('DATA-24', [None])[0] == 'BE2-05' and data.get('DATA-25', [None])[0] == 'BE2-01', 'shared review/job maintainers')

    source_rows = rows(srs_path.read_text(encoding='utf-8'))
    source_fr = {r[0]: r for r in source_rows if re.fullmatch(r'FR\d{3}', r[0]) and len(r) == 4}
    check(len(source_fr) == 66, 'source FR catalog shape changed')
    for ident, values in fr.items():
        check(values[0] == source_fr[ident][1] and values[1] == source_fr[ident][2], f'{ident} source wording/status changed')
        check(bool(compact_tasks(values[2])) and bool(compact_tasks(values[3])) and bool(compact_tasks(values[4])), f'{ident} missing role trace')
    for ident in ('FR052', 'FR053', 'FR054'):
        check('BE2-13' in fr.get(ident, ['', '', '', ''])[3], f'{ident} missing preset semantics owner')

    dep_rows = table(text, 'DEPENDENCIES', r'(?:FE|BE1|BE2|INTG)-\d{2}')
    deps = {t: sorted(compact_tasks(values[0])) for t, values in dep_rows.items()}
    check(set(deps) == expected, 'dependency table must contain all cards')
    check(all(set(v) <= expected for v in deps.values()), 'unknown dependency')
    initial = {'FE-01', 'BE1-01', 'BE2-01', 'INTG-01'}
    check(all(not deps.get(t) for t in initial), 'four foundations must have no hard dependency')
    resolved: set[str] = set()
    while len(resolved) < len(deps):
        available = {t for t, parents in deps.items() if set(parents) <= resolved} - resolved
        if not available:
            check(False, f'dependency cycle/unresolved: {sorted(set(deps) - resolved)}')
            break
        resolved.update(available)
    def ancestors(task: str) -> set[str]:
        found, pending = set(), list(deps.get(task, []))
        while pending:
            t = pending.pop()
            if t not in found:
                found.add(t); pending.extend(deps.get(t, []))
        return found
    check('INTG-05' not in ancestors('INTG-06'), 'gallery/video forced through Sketch')
    check(not {'BE2-04', 'BE2-05'} & ancestors('BE2-09'), 'video waits for live Sketch runtime')
    check('shared DATA-24' in text and 'ProviderCopyLifecycle' in text, 'missing shared-schema/provider-copy boundary')
    check('Phase 2 có gate' in text and 'Đạt Phase 2 sau OD18' in text, 'Phase2 grouping integration gap')

    h_rows = [r for r in rows(text) if re.fullmatch(r'H-[A-Z-]+', r[0])]
    defined_h = {r[0] for r in h_rows}
    used_h = set(re.findall(r'\bH-[A-Z]+(?:-[A-Z]+)*\b', text))
    check(len(h_rows) == len(defined_h) == 14 and used_h == defined_h, '14 handoffs must resolve uniquely')
    for h in h_rows:
        check(bool(compact_tasks(h[1])) and bool(compact_tasks(h[3])), f'{h[0]} missing producer/consumer')
    check(not re.search(r'\b\d+\s*(tuần|giờ công|ngày làm việc|sprint points)\b', text, re.I), 'unrequested duration/effort estimate')

    required_paths = ['CONTEXT.md', 'DECISIONS.md', 'plan/PLAN.md', 'approvals/TASK_APPROVAL.md', 'status/STATUS.md', 'evidence/README.md', 'evidence/raw', 'evidence/metrics', 'evidence/notes', 'evidence/screenshots', 'assets/REVIEW.md']
    for relative in required_paths:
        check((FEATURE / relative).exists(), f'missing own harness {relative}')
    approval = (FEATURE / 'approvals/TASK_APPROVAL.md').read_text(encoding='utf-8')
    check('- Status: APPROVED' in approval and 'nối lại tất cả' in approval, 'owner approval/allocation not recorded')
    rules = runpy.run_path(str(ROOT / 'tools/validate_repository_security.py'))['CONTENT_RULES']
    adr = ROOT / 'docs/adr/ADR-0015-four-person-role-and-integration-allocation.md'
    check(adr.exists(), 'missing allocation ADR')
    for label, pattern in rules.items():
        check(not pattern.search(adr.read_text(encoding='utf-8')), f'new ADR security: {label}')
    scanned = 0
    for path in FEATURE.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        scanned += 1
        for label, pattern in rules.items():
            check(not pattern.search(content), f'own security: {label}: {path.relative_to(FEATURE)}')
        if path.suffix == '.md':
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', content):
                if target.startswith(('http:', 'https:', '#')):
                    continue
                relative = target.strip('<>').split('#')[0]
                check((path.parent / relative).exists(), f'broken link {path.relative_to(FEATURE)} -> {target}')
    manifest = json.loads((FEATURE / 'evidence/metrics/PLAN_MANIFEST.json').read_text(encoding='utf-8'))
    check(deps == {t: sorted(d) for t, d in manifest['dependencies'].items()}, 'manifest dependencies mismatch')
    for key, actual in [('cmd_owners', cmd), ('data_owners', data), ('ui_owners', ui)]:
        check({k: v[0] for k, v in actual.items()} == manifest[key], f'manifest {key} mismatch')
    result = {'result': 'FAIL' if errors else 'PASS', 'errors': errors, 'task_count': len(cards),
              'counts': {'CMD': len(cmd), 'DATA': len(data), 'UI': len(ui), 'FR': len(fr), 'M': len(modules), 'H': len(h_rows)},
              'dependency_nodes': len(deps), 'resolved_nodes': len(resolved), 'foundations': sorted(initial),
              'srs_sha256': PIN, 'artifact_sha256': hashlib.sha256(doc.read_bytes()).hexdigest(),
              'own_text_files_scanned': scanned, 'runtime_verified': False}
    (FEATURE / 'evidence/metrics/PLAN_CHECK.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
