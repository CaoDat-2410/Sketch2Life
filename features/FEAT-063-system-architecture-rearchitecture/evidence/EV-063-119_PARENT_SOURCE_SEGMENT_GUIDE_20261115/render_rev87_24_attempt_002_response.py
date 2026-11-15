import json,html
from pathlib import Path
r=Path(__file__).resolve().parent/'attempt_002'
d=json.loads((r/'response.json').read_text(encoding='utf-8'))
paths={p['path_id']:p for p in d['document']['paths']}
seen=[]
for stage in d['guide']['stages']:
    seen.extend(stage['new_path_ids'])
    assert len(seen)==len(set(seen))
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">']
    for pid in seen:
        p=paths[pid]
        out.append('<path d="'+html.escape(p['d'],quote=True)+'" fill="none" stroke="#202938" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append('</svg>')
    (r/f'cumulative_stage_{stage["step_index"]:02d}.svg').write_text('\n'.join(out),encoding='utf-8')
assert len(seen)==len(paths), (len(seen),len(paths))
(r/'render_manifest.json').write_text(json.dumps({'stage_count':len(d['guide']['stages']),'path_count':len(paths),'all_paths_assigned_once':True,'source_asset_id':d['reference_source']['asset_id'],'source_sha256':d['reference_source']['source_sha256'],'stages':d['guide']['stages']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
