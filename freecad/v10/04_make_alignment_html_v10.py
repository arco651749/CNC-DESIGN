# -*- coding: utf-8 -*-
"""v10 alignment animation page: how each geometric check is measured and adjusted, played on the v10 model.
Mesh data and three.js come from the v10 motion page; the scenes live in alignment_page.html.
Run (plain Python, after 03_export_motion_html_v10.py):  python freecad/v10/04_make_alignment_html_v10.py
Out: output/v10/CNC_alignment_v10.html"""
import os, re

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
SRC = os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html')
TPL = os.path.join(ROOT, 'freecad', 'v10', 'alignment_page.html')
OUT = os.path.join(ROOT, 'output', 'v10', 'CNC_alignment_v10.html')

src = open(SRC, encoding='utf-8').read()
m = re.search(r'^const DATA=\[.*\];', src, re.M)
three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]
page = open(TPL, encoding='utf-8').read()
assert '<!--THREE-->' in page and '/*DATA*/' in page
page = page.replace('<!--THREE-->', three, 1).replace('/*DATA*/', m.group(0), 1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(page)
print('wrote %s (%d bytes)' % (OUT, len(page)))
