# -*- coding: utf-8 -*-
"""Base protection cabinet 3D (machine coordinates).  CNC_ROOT=<repo> /opt/freecad/bin/freecadcmd base_cabinet/build_step.py
Out: base_cabinet/base_cabinet.step, mesh.json, step_check.txt"""
import os, sys, json
import FreeCAD as App, Part, Import
from FreeCAD import Vector as V
ROOT = os.environ.get('CNC_ROOT', os.getcwd()); HERE = os.path.join(ROOT, 'base_cabinet'); sys.path.insert(0, HERE)
import layout as L
doc = App.newDocument('base_cabinet'); OBJ = {}
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cyl(ax, r, a0, a1, p, q):
    d = {'x': V(1, 0, 0), 'y': V(0, 1, 0), 'z': V(0, 0, 1)}[ax]; o = {'x': V(a0, p, q), 'y': V(p, a0, q), 'z': V(p, q, a0)}[ax]
    return Part.makeCylinder(r, a1 - a0, o, d)
def add(n, s, g): o = doc.addObject('Part::Feature', n); o.Shape = s; OBJ[n] = (o, g)
BX, FLOOR = 517.5, -790
# ---- base frame stub (front part only, as in v13/v14: legs 40x40, front beams)
add('Base_leg_FL', box(-BX - 20, -BX + 20, -600, -560, FLOOR + 60, -130), 'frame (existing)'); add('Base_leg_FR', box(BX - 20, BX + 20, -600, -560, FLOOR + 60, -130), 'frame (existing)')
add('Base_top_front', box(-BX - 20, BX + 20, -600, -560, -130, -90), 'frame (existing)'); add('Base_low_front', box(-BX + 20, BX - 20, -600, -560, -700, -660), 'frame (existing)')
# ---- NEW: two uprights and two rails
for sx, nm in ((-230, 'L'), (230, 'R')): add('Upright_' + nm, box(sx - 20, sx + 20, -600, -560, -660, -130), 'NEW frame (40x40 upright between the low and top front beams)')
for k, z in enumerate((-470, -290), 1): add('Rail_%d' % k, box(-210, 210, -560, -520, z - 20, z + 20), 'NEW frame (40x40 rail behind the uprights)')
# ---- cabinet
x0, y0, z0 = L.CAB_X0, L.CAB_Y0, L.CAB_Z0; yb = y0 + L.CAB_D                  # back face y = -560
shell = box(x0, x0 + L.CAB_W, y0 + 3, yb, z0, z0 + L.CAB_H).cut(box(x0 + 2, x0 + L.CAB_W - 2, y0 + 3, yb - 2, z0 + 2, z0 + L.CAB_H - 2))
add('Cabinet_box', shell, 'NEW cabinet (steel wall box 400x300x130, IP54)')
add('Cabinet_door', box(x0, x0 + L.CAB_W, y0, y0 + 3, z0, z0 + L.CAB_H), 'NEW cabinet (door, hinged on the left, key lock)')
bx = x0 + 100
add('S1_estop', cyl('y', 20, y0 - 38, y0, x0 + 90, z0 + 230).fuse(cyl('y', 11, y0, y0 + 40, x0 + 90, z0 + 230)), 'parts (e-stop S1, 22 mm hole in the door, mushroom D40)')
add('S2_start', cyl('y', 14, y0 - 12, y0, x0 + 150, z0 + 230).fuse(cyl('y', 11, y0, y0 + 30, x0 + 150, z0 + 230)), 'parts (start button S2, 22 mm hole)')
add('Cabinet_door_holes_note', box(0, 0.01, 0, 0.01, 0, 0.01), 'note')
OBJ.pop('Cabinet_door_holes_note'); 
px = yb - 2 - 0                                                              # plate face y (inner back wall)
pu0 = x0 + (L.CAB_W - L.PLATE_W) / 2; pv0 = z0 + L.CAB_H - (L.CAB_H - L.PLATE_H) / 2          # plate top-left corner (x, z)
add('Cabinet_plate', box(pu0, pu0 + L.PLATE_W, px - 2.5, px, pv0 - L.PLATE_H, pv0), 'NEW cabinet (mounting plate 360x260x2.5)')
parts, hh = L.place()
for p in parts:
    X = pu0 + p['x']; Z = pv0 - p['y'] - p['h']; yf = px - 2.5 - L.RAIL
    add(p['des'], box(X, X + p['w'], yf - p['d'], yf, Z, Z + p['h']), 'parts (box models, catalog size)' if p['des'] != 'FL2' else 'reserved space')
for k, p in enumerate([q for q in parts if q['des'] in ('RCD', 'QF2')], 1): pass
for r, (title, keys) in enumerate(L.ROWS):
    rp = [q for q in parts if q['key'] in keys]; ym = rp[0]['y'] + max(q['h'] for q in rp) / 2
    add('DIN_%d' % (r + 1), box(pu0 + 5, pu0 + L.PLATE_W - 5, px - 2.5 - L.RAIL, px - 2.5, pv0 - ym - 17.5, pv0 - ym + 17.5), 'DIN rails')
doc.recompute()
names = list(OBJ); bad = []
def vol(a, b):
    A, B = OBJ[a][0].Shape, OBJ[b][0].Shape
    return A.common(B).Volume if A.BoundBox.intersect(B.BoundBox) else 0
pn = [n for n in names if OBJ[n][1].startswith('parts') or OBJ[n][1] == 'DIN rails']
others = [n for n in names if n not in pn]
for a in pn:
    for b in others:
        if a.startswith('S1') or a.startswith('S2'):
            if b in ('Cabinet_door',): continue
        v = vol(a, b)
        if v > 1: bad.append('%s x %s: %.0f mm3' % (a, b, v))
for i, a in enumerate(pn):
    for b in pn[i + 1:]:
        v = vol(a, b)
        if v > 1 and not (a.startswith('DIN') or b.startswith('DIN')): bad.append('%s x %s: %.0f mm3' % (a, b, v))
txt = ['base cabinet: %d objects, plate height used %d / %d' % (len(names), hh, L.PLATE_H), 'interferences: %d' % len(bad)] + bad
open(os.path.join(HERE, 'step_check.txt'), 'w').write('\n'.join(txt) + '\n'); print('\n'.join(txt))
Import.export([o for o, g in OBJ.values()], os.path.join(HERE, 'base_cabinet.step'))
M = []
for n, (o, g) in OBJ.items():
    pts, tris = o.Shape.tessellate(0.5); M.append({'n': n, 'g': g, 'p': [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in pts], 't': tris})
json.dump(M, open(os.path.join(HERE, 'mesh.json'), 'w'))
