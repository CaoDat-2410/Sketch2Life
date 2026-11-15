from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,textwrap
base=Path(__file__).resolve().parent
attempt=base/'attempt_002'; atlas=base/'source_atlas_rev87_24'
manifest=json.loads((attempt/'render_manifest.json').read_text(encoding='utf-8'))
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',18); small=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',15)
card_w,card_h=450,430; cols=3; rows=3
sheet=Image.new('RGB',(cols*card_w,rows*card_h),'#e9eef5'); draw=ImageDraw.Draw(sheet)
def draw_card(ix,title,caption,img):
 x=(ix%cols)*card_w; y=(ix//cols)*card_h
 draw.rounded_rectangle((x+8,y+8,x+card_w-8,y+card_h-8),radius=12,fill='white',outline='#cad4e2',width=2)
 draw.text((x+22,y+18),title,fill='#15243c',font=font)
 lines=textwrap.wrap(caption,width=44)
 for j,line in enumerate(lines[:3]): draw.text((x+22,y+48+22*j),line,fill='#42536b',font=small)
 im=img.convert('RGB'); im.thumbnail((390,340)); sheet.paste(im,(x+(card_w-im.width)//2,y+112))
source=Image.open(atlas/'source_color_reference.png'); draw_card(0,'Ảnh màu nguồn CC0',manifest['source_asset_id'],source)
for st in manifest['stages']:
 image=Image.open(attempt/f'cumulative_stage_{st["step_index"]:02d}.png')
 draw_card(st['step_index'],f'Bước {st["step_index"]} · '+', '.join(st['new_path_ids']),st['instruction_vi'],image)
sheet.save(attempt/'cumulative_stage_review.png')
