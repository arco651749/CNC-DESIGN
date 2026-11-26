# -*- coding: utf-8 -*-
"""v14 back plate viewer: output/v14/panel/CNC_v14_panel.FCStd -> output/v14/panel/CNC_v14_panel.html (keep-out boxes toggled by a button).
Run:  freecadcmd freecad/v14/21_export_panel_html_v14.py"""
import os, re, json, base64, struct
import FreeCAD as App
ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
src = open(os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html'), encoding='utf-8').read()
m = re.search(r'^const DATA=\[.*\];', src, re.M); three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]
doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'panel', 'CNC_v14_panel.FCStd'))
def colour(n):
    if n.startswith('Keepout'): return [0.9, 0.3, 0.2]
    if 'bolt' in n: return [0.95, 0.75, 0.1]
    if n.startswith('Servo_amp'): return [0.2, 0.22, 0.25]
    if n.startswith('Controller'): return [0.1, 0.45, 0.25]
    if 'standoff' in n.lower(): return [0.75, 0.76, 0.78]
    return [0.62, 0.66, 0.7]
out = []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull(): continue
    pts, tris = o.Shape.tessellate(0.08)
    c = [int(round(v * 10)) for p in pts for v in (p.x, p.y, p.z)]; idx = [i for t in tris for i in t]; w = 1 if len(pts) < 65536 else 0
    out.append({'n': o.Label, 'c': colour(o.Label), 'k': 1 if o.Label.startswith('Keepout') else 0,
                'p': base64.b64encode(struct.pack('<%dh' % len(c), *c)).decode(), 'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode(), 'w': w})
info = open(os.path.join(ROOT, 'output', 'v14', 'panel', 'logs', 'panel_check.txt'), encoding='utf-8').read().split('\n')[0]
page = open(os.path.join(ROOT, 'freecad', 'v14', 'panel_page.html'), encoding='utf-8').read().replace('<!--THREE-->', three, 1).replace(
    '/*DATA*/', 'const DATA=' + json.dumps(out, separators=(',', ':')) + ';', 1).replace('/*INFO*/',
    '背板 290 × 260 t5（原本 220 × 220）：3 台 MR-J4-40A 間距 10、上下各留 46；RP23CNC 用 4 支 M3×10 支撐柱；背面 3 支 D20×75 支撐柱鎖 X 底板。按「禁區 顯示」看伺服散熱與控制板配線空間。', 1)
open(os.path.join(ROOT, 'output', 'v14', 'panel', 'CNC_v14_panel.html'), 'w', encoding='utf-8').write(page)
print('parts', len(out), 'size', len(page))
