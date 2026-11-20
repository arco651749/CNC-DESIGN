# -*- coding: utf-8 -*-
"""v12 from v10 (frozen), owner's architecture: the Y axis is the datum, everything else is set against it and then frozen.

  1 Y datum      Y rails and Y blocks located by reference pins on ground faces (no adjustment)
  2 X perp Y     gantry (columns + X plate) is one body: LEFT foot turns on a vertical D10 pivot pin, the RIGHT foot is pushed/pulled
                 in Y (lever 640); a second D10 dowel is reamed at the right foot afterwards
  3 X level      X plate turns on a horizontal D10 pin in the LEFT column, a vertical M8x0.75 jack lifts the RIGHT end (lever 640).
                 The X plate stands 1 mm off the column faces (1 mm step milled on its front face outside the rails) and the joint
                 is frozen by injected epoxy pads, so two columns that lean differently cannot twist the ground X plate
  4 Z (3 axes)   saddle (on the X blocks) + Z plate, 1 mm apart. At the CENTRE of the plates a spherical plain bearing
                 (MISUMI RBPB8) in the saddle carries a D8 pin pressed into the Z plate: it fixes the in-plane position (X, Z)
                 and is the pivot for every rotation. The pin slides in the inner ring (g6), so the bearing never takes the
                 Y (thrust) load. Y is held by three differential push screws (0.25 mm/rev) through the Z plate, two at the
                 top and one at the bottom: together = gap, top vs bottom = nod about X, left vs right = turn about Z (no
                 effect on squareness). Opposed differential side screws = roll about Y. Frozen by epoxy pads round the 6 bolts
  5 spindle      same pivot as the Z plate: RBPB8 in the Z slide at the centre behind the clamp body, shouldered stud screwed into
                 the clamp; three differential face screws (gap, nod) and opposed side screws (roll); fixed by shim packs at the 4
                 bolts so it stays re-adjustable. Spindles are screened at goods-in. Spindle axis at y-20: flat steel back plate + plain clamp block
Removable alignment kit (Kit = 'removable'): yaw push-pull block, X-level jack + bracket, Z face screws, Z roll blocks,
spindle roll blocks. After the epoxy has cured they come off and are reused on the next machine.
Run:  freecadcmd freecad/v12/01_v12_adjusters.py      Out: output/v12/CNC_v12.FCStd, output/v12/logs/v12_build.txt"""
import os, re
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v12'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v10', 'CNC_v10.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
GROUPS = {g.Label: g for g in doc.Objects if g.TypeId == 'App::DocumentObjectGroup'}
NEW = []


def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def zcyl(r, z0, z1, x=0, y=0): return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))
def cyl(ax, r, a0, a1, p, q):
    if ax == 'x': return Part.makeCylinder(r, a1 - a0, V(a0, p, q), V(1, 0, 0))
    if ax == 'y': return Part.makeCylinder(r, a1 - a0, V(p, a0, q), V(0, 1, 0))
    return Part.makeCylinder(r, a1 - a0, V(p, q, a0), V(0, 0, 1))
def mir(s, sgn): return s if sgn > 0 else s.mirror(V(0, 0, 0), V(1, 0, 0))
def fuse(*ss):
    r = ss[0]
    for s in ss[1:]: r = r.fuse(s)
    return r.removeSplitter()
def prop(o, name, val):
    if name not in o.PropertiesList: o.addProperty('App::PropertyString', name, 'CNC')
    setattr(o, name, val)
def add(label, shape, group, spec, motion, adj):
    o = doc.addObject('Part::Feature', label); o.Label = label; o.Shape = shape
    prop(o, 'Spec', spec); prop(o, 'Motion', motion); prop(o, 'Adj', adj)
    GROUPS[group].addObject(o); NEW.append(label); return o
def cut(label, *tools):
    o = O(label); s = o.Shape
    for t in tools: s = s.cut(t)
    o.Shape = s
def tag(label, adj): prop(O(label), 'Adj', adj)

for lab in ('08 Adjusters', '10 Epoxy pads'):
    g = doc.addObject('App::DocumentObjectGroup', 'G'); g.Label = lab; GROUPS[lab] = g
G, GE = '08 Adjusters', '10 Epoxy pads'

# ================================================================ 2. gantry yaw: left pivot pin, right push-pull
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    foot = O('Column_foot_' + T)
    f = box(280, 360, -28, 182, 0, 18)
    hole = 5.0 if T == 'L' else 5.75                       # right foot: clearance for the yaw movement
    for x in (296, 344): f = f.cut(cyl('z', hole, 0, 18, x, 172))
    f = f.cut(cyl('z', hole, 0, 18, 320, -13))
    foot.Shape = m(f)
    prop(foot, 'Spec', 'steel foot t18, 80x210, front flange 30 (hold-down bolt, push-pull contact); full-face contact on the datum plate')
    tag('Column_foot_' + T, 'yaw')
    for k, (x, y) in enumerate(((296, 172), (344, 172), (320, -13)), 1):
        add('Foot_bolt_%s%d' % (T, k), m(fuse(cyl('z', 4, -14, 18, x, y), cyl('z', 6.5, 18, 26, x, y))), G,
            'M8 SHCS hold-down' + ('' if T == 'L' else ', hole D11.5: the right foot slides +-0.75 for yaw'), '', 'yaw')
        cut('Datum_base_plate', m(cyl('z', 4, -14, 0, x, y)))
    for k, (x, y) in enumerate(((300, 22), (340, 22), (300, 142), (340, 142)), 1):
        s = m(fuse(cyl('z', 6.5, 1, 9, x, y), cyl('z', 4, 9, 38, x, y)))
        add('Foot_col_bolt_%s%d' % (T, k), s, G, 'M8 SHCS from below into the column end tap', '', '')
        cut(foot.Label, m(cyl('z', 7, 0, 9.5, x, y)), m(cyl('z', 4.5, 9.5, 18, x, y))); cut('Gantry_column_' + T, m(cyl('z', 4, 18, 38, x, y)))
    s = m(cyl('z', 5, -12, 18, 320, 172))
    if T == 'L':
        add('Yaw_pivot_pin', s, G, 'dowel D10x30: the gantry turns about this pin (left foot, rear strip, open from above)', '', 'yaw')
    else:
        add('Yaw_lock_dowel', s, G, 'dowel D10x30, reamed through the right foot into the datum plate AFTER X perp Y is set', '', 'pins')
    cut(foot.Label, s); cut('Datum_base_plate', s)
blk = box(300, 340, -62, -36, 0, 25).cut(cyl('y', 3, -62, -36, 312, 12)).cut(cyl('y', 3.5, -62, -36, 328, 12))
for x in (304, 336): blk = blk.cut(cyl('z', 2.75, 0, 25, x, -49))
add('Yaw_push_block', blk, G, 'steel block 40x26x25 on the datum plate in front of the RIGHT foot flange', '', 'yaw')
add('Yaw_push_screw', fuse(cyl('y', 3, -72, -28, 312, 12), cyl('y', 5.5, -67, -62, 312, 12)), G, 'M6x0.75 push screw + jam nut: 10 deg = 33 urad (lever 640)', '', 'yaw')
add('Yaw_pull_screw', fuse(cyl('y', 3, -62, -16, 328, 12), cyl('y', 5, -68, -62, 328, 12)), G, 'M6x0.75 pull screw into a tap in the flange', '', 'yaw')
cut('Column_foot_R', cyl('y', 3, -28, -16, 328, 12))
for k, x in enumerate((304, 336), 1):
    add('Yaw_block_bolt_%d' % k, fuse(cyl('z', 2.5, -10, 25, x, -49), cyl('z', 4.25, 25, 30, x, -49)), G, 'M5 SHCS', '', 'yaw')
    cut('Datum_base_plate', cyl('z', 2.5, -10, 0, x, -49))

# ================================================================ 3. X level: pin in the left column, jack under the right end, epoxy joint
xp = O('X_base_plate')
s = xp.Shape
for sg in (1, -1): s = s.cut(mir(box(272, 360, 162, 163, 230, 490), sg))   # 1 mm step = epoxy gap at the column faces
xp.Shape = s
prop(xp, 'Spec', xp.Spec + '. Front face stepped 1 mm down outside x+-272: stands 1 mm off the columns, joined by 8 epoxy pads')
tag('X_base_plate', 'xlevel')
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    for k, (x, z) in enumerate(((300, 270), (340, 270), (300, 450), (340, 450)), 1):
        add('X_plate_bolt_%s%d' % (T, k), m(fuse(cyl('y', 4, 150, 182, x, z), cyl('y', 6.5, 182, 190, x, z))), G,
            'M8 SHCS + T-nut, X plate to column; plate hole D10 (rotation range)', '', 'xlevel')
        cut('X_base_plate', m(cyl('y', 5, 163, 182, x, z)))
        add('X_epoxy_pad_%s%d' % (T, k), m(cyl('y', 15, 162, 163, x, z).cut(cyl('y', 5, 162, 163, x, z))), GE,
            'injected metal-filled epoxy pad D30x1 round the bolt (fill hole and vent hole through the X plate)', '', 'epoxy')
        for dz in (10, -10): cut('X_base_plate', m(cyl('y', 2, 163, 182, x, z + dz)))
s = cyl('y', 5, 150, 182, -320, 360)
add('X_roll_pin', s, G, 'dowel D10: the X plate turns on it (left column, centre of the joint; steel insert in the column slot)', '', 'xlevel')
cut('X_base_plate', s); cut('Gantry_column_L', s)
br = box(290, 350, 162, 186, 192, 224).cut(cyl('z', 4, 192, 224, 320, 172))
for x in (300, 340): br = br.cut(cyl('y', 3.3, 162, 186, x, 208))
add('X_roll_bracket', br, G, 'steel block 60x24x32 on the right column rear face (T-slots), under the X plate', '', 'xlevel')
add('X_roll_jack', fuse(cyl('z', 4, 184, 230, 320, 172), cyl('z', 6.5, 186, 192, 320, 172)), G,
    'M8x0.75 jack + jam nut under the right end of the X plate: 10 deg = 33 urad (lever 640)', '', 'xlevel')
for k, x in enumerate((300, 340), 1):
    add('X_roll_bracket_bolt_%d' % k, fuse(cyl('y', 3, 157, 186, x, 208), cyl('y', 5, 186, 192, x, 208)), G, 'M6 SHCS + T-nut', '', 'xlevel')

# ================================================================ 4. Z: saddle + Z plate on an RBPB8 spherical bearing, epoxy joint
zp = O('X_carriage_plate')
zp.Shape = box(-120, 120, 104, 121, 222, 710)
prop(zp, 'Spec', 'Z plate, steel t17 240x488: Z rails, Z screw, Z motor plate. 1 mm off the saddle, D8 pin (H7 hole) in the RBPB8 spherical bearing of the saddle; frozen by 6 epoxy pads')
tag('X_carriage_plate', 'ztram')
sad = fuse(box(-120, 120, 122, 134, 222, 706), box(120, 142, 122, 134, 652, 706), box(-142, -120, 122, 134, 652, 706))
add('X_saddle_plate', sad, '04 X-axis', 'saddle, steel t12 with two ears above the columns: bolted to the 4 X blocks and the X nut bracket', 'x', 'ztram')
BC = (0, 466)                                                      # bearing centre (x, z), centre of the Z plate
brg = Part.read(os.path.join(ROOT, 'vendor', 'misumi', 'RBPB8', 'RBPB8.stp'))   # vendor model: axis Z, sphere centre (0, 0, -6)
brg.translate(V(0, 0, 6)); brg.rotate(V(0, 0, 0), V(1, 0, 0), -90); brg.translate(V(BC[0], 128, BC[1]))   # axis -> Y, centre in the saddle
add('Z_pivot_bearing', brg, G, 'spherical plain bearing MISUMI RBPB8, vendor STEP (D22 h6, d8 H7, B 9, B1 12, static radial 16.7 kN, '
    'tilt 8 deg+), bonded into the saddle at its centre (H7 bore / h6 ring + retaining compound Loctite 641); takes only in-plane (radial) load', 'x', 'ztram')
cut('X_saddle_plate', cyl('y', 11, 122, 134, *BC))
pin = cyl('y', 4, 108, 134, *BC)
add('Z_pivot_pin', pin, G, 'D8 pin pressed into the Z plate, slide fit (g6) in the bearing inner ring: fixes X and Z, leaves Y free', 'x', 'ztram')
cut('X_carriage_plate', pin)
k = 0
for x in (-108, 108):
    for z in (240, 620, 696):
        k += 1
        add('Z_clamp_bolt_%d' % k, fuse(cyl('y', 5, 98, 104, x, z), cyl('y', 3, 104, 132, x, z)), G,
            'M6 SHCS with disc springs, Z plate to saddle; plate hole D7. Snug while adjusting, torqued after the epoxy cures', 'x', 'ztram')
        cut('X_carriage_plate', cyl('y', 3.5, 104, 121, x, z)); cut('X_saddle_plate', cyl('y', 3, 122, 132, x, z))
        add('Z_epoxy_pad_%d' % k, cyl('y', 11, 121, 122, x, z).cut(cyl('y', 3.5, 121, 122, x, z)), GE,
            'injected epoxy pad D22x1 round the clamp bolt (fill hole through the Z plate)', 'x', 'epoxy')
        cut('X_carriage_plate', cyl('y', 1.5, 104, 121, x, z + 8))
s = fuse(cyl('y', 4, 92, 122, 0, 236), cyl('y', 6.5, 98, 104, 0, 236))
add('Z_face_screw_B', s, G, 'differential push screw (0.25 mm/rev) at the bottom centre, 230 below the bearing: with the two top screws it '
    'holds the Y gap; top pair vs this one = nod about X. 10 deg = 30 urad', 'x', 'ztram')
cut('X_carriage_plate', cyl('y', 4, 104, 121, 0, 236))
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    s = m(fuse(cyl('y', 4, 92, 122, 90, 700), cyl('y', 6.5, 98, 104, 90, 700)))
    add('Z_face_screw_' + T, s, G, 'differential push screw (M8x0.75 outer / M6x0.5 inner = 0.25 mm/rev) through the Z plate, tip on the saddle, '
        '234 above the bearing: top pair vs bottom screw = nod about X, left vs right = turn about Z (no effect on squareness). 10 deg = 30 urad', 'x', 'ztram')
    cut('X_carriage_plate', m(cyl('y', 4, 104, 121, 90, 700)))
    add('Z_roll_block_' + T, m(box(124, 142, 104, 122, 664, 696).cut(cyl('x', 3, 124, 142, 112.5, 680)).cut(cyl('y', 2.75, 104, 122, 133, 670)).cut(cyl('y', 2.75, 104, 122, 133, 690))),
        G, 'steel block 18x18x32 on the saddle ear, beside the Z plate edge', 'x', 'ztram')
    add('Z_roll_screw_' + T, m(fuse(cyl('x', 3, 120, 150, 112.5, 680), cyl('x', 5.5, 142, 147, 112.5, 680))), G,
        'opposed differential side screw (0.25 mm/rev), tip on the Z plate edge 214 above the bearing: roll about Y. 10 deg = 32 urad', 'x', 'ztram')
    for kk, z in enumerate((670, 690), 1):
        add('Z_roll_block_bolt_%s%d' % (T, kk), m(fuse(cyl('y', 4.25, 99, 104, 133, z), cyl('y', 2.5, 104, 132, 133, z))), G, 'M5 SHCS', 'x', 'ztram')
        cut('X_saddle_plate', m(cyl('y', 2.5, 122, 132, 133, z)))

# ================================================================ 5. spindle: same pivot as the Z plate, fixed by shims
# RBPB8 in the Z slide at the centre, behind the clamp body; a shouldered stud is screwed into the clamp rear wall and its D8 g6
# shoulder slides in the inner ring (no thrust on the bearing). Spindle axis at y-12 so the rear wall is 11.5 thick (stud thread 10).
# Three differential face screws through the ears set the 2 mm gap and nod; opposed side screws set roll. Fixed by ground shim
# packs at the 4 clamp bolts (re-adjustable); spindles are screened for housing-to-axis error at goods-in.
DY = -20
for l in ('Spindle_body', 'Spindle_fan_cover', 'Spindle_plug', 'Spindle_nose', 'ER11_nut', 'Tool_D5'):
    o = O(l); s = o.Shape.copy(); s.translate(V(0, DY, 0)); o.Shape = s; tag(l, 'spindle')
SB = (0, 366)                                              # spindle pivot (x, z)
BOLTS = [(-63, 420), (63, 420), (-63, 455), (63, 455)]            # clear of the Z-block screws in the slide
SCREWS = [('TC', 0, 490), ('BL', -63, 335), ('BR', 63, 335)]       # turn about Z is irrelevant for the spindle: one top screw
CB = [(-41, 340), (41, 340), (-41, 396), (41, 396)]       # clamp block to plate
# back plate: flat steel 156x181x12, every hole from the front face (2.5D, one set-up)
pl = box(-78, 78, 20, 32, 319, 500)
for x, z in BOLTS: pl = pl.cut(cyl('y', 3.5, 20, 32, x, z))
for _, x, z in SCREWS: pl = pl.cut(cyl('y', 4, 20, 32, x, z))
for x, z in CB: pl = pl.cut(cyl('y', 3, 20, 32, x, z))
pl = pl.cut(cyl('y', 3, 20, 32, *SB))
add('Spindle_mount_plate', pl, G, 'flat steel plate 156x181x12, ground both faces, all holes from the front: M6 tap for the pivot stud, 4 shim-bolt holes, '
    '3 differential-screw taps, 4 M6 taps for the clamp block. Stands 2 mm off the slide on 4 shim packs', 'z', 'spindle')
# clamp block: plain block with the D65 bore, front split, 2 pinch screws, 4 bolts from the front into the plate
c = box(-48, 48, -63, 20, 331, 405).cut(cyl('z', 32.5, 331, 405, 0, DY)).cut(box(-1, 1, -63, DY, 331, 405))
for z in (355, 381): c = c.cut(cyl('x', 3, -48, 30, -57, z)).cut(cyl('x', 5.5, 30, 48, -57, z))
for x, z in CB: c = c.cut(cyl('y', 3.25, -57, 20, x, z)).cut(cyl('y', 5.5, -63, -57, x, z))
cl = O('Spindle_clamp'); cl.Shape = c
prop(cl, 'Spec', '6061 clamp block 96x83x74: bore D65 at (x0, y-20), rear wall 7.5, front split with 2 M6 pinch screws; bolted to the back plate '
                 'with 4 M6x80 from the front')
tag('Spindle_clamp', 'spindle')
for k, z in enumerate((355, 381), 1):
    add('Spindle_pinch_screw_%d' % k, fuse(cyl('x', 3, -38, 34, -57, z), cyl('x', 5, 34, 40, -57, z)), G, 'M6 pinch screw, fixed torque before tramming', 'z', 'spindle')
for k, (x, z) in enumerate(CB, 1):
    add('Spindle_clamp_bolt_%d' % k, fuse(cyl('y', 5, -63, -57, x, z), cyl('y', 3, -57, 30, x, z)), G, 'M6x80 SHCS, clamp block to back plate', 'z', 'spindle')
brg = Part.read(os.path.join(ROOT, 'vendor', 'misumi', 'RBPB8', 'RBPB8.stp'))
brg.translate(V(0, 0, 6)); brg.rotate(V(0, 0, 0), V(1, 0, 0), -90); brg.translate(V(SB[0], 40, SB[1]))   # inner ring y34..46
add('Spindle_pivot_bearing', brg, G, 'spherical plain bearing MISUMI RBPB8 bonded into the Z slide (H7 / h6 + Loctite 641) at the centre behind the back plate: fixes the '
    'bracket in X and Z, pivot for nod and roll; takes no thrust', 'z', 'spindle')
cut('Z_slide_plate', cyl('y', 11, 34, 46, *SB))
add('Spindle_pivot_stud', fuse(cyl('y', 3, 20, 32, *SB), cyl('y', 4, 32, 46, *SB)), G,
    'shouldered stud: M6 thread 12 into the steel back plate, D8 g6 shoulder sliding in the bearing inner ring', 'z', 'spindle')
for k, (x, z) in enumerate(BOLTS, 1):
    sh = box(x - 11, x + 11, 32, 34, z - 8, z + 8).cut(box(x - 3.5, x + 3.5, 32, 34, z - 8, z)).cut(cyl('y', 3.5, 32, 34, x, z))
    add('Spindle_shim_%d' % k, sh, G, 'ground shim pack 22x16, nominal 2.0, U-slot: fitted to the measured gap after adjusting, then the bolt is torqued '
        'and the face screws backed off', 'z', 'spindle')
    add('Spindle_bolt_%d' % k, fuse(cyl('y', 5, 14, 20, x, z), cyl('y', 3, 20, 46, x, z)), G, 'M6 SHCS through back plate and shim; hole D7', 'z', 'spindle')
    cut('Z_slide_plate', cyl('y', 3, 34, 46, x, z))
for nm, x, z in SCREWS:
    add('Spindle_face_screw_' + nm, fuse(cyl('y', 4, 14, 34, x, z), cyl('y', 6.5, 14, 20, x, z)), G,
        'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the ear, tip on the slide face: the three set the 2 mm gap; '
        'top vs bottom pair = nod (lever about 124, 10 deg = 56 urad)', 'z', 'spindle')
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    add('Spindle_roll_block_' + T, m(box(80, 98, 14, 34, 474, 504).cut(cyl('x', 3, 80, 98, 24, 489)).cut(cyl('y', 2.2, 14, 34, 89, 500))), G,
        'steel block beside the top of the ear', 'z', 'spindle')
    add('Spindle_roll_screw_' + T, m(fuse(cyl('x', 3, 78, 104, 24, 489), cyl('x', 5, 98, 102, 24, 489))), G,
        'opposed differential side screw (0.25 mm/rev) on the ear side, 123 above the pivot: roll. 10 deg = 56 urad', 'z', 'spindle')
    add('Spindle_roll_block_bolt_' + T, m(fuse(cyl('y', 3.5, 10, 14, 89, 500), cyl('y', 2, 14, 46, 89, 500))), G, 'M4 SHCS', 'z', 'spindle')
    cut('Z_slide_plate', m(cyl('y', 2, 34, 46, 89, 500)))

# ================================================================ 1. rail references (Y = datum)
def refs(prefix, face, pin_r, ecc_r, scr_r, master, slave, at, pin_h, parent, motion):
    a0, a1, b0, b1 = face - pin_h, face, face, face + 8
    def stud(r_head, r_shank, c, t, h=None):
        return _c(r_head, a0 if h is None else face - h, a1, c, t), _c(r_shank, b0, b1, c, t)
    for i, t in enumerate(at, 1):
        hd, sh = stud(pin_r, pin_r, master[0], t)
        add('%s_ref_pin_%d' % (prefix, i), fuse(hd, sh), G, 'reference dowel, master rail leans on it', motion, 'rails'); cut(parent, sh)
        hd, sh = stud(ecc_r, pin_r, slave[0], t)
        add('%s_ecc_pin_%d' % (prefix, i), fuse(hd, sh), G, 'eccentric pin, shifts the slave rail', motion, 'rails'); cut(parent, sh)
        for side, cc in (('M', master[1]), ('S', slave[1])):
            hd, sh = stud(scr_r, scr_r / 2.0, cc, t, 2.5)
            add('%s_side_screw_%s%d' % (prefix, side, i), fuse(hd, sh), G, SIDE_SPEC[prefix], motion, 'rails'); cut(parent, sh)
SIDE_SPEC = {   # BOM: rail side-press screws, opposite each pin (cone of a countersunk screw bears on the rail side)
    'X': 'ISO 10642 hex socket countersunk M4x10, 10.9 black oxide; tapped M4 in the X plate, countersink 0.5 deep, axis 3.75 from the rail side; '
         'the cone touches the rail 0.6..2.0 above the base (flat side band of SX2RNL28: 0.6..6.0)',
    'Z': 'ISO 10642 hex socket countersunk M4x10, 10.9 black oxide; tapped M4 in the Z plate, countersink 0.5 deep, axis 3.75 from the rail side; '
         'the cone touches the rail 0.6..2.0 above the base (flat side band of SX2RNL28: 0.6..6.0)',
    'Y': 'ISO 10642 hex socket countersunk M6x12, 10.9 black oxide; tapped M6 in the table underside, countersink 0.5 deep, axis 6.0 from the rail side; '
         'the cone touches the rail 1.5..3.2 above the base (flat side band of C-HLG45: 1.5..7.1)'}
_c = lambda r, h0, h1, c, t: cyl('y', r, h0, h1, t, c)
refs('X', 162, 3, 5, 4, (237, 264), (455, 484), (-240, 0, 240), 4.5, 'X_base_plate', '')
_c = lambda r, h0, h1, c, t: cyl('y', r, h0, h1, c, t)
refs('Z', 104, 3, 5, 4, (-67, -94), (65, 94), (300, 462, 624), 4.5, 'X_carriage_plate', 'x')
_c = lambda r, h0, h1, c, t: cyl('z', r, h0, h1, c, t)
refs('Y', 70, 4, 6, 6, (-133.5, -188.5), (131.5, 188.5), (-150, 50, 250), 7.0, 'Work_table', 'y')
for i, y in enumerate((-130, -30, 30, 130), 1):
    add('Y_block_ref_pin_%d' % i, cyl('z', 4, -8, 12, -207, y), G, 'reference dowel in the datum plate, master-side Y blocks lean on it', '', 'ydatum')
    cut('Datum_base_plate', cyl('z', 4, -8, 0, -207, y))
for l in NEW:
    if l.startswith(('Y_ref_pin', 'Y_ecc_pin', 'Y_side_screw')): tag(l, 'ydatum')

# ================================================================ rail and block screws (fasteners: one colour in the pages)
# hole positions read from the MISUMI models; low-head screws (DIN 7984) where the part is too thin for a normal head
LOWHEAD = {5: (4.25, 3.5), 10: (8.0, 6.0)}                 # thread: (head radius, head height)
NORMAL = {5: (4.25, 5.0), 12: (9.0, 12.0)}
for T, xc in (('L', -160), ('R', 160)):                    # Y rails: M12 from the rail bottom (inverted rail) into the table
    for k, y in enumerate((-160, -55, 50, 155), 1):          # the rail holes at y-265 / 260 / 365 lie outside the table
        add('Y_rail_bolt_%s%d' % (T, k), fuse(cyl('z', 9, 37, 49, xc, y), cyl('z', 6, 49, 84, xc, y)), G,
            'M12x35 SHCS in the rail counterbore, tapped 14 into the table', 'y', 'fasten')
        cut('Work_table', cyl('z', 6, 70, 84, xc, y))
for T, xs in (('L', (-190, -130)), ('R', (130, 190))):      # Y blocks: low-head M10 from under the datum plate
    for n, ys in ((1, (-102, -42)), (2, (42, 102))):
        for x in xs:
            for y in ys:
                add('Y_block_bolt_%s%d_%d_%d' % (T, n, x, y), fuse(cyl('z', 8, -20, -14, x, y), cyl('z', 4.19, -14, 11, x, y)), G,
                    'M10x25 low-head (DIN 7984) from under the datum plate, 11 into the block tap', '', 'fasten')
                cut('Datum_base_plate', cyl('z', 8.5, -20, -13.5, x, y), cyl('z', 5.5, -13.5, 0, x, y))
for r, z in ((1, 250), (2, 470)):                           # X rails: M5 in the rail counterbores into the X plate
    for x in (-210, -150, -90, -30, 30, 90, 150, 210):
        add('X_rail_bolt_%d_%d' % (r, x), fuse(cyl('y', 4.25, 150, 155, x, z), cyl('y', 2.5, 155, 171, x, z)), G,
            'M5x16 SHCS in the rail counterbore, tapped 9 into the X plate', '', 'fasten')
        cut('X_base_plate', cyl('y', 2.5, 162, 171, x, z))
for blk, xs, zs in (('11', (-69.5, -37.5), (234, 266)), ('12', (37.5, 69.5), (234, 266)), ('21', (-69.5, -37.5), (454, 486)), ('22', (37.5, 69.5), (454, 486))):
    for x in xs:                                            # X blocks: low-head M5 from the saddle front (1 mm gap to the Z plate)
        for z in zs:
            add('X_block_bolt_%s_%d_%d' % (blk, x, z), fuse(cyl('y', 4.25, 122.5, 126, x, z), cyl('y', 2.07, 126, 140, x, z)), G,
                'M5x14 low-head (DIN 7984) from the saddle front, head sunk 4 into the saddle (fit before the Z plate)', 'x', 'fasten')
            cut('X_saddle_plate', cyl('y', 4.75, 122, 126, x, z), cyl('y', 2.75, 126, 134, x, z))
for T, xc in (('L', -80), ('R', 80)):                       # Z rails: M5 in the rail counterbores into the Z plate
    for z in range(282, 643, 60):
        add('Z_rail_bolt_%s_%d' % (T, z), fuse(cyl('y', 4.25, 92, 97, xc, z), cyl('y', 2.5, 97, 113, xc, z)), G,
            'M5x16 SHCS in the rail counterbore, tapped 9 into the Z plate', 'x', 'fasten')
        cut('X_carriage_plate', cyl('y', 2.5, 104, 113, xc, z))
for T, xs in (('L', (-96, -64)), ('R', (64, 96))):          # Z blocks: M5 from the slide front through slide and spacer
    for n, zs in ((1, (362.5, 394.5)), (2, (474.5, 506.5))):        # upper blocks are mounted the other way round
        for x in xs:
            for z in zs:
                add('Z_block_bolt_%s%d_%d_%d' % (T, n, x, z), fuse(cyl('y', 4.25, 37, 42, x, z), cyl('y', 2.07, 42, 82, x, z)), G,
                    'M5x40 SHCS from the slide front, counterbore 8, through slide and spacer, 6 into the block (fit before the spindle plate)', 'z', 'fasten')
                cut('Z_slide_plate', cyl('y', 4.75, 34, 42, x, z), cyl('y', 2.75, 42, 62, x, z)); cut('Z_spacer_' + T, cyl('y', 2.75, 62, 76, x, z))

# ================================================================ nut housings and motor blocks: flange screws and mounting screws
# nut flange (C-KBS1505, read from the MISUMI STEP): 6 x D5.5 on PCD 38 -> M5x16 into taps in the housing face
# motor flange (HG-KR43, read from the Mitsubishi STEP): 4 x D5.8 on PCD 70 (+-24.7) -> M5x16 into taps in the block face
CHK = []
def hole(label, *tools):                                    # cut + check the tool lies in material (no break-out, no clash)
    o = O(label)
    for t in tools: CHK.append((label, t.common(o.Shape).Volume / t.Volume))
    cut(label, *tools)
def screw(label, head, shank, spec, motion):
    add(label, fuse(head, shank), G, spec, motion, 'fasten')
PCD38 = [(19, 0), (-19, 0), (13.4, 13.4), (13.4, -13.4), (-13.4, 13.4), (-13.4, -13.4)]
# Y nut bracket (fixed on the datum plate, nut flange on its +y face y-113..-103)
for i, (a, b) in enumerate(PCD38, 1):
    x, z = a, 45 + b
    hole('Y_nut_bracket', cyl('y', 2.5, -123, -113, x, z))
    screw('Y_nut_flange_bolt_%d' % i, cyl('y', 4.25, -103, -98, x, z), cyl('y', 2.5, -119, -103, x, z), 'M5x16 SHCS, nut flange into the housing (tap M5 depth 10)', '')
for i, (x, y) in enumerate(((-18, -139), (18, -139), (-18, -119), (18, -119)), 1):
    hole('Y_nut_bracket', cyl('z', 3, 0, 12, x, y))
    hole('Datum_base_plate', cyl('z', 3.3, -13.5, 0, x, y), cyl('z', 5.5, -20, -13.5, x, y))
    screw('Y_nut_mount_bolt_%d' % i, cyl('z', 5, -20, -14, x, y), cyl('z', 3, -14, 11, x, y), 'M6x25 SHCS from under the datum plate into the housing (tap M6 depth 12)', '')
# X nut bracket (on the saddle rear face, nut flange on its +x face x11..21)
for i, (a, b) in enumerate(PCD38, 1):
    y, z = 207 + b, 360 + a
    hole('X_nut_bracket', cyl('x', 2.5, 1, 11, y, z))
    screw('X_nut_flange_bolt_%d' % i, cyl('x', 4.25, 21, 26, y, z), cyl('x', 2.5, 5, 21, y, z), 'M5x16 SHCS, nut flange into the housing (tap M5 depth 10)', 'x')
for i, (x, z) in enumerate(((-19, 342), (4, 342), (-19, 378), (4, 378)), 1):
    hole('X_nut_bracket', cyl('y', 3, 134, 148, x, z))
    hole('X_saddle_plate', cyl('y', 3.3, 126.5, 134, x, z), cyl('y', 5.5, 122, 126.5, x, z))
    screw('X_nut_mount_bolt_%d' % i, cyl('y', 5, 122.5, 126.5, x, z), cyl('y', 3, 126.5, 146.5, x, z),
          'M6x20 low-head (DIN 7984) from the saddle front, head sunk in the saddle (fit before the Z plate)', 'x')
# Z nut housing: widened to x+-44 so it bears on the slide rear face beside the nut pocket (pocket x+-28), front part sits in the pocket
cut('Z_slide_plate', box(-28, 28, 54, 62, 455, 461))         # nut pocket 6 mm higher: room for the nut flange screw heads
zh = O('Z_nut_housing')
zh.Shape = fuse(box(-26, 26, 56, 101.6, 411, 443), box(-44, 44, 62, 101.6, 411, 443)).cut(cyl('z', 14.1, 411, 443, 0, 79))
prop(zh, 'Spec', 'Z nut housing (CNC, steel): wraps the nut body, nut flange on its top face (6 x M5), wings x+-44 bolted to the slide rear face '
     'with 4 x M6 low-head from the slide front; the front part sits in the slide pocket')
for i, (a, b) in enumerate(PCD38, 1):
    x, y = a, 79 + b
    hole('Z_nut_housing', cyl('z', 2.5, 433, 443, x, y))
    screw('Z_nut_flange_bolt_%d' % i, cyl('z', 4.25, 453, 458, x, y), cyl('z', 2.5, 437, 453, x, y), 'M5x16 SHCS, nut flange into the housing (tap M5 depth 10)', 'z')
for i, (x, z) in enumerate(((-36, 418), (36, 418), (-36, 436), (36, 436)), 1):
    hole('Z_nut_housing', cyl('y', 3, 62, 76, x, z))
    hole('Z_slide_plate', cyl('y', 3.3, 38.5, 62, x, z), cyl('y', 5.5, 34, 38.5, x, z))
    screw('Z_nut_mount_bolt_%d' % i, cyl('y', 5, 34.5, 38.5, x, z), cyl('y', 3, 38.5, 73.5, x, z),
          'M6x35 low-head (DIN 7984) from the slide front, head sunk in the slide (fit before the spindle plate)', 'z')
MOT = [(24.7, 24.7), (24.7, -24.7), (-24.7, 24.7), (-24.7, -24.7)]
# Y motor block (rides with the table): motor flange on its +y face y279.5; 4 x M6 up into the table underside
for i, (a, b) in enumerate(MOT, 1):
    x, z = a, 45 + b
    hole('Y_motor_block', cyl('y', 2.5, 269.5, 279.5, x, z))
    screw('Y_motor_flange_bolt_%d' % i, cyl('y', 4.25, 286.5, 291.5, x, z), cyl('y', 2.5, 270.5, 286.5, x, z), 'M5x16 SHCS, motor flange into the block (tap M5 depth 10)', 'y')
for i, x in enumerate((-50, -34, 34, 50), 1):
    hole('Work_table', cyl('z', 3, 70, 82, x, 252.5))
    screw('Y_motor_mount_bolt_%d' % i, cyl('z', 5, 9, 15, x, 252.5), cyl('z', 3, 15, 80, x, 252.5), 'M6x65 SHCS from below into the table (tap M6 depth 12)', 'y')
# X motor block (in the pocket of the X plate rear face): mounting holes moved to x 278 / 293 so they clear the motor flange taps
xb = O('X_motor_block'); s = box(271.5, 309.5, 175, 242, 322, 398).cut(cyl('x', 25.05, 271.5, 309.5, 207, 360))
for x in (278, 293):
    for z in (330, 390): s = s.cut(cyl('y', 3.3, 175, 242, x, z))
xb.Shape = s
for i, (a, b) in enumerate(MOT, 1):
    y, z = 207 + a, 360 + b
    hole('X_motor_block', cyl('x', 2.5, 299.5, 309.5, y, z))
    screw('X_motor_flange_bolt_%d' % i, cyl('x', 4.25, 316.5, 321.5, y, z), cyl('x', 2.5, 300.5, 316.5, y, z), 'M5x16 SHCS, motor flange into the block (tap M5 depth 10)', '')
k = 0
for x in (278, 293):
    for z in (330, 390):
        k += 1; hole('X_base_plate', cyl('y', 3, 165, 175, x, z))
        screw('X_motor_mount_bolt_%d' % k, cyl('y', 5, 242, 248, x, z), cyl('y', 3, 167, 242, x, z), 'M6x75 SHCS into the X plate rear face (tap M6 depth 10)', '')
# Z motor plate (on the Z plate top): motor flange on its top face z726; 4 x M6 into the Z plate front face
for i, (a, b) in enumerate(MOT, 1):
    x, y = a, 79 + b
    hole('Z_motor_plate', cyl('z', 2.5, 716, 726, x, y))
    screw('Z_motor_flange_bolt_%d' % i, cyl('z', 4.25, 733, 738, x, y), cyl('z', 2.5, 717, 733, x, y), 'M5x16 SHCS, motor flange into the plate (tap M5 depth 10)', 'x')
for i, x in enumerate((-50, -34, 34, 50), 1):
    hole('X_carriage_plate', cyl('y', 3, 104, 116, x, 699))
    screw('Z_motor_mount_bolt_%d' % i, cyl('y', 5, 38, 44, x, 699), cyl('y', 3, 44, 114, x, 699), 'M6x70 SHCS into the Z plate front face (tap M6 depth 12)', 'x')
# ================================================================ camera: looks down at the work, and at the tool through a turning mirror on the table
# Basler daA2448-70uc (CS) + 5 mm CS->C ring + Moritex MML05-HR110D (0.5x object-side telecentric, WD 110, coaxial light port).
# Layout B: camera axis D = 80 IN FRONT of the spindle axis (same x), so the camera sees the full 300 x 300 (Y travel has 100 to spare).
# Tool length: a 45 deg mirror on a bracket at the FRONT-LEFT edge of the table (x -150, 20 in front of the table edge, sight line 35 above
# the table). X -150, table +130 puts it under the camera; the view turns +Y (back) onto the tool 80 behind.
# Path = (lens front - tip) + D = 110  ->  lens front 30 above the nominal tool tip; tool tip read at the mirror's sight line.
import math
gl = '11 Camera'
g = doc.addObject('App::DocumentObjectGroup', 'G'); g.Label = gl; GROUPS[gl] = g
D_CAM = 80.0
SPX, SPY = 0.0, -20.0                                           # spindle axis
CAMX, CAMY = SPX, SPY - D_CAM
TIP = O('Tool_D5').Shape.BoundBox.ZMin                         # 180 at home
ZF = TIP + (110.0 - D_CAM)                                      # lens front
def place(shape, rx180=True, rz=0.0, t=(0, 0, 0)):
    s = shape.copy()
    if rx180: s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    if rz: s.rotate(V(0, 0, 0), V(0, 0, 1), rz)
    s.translate(V(*t)); return s
lens = Part.read(os.path.join(ROOT, 'vendor', 'moritex', 'MML05-HR110D', 'MML05-HR110D.step'))  # front z+91.47, C flange z-43.64, port +Y
lens = place(lens, True, 0, (CAMX, CAMY, ZF + 91.47))          # front down at ZF, coaxial port toward -Y (front)
ZC = ZF + 91.47 + 43.64                                         # C flange
add('Camera_lens', lens, gl, 'Moritex MML05-HR110D telecentric 0.5x, WD 110+-5.5, DOF 3, C-mount, coaxial light port D8 H7 (vendor STEP)', 'z', 'camera')
ring5 = Part.makeCylinder(15.0, 5.026, V(0, 0, 0)).cut(Part.makeCylinder(12.7, 5.026, V(0, 0, 0)))
add('Camera_CS_C_adapter', place(ring5, False, 0, (CAMX, CAMY, ZC)), gl, 'Basler CS-mount to C-mount adapter ring 5 mm (2200002382)', 'z', 'camera')
cam = Part.read(os.path.join(ROOT, 'vendor', 'basler', 'daA2448-70uc', 'daA2448-70uc_CS_from_drawing.step'))   # axis +Z, CS flange z0
add('Camera_body', place(cam, True, -90, (CAMX, CAMY, ZC + 5.026)), gl,
    'Basler dart R daA2448-70uc (CS-Mount), IMX548 1/1.8" 5 MP, USB3 toward the front; sensor long side along Y; '
    'model from the Basler dimension drawing', 'z', 'camera')
PZ = ZF + 91.47 - 6.8                                           # coaxial port centre height
add('Camera_light_guide', fuse(cyl('y', 4, CAMY - 76, CAMY - 46, CAMX, PZ), cyl('y', 5.5, CAMY - 96, CAMY - 76, CAMX, PZ)), gl,
    'light guide (fibre) end into the coaxial port D8 (to an LED light source)', 'z', 'camera')
# camera bracket (CNC, 6061): short block bolted to the LEFT half of the spindle clamp front face (not across its slit), web forward,
# split ring on the D22 lens tube. Bolts at x -28 avoid the clamp bolts (x+-41), the web and the pinch screws (z 355 / 381).
CF = O('Spindle_clamp').Shape.BoundBox.YMin                   # clamp front face (-63)
RZ0, RZ1 = 316.0, 336.0
br = fuse(box(-36, -6, CF - 10, CF, 334, 378), box(-20, -6, CAMY + 12, CF, RZ0, RZ1), box(-20, -6, CAMY + 17, CF, RZ1, 345),   # top of the web clears the lens D29 ring
          cyl('z', 20, RZ0, RZ1, CAMX, CAMY), box(CAMX + 16, CAMX + 30, CAMY - 8, CAMY + 8, RZ0 + 2, RZ1 - 2))
br = br.cut(cyl('z', 11.05, RZ0, RZ1, CAMX, CAMY)).cut(box(CAMX + 10, CAMX + 31, CAMY - 0.5, CAMY + 0.5, RZ0, RZ1))
PZM = (RZ0 + RZ1) / 2
br = br.cut(cyl('y', 2.25, CAMY - 8, CAMY - 0.5, CAMX + 24, PZM)).cut(cyl('y', 2.0, CAMY + 0.5, CAMY + 8, CAMX + 24, PZM))
add('Camera_bracket', br, gl, 'camera bracket (CNC, 6061): 2 x M5 on the left half of the spindle clamp front face, split ring D22 on the lens '
    'tube, M4 pinch screw', 'z', 'camera')
add('Camera_pinch_bolt', fuse(cyl('y', 3.5, CAMY - 12, CAMY - 8, CAMX + 24, PZM), cyl('y', 2.0, CAMY - 8, CAMY + 6, CAMX + 24, PZM)), gl,
    'M4x14 SHCS, ring pinch screw', 'z', 'fasten')
for i, z in enumerate((342, 368), 1):
    hole('Spindle_clamp', cyl('y', 2.5, CF, CF + 10, -28, z))
    bo = O('Camera_bracket'); bo.Shape = bo.Shape.cut(cyl('y', 2.75, CF - 10, CF, -28, z))
    add('Camera_bracket_bolt_%d' % i, fuse(cyl('y', 4.25, CF - 15, CF - 10, -28, z), cyl('y', 2.5, CF - 10, CF + 8, -28, z)), gl,
        'M5x18 SHCS into the spindle clamp front face (tap M5 depth 10)', 'z', 'fasten')
# turning mirror on the table (moves in Y): at table x -150, 20 in front of the table front edge, sight line 35 above the table top
TT = O('Work_table').Shape.BoundBox
MX, MY, MZ = -150.0, TT.YMin - 20.0, TT.ZMax + 35.0
mir = box(-10, 10, -10, 10, -3, 0); mir.rotate(V(0, 0, 0), V(1, 0, 0), -45); mir.translate(V(MX, MY, MZ))   # normal (0,1,1): down -> +Y
add('Tool_mirror', mir, gl, 'first-surface mirror 20x20x3 at 45 deg (or 20 mm right-angle prism) on the table: turns the camera view onto the tool', 'y', 'camera')
c, o3 = 10 / math.sqrt(2), 3 / math.sqrt(2)
E1, E2 = (MY - c - o3, MZ + c - o3), (MY + c - o3, MZ - c - o3)
tri = Part.Face(Part.makePolygon([V(MX - 12, E1[0], E1[1]), V(MX - 12, E2[0], E2[1]), V(MX - 12, E1[0], E2[1]), V(MX - 12, E1[0], E1[1])])).extrude(V(24, 0, 0))
YF = TT.YMin                                                    # table front face
mb = fuse(tri, box(MX - 8, MX + 8, E1[0], YF - 4, TT.ZMax - 14, MZ - 9.5), box(MX - 30, MX + 30, YF - 10, YF, TT.ZMin + 4, TT.ZMax - 4))
for x in (MX - 18, MX + 18): mb = mb.cut(cyl('y', 3.3, YF - 10, YF, x, (TT.ZMin + TT.ZMax) / 2))
add('Mirror_bracket', mb, gl, 'mirror bracket (CNC, steel): plate on the table front end face (2 x M6), arm, 45 deg seat for the mirror', 'y', 'camera')
for k, x in enumerate((MX - 18, MX + 18), 1):
    zc = (TT.ZMin + TT.ZMax) / 2
    hole('Work_table', cyl('y', 3, YF, YF + 12, x, zc))
    add('Mirror_bracket_bolt_%d' % k, fuse(cyl('y', 5, YF - 16, YF - 10, x, zc), cyl('y', 3, YF - 10, YF + 10, x, zc)), gl,
        'M6x20 SHCS into the table front face (tap M6 depth 12)', 'y', 'fasten')
print('CAMERA layout B: camera (%.0f, %.0f), lens front z %.1f, tip %.1f, mirror (%.0f, %.0f, %.0f), path %.1f, measure at X %.0f, table +%.0f'
      % (CAMX, CAMY, ZF, TIP, MX, MY, MZ, (ZF - TIP) + D_CAM, MX - SPX, CAMY - MY))

bad = [(l, round(r, 3)) for l, r in CHK if r < 0.98]
print('HOLE_CHECK', len(CHK), 'tools, not fully in material:', bad)

# ================================================================ removable alignment kit
KIT_RX = r'^(Yaw_push|Yaw_pull|Yaw_block_bolt|X_roll_bracket|X_roll_jack|Z_face_screw|Z_roll_block|Z_roll_screw|Spindle_face_screw|Spindle_roll_block|Spindle_roll_screw)'
G_KIT = doc.addObject('App::DocumentObjectGroup', 'Kit'); G_KIT.Label = '09 Alignment kit'
KIT = [l for l in NEW if re.match(KIT_RX, l)]
for l in KIT:
    o = O(l); GROUPS[G].removeObject(o); G_KIT.addObject(o); prop(o, 'Kit', 'removable')

# ground faces (the rail / block faces); the Y slide table is ground on both faces
prop(O('Datum_base_plate'), 'Spec', 'Q235 t20 720x327 datum plate, top face ground (Y block seats): Y blocks, Y nut seat, column feet')
prop(O('Work_table'), 'Spec', O('Work_table').Spec + '; Y slide table: both faces ground (rail face underside, work face top)')

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v12.FCStd'))
L = ['v12 = v10 + owner architecture.  new parts: %d, alignment kit: %d, epoxy pads: %d' % (len(NEW), len(KIT), sum(1 for l in NEW if 'epoxy' in l)), '']
for l in ['Column_foot_R', 'X_base_plate', 'X_carriage_plate', 'Spindle_clamp', 'Spindle_body'] + NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s %-2s %-8s %-4s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, getattr(o, 'Motion', '') or '-', getattr(o, 'Adj', '') or '-',
             'KIT' if l in KIT else '', b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v12_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
