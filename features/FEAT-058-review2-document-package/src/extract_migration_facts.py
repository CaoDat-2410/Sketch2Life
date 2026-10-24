import re, pathlib
for path in sorted(pathlib.Path('backend/alembic/versions').glob('*.py')):
 s=path.read_text(encoding='utf8'); rev=re.search(r'^revision\s*=\s*["\'](.+?)["\']',s,re.M); down=re.search(r'^down_revision\s*=\s*(.+)$',s,re.M)
 names=re.findall(r'op\.create_table\(\s*["\']([^"\']+)',s)
 fks=re.findall(r'sa\.ForeignKey\(\s*["\']([^"\']+)',s)
 print(path.name,'rev=',rev.group(1) if rev else '?','down=',down.group(1).strip() if down else '?','tables=',','.join(names),'fks=',','.join(fks))
