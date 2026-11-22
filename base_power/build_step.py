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
LZ = FLOOR + 60
for i, (x, y) in enumerate([(-BX, -580), (BX, -580), (-BX, 40), (BX, 40), (-BX, 560), (BX, 560)], 1):
    add('Base_leg_%d' % i, box(x - 20, x + 20, y - 20, y + 20, FLOOR + 60, -130), 'frame')
for T, x0, x1 in (('L', -BX - 20, -BX + 20), ('R', BX - 20, BX + 20)):
    add('Base_top_side_' + T, box(x0, x1, -560, 540, -130, -90), 'frame')
    add('Base_low_side_' + T, box(x0, x1, -560, 540, LZ, LZ + 40), 'frame (low ring lowered to the leg bottoms)')
add('Base_top_front', box(-BX - 20, BX + 20, -600, -560, -130, -90), 'frame'); add('Base_top_rear', box(-BX - 20, BX + 20, 540, 580, -130, -90), 'frame')
for k, y in enumerate((-120, 168), 1): add('Base_cross_%d' % k, box(-BX + 20, BX - 20, y - 20, y + 20, -130, -90), 'frame')
for k, y in enumerate((-500, -330), 1): add('Cabinet_rail_%d' % k, box(-BX + 20, BX - 20, y - 20, y + 20, LZ, LZ + 40), 'NEW cabinet cross rail 40x40 (replaces the low front beam)')
x0, y0, z0 = L.CAB_X0, L.CAB_Y0, L.CAB_Z0
shell = box(x0, x0 + L.CAB_W, y0, y0 + L.CAB_D, z0, z0 + L.CAB_H).cut(box(x0 + 2, x0 + L.CAB_W - 2, y0 + 2, y0 + L.CAB_D - 2, z0 + 2, z0 + L.CAB_H - 2))
add('Cabinet_box', shell, 'NEW steel box 940x540x250 IP54, two front doors')
px, pz = x0 + (L.CAB_W - L.PLATE_W) / 2, z0 + (L.CAB_H - L.PLATE_H) / 2
yb = y0 + L.CAB_D - 2 - 3                                   # plate on the rear wall, 3 mm standoff
add('Cabinet_plate', box(px, px + L.PLATE_W, yb, yb + 2.5, pz, pz + L.PLATE_H), 'NEW mounting plate 880x480')
parts, rep, ok = L.place()
for p in parts:
    X = px + p['x']; Z = pz + L.PLATE_H - p['y'] - p['h']
    add('%s_%s_%d' % (p['key'], p['row'], p['idx']), box(X, X + p['w'], yb - p['d'], yb, Z, Z + p['h']), 'part')
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
    if OBJ[a][0].Shape.cut(box(x0 + 2, x0 + L.CAB_W - 2, y0 + 2, y0 + L.CAB_D - 2, z0 + 2, z0 + L.CAB_H - 2)).Volume > 1: bad.append('%s sticks out of the cabinet' % a)
dz = z0 + L.CAB_H; ring_bottom = -130
txt = ['cabinet top z=%d, top ring bottom z=%d, gap %d mm' % (dz, ring_bottom, ring_bottom - dz), 'interferences: %d' % len(bad)] + bad
open(os.path.join(HERE, 'step_check.txt'), 'w').write('\n'.join(txt) + '\n'); print('\n'.join(txt))
Import.export([o for o, g in OBJ.values()], os.path.join(HERE, 'base_power.step'))
