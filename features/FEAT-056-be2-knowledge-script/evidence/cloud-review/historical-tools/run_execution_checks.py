"""Feature-owned evidence runner; never installs or calls a live provider."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
FEATURE = ROOT / 'features/FEAT-056-be2-knowledge-script'
LOCAL = FEATURE / 'evidence/local'
SOURCE = ROOT / 'backend/src'
os.environ['PYTHONPATH'] = str(SOURCE)
os.environ['MYPYPATH'] = str(SOURCE)
sys.path.insert(0, str(SOURCE))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def own_files():
    return sorted({*ROOT.glob('backend/src/sketch2life/**/knowledge_bundle.py'),
                   *ROOT.glob('backend/src/sketch2life/contracts/schemas/knowledge_bundles.py'),
                   *ROOT.glob('backend/src/sketch2life/infrastructure/knowledge_bundle/*.py'),
                   *ROOT.glob('backend/tests/unit/test_knowledge_bundle_*.py'),
                   *ROOT.glob('backend/tests/contract/test_knowledge_bundles.py')})

def manifest():
    paths = set(own_files())
    baseline=json.loads((LOCAL/'execution-baseline/backend-before.json').read_text())
    paths.update(ROOT/p for p in baseline)
    paths.add(ROOT/'backend/pyproject.toml')
    paths.update(FEATURE.glob('artifacts/*.json'))
    paths.add(FEATURE/'plan/PLAN_REV1_APPROVED.md')
    paths.add(Path(__file__).resolve())
    paths.add(LOCAL/'finalize_acceptance_map.py')
    paths.update(LOCAL/'execution-baseline'/name for name in ['backend-before.json','tracked-before.json','required-01-06-files.json','external-before.json'])
    paths.add(LOCAL/'claude-remediation-20261020/before-files.json')
    paths.add(LOCAL/'claude-remediation-20261020/historical-review-note-move.json')
    return {p.relative_to(ROOT).as_posix(): {'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)}

def profile_gate(selection):
    baseline=json.loads((LOCAL/'execution-baseline/required-01-06-files.json').read_text())
    profile=json.loads((FEATURE/'artifacts/OFFLINE_BATCH_PROFILE.json').read_text())
    actual=[p.relative_to(ROOT).as_posix() for p in own_files() if '/tests/' in p.as_posix()]
    assert len(baseline)==50 and profile['baseline_01_06']==baseline
    assert set(profile['required_07'])==set(actual)
    assert len(selection)==len(set(selection)) and set(selection)==set(baseline+actual)
    assert all((ROOT/p).is_file() for p in selection)
    assert not profile['installs_allowed'] and not profile['runtime_execution']
    assert profile['excluded'][0]['path']=='backend/tests/unit/test_lightning_vision_v2_server.py'
    assert 'Pillow' in profile['excluded'][0]['reason']
    return {'passed':True,'execution_kind':'evidence_gate','runner_function':'run_execution_checks.py::profile_gate',
            'baseline_01_06_files':len(baseline),'current_07_files':len(actual),'selected_files':len(selection),
            'baseline_selection_ref':'evidence/local/execution-baseline/required-01-06-files.json',
            'baseline_selection_sha256':sha(LOCAL/'execution-baseline/required-01-06-files.json'),
            'profile_sha256':sha(FEATURE/'artifacts/OFFLINE_BATCH_PROFILE.json')}

def text_hygiene():
    paths=set(own_files())
    paths.update(p for p in FEATURE.rglob('*') if p.is_file() and 'local' not in p.relative_to(FEATURE).parts and p.suffix in {'.md','.json','.py'})
    original=json.loads((LOCAL/'claude-remediation-20261020/before-files.json').read_text())
    approval='features/FEAT-056-be2-knowledge-script/approvals/TASK_APPROVAL.md'
    checked=[];exceptions=[]
    for path in sorted(paths):
        relative=path.relative_to(ROOT).as_posix()
        raw=path.read_bytes();value=raw.decode('utf-8')
        assert not raw.startswith(b'\xef\xbb\xbf') and b'\r' not in raw,relative
        assert all(line==line.rstrip() for line in value.splitlines()),relative
        if raw.endswith(b'\n\n'):
            assert relative==approval and sha(path)==original[relative]['sha256'],relative
            exceptions.append({'path':relative,'sha256':sha(path),'issue':'frozen approval has a trailing blank line','disposition':'PRESERVED_AUTHORIZATION_RECORD; no approval bytes edited'})
        checked.append(relative)
    headings=['docs/context/PROJECT_CONTEXT.md','docs/context/SOURCE_REGISTER.md','features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md']
    assert all((ROOT/p).read_bytes().splitlines()[0].startswith(b'# ') for p in headings)
    normalized=['features/FEAT-056-be2-knowledge-script/evidence/notes/PART6_ADAPTERS.md','features/FEAT-056-be2-knowledge-script/evidence/notes/PART8_EXAMPLES.md']
    return {'passed':True,'scanned_files':len(checked),'scanned_paths':checked,'frozen_exceptions':exceptions,
            'routing_h1_first':headings,'explicit_eol_normalizations':[{'path':p,'before_sha256':original[p]['sha256'],'after_sha256':sha(ROOT/p)} for p in normalized]}

def run(out, name, argv):
    started=datetime.now(timezone.utc).isoformat()
    start=time.monotonic()
    with (out/f'{name}.log').open('wb') as log:
        result=subprocess.run(argv,cwd=ROOT,env=os.environ,stdout=log,stderr=subprocess.STDOUT)
    receipt={'argv':argv,'cwd':str(ROOT),'PYTHONPATH':str(SOURCE),'MYPYPATH':str(SOURCE),
             'exit':result.returncode,'seconds':round(time.monotonic()-start,3),
             'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
             'interpreter':sys.executable,
             'log_sha256':sha(out/f'{name}.log')}
    (out/f'{name}-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(name,result.returncode,(out/f'{name}.log').read_text(encoding='utf-8',errors='replace')[-2200:],flush=True)
    return receipt

def invariants():
    before=json.loads((LOCAL/'execution-baseline/tracked-before.json').read_text())
    allowed={'.gitignore','docs/context/PROJECT_CONTEXT.md','docs/context/SOURCE_REGISTER.md',
             'features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md'}
    changed=[p for p,v in before.items() if p not in allowed and sha(ROOT/p)!=v['sha256']]
    assert not changed,changed
    backend=json.loads((LOCAL/'execution-baseline/backend-before.json').read_text())
    assert len(backend)==572 and all(sha(ROOT/p)==v['sha256'] for p,v in backend.items())
    for p in allowed- {'.gitignore'}:
        original=subprocess.check_output(['git','show',f'HEAD:{p}'],cwd=ROOT).split(b'\n',1)[1]
        assert (ROOT/p).read_bytes().endswith(original),p
    assert sha(FEATURE/'plan/PLAN.md')==sha(FEATURE/'plan/PLAN_REV1_APPROVED.md')=='6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36'
    assert sha(LOCAL/'planning-inputs/BE207_COMPONENT_PLAN_DRAFT_20261019.md')=='e64d25b713fdc8c2208958024852ec84637c7c2b69475119ddfbcce3146ee7ea'
    original=json.loads((LOCAL/'claude-remediation-20261020/before-files.json').read_text())
    prefix='features/FEAT-056-be2-knowledge-script/'
    protected=[p for p in original if p.startswith(prefix) and (p.startswith(prefix+'approvals/') or p.startswith(prefix+'plan/') or p.startswith(prefix+'evidence/metrics/') or p.startswith(prefix+'evidence/notes/INDEPENDENT'))]
    restored=prefix+'evidence/notes/INDEPENDENT_ATOMIC_REVIEW.md'
    assert sha(ROOT/restored)=='ee6375258272db67b03b0c0b79e48345137925761276e8427f5e98812585e20a'
    assert all(sha(ROOT/p)==original[p]['sha256'] for p in protected if p!=restored),'frozen authorization/plan/prior evidence changed'
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).strip()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()=='23acf9e83e181305edfeb345be9a8e7eb9dbef88'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='feature/be2-07-knowledge-script'
    new=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    own={p.relative_to(ROOT).as_posix() for p in own_files()}
    assert all(p in own or p.startswith('features/FEAT-056-be2-knowledge-script/') for p in new if p),new
    assert not subprocess.check_output(['git','ls-files','features/FEAT-056-be2-knowledge-script/evidence/local'],cwd=ROOT).strip()
    lf=[]
    for p in own_files():
        data=p.read_bytes();data.decode('utf-8');assert b'\r' not in data and not data.startswith(b'\xef\xbb\xbf'),str(p)
        lf.append(p.relative_to(ROOT).as_posix())
    return {'baseline_backend_unchanged':len(backend),'other_tracked_unchanged':len(before)-len(allowed),'staged':0,'head_unchanged':True,'shared_history_preserved':True,'old_draft_unchanged':True,'approved_plan_unchanged':True,'prior_authorization_plan_evidence_unchanged_files':len(protected),'preserved_records':protected,'pre_remediation_baseline_ref':'evidence/local/claude-remediation-20261020/before-files.json','historical_note_restoration_ref':'evidence/local/claude-remediation-20261020/historical-review-note-move.json','own_source_utf8_lf':lf}

def external_invariants():
    expected=json.loads((LOCAL/'execution-baseline/external-before.json').read_text())
    checked={}
    for label,base in [('main',ROOT.parents[1]),('shared',ROOT.parent/'be2-01-07')]:
        differences=[p for p,expected_hash in expected[label].items() if not (base/p).is_file() or sha(base/p)!=expected_hash]
        assert not differences,(label,differences)
        command=['git','-c',f'safe.directory={base.as_posix()}','status','--porcelain']
        assert subprocess.check_output(command,cwd=base,text=True)==expected[label+'_status'],label
        checked[label+'_unchanged_files']=len(expected[label])
    foundation=ROOT.parent/'be2-01-ai-job-foundation/features/FEAT-044-be2-ai-job-foundation/evidence/local/a17fix01-studio-package-20261016'
    actual={p.relative_to(foundation).as_posix():sha(p) for p in foundation.rglob('*') if p.is_file()}
    assert actual==expected['a17'],'frozen A17 changed'
    checked['a17_unchanged_files']=len(actual)
    checked['external_baseline_sha256']=sha(LOCAL/'execution-baseline/external-before.json')
    checked['external_baseline_ref']='evidence/local/execution-baseline/external-before.json'
    return checked

def main():
    parser=argparse.ArgumentParser();parser.add_argument('name');parser.add_argument('--tests',nargs='*');parser.add_argument('--final',action='store_true');parser.add_argument('--static',action='store_true');parser.add_argument('--invariants',action='store_true');args=parser.parse_args()
    out=LOCAL/args.name;out.mkdir(exist_ok=False)
    before=manifest();(out/'source-before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8',newline='\n')
    env={'python':sys.version,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'packages':{x:importlib.metadata.version(x) for x in ['pytest','pydantic','ruff','mypy']},'imports':{}}
    for path in own_files():
        if path.is_relative_to(SOURCE) and path.name!='__init__.py':
            module='.'.join(path.relative_to(SOURCE).with_suffix('').parts)
            imported=importlib.import_module(module)
            assert Path(imported.__file__).resolve()==path.resolve(),module
            env['imports'][module]=str(Path(imported.__file__).resolve())
    (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf-8',newline='\n')
    checks={}
    if args.final:
        selection=json.loads((LOCAL/'execution-baseline/required-01-06-files.json').read_text())
        assert len(selection)==50
        selection+= [p.relative_to(ROOT).as_posix() for p in own_files() if '/tests/' in p.as_posix()]
        profile_result=profile_gate(selection)
        (out/'batch-profile-checks.json').write_text(json.dumps(profile_result,indent=2)+'\n',encoding='utf-8',newline='\n')
        (out/'selected-files.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8',newline='\n')
        checks['collection']=run(out,'collection',[sys.executable,'-m','pytest','-c','backend/pyproject.toml','-o','addopts=','--collect-only','-q',*selection])
        args.tests=selection if checks['collection']['exit']==0 else None
    if args.tests:
        checks['pytest']=run(out,'pytest',[sys.executable,'-m','pytest','-c','backend/pyproject.toml',*args.tests,'-ra',f'--junitxml={out}/junit.xml',f'--basetemp={out}/pytest-temp'])
        if (out/'junit.xml').exists():
            junit=ET.parse(out/'junit.xml'); cases=junit.findall('.//testcase')
            counts={'collected':len(cases),'passed':sum(not any(c.find(n)is not None for n in ['failure','error','skipped']) for c in cases),'failed':sum(c.find('failure')is not None for c in cases),'errors':sum(c.find('error')is not None for c in cases),'skipped':sum(c.find('skipped')is not None for c in cases)}
            (out/'junit-summary.json').write_text(json.dumps({'counts':counts,'junit_sha256':sha(out/'junit.xml'),'cases':[{'classname':c.get('classname'),'name':c.get('name'),'status':next((n for n in ['failure','error','skipped'] if c.find(n)is not None),'passed'),'detail':next((str(c.find(n).get('message')) for n in ['failure','error','skipped'] if c.find(n)is not None),'')} for c in cases]},indent=2)+'\n',encoding='utf-8',newline='\n')
            print(counts,flush=True)
    if args.static or args.final:
        source=[str(p.relative_to(ROOT)) for p in own_files() if '/src/' in p.as_posix()]
        checks['ruff']=run(out,'ruff',[sys.executable,'-m','ruff','check','--config','backend/pyproject.toml','--config','lint.isort.known-first-party=["sketch2life"]',*[str(p.relative_to(ROOT)) for p in own_files()]])
        checks['evidence-script-ruff']=run(out,'evidence-script-ruff',[sys.executable,'-m','ruff','check','--config','backend/pyproject.toml',str((LOCAL/'finalize_acceptance_map.py').relative_to(ROOT))])
        for label in ['mypy-strict','mypy-fresh-cache']:
            extra=[] if label=='mypy-strict' else ['--no-incremental',f'--cache-dir={out}/mypy-fresh-cache']
            checks[label]=run(out,label,[sys.executable,'-m','mypy','--strict','--follow-imports=silent','--config-file','backend/pyproject.toml',*extra,*source])
    if args.final:
        for validator in ['harness','repository_security','architecture','skeleton']:
            checks['validate-'+validator]=run(out,'validate-'+validator,[sys.executable,f'tools/validate_{validator}.py'])
        checks['diff-check']=run(out,'diff-check',['git','diff','--check'])
    if args.invariants or args.final:
        (out/'invariants.json').write_text(json.dumps(invariants(),indent=2)+'\n',encoding='utf-8',newline='\n')
    if args.final:
        (out/'external-invariants.json').write_text(json.dumps(external_invariants(),indent=2)+'\n',encoding='utf-8',newline='\n')
        (out/'text-hygiene.json').write_text(json.dumps(text_hygiene(),indent=2)+'\n',encoding='utf-8',newline='\n')
    after=manifest();assert before==after,'source changed during check'
    (out/'source-after.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('snapshot_sha256',sha(out/'source-before.json'),flush=True)
    return int(any(c['exit']!=0 for c in checks.values()))

if __name__=='__main__': raise SystemExit(main())
