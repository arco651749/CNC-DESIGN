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
# ---- existing v14 frame (reference only, coordinates from the mechanical session; NOT exported to the STEP)
add('ref_leg_FL', box(-492.5, -452.5, -600, -560, -730, -130), 'ref (existing frame)'); add('ref_leg_FR', box(452.5, 492.5, -600, -560, -730, -130), 'ref (existing frame)')
add('ref_top_front', box(-452.5, 452.5, -560, -520, -130, -90), 'ref (existing frame)'); add('ref_low_front', box(-452.5, 452.5, -600, -560, -660, -620), 'ref (existing frame)')
add('ref_low_side_L', box(-492.5, -452.5, -560, 20, -700, -660), 'ref (existing frame)'); add('ref_low_side_R', box(452.5, 492.5, -560, 20, -700, -660), 'ref (existing frame)')
add('ref_pan_bottom', box(-500, 500, -595, 575, -90, -88), 'ref (existing frame)')
# ---- NEW: two uprights (sit on the front low beam, top 1 mm under the pan), angle brackets, two rails
for sx, nm in ((-230, 'L'), (230, 'R')):
    add('Upright_' + nm, box(sx - 20, sx + 20, -600, -560, -620, -91), 'NEW frame (40x40 upright on the front low beam)')
    q = 1 if sx > 0 else -1                                  # side of the upright that faces the cabinet is the inner one
    def X(x0, x1): return (min(q * x0, q * x1), max(q * x0, q * x1))
    xa, xb = X(207, 210); xc, xd = X(170, 210)
    add('Bracket_top_' + nm, box(xa, xb, -600, -560, -135, -95).fuse(box(xc, xd, -563, -560, -135, -95)), 'NEW frame (angle 3 t: upright inner side to the front face of the front top beam, 2 x M8)')
    add('Bracket_bot_' + nm, box(xa, xb, -600, -560, -620, -585).fuse(box(xc, xd, -600, -560, -620, -617)), 'NEW frame (angle 3 t: upright inner side to the top face of the front low beam, 2 x M8)')
for k, z in enumerate((-490, -310), 1): add('Rail_%d' % k, box(-210, 210, -560, -520, z - 20, z + 20), 'NEW frame (40x40 rail behind the uprights, centres z -490 / -310)')
# ---- NEW operator box (S1 e-stop, S2 start) hung on the right upright
add('Bracket_opbox_side', box(250, 253, -600, -560, -335, -225).fuse(box(250, 422, -603, -600, -335, -225)), 'NEW frame (angle 3 t on the right upright, carries the operator box, 2 x M6)')
add('OpBox', box(262, 422, -663, -603, -330, -230).cut(cyl('z', 8, -331, -325, 300, -633)), 'parts (operator box 160x100x60, IP54, front face -y)')
add('S1_estop', cyl('y', 20, -690, -663, 300, -280).fuse(cyl('y', 11, -663, -640, 300, -280)), 'parts (e-stop S1 2NC, 22 mm hole, mushroom D40)')
add('S2_start', cyl('y', 14, -675, -663, 380, -280).fuse(cyl('y', 11, -663, -645, 380, -280)), 'parts (start button S2, 22 mm hole)')
# ---- cabinet
x0, y0, z0 = L.CAB_X0, L.CAB_Y0, L.CAB_Z0; yb = y0 + L.CAB_D                  # back face y = -560
shell = box(x0, x0 + L.CAB_W, y0 + 3, yb, z0, z0 + L.CAB_H).cut(box(x0 + 2, x0 + L.CAB_W - 2, y0 + 3, yb - 2, z0 + 2, z0 + L.CAB_H - 2)).cut(cyl('z', 23.65, z0 - 1, z0 + 3, -150, -640)).cut(cyl('z', 11.35, z0 - 1, z0 + 3, -90, -640)).cut(cyl('x', 8, x0 + L.CAB_W - 3, x0 + L.CAB_W + 1, -625, -400))
add('Cabinet_box', shell, 'NEW cabinet (steel wall box 360x280x120, IP54; feeder holes in the bottom: power D47.3 at (x -150, y -640) for KSS PAQ-3636 (PG36), control D22.7 at (x -90, y -640) for PAQ-1716 (PG16); D16 hole in the right wall at y -625, z -400 for the operator-box cable)')
add('Cabinet_door', box(x0, x0 + L.CAB_W, y0, y0 + 3, z0, z0 + L.CAB_H), 'NEW cabinet (door, hinged on the left, key lock)')
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
others = [n for n in names if n not in pn and not OBJ[n][1].startswith('ref')]
for a in pn:
    for b in others:
        if b == 'OpBox' and a in ('S1_estop', 'S2_start'): continue          # the button bodies go through the box front
        v = vol(a, b)
        if v > 1: bad.append('%s x %s: %.0f mm3' % (a, b, v))
for i, a in enumerate(pn):
    for b in pn[i + 1:]:
        if {a, b} & {'S1_estop', 'S2_start'} and {a, b} & {'OpBox'}: continue          # the button bodies go through the box front
        v = vol(a, b)
        if v > 1 and not (a.startswith('DIN') or b.startswith('DIN')): bad.append('%s x %s: %.0f mm3' % (a, b, v))
frame_new = [n for n in names if OBJ[n][1].startswith('NEW frame')]
for a in frame_new:
    for b in names:
        if OBJ[b][1].startswith('ref') and vol(a, b) > 1: bad.append('%s x %s: %.0f mm3' % (a, b, vol(a, b)))
txt = ['base cabinet: %d objects, plate height used %d / %d' % (len(names), hh, L.PLATE_H), 'interferences: %d' % len(bad)] + bad
open(os.path.join(HERE, 'step_check.txt'), 'w').write('\n'.join(txt) + '\n'); print('\n'.join(txt))
Import.export([o for o, g in OBJ.values() if not g.startswith('ref')], os.path.join(HERE, 'base_cabinet.step'))
M = []
for n, (o, g) in OBJ.items():
    pts, tris = o.Shape.tessellate(0.5); M.append({'n': n, 'g': g, 'p': [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in pts], 't': tris})
json.dump(M, open(os.path.join(HERE, 'mesh.json'), 'w'))
