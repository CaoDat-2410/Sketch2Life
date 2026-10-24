"""Validate individual PNG coverage and build a local image gallery/delivery ZIP."""
from __future__ import annotations
import hashlib
import html
import json
import struct
import subprocess
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FEATURE=Path(__file__).resolve().parents[1]
ROOT=FEATURE.parents[1]
TITLE={
'C01':'Tham gia phiên','C02':'Phòng chờ','C03':'Bàn vẽ','C04':'Gợi ý tham khảo','C05':'Cùng vẽ nhóm','C06':'Xem tranh','C07':'Khám phá kiến thức','C08':'Hoạt động ngoài màn hình','C09':'Cảm nhận','C10':'Kết nối lại','C03b':'Bàn vẽ nâng cao 9–12','C04b':'Chờ giáo viên duyệt','C07b':'Đang tạo video',
'T00':'Đăng nhập giáo viên','T01':'Trang chủ giáo viên','T02':'Lớp và hồ sơ trẻ','T03':'Thiết lập phiên','T04':'Phòng chờ và tiếp nhận','T05':'Điều phối lớp','T06':'Không gian nhóm','T07':'Duyệt gợi ý AI','T08':'Phòng tranh','T09':'Duyệt video','T10':'Hoạt động ngoài màn hình','T11':'Phản hồi và quan sát','T12':'Hồ sơ học tập','T13':'Soạn nội dung','T14':'Mẫu phiên và tự động hóa','T07b':'Gợi ý không còn hợp lệ','T09b':'Đang tạo video','T09c':'Lỗi video: giáo viên quyết định',
'A00':'Đăng nhập quản trị','A01':'Tổng quan','A02':'Người dùng và vai trò','A03':'Lớp và trường','A04':'Quản trị nội dung','A05':'Chính sách AI','A06':'Giám sát và sự cố','A07':'Báo cáo','A08':'Consent và yêu cầu dữ liệu','A09':'Nhật ký','A10':'Cấu hình','A08b':'Xóa dữ liệu: hoàn tất một phần'}
ROLES={'child-app':'Child','teacher-app':'Teacher','admin-app':'Admin'}

def main() -> None:
    inventory=json.loads((FEATURE/'artifacts/SCREEN_INVENTORY.json').read_text(encoding='utf-8'))
    baseline=json.loads((FEATURE/'evidence/metrics/BASELINE.json').read_text(encoding='utf-8'))
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==baseline['original_branch']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==baseline['original_head']
    for name,expected in baseline['protected_local_runtime_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    assert hashlib.sha256((ROOT/'features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md').read_bytes()).hexdigest()==baseline['canonical_srs_sha256']
    rows=[]
    for row in inventory['screens']:
        sid=row['id']
        p=FEATURE/'assets/generated'/row['role']/row['filename']
        assert p.is_file(),f'Missing image: {sid}'
        mpath=FEATURE/'assets/manifests'/(sid+'.asset.json')
        m=json.loads(mpath.read_text(encoding='utf-8'))
        data=p.read_bytes()
        assert data[:8]==bytes([137,80,78,71,13,10,26,10])
        dims=struct.unpack('>II',data[16:24])
        assert hashlib.sha256(data).hexdigest()==m['sha256']
        assert dims==(m['width'],m['height']) and dims[0]>=800 and dims[1]>=600
        assert m['asset_id']==sid and m['status']=='REVIEW_PENDING' and m['review']['status']=='REVIEW_PENDING' and m['applied_path'] is None
        assert m['original_copied_unchanged'] and m['synthetic_data_only'] and m['generator']=='built-in image_gen.imagegen'
        assert (FEATURE/m['prompt']).is_file() and m['qa']['status']=='INSPECTED'
        for source in m.get('input_images',[]):
            assert hashlib.sha256((FEATURE/source['path']).read_bytes()).hexdigest()==source['sha256']
        rows.append(dict(row,title=TITLE[sid],status='GENERATED_REVIEW_PENDING',width=dims[0],height=dims[1],bytes=len(data),sha256=m['sha256'],image='../'+p.relative_to(FEATURE).as_posix(),prompt='../'+m['prompt'],manifest='../'+mpath.relative_to(FEATURE).as_posix()))
    counts=Counter(row['role'] for row in rows)
    assert counts=={'child-app':13,'teacher-app':18,'admin-app':12} and len(rows)==43
    main_ids={row['srs_ui_id'] for row in rows if row['kind']=='main'}
    expected={f'C{i:02}' for i in range(1,11)}|{f'T{i:02}' for i in range(1,15)}|{f'A{i:02}' for i in range(1,11)}
    assert main_ids==expected
    for role in ROLES:
        actual={p.name for p in (FEATURE/'assets/generated'/role).glob('*.png')}
        assert actual=={r['filename'] for r in rows if r['role']==role},(role,actual)
    assert len({r['sha256'] for r in rows})==43,'Screens must be distinct images'
    inventory['screens']=rows
    inventory['status']='GENERATED_REVIEW_PENDING'
    (FEATURE/'artifacts/SCREEN_INVENTORY.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    cards=[]
    for r in rows:
        cards.append('<article class="card" data-role="'+r['role']+'" data-kind="'+r['kind']+'" data-search="'+html.escape((r['id']+' '+r['title']).lower(),quote=True)+'"><button class="preview" data-id="'+r['id']+'" aria-label="Mở '+html.escape(r['title'],quote=True)+'"><img loading="lazy" src="'+r['image']+'" alt="'+html.escape(r['title'],quote=True)+'"></button><div class="meta"><div class="eyebrow">'+ROLES[r['role']]+' · '+r['id']+' · '+('Màn chính' if r['kind']=='main' else 'Trạng thái bổ sung')+'</div><h2>'+html.escape(r['title'])+'</h2><div class="links"><a href="'+r['image']+'" download>Tải PNG</a><a href="'+r['prompt']+'">Prompt</a><a href="'+r['manifest']+'">Provenance</a><span>'+str(r['width'])+'×'+str(r['height'])+'</span></div></div></article>')
    page="""<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Sketch2Life · Bộ ảnh UI SRS v3.1</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f8fafc;color:#0f172a;font-family:Arial,system-ui,sans-serif}header{padding:36px 5vw 24px;background:linear-gradient(125deg,#e0f2fe,#fff);border-bottom:1px solid #e2e8f0}.brand{font-weight:800;color:#2563eb;font-size:18px}h1{font-size:30px;letter-spacing:-.6px;margin:12px 0}p{color:#475569;line-height:1.5;margin:10px 0}header a{color:#2563eb}.toolbar{position:sticky;top:0;z-index:2;display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:16px 5vw;background:#ffffffef;backdrop-filter:blur(12px);border-bottom:1px solid #e2e8f0}button,input,select{font:inherit}button{cursor:pointer}.chip{border:1px solid #cbd5e1;border-radius:999px;padding:10px 16px;background:white;color:#334155}.chip.active{background:#2563eb;color:white;border-color:#2563eb}input,select{border:1px solid #cbd5e1;border-radius:12px;padding:10px;background:white}input{min-width:220px}.count{margin-left:auto;color:#64748b;font-size:13px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:24px;padding:28px 5vw 60px}.card{background:white;border:1px solid #e2e8f0;border-radius:18px;overflow:hidden;box-shadow:0 6px 18px #0f172a05}.card[hidden]{display:none}.preview{border:0;padding:0;width:100%;display:block;background:#eff6ff}.preview img{display:block;width:100%;aspect-ratio:1.6;object-fit:contain}.preview:focus-visible,.chip:focus-visible{outline:3px solid #fbbf24;outline-offset:3px}.meta{padding:18px}.eyebrow{font-size:12px;color:#64748b}h2{font-size:17px;margin:9px 0 14px}.links{display:flex;gap:14px;align-items:center;font-size:12px}.links a{color:#2563eb;text-decoration:none}.links span{margin-left:auto;color:#94a3b8}.note{font-size:13px;color:#64748b}dialog{width:min(97vw,1800px);max-width:none;border:0;border-radius:18px;padding:16px;background:#fff}dialog::backdrop{background:#0f172ad9}dialog img{width:100%;max-height:82vh;object-fit:contain;display:block}.viewer-head{display:flex;align-items:center;gap:12px;padding:0 5px 12px}.viewer-head strong{flex:1}.viewer-head button,.viewer-head a{border:1px solid #cbd5e1;border-radius:10px;background:white;padding:8px 12px;color:#2563eb;text-decoration:none;font-size:13px}footer{padding:0 5vw 30px;color:#64748b;font-size:13px}@media(max-width:600px){h1{font-size:25px}.grid{grid-template-columns:1fr}.count{margin-left:0}header{padding-top:24px}}</style>
<header><div class="brand">Sketch2Life</div><h1>Bộ ảnh UI theo SRS v3.1</h1><p>43 ảnh riêng · Child 13 · Teacher 18 · Admin 12<br>34 màn chính và 9 trạng thái bổ sung. Chọn một ảnh để xem đầy đủ.</p><p class="note">Bản đề xuất thiết kế, dữ liệu minh họa. Chưa áp dụng vào ứng dụng.</p><a href="Sketch2Life_UI_SRS_v3.1.zip" download>Tải toàn bộ ba thư mục</a></header>
<nav class="toolbar" aria-label="Lọc màn hình"><button class="chip active" data-filter="all">Tất cả 43</button><button class="chip" data-filter="child-app">Child 13</button><button class="chip" data-filter="teacher-app">Teacher 18</button><button class="chip" data-filter="admin-app">Admin 12</button><input id="search" placeholder="Tìm mã hoặc tên màn…" aria-label="Tìm màn hình"><select id="kind" aria-label="Loại màn"><option value="all">Mọi loại</option><option value="main">Màn chính SRS</option><option value="supplementary">Trạng thái bổ sung</option></select><span id="count" class="count">43 ảnh</span></nav><main class="grid">__CARDS__</main><footer>Màu và thành phần tiếp nối app hiện tại. Prompt và provenance được giữ riêng cho từng ảnh. Đăng nhập T00/A00 và suffix b/c là ảnh bổ trợ, không phải ID SRS mới.</footer>
<dialog id="viewer"><div class="viewer-head"><strong id="viewerTitle"></strong><button id="prev" aria-label="Ảnh trước">←</button><button id="next" aria-label="Ảnh tiếp">→</button><a id="download" download>Tải PNG</a><button id="close">Đóng</button></div><img id="fullImage" alt=""></dialog>
<script>const data=__DATA__;let role='all',active=0;const cards=[...document.querySelectorAll('.card')],search=document.querySelector('#search'),kind=document.querySelector('#kind'),viewer=document.querySelector('#viewer');function filtered(){return data.filter(r=>(role==='all'||r.role===role)&&(kind.value==='all'||r.kind===kind.value)&&(r.id+' '+r.title).toLocaleLowerCase('vi').includes(search.value.toLocaleLowerCase('vi')))}function refresh(){const visible=new Set(filtered().map(r=>r.id));cards.forEach(c=>c.hidden=!visible.has(c.querySelector('button').dataset.id));document.querySelector('#count').textContent=visible.size+' ảnh'}document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{role=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));refresh()});search.oninput=refresh;kind.onchange=refresh;function show(id){const list=filtered(),r=list.find(x=>x.id===id);if(!r)return;active=list.indexOf(r);document.querySelector('#viewerTitle').textContent=r.id+' · '+r.title;const image=document.querySelector('#fullImage');image.src=r.image;image.alt=r.title;document.querySelector('#download').href=r.image;if(!viewer.open)viewer.showModal()}document.querySelectorAll('.preview').forEach(b=>b.onclick=()=>show(b.dataset.id));function move(n){const list=filtered();if(list.length)show(list[(active+n+list.length)%list.length].id)}document.querySelector('#prev').onclick=()=>move(-1);document.querySelector('#next').onclick=()=>move(1);document.querySelector('#close').onclick=()=>viewer.close();document.addEventListener('keydown',e=>{if(viewer.open&&e.key==='ArrowRight')move(1);if(viewer.open&&e.key==='ArrowLeft')move(-1)});viewer.addEventListener('click',e=>{const b=viewer.getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)viewer.close()});</script></html>"""
    page=page.replace('__CARDS__',''.join(cards)).replace('__DATA__',json.dumps(rows,ensure_ascii=False).replace('</',r'<\/'))
    (FEATURE/'artifacts/UI_GALLERY.html').write_text(page,encoding='utf-8',newline='\n')
    index=['# Sketch2Life UI · SRS v3.1','', '43 independent PNGs: Child13, Teacher18, Admin12. Main34SRS screens plus9essential variants. Vietnamese synthetic mockups, REVIEW_PENDING; not runtime implementation.','', '| Role | ID | Screen | Type | PNG |','| --- | --- | --- | --- | --- |']
    for r in rows:
        index.append('| '+ROLES[r['role']]+' | '+r['id']+' | '+r['title']+' | '+r['kind']+' | ['+r['filename']+']('+r['image']+') |')
    (FEATURE/'artifacts/SCREEN_INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf-8',newline='\n')
    for role,label in ROLES.items():
        lines=['# '+label+' UI','', 'SRSv3.1 design proposal PNGs; one image per screen/state. Visual approval pending.','']
        lines.extend('- ['+r['id']+' — '+r['title']+']('+r['filename']+')' for r in rows if r['role']==role)
        (FEATURE/'assets/generated'/role/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    bundle=FEATURE/'artifacts/Sketch2Life_UI_SRS_v3.1.zip'
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_STORED) as z:
        for r in rows:
            z.write(FEATURE/'assets/generated'/r['role']/r['filename'],r['role']+'/'+r['filename'])
            z.write(FEATURE/'assets/manifests'/(r['id']+'.asset.json'),'provenance/'+r['id']+'.asset.json')
        for p in sorted((FEATURE/'assets/prompts').rglob('*.txt')):
            z.write(p,'prompts/'+p.relative_to(FEATURE/'assets/prompts').as_posix())
        def portable_links(value: str) -> str:
            return value.replace('../assets/generated/','').replace('../assets/prompts/','prompts/').replace('../assets/manifests/','provenance/')
        zip_page=portable_links(page).replace('<a href="Sketch2Life_UI_SRS_v3.1.zip" download>Tải toàn bộ ba thư mục</a>','<a href="SCREEN_INDEX.md">Danh sách toàn bộ màn hình</a>')
        z.writestr('UI_GALLERY.html',zip_page)
        z.writestr('SCREEN_INDEX.md',portable_links('\n'.join(index)+'\n'))
        portable_inventory=dict(inventory,screens=[dict(r,image=portable_links(r['image']),prompt=portable_links(r['prompt']),manifest=portable_links(r['manifest'])) for r in rows])
        z.writestr('SCREEN_INVENTORY.json',json.dumps(portable_inventory,ensure_ascii=False,indent=2)+'\n')
        z.writestr('README.md','Sketch2Life SRS v3.1: 43 individual UI images in child-app/, teacher-app/, admin-app/. 34 main screens plus 9 essential variants. Unzip, then open UI_GALLERY.html to browse offline. Generated with built-in imagegen; Vietnamese synthetic design proposals, visual approval pending. All generation/edit prompts and final provenance included. Provenance preserves original repository-relative paths; superseded edit inputs remain in the feature evidence, outside this selected-image delivery. No runtime or device acceptance claimed.\n')
    report={'status':'UI_IMAGE_DELIVERY_VALID','verified_at_utc':datetime.now(timezone.utc).isoformat(),'total_images':43,'main_srs_screens':34,'supplementary_images':9,'role_counts':dict(counts),'unique_png_hashes':43,'png_bytes':sum(r['bytes'] for r in rows),'bundle_bytes':bundle.stat().st_size,'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'all_images_review_pending':True,'original_eight_runtime_files_unchanged':True,'canonical_srs_unchanged':True,'original_branch_and_head_unchanged':True,'runtime_asset_references_added':False}
    (FEATURE/'evidence/metrics/DELIVERY_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
