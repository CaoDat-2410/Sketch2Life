from docx import Document
p=r'.runtime/fe058_docx_work/Report7-reference.docx'; d=Document(p)
for ti,t in enumerate(d.tables):
 print('TABLE',ti)
 for ri,row in enumerate(t.rows):
  print(ri, [c.text.replace('\n',' / ') for c in row.cells])
