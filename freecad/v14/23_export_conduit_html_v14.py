# -*- coding: utf-8 -*-
"""v14 conduit review page (light, a few MB so the app preview opens it): the machine without the base, small parts dropped, coarse
mesh, X / Y / Z sliders and an auto run; conduits from output/v14/conduits.json via conduit_inject.py.
Run:  freecadcmd freecad/v14/23_export_conduit_html_v14.py      Out: output/v14/CNC_v14_conduits.html"""
import os, re, json, base64, struct
import FreeCAD as App, Part
ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
src = open(os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html'), encoding='utf-8').read()
m = re.search(r'^const DATA=\[.*\];', src, re.M); three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]
doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14.FCStd'))
def cls(o):
    n = o.Label
    if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''
def colour(n, k):
    if n.startswith(('Servo_amp', 'X_motor', 'Y_motor', 'Z_motor')) and 'plate' not in n and 'block' not in n: return [0.2, 0.22, 0.25]
    if n.startswith('Controller'): return [0.1, 0.45, 0.25]
    return {'y': [0.78, 0.62, 0.42], 'x': [0.5, 0.64, 0.8], 'z': [0.62, 0.72, 0.84]}.get(k, [0.68, 0.71, 0.75])
out = []
OBJS = list(doc.Objects)
CB = os.path.join(ROOT, 'column_box', 'column_box.step')   # electrical box (electrical session): parts inside drawn, sheet metal shown as the translucent envelope
if os.path.exists(CB):
    import Import
    cbd = App.newDocument('column_box'); Import.insert(CB, cbd.Name)
    OBJS += [o for o in cbd.Objects if not o.Label.startswith('Box_')]
for o in OBJS:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    sh = o.Shape; b = sh.BoundBox
    if o.Label.startswith(('Electrical_panel', 'Servo_amp', 'Controller', 'Board_standoff', 'Panel_standoff', 'Keepout')): continue   # old back plate: replaced by the column box (drawn as its envelope)
    OWN = ('Conduit_', 'Feeder_entry', 'X_cable_box', 'Table_cable')                # conduit adaptors / glands / boxes are drawn
    if sh.Volume < 400 or (re.search(r'(bolt|screw|_pin|dowel|epoxy|shim|fitting|tube|reed|nut$)', o.Label, re.I) and not
            (o.Label.startswith(OWN) and not re.search(r'(bolt|screw)', o.Label))): continue
    if len(sh.Faces) > 60 and not o.Label.startswith(('Box_top', 'Conduit_', 'Feeder_', 'X_cable_box', 'Table_')):   # vendor-detailed parts as boxes; own sheet parts keep their real outline
        sh = Part.makeBox(b.XLength, b.YLength, b.ZLength, App.Vector(b.XMin, b.YMin, b.ZMin))
    pts, tris = sh.tessellate(max(1.5, 0.012 * max(b.XLength, b.YLength, b.ZLength)))
    c = [int(round(v * 4)) for p in pts for v in (p.x, p.y, p.z)]; idx = [i for t in tris for i in t]; w = 1 if len(pts) < 65536 else 0
    k = cls(o)
    out.append({'n': o.Label, 'k': k, 'c': colour(o.Label, k), 'p': base64.b64encode(struct.pack('<%dh' % len(c), *c)).decode(),
                'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode(), 'w': w})
page = open(os.path.join(ROOT, 'freecad', 'v14', 'conduit_page.html'), encoding='utf-8').read().replace('<!--THREE-->', three, 1).replace(
    '/*DATA*/', 'const DATA=' + json.dumps(out, separators=(',', ':')) + ';', 1)
_nc = {}; exec(open(os.path.join(ROOT, 'freecad', 'v14', 'conduit_inject.py'), encoding='utf-8').read(), _nc)
page, _ = _nc['inject'](page, ROOT)
open(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_conduits.html'), 'w', encoding='utf-8').write(page)
print('parts', len(out), 'size', len(page))
