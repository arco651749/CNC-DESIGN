# -*- coding: utf-8 -*-
"""v14 exploded view (machine on the coolant base): parts grouped by sub-assembly, each group moved along its own direction by a slider
(base down, columns out, X axis back, X carriage / Z slide / tool head up and forward, table forward). Click a legend entry to hide a group.
Run:  freecadcmd freecad/v14/14_export_exploded_v14.py      Out: output/v14/CNC_v14_exploded.html (internal: contains vendor models)"""
import os, re, json, base64, struct
import FreeCAD as App
ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
src = open(os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html'), encoding='utf-8').read()
m = re.search(r'^const DATA=\[.*\];', src, re.M)
three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]
doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))
def cls(o):
    n = o.Label
    if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''
# clusters: id -> (label, offset vector at full explosion, colour)
CL = {'base': ('A 切削液底座（鋁擠、水盤、水箱）', (0, 0, -700), [0.62, 0.66, 0.7]),
      'guard': ('護板', (0, 0, -700), [0.72, 0.76, 0.8]),
      'datum': ('基準底板＋Y 滑塊', (0, 0, -300), [0.85, 0.6, 0.3]),
      'y': ('Y 工作台＋稜鏡站', (0, -650, -300), [0.75, 0.55, 0.3]),
      'colL': ('龍門立柱（左）', (-300, 0, -120), [0.55, 0.6, 0.66]),
      'colR': ('龍門立柱（右）', (300, 0, -120), [0.55, 0.6, 0.66]),
      'xs': ('X 軸（底板、滑軌、螺桿、馬達）', (0, 380, 220), [0.3, 0.5, 0.75]),
      'elec': ('電控', (0, 650, 280), [0.3, 0.3, 0.32]),
      'x': ('X 滑座＋Z 軸板', (0, 0, 260), [0.45, 0.62, 0.78]),
      'z': ('Z 滑座', (0, -260, 360), [0.6, 0.72, 0.85]),
      'head': ('工具頭模組板＋主軸', (0, -500, 380), [0.4, 0.45, 0.52]),
      'cam': ('相機模組', (-220, -700, 380), [0.15, 0.6, 0.55]),
      'probe': ('探針模組', (180, -820, 380), [0.85, 0.5, 0.1])}
def cluster(o):
    n = o.Label; c = cls(o)
    if n.startswith('Guard_'): return 'guard'
    if (('Adj' in o.PropertiesList and o.Adj == 'base') or n.startswith(('Base_', 'Coolant_'))) and not n.startswith(('Coolant_nozzle',)): return 'base'
    if n.startswith('Coolant_nozzle'): return 'head'
    if c == 'y': return 'y'
    if c == 'z':
        if n.startswith('Camera'): return 'cam'
        if n.startswith('Probe'): return 'probe'
        if n.startswith(('Spindle', 'ER11', 'Tool')): return 'head'
        return 'z'
    if c == 'x': return 'x'
    if n.startswith(('Servo_amp', 'Electrical')): return 'elec'
    if n.startswith(('Gantry_column', 'Column_foot', 'Foot_')): return 'colL' if o.Shape.BoundBox.Center.x < 0 else 'colR'
    b = o.Shape.BoundBox
    if n.startswith(('X_', 'Yaw', 'Roll')) or b.ZMin > 150: return 'xs'
    return 'datum'
def colour(o, k):
    n = o.Label
    if re.search(r'(bolt|screw|_pin|dowel|stud|jack)', n, re.I) and 'ballscrew' not in n: return [0.95, 0.75, 0.1]
    if 'fitting' in n: return [0.1, 0.1, 0.11]
    if 'tube' in n or 'hose' in n: return [0.15, 0.45, 0.85]
    if 'epoxy' in n: return [0.13, 0.62, 0.56]
    if n.startswith(('X_motor', 'Y_motor', 'Z_motor')) and 'plate' not in n and 'block' not in n: return [0.2, 0.22, 0.25]
    return CL[k][2]
out = []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    k = cluster(o)
    b = o.Shape.BoundBox
    tol = 0.25 if max(b.XLength, b.YLength, b.ZLength) > 150 else 0.12
    pts, tris = o.Shape.tessellate(tol)
    coords = [int(round(v * 4)) for p in pts for v in (p.x, p.y, p.z)]
    idx = [i for t in tris for i in t]; w = 1 if len(pts) < 65536 else 0
    out.append({'n': o.Label, 'k': k, 'c': colour(o, k), 'p': base64.b64encode(struct.pack('<%dh' % len(coords), *coords)).decode(),
                'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode(), 'w': w})
cl = {k: {'t': v[0], 'o': v[1], 'c': v[2]} for k, v in CL.items()}
page = open(os.path.join(ROOT, 'freecad', 'v14', 'exploded_page.html'), encoding='utf-8').read().replace('<!--THREE-->', three, 1).replace(
    '/*DATA*/', 'const DATA=' + json.dumps(out, separators=(',', ':')) + ';const CL=' + json.dumps(cl, ensure_ascii=False) + ';', 1)
open(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_exploded.html'), 'w', encoding='utf-8').write(page)
from collections import Counter
print('parts', len(out), 'size', len(page), Counter(p['k'] for p in out))
