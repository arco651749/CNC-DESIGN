# -*- coding: utf-8 -*-
"""FreeCAD: base frame (changed parts) + electrical cabinet with plate and parts -> base_power.step, interference report.
Run: /opt/freecad/bin/freecadcmd base_power/build_step.py   (set CNC_ROOT to the repo root)"""
import os, sys
import FreeCAD as App, Part, Import
from FreeCAD import Vector as V
ROOT = os.environ.get('CNC_ROOT', os.getcwd()); HERE = os.path.join(ROOT, 'base_power'); sys.path.insert(0, HERE)
import layout as L
BX, FLOOR = 517.5, -790
doc = App.newDocument('base_power'); OBJ = {}
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def add(name, shape, grp):
    o = doc.addObject('Part::Feature', name); o.Shape = shape; OBJ[name] = (o, grp); return o
LZ = FLOOR + 90
for i, (x, y) in enumerate([(-BX, -580), (BX, -580), (-BX, 40), (BX, 40), (-BX, 560), (BX, 560)], 1):
    add('Base_leg_%d' % i, box(x - 20, x + 20, y - 20, y + 20, FLOOR + 60, -130), 'frame')
for T, x0, x1 in (('L', -BX - 20, -BX + 20), ('R', BX - 20, BX + 20)):
    add('Base_top_side_' + T, box(x0, x1, -560, 540, -130, -90), 'frame')
    add('Base_low_side_' + T, box(x0, x1, -560, 540, LZ, LZ + 40), 'frame')
add('Base_top_front', box(-BX - 20, BX + 20, -600, -560, -130, -90), 'frame'); add('Base_top_rear', box(-BX - 20, BX + 20, 540, 580, -130, -90), 'frame')
add('Base_low_front', box(-BX + 20, BX - 20, -600, -560, LZ, LZ + 40), 'frame')
for k, y in enumerate((-120, 168), 1): add('Base_cross_%d' % k, box(-BX + 20, BX - 20, y - 20, y + 20, -130, -90), 'frame')
x0, y0, z0 = L.CAB_X0, L.CAB_Y0, L.CAB_Z0
cw, ch, cd = L.CAB_D, L.CAB_W, L.CAB_H          # x depth, y width, z height
shell = box(x0, x0 + cw, y0, y0 + ch, z0, z0 + cd).cut(box(x0 + 2, x0 + cw - 2, y0 + 2, y0 + ch - 2, z0 + 2, z0 + cd - 2))
add('Cabinet_box', shell, 'NEW steel box 250 deep x 620 wide x 580 high, IP54, door on the +x side; the plate is its back panel')
for k, (fx, fy) in enumerate(((x0 + 40, y0 + 40), (x0 + cw - 40, y0 + 40), (x0 + 40, y0 + ch - 40), (x0 + cw - 40, y0 + ch - 40)), 1):
    add('Cabinet_foot_%d' % k, box(fx - 30, fx + 30, fy - 30, fy + 30, FLOOR, FLOOR + 60), 'NEW levelling foot (box rests on the floor)')
for k, z in enumerate((-600, -250), 1):
    add('Cabinet_bracket_%d' % k, box(BX + 20, x0, 0, 60, z - 30, z + 30), 'NEW bracket 3 t plate: leg 3 (y=40) to the box back wall, M8 x2 each side')
px = x0 + 2 + 3                                              # plate face x (3 mm standoff from the back wall)
py = y0 + (ch - L.PLATE_W) / 2; pz = z0 + (cd - L.PLATE_H) / 2
add('Cabinet_plate', box(px - 2.5, px, py, py + L.PLATE_W, pz, pz + L.PLATE_H), 'NEW mounting plate 580x540x2.5 (back panel)')
parts, rep, ok = L.place()
for p in parts:
    Y = py + p['x']; Z = pz + L.PLATE_H - p['y'] - p['h']
    add('%s_%s_%d' % (p['key'], p['row'], p['idx']), box(px, px + p['d'], Y, Y + p['w'], Z, Z + p['h']), 'part')
doc.recompute()
# interference: everything vs everything inside the electrical group, and cabinet vs frame
names = list(OBJ); bad = []
cab = ['Cabinet_box']
for a in names:
    for b in names:
        if a < b and (a in cab or b in cab) and not ('Cabinet_' in a and 'Cabinet_' in b):
            v = OBJ[a][0].Shape.common(OBJ[b][0].Shape).Volume
            if v > 1: bad.append('%s x %s: %.0f mm3' % (a, b, v))
parts_obj = [n for n in names if OBJ[n][1] == 'part']
for i, a in enumerate(parts_obj):
    for b in parts_obj[i + 1:]:
        v = OBJ[a][0].Shape.common(OBJ[b][0].Shape).Volume
        if v > 1: bad.append('%s x %s: %.0f mm3' % (a, b, v))
    # parts must lie inside the cabinet interior
    if OBJ[a][0].Shape.cut(box(x0 + 2, x0 + cw - 2, y0 + 2, y0 + ch - 2, z0 + 2, z0 + cd - 2)).Volume > 1: bad.append('%s sticks out of the cabinet' % a)
dz = z0 + cd; ring_bottom = -90
txt = ['cabinet top z=%d, coolant pan bottom z=%d (box is outside the guard, x>%d)' % (dz, ring_bottom, x0), 'interferences: %d' % len(bad)] + bad
open(os.path.join(HERE, 'step_check.txt'), 'w').write('\n'.join(txt) + '\n'); print('\n'.join(txt))
Import.export([o for o, g in OBJ.values()], os.path.join(HERE, 'base_power.step'))
