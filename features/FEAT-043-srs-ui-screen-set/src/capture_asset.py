"""Copy one unchanged imagegen PNG and record its design provenance."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--qa-note', required=True)
    args=parser.parse_args()
    inventory=json.loads((FEATURE/'artifacts/SCREEN_INVENTORY.json').read_text(encoding='utf-8'))
    item=next(row for row in inventory['screens'] if row['id']==args.id)
    assert 'Status: APPROVED' in (FEATURE/'approvals/TASK_APPROVAL.md').read_text(encoding='utf-8')
    prompt=FEATURE/'assets/prompts'/(args.id+'.txt')
    assert prompt.is_file() and prompt.stat().st_size>200
    source=args.source.resolve(strict=True)
    content=source.read_bytes()
    assert content[:8]==bytes([137,80,78,71,13,10,26,10]), 'Expected unchanged PNG source'
    width,height=struct.unpack('>II',content[16:24])
    assert width>=800 and height>=600
    target=FEATURE/'assets/generated'/item['role']/item['filename']
    assert not target.exists(), 'Do not overwrite; inspect/revise before capture'
    shutil.copyfile(source,target)
    assert target.read_bytes()==content
    record={'asset_id':args.id,'use_case':'ui-mockup','status':'REVIEW_PENDING','generated_path':target.relative_to(FEATURE).as_posix(),'srs_ui_id':item['srs_ui_id'],'screen_kind':item['kind'],'role':item['role'],'prompt':prompt.relative_to(FEATURE).as_posix(),'source_references':[{'path':'features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md','sha256':inventory['srs_sha256'],'section':item['source']},{'path':'apps/ui-mobile/src/theme.ts','purpose':'existing design tokens'}],'generator':'built-in image_gen.imagegen','captured_at_utc':datetime.now(timezone.utc).isoformat(),'generator_output_filename':source.name,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content),'width':width,'height':height,'original_copied_unchanged':True,'synthetic_data_only':True,'qa':{'reviewer':'Codex visual inspection','status':'INSPECTED','note':args.qa_note},'review':{'status':'REVIEW_PENDING','reviewer':None,'reviewed_at':None},'applied_path':None,'limitations':'Generated design proposal; not implemented runtime, approved visual or device acceptance.'}
    manifest=FEATURE/'assets/manifests'/(args.id+'.asset.json')
    assert not manifest.exists()
    manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'id':args.id,'target':target.relative_to(FEATURE).as_posix(),'sha256':record['sha256'],'size':[width,height],'status':'REVIEW_PENDING'}))

if __name__=='__main__':
    main()
