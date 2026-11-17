from docx import Document
p=r'.runtime/fe058_docx_work/Report7-reference.docx'
d=Document(p)
for i,e in enumerate(d._element.body):
 t=''.join(e.itertext()).strip().replace('\n',' ')
 if e.tag.endswith('}p'): k='P'
 elif e.tag.endswith('}tbl'): k='TABLE'
 else: k=e.tag.split('}')[-1]
 print(i,k,repr(t[:180]))
