from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
base=Path(__file__).resolve().parent/'source_atlas_rev87_24'
source=Image.open(base/'source_color_reference.png').convert('RGB')
parts=[Image.open(base/f'segment_{i:03d}.png').convert('RGB') for i in (5,6)]
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',22)
canvas=Image.new('RGB',(4*540,590),'#edf1f6'); draw=ImageDraw.Draw(canvas)
items=[('Màu nguồn',source),('Bước 1 · nét 1',parts[0]),('Bước 1 · nét 2',parts[1])]
red_layer=Image.new('RGBA',(512,512),(255,255,255,0))
pix=red_layer.load()
for im in parts:
  p=im.load()
  for y in range(512):
    for x in range(512):
      if min(p[x,y])<235: pix[x,y]=(220,38,38,255)
overlay=source.convert('RGBA'); overlay.alpha_composite(red_layer)
items.append(('Hai nét đặt lên màu nguồn',overlay.convert('RGB')))
for i,(label,im) in enumerate(items):
  x=i*540+14; draw.text((x,10),label,fill='#17243e',font=font); im.thumbnail((510,510)); canvas.paste(im,(x,48))
canvas.save(base/'starter_geometry_comparison.png')
