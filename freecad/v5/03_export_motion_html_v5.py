# -*- coding: utf-8 -*-
"""v5 motion-simulation page: same viewer as v4 (template = v4 page as committed), DATA rebuilt from CNC_v5.FCStd.
g (translation axis) / r (spin axis) / colour come from the v4 page by label; new v5 parts use OVERRIDE.
Run:  freecadcmd freecad/v5/03_export_motion_html_v5.py      Out: output/v5/CNC_motion_v5.html"""
import os, re, json, base64, struct
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
TEMPLATE = os.path.join(ROOT, 'output', 'v4', 'CNC_motion_v4_screws.html')
FCSTD = os.path.join(ROOT, 'output', 'v5', 'CNC_v5.FCStd')
OUT = os.path.join(ROOT, 'output', 'v5', 'CNC_motion_v5.html')
LOG = os.path.join(ROOT, 'output', 'v5', 'logs', 'export_motion_html_v5.txt')
OVERRIDE = {   # new in v5: (g, r, colour)
    'X_block_R1': ('x', '', [0.3, 0.33, 0.36]), 'X_block_R2': ('x', '', [0.3, 0.33, 0.36]),
    'X_saddle_bridge': ('x', '', [0.9, 0.45, 0.15]), 'X_saddle_rear': ('x', '', [0.9, 0.45, 0.15]),
    'X_rail_rear': ('', '', [0.66, 0.68, 0.7]),
    'Box_rear_plate': ('', '', [0.55, 0.6, 0.65]), 'Box_top_plate': ('', '', [0.55, 0.6, 0.65]),
    'Box_bottom_plate': ('', '', [0.55, 0.6, 0.65]),
}

html = open(TEMPLATE, encoding='utf-8').read()
m = re.search(r'^const DATA=(\[.*\]);', html, re.M)
old = {d['n']: d for d in json.loads(m.group(1))}
doc = App.openDocument(FCSTD)
out, log = [], []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids:
        continue
    name = o.Label
    if name in OVERRIDE:
        g, r, c = OVERRIDE[name]
    elif name in old:
        g, r, c = old[name]['g'], old[name]['r'], old[name]['c']
    else:
        g, r, c = '', '', [0.7, 0.72, 0.75]; log.append('NO MAPPING (static) ' + name)
    pts, tris = o.Shape.tessellate(0.15)
    if not tris:
        continue
    coords = [int(round(v * 10)) for p in pts for v in (p.x, p.y, p.z)]
    w = 1 if len(pts) < 65536 else 0
    idx = [k for t in tris for k in t]
    out.append({'n': name, 'c': c, 'g': g, 'r': r,
                'p': base64.b64encode(struct.pack('<%dh' % len(coords), *coords)).decode('ascii'),
                'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode('ascii'),
                'w': w, 'nt': len(tris)})
    log.append('%s g=%r r=%r tris=%d' % (name, g, r, len(tris)))
html2 = html[:m.start()] + 'const DATA=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';' + html[m.end():]
html2 = re.sub(r'<div class="sub">.*?</div>',
               '<div class="sub">v5（鞍座跨箱型樑：前、後板各一條 X 線軌；X 螺桿在箱內；電控待移位）· 拖曳旋轉、滾輪縮放</div>', html2, count=1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(html2)
log.insert(0, 'parts=%d size=%d' % (len(out), len(html2)))
open(LOG, 'w', encoding='utf-8').write('\n'.join(log))
