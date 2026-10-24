import importlib.util
for x in ['matplotlib','networkx','cairosvg','svglib','PIL','docx','pypdfium2']:
 print(x, bool(importlib.util.find_spec(x)))
