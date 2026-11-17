import re
p='features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.1.md'
lines=open(p,encoding='utf-8').read().splitlines()
for i,line in enumerate(lines):
 if re.search(r'^\|\s*(FR\d+|UC-\d{3}|UC\d+|NFR\d+|B\d+|AC\d+)',line):
  s=re.sub(r'\s+',' ',line.strip())
  print(f'{i+1}: {s[:300]}')
