import pypdfium2 as p
f=p.PdfDocument(r'features/FEAT-058-review2-document-package/evidence/render/final/DesignBrief.pdf')
for i in range(len(f)):
 t=f[i].get_textpage().get_text_range().replace('\n',' | ')
 print(i+1,t[:450])
