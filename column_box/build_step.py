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
NUTS = [(x, 272) for x in (-350, -250, -150, -50, 50, 150, 250, 350)] + [(x, 490) for x in (-350, -250, -150, -50, 50, 100, 250, 350)] + [(sx, y) for sx in (-376, 376) for y in (365, 435)]
# ONE bent L plate (owner: no covers): flange z 487..491 over y 255..495, vertical plate y 255..259 hanging down at the front (z 241..491), t4, R4 inside bend
fl = box(-380, 380, 255, 495, 487, 491).cut(cyl('z', 22.5, 486, 492, 50, 390))
for (nx, ny) in NUTS: fl = fl.cut(cyl('z', 4, 486, 492, nx, ny))
add('L_plate_flange', fl, 'L plate (SPHC t4, bent): horizontal flange under the mechanical top plate; 20 M5 holes with pull nuts, X bellows hole D45')
add('L_plate_vertical', box(-380, 380, 255, 259, 241, 487), 'L plate (SPHC t4, bent): vertical plate at the front, hangs down behind the X base plate; the drives, VFD and DIN rail screw to its REAR face')
for sx, nm in ((-370, 'L'), (370, 'R')):
    add('L_plate_gusset_' + nm, box(sx - 5, sx + 5, 259, 299, 447, 487).cut(box(sx - 6, sx + 6, 279, 300, 446, 467)), 'L plate (gusset t10 at each end, stiffens the bend)')
for k, (nx, ny) in enumerate(NUTS, 1): add('PullNut_M5_%02d' % k, cyl('z', 3.75, 478, 487, nx, ny).cut(cyl('z', 2.1, 478, 487, nx, ny)), 'parts (M5 pull nut, 9 mm below the flange)')
# ------------------------------------------------ DIN rails (35 x 7.5)
for nm, (x0, x1, y0, y1, z0, z1) in {'Rail_roof_A': (-365, -125, 292.5, 327.5, 479.5, 487), 'Rail_wall': (-210, 112, 259, 266.5, 330, 365)}.items():
    add(nm, box(x0, x1, y0, y1, z0, z1), 'DIN rails')
# ------------------------------------------------ parts
def bbox(p): return (p[3], p[3] + p[6], p[4], p[4] + p[7], p[5], p[5] + p[8])
for p in L.PARTS:
    if p[1].startswith('SV') or p[1] == 'BD': continue
    b = bbox(p); add(p[1], box(*b), 'reserved space (envelope incl. heatsink)' if p[1] in ('FL2', 'PC') else 'parts (box models, catalog size)')
sv = Part.read(SERVO_STEP)                       # local: x +-20, y +-84, z 0..175.9 (back face z=0, front +z)
for p in L.PARTS:
    if p[1].startswith('SV'):
        b = bbox(p); s = sv.copy(); s.Placement = Placement(V((b[0] + b[1]) / 2, L.WALL_Y, (b[4] + b[5]) / 2), Rotation(V(0, 0, 1), 180).multiply(Rotation(V(1, 0, 0), 90)))
        add(p[1], s, 'parts (vendor STEP)')
        for dz in (-78, 78): add(p[1] + '_bolt_%d' % (1 if dz < 0 else 2), cyl('y', 4, L.WALL_Y + 6, L.WALL_Y + 10, (b[0] + b[1]) / 2 + 14, (b[4] + b[5]) / 2 + dz), 'fasteners')
bd = next(p for p in L.PARTS if p[1] == 'BD'); b = bbox(bd)
bs = Part.read(BOARD_STEP)                        # PCB x 81..177, y -144..-48, z 0..1.6, components +z
r = bs.copy(); r.Placement = Placement(V(b[0] - 81, b[2] + 48 + 0 + (-0), 478), Rotation(V(1, 0, 0), 180))
# y' = -y + ty with y=-48 -> b[2]: ty = b[2] - 48
r.Placement = Placement(V(b[0] - 81, b[2] - 48, 477), Rotation(V(1, 0, 0), 180))
add('BD', r, 'parts (vendor STEP)')
for k, (hx, hy) in enumerate(((4, 4), (92, 4), (4, 92), (92, 92)), 1): add('BD_standoff_%d' % k, cyl('z', 2.75, 477, 487, b[0] + hx, b[2] + hy), 'fasteners')
# LattePanda IOTA mount: 4 M3 rivet nuts in the roof plate, 4 M3 standoffs 10 mm, board hangs components-down.
# Board hole pattern read from the vendor STEP: 63.0 x 81.0 mm, M3 (D3.3); board 70.8 x 90.0 x 19.4, PCB z -1..0, parts z -3.8..15.6.
IOTA_HOLES = [(-30.12, -160.11), (32.87, -160.11), (-30.12, -241.12), (32.87, -241.12)]
TX, TY, TZ = -50.6, 240.4, 476.0                 # board local (x, y, z) -> machine (x+TX, -y+TY, -z+TZ)
def ib(lx0, lx1, ly0, ly1, lz0, lz1): return box(lx0 + TX, lx1 + TX, -ly1 + TY, -ly0 + TY, -lz1 + TZ, -lz0 + TZ)
pcb = ib(-34.4, 36.4, -244.6, -154.6, -1.0, 0.0)
for (hx, hy) in IOTA_HOLES: pcb = pcb.cut(cyl('z', 1.65, 470, 480, hx + TX, -hy + TY))
add('IOTA_pcb', pcb, 'parts (LattePanda IOTA, simplified: vendor board outline and hole pattern)')
add('IOTA_components', ib(-30, 33, -240, -158, 0.0, 15.6), 'parts (LattePanda IOTA, component envelope 63 x 82 x 15.6, heatsink not modelled)')
for k, (hx, hy) in enumerate(IOTA_HOLES, 1):
    x, y = hx + TX, -hy + TY
    add('IOTA_standoff_%d' % k, cyl('z', 2.75, 477, 487, x, y).cut(cyl('z', 1.25, 477, 487, x, y)), 'parts (M3 hex standoff F-F 10)')
    add('IOTA_screw_%d' % k, cyl('z', 1.5, 476, 480, x, y).fuse(cyl('z', 2.75, 473.5, 476, x, y)), 'parts (M3x6 pan head screw from the component side)')
    rp = OBJ['L_plate_flange'][0].Shape.cut(cyl('z', 2.5, 486, 492, x, y)); OBJ['L_plate_flange'][0].Shape = rp
    add('IOTA_rivetnut_%d' % k, cyl('z', 2.25, 482, 487, x, y).cut(cyl('z', 1.25, 482, 487, x, y)), 'parts (M3 rivet nut in the roof plate t4)')
# IOTA active cooler FIT1027 (vendor STEP 87 x 69 x 11): rotated 90 deg about z so that 69 runs along the board width, centred on the board,
# base on the CPU (board z 4.6 .. 15.6). The exact position over the CPU is not in the vendor data; check against the real board.
cool = Part.read(os.path.join(ROOT, 'vendor', 'lattepanda', 'fit1027.stp'))
cool.Placement = Placement(V(TX, TY, TZ), Rotation(V(1, 0, 0), 180)).multiply(Placement(V(50.7, -269.1, 16.3), Rotation(V(0, 0, 1), 90)))
add('IOTA_cooler', cool, 'parts (LattePanda FIT1027 active cooler, vendor STEP; position over the CPU assumed)')
# fan (intake, at the bottom cover) and the filter plates
doc.recompute()
# ------------------------------------------------ checks
names = list(OBJ); bad = []
def vol(a, b):
    A, B = OBJ[a][0].Shape, OBJ[b][0].Shape
    if not A.BoundBox.intersect(B.BoundBox): return 0
    return A.common(B).Volume
encl = [n for n in names if n.startswith('L_plate')]
partn = [n for n in names if (OBJ[n][1].startswith('parts') or OBJ[n][1] == 'DIN rails')]
for a in partn:
    for e in encl:
        v = vol(a, e)
        if v > 1: bad.append('%s x %s: %.0f mm3' % (a, e, v))
for i, a in enumerate(partn):
    for c in partn[i + 1:]:
        if a.startswith('IOTA_') and c.startswith('IOTA_'): continue          # threaded engagement inside the mount itself
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
