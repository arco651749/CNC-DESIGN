# -*- coding: utf-8 -*-
"""Gantry-column electrical box, 3D (machine coordinates): sheet-metal enclosure, DIN rails, openings, all parts
(vendor STEP for the MR-J4 drives and the RP23CNC board, boxes for the rest).
Run: CNC_ROOT=<repo> /opt/freecad/bin/freecadcmd column_box/build_step.py
Out: column_box/column_box.step, column_box/mesh.json (for the preview), column_box/step_check.txt"""
import os, sys, json
import FreeCAD as App, Part, Import
from FreeCAD import Vector as V, Placement, Rotation
ROOT = os.environ.get('CNC_ROOT', os.getcwd()); HERE = os.path.join(ROOT, 'column_box'); sys.path.insert(0, HERE)
import layout as L
SERVO_STEP = os.environ.get('SERVO_STEP') or os.path.join(ROOT, 'vendor', 'mitsubishi', 'MR-J4-40A', 'step', 'mr-j4-40ab.stp')
BOARD_STEP = os.path.join(ROOT, 'vendor', 'rp23cnc', 'RP23CNC_v2.02.step')
doc = App.newDocument('column_box'); OBJ = {}
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cyl(ax, r, a0, a1, p, q):
    d = {'x': V(1, 0, 0), 'y': V(0, 1, 0), 'z': V(0, 0, 1)}[ax]
    o = {'x': V(a0, p, q), 'y': V(p, a0, q), 'z': V(p, q, a0)}[ax]
    return Part.makeCylinder(r, a1 - a0, o, d)
def add(name, shape, grp):
    o = doc.addObject('Part::Feature', name); o.Shape = shape; OBJ[name] = (o, grp); return o
X0, X1, Y0, Y1, Z0, Z1 = L.ENV
# ------------------------------------------------ enclosure
NUTS = [(x, 259) for x in (-350, -250, -150, -50, 50, 150, 250, 350)] + [(x, 490) for x in (-350, -250, -150, -50, 50, 100, 250, 350)] + [(sx, y) for sx in (-376, 376) for y in (365, 435)]
rp = box(-380, 380, 255, 495, 487, 491).cut(cyl('z', 22.5, 486, 492, 50, 390))
for (nx, ny) in NUTS: rp = rp.cut(cyl('z', 4, 486, 492, nx, ny))
add('Box_roof_plate', rp, 'enclosure (mounting plate t4 z487..491; the mechanical top plate t3 z491..494 sits on it and is not modelled here; 20 M5 holes with pull nuts)')
for k, (nx, ny) in enumerate(NUTS, 1): add('PullNut_M5_%02d' % k, cyl('z', 3.75, 478, 487, nx, ny).cut(cyl('z', 2.1, 478, 487, nx, ny)), 'parts (M5 pull nut, 9 mm below the plate)')
wall = box(-383, 383, 495, 500, 241, 491).cut(box(125, 215, 494, 501, 459, 484))
add('Box_back_wall', wall, 'enclosure (back wall, plate t5: the drives and the VFD screw into it)')
add('Box_side_L', box(-383, -380, 252, 500, 241, 491), 'enclosure (sheet metal t3)')
add('Box_side_R', box(380, 383, 252, 500, 241, 491), 'enclosure (sheet metal t3)')
add('Box_front_cover', box(-380, 380, 252, 255, 244, 487), 'enclosure (removable service cover, t3)')
bot = box(-380, 380, 255, 495, 241, 244)
for (hx, hy, r) in ((-340, 270, 12.5), (-120, 330, 22.5), (350, 262, 20), (-250, 400, 65)): bot = bot.cut(cyl('z', r, 240, 245, hx, hy))
add('Box_bottom_cover', bot, 'enclosure (removable bottom cover t3, cable entries)')
# ------------------------------------------------ DIN rails (35 x 7.5)
for nm, (x0, x1, y0, y1, z0, z1) in {'Rail_roof_1': (-370, -10, 293, 328, 479.5, 487), 'Rail_roof_2': (-370, -195, 390, 425, 479.5, 487),
                                     'Rail_roof_3': (-375, -215, 445, 480, 479.5, 487), 'Rail_wall_PSU': (-55, 55, 487.5, 495, 350, 385)}.items():
    add(nm, box(x0, x1, y0, y1, z0, z1), 'DIN rails')
# ------------------------------------------------ parts
def bbox(p): return (p[3], p[3] + p[6], p[4], p[4] + p[7], p[5], p[5] + p[8])
for p in L.PARTS:
    if p[1].startswith('SV') or p[1] == 'BD': continue
    b = bbox(p); add(p[1], box(*b), 'parts (box models, catalog size)' if p[1] != 'FL2' else 'reserved space')
sv = Part.read(SERVO_STEP)                       # local: x +-20, y +-84, z 0..175.9 (back face z=0, front +z)
for p in L.PARTS:
    if p[1].startswith('SV'):
        b = bbox(p); s = sv.copy(); s.Placement = Placement(V((b[0] + b[1]) / 2, L.WALL_Y, (b[4] + b[5]) / 2), Rotation(V(1, 0, 0), 90))
        add(p[1], s, 'parts (vendor STEP)')
        for dz in (-78, 78): add(p[1] + '_bolt_%d' % (1 if dz < 0 else 2), cyl('y', 4, 495 - 10, 495 - 6, (b[0] + b[1]) / 2 - 14, (b[4] + b[5]) / 2 + dz), 'fasteners')
bd = next(p for p in L.PARTS if p[1] == 'BD'); b = bbox(bd)
bs = Part.read(BOARD_STEP)                        # PCB x 81..177, y -144..-48, z 0..1.6, components +z
r = bs.copy(); r.Placement = Placement(V(b[0] - 81, b[2] + 48 + 0 + (-0), 478), Rotation(V(1, 0, 0), 180))
# y' = -y + ty with y=-48 -> b[2]: ty = b[2] - 48
r.Placement = Placement(V(b[0] - 81, b[2] - 48, 477), Rotation(V(1, 0, 0), 180))
add('BD', r, 'parts (vendor STEP)')
for k, (hx, hy) in enumerate(((4, 4), (92, 4), (4, 92), (92, 92)), 1): add('BD_standoff_%d' % k, cyl('z', 2.75, 477, 487, b[0] + hx, b[2] + hy), 'fasteners')
# fan (intake, at the bottom cover) and the filter plates
add('Fan_120', box(-310, -190, 340, 460, 244, 269), 'parts (box models, catalog size)')
add('Louvre_filter', box(125, 215, 489, 495, 459, 484), 'parts (box models, catalog size)')
doc.recompute()
# ------------------------------------------------ checks
names = list(OBJ); bad = []
def vol(a, b):
    A, B = OBJ[a][0].Shape, OBJ[b][0].Shape
    if not A.BoundBox.intersect(B.BoundBox): return 0
    return A.common(B).Volume
encl = [n for n in names if n.startswith('Box_')]
partn = [n for n in names if (OBJ[n][1].startswith('parts') or OBJ[n][1] == 'DIN rails')]
for a in partn:
    for e in encl:
        v = vol(a, e)
        if v > 1: bad.append('%s x %s: %.0f mm3' % (a, e, v))
for i, a in enumerate(partn):
    for c in partn[i + 1:]:
        v = vol(a, c)
        if v > 1: bad.append('%s x %s: %.0f mm3' % (a, c, v))
txt = ['enclosure + parts: %d objects' % len(names), 'interferences: %d' % len(bad)] + bad
open(os.path.join(HERE, 'step_check.txt'), 'w').write('\n'.join(txt) + '\n'); print('\n'.join(txt))
Import.export([o for o, g in OBJ.values()], os.path.join(HERE, 'column_box.step'))
# mesh for the preview
M = []
for n, (o, g) in OBJ.items():
    sh = o.Shape
    if len(sh.Solids) > 1: sh = Part.makeCompound([s for s in sh.Solids if s.Volume > 60]) or sh
    pts, tris = sh.tessellate(1.5 if n.startswith(('SV', 'BD')) else 0.5)
    M.append({'n': n, 'g': g, 'p': [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in pts], 't': tris})
json.dump(M, open(os.path.join(HERE, 'mesh.json'), 'w'))
