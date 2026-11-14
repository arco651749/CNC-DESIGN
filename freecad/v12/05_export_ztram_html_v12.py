# -*- coding: utf-8 -*-
"""v12 Z-plate pivot joint, on its own: saddle, Z plate, RBPB8 spherical bearing and pin, face screws, side screws, clamp bolts, epoxy pads
(X blocks and Z rails as faded context). The page adds an exploded view, a section through the ball and the three
adjustment motions about the ball. three.js comes from the v10 motion page.
Run:  freecadcmd freecad/v12/05_export_ztram_html_v12.py      Out: output/v12/CNC_ztram_v12.html"""
import os, re, json, base64, struct
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
V10 = os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html')
TPL = os.path.join(ROOT, 'freecad', 'v12', 'ztram_page.html')
OUT = os.path.join(ROOT, 'output', 'v12', 'CNC_ztram_v12.html')
src = open(V10, encoding='utf-8').read()
m = re.search(r'^const DATA=\[.*\];', src, re.M)
three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]

ROLE = [('pad', r'^Z_epoxy_pad_'), ('zp', r'^(X_carriage_plate|Z_face_screw_|Z_clamp_bolt_|Z_rail_|Z_pivot_pin)'),
        ('sad', r'^(X_saddle_plate|Z_pivot_bearing|Z_roll_block|Z_roll_screw|X_block_)')]
CTX = r'^(X_block_|Z_rail_)'
def colour(n):
    if 'epoxy' in n: return [0.13, 0.62, 0.56]
    if n.startswith('Z_pivot_'): return [0.16, 0.5, 0.78]
    if 'bolt' in n: return [0.45, 0.48, 0.5]
    if '_block' in n and not n.startswith('X_block'): return [0.2, 0.23, 0.26]
    if 'screw' in n: return [0.88, 0.36, 0.12]
    if n == 'X_saddle_plate': return [0.52, 0.56, 0.6]
    if n == 'X_carriage_plate': return [0.74, 0.77, 0.8]
    return [0.7, 0.72, 0.75]
doc = App.openDocument(os.path.join(ROOT, 'output', 'v12', 'CNC_v12.FCStd'))
out = []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    role = next((r for r, rx in ROLE if re.match(rx, o.Label)), None)
    if not role: continue
    pts, tris = o.Shape.tessellate(0.06 if o.Label.startswith('Z_pivot_') else 0.15)
    coords = [int(round(v * 10)) for p in pts for v in (p.x, p.y, p.z)]
    w = 1 if len(pts) < 65536 else 0
    idx = [k for t in tris for k in t]
    out.append({'n': o.Label, 'c': colour(o.Label), 'k': role, 'x': 1 if re.match(CTX, o.Label) else 0,
                'p': base64.b64encode(struct.pack('<%dh' % len(coords), *coords)).decode('ascii'),
                'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode('ascii'), 'w': w, 'nt': len(tris)})
page = open(TPL, encoding='utf-8').read()
page = page.replace('<!--THREE-->', three, 1).replace('/*DATA*/', 'const DATA=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';', 1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(page)
print('parts=%d size=%d' % (len(out), len(page)))
