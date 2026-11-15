from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
base=Path(__file__).resolve().parent/'source_atlas_rev87_24'
root=base.parent
m=json.loads((root/'source_segment_preflight_rev87_24.json').read_text(encoding='utf-8'))
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',15)
cw,ch=260,270; cols=4; rows=(len(m['segments'])+cols-1)//cols
sheet=Image.new('RGB',(cols*cw,rows*ch),'#e9eef5'); draw=ImageDraw.Draw(sheet)
for i,s in enumerate(m['segments']):
 x=i%cols*cw; y=i//cols*ch
 draw.rounded_rectangle((x+5,y+5,x+cw-5,y+ch-5),radius=10,fill='white',outline='#cbd5e1',width=2)
 draw.text((x+14,y+12),f"P{i+1:02d} · {s['segment_id']}",fill='#17243e',font=font)
 draw.text((x+14,y+34),f"{s['source_path_id']} · {s['drawable_command_count']} lệnh",fill='#56657a',font=font)
 im=Image.open(base/f"segment_{i+1:03d}.png").convert('RGB'); im.thumbnail((220,205)); sheet.paste(im,(x+(cw-im.width)//2,y+54))
sheet.save(root/'attempt_002'/'source_segment_mapping.png')
