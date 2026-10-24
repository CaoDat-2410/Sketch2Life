from pathlib import Path
import sys
import pypdfium2 as pdfium
from PIL import Image,ImageOps,ImageDraw
sys.stdout.reconfigure(encoding='utf-8')
root=Path(r'features/FEAT-058-review2-document-package/evidence/render/final')
for name in ['Reports1-5_Tracking','DesignBrief','Report2_Project_Management_Plan']:
 pdf=pdfium.PdfDocument(root/(name+'.pdf'))
 out=root/(name+'_pages'); out.mkdir(exist_ok=True)
 for stale in list(out.glob('page-*.png')) + list(out.glob('contact-*.png')):
  stale.unlink()
 print('\nDOC',name,'PAGES',len(pdf))
 thumbs=[]
 for i in range(len(pdf)):
  page=pdf[i]; text=page.get_textpage().get_text_range().replace('\n',' | ')
  print(f'PAGE {i+1}: {text[:280]}')
  bmp=page.render(scale=1.55)
  img=bmp.to_pil(); path=out/f'page-{i+1:02d}.png'; img.save(path)
  thumb=img.copy(); thumb.thumbnail((510,720))
  canvas=Image.new('RGB',(530,755),'#d7dce3'); canvas.paste(thumb,((530-thumb.width)//2,20))
  ImageDraw.Draw(canvas).text((12,732),f'{name} page {i+1}',fill='black')
  thumbs.append(canvas)
 for offset in range(0,len(thumbs),4):
  selected=thumbs[offset:offset+4]
  sheet=Image.new('RGB',(1060,755*((len(selected)+1)//2)),'white')
  for j,im in enumerate(selected): sheet.paste(im,((j%2)*530,(j//2)*755))
  sheet.save(out/f'contact-{offset//4+1:02d}.png')
