# -*- coding: utf-8 -*-
"""v12 from v10 (frozen), owner's architecture: the Y axis is the datum, everything else is set against it and then frozen.

  1 Y datum      Y rails and Y blocks located by reference pins on ground faces (no adjustment)
  2 X perp Y     gantry (columns + X plate) is one body: LEFT foot turns on a vertical D10 pivot pin, the RIGHT foot is pushed/pulled
                 in Y (lever 640); a second D10 dowel is reamed at the right foot afterwards
  3 X level      X plate turns on a horizontal D10 pin in the LEFT column, a vertical M8x0.75 jack lifts the RIGHT end (lever 640).
                 The X plate stands 1 mm off the column faces (1 mm step milled on its front face outside the rails) and the joint
                 is frozen by injected epoxy pads, so two columns that lean differently cannot twist the ground X plate
  4 Z (3 axes)   saddle (on the X blocks) + Z plate, 1 mm apart, touching only through a D12 steel ball at the CENTRE of the
                 plate (pivot for every rotation; tilts either way, +-4.1 mrad before the plate edge meets the saddle).
                 Two differential push screws (0.25 mm/rev) through the Z plate at the top (common mode = nod about X,
                 differential = turn about Z, which does not affect squareness), opposed differential side screws = roll
                 about Y (levers 234 / 214). Frozen by injected epoxy pads round the 6 clamp bolts
  5 spindle      spindle // Z rails preset as a sub-assembly: tall clamp ears on 4 shim packs (nod, lever 165) and a D6 roll pivot
                 with removable push blocks (roll). Spindle axis moved to y-8 so the clamp has a real rear wall
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

# ================================================================ 4. Z: saddle + Z plate on a steel ball, epoxy joint
zp = O('X_carriage_plate')
zp.Shape = box(-120, 120, 104, 121, 222, 710)
prop(zp, 'Spec', 'Z plate, steel t17 240x488: Z rails, Z screw, Z motor plate. 1 mm off the saddle, on a D12 ball; frozen by 6 epoxy pads')
tag('X_carriage_plate', 'ztram')
sad = fuse(box(-120, 120, 122, 134, 222, 706), box(120, 142, 122, 134, 652, 706), box(-142, -120, 122, 134, 652, 706))
add('X_saddle_plate', sad, '04 X-axis', 'saddle, steel t12 with two ears above the columns: bolted to the 4 X blocks and the X nut bracket', 'x', 'ztram')
ball = Part.makeSphere(6, V(0, 121.5, 466))
add('Z_ball', ball, G, 'D12 hardened steel ball in spherical seats in both plates, at the centre of the Z plate (z466): the single contact '
    'and pivot; the plate tilts either way by up to 1/244 = 4.1 mrad before an edge meets the saddle', 'x', 'ztram')
cut('X_carriage_plate', ball); cut('X_saddle_plate', ball)
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
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    s = m(fuse(cyl('y', 4, 92, 122, 90, 700), cyl('y', 6.5, 98, 104, 90, 700)))
    add('Z_face_screw_' + T, s, G, 'differential push screw (M8x0.75 outer / M6x0.5 inner = 0.25 mm/rev) through the Z plate, tip on the saddle, '
        '234 above the ball: both = nod about X, one = turn about Z (no effect on squareness, keep equal). 10 deg = 30 urad', 'x', 'ztram')
    cut('X_carriage_plate', m(cyl('y', 4, 104, 121, 90, 700)))
    add('Z_roll_block_' + T, m(box(124, 142, 104, 122, 664, 696).cut(cyl('x', 3, 124, 142, 112.5, 680)).cut(cyl('y', 2.75, 104, 122, 133, 670)).cut(cyl('y', 2.75, 104, 122, 133, 690))),
        G, 'steel block 18x18x32 on the saddle ear, beside the Z plate edge', 'x', 'ztram')
    add('Z_roll_screw_' + T, m(fuse(cyl('x', 3, 120, 150, 112.5, 680), cyl('x', 5.5, 142, 147, 112.5, 680))), G,
        'opposed differential side screw (0.25 mm/rev), tip on the Z plate edge 214 above the ball: roll about Y. 10 deg = 32 urad', 'x', 'ztram')
    for kk, z in enumerate((670, 690), 1):
        add('Z_roll_block_bolt_%s%d' % (T, kk), m(fuse(cyl('y', 4.25, 99, 104, 133, z), cyl('y', 2.5, 104, 132, 133, z))), G, 'M5 SHCS', 'x', 'ztram')
        cut('X_saddle_plate', m(cyl('y', 2.5, 122, 132, 133, z)))

# ================================================================ 5. spindle preset: tall ears on shims, roll pivot
DY = -8
for l in ('Spindle_body', 'Spindle_fan_cover', 'Spindle_plug', 'Spindle_nose', 'ER11_nut', 'Tool_D5'):
    o = O(l); s = o.Shape.copy(); s.translate(V(0, DY, 0)); o.Shape = s; tag(l, 'spindle')
PADS = [(-64, 327), (64, 327), (-64, 492), (64, 492)]
PIN = (-64, 352)
c = fuse(box(-40, 40, -55, 32, 331, 401), box(40, 78, 2, 32, 319, 500), box(-78, -40, 2, 32, 319, 500))
c = c.cut(cyl('z', 32.5, 331, 401, 0, DY)).cut(box(-1, 1, -55, DY, 331, 401))
for z in (345, 388): c = c.cut(cyl('x', 3, -40, 30, -48, z)).cut(cyl('x', 5.5, 26, 40, -48, z))
for x, z in PADS: c = c.cut(cyl('y', 3.5, 2, 32, x, z))
c = c.cut(cyl('y', 3, 20, 32, *PIN))
cl = O('Spindle_clamp'); cl.Shape = c
prop(cl, 'Spec', '6061 split clamp, bore D65 at (x0, y-8), rear wall 7.5; tall ears 38x30x181 stand 2 mm off the slide on 4 shim packs')
tag('Spindle_clamp', 'spindle')
for k, z in enumerate((345, 388), 1):
    add('Spindle_pinch_screw_%d' % k, fuse(cyl('x', 3, -30, 30, -48, z), cyl('x', 5, 30, 36, -48, z)), G, 'M6 pinch screw, fixed torque before tramming', 'z', 'spindle')
for k, (x, z) in enumerate(PADS, 1):
    sh = box(x - 12, x + 12, 32, 34, z - 8, z + 8).cut(box(x - 3.5, x + 3.5, 32, 34, z - 8, z)).cut(cyl('y', 3.5, 32, 34, x, z))
    add('Spindle_shim_%d' % k, sh, G, 'ground shim pack 24x16, nominal 2.0, U-slot: top pair minus bottom pair sets nod (0.01 mm = 61 urad, lever 165)', 'z', 'spindle')
    add('Spindle_bolt_%d' % k, fuse(cyl('y', 5, -4, 2, x, z), cyl('y', 3, 2, 46, x, z)), G, 'M6 SHCS through ear and shim; ear hole D7 (roll range)', 'z', 'spindle')
    cut('Z_slide_plate', cyl('y', 3, 34, 46, x, z))
s = cyl('y', 3, 20, 46, *PIN)
add('Spindle_roll_pin', s, G, 'D6 pin pressed in the slide, engages the left ear: roll pivot', 'z', 'spindle'); cut('Z_slide_plate', s)
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    add('Spindle_roll_block_' + T, m(box(80, 98, 14, 34, 474, 504).cut(cyl('x', 2.5, 80, 98, 24, 489)).cut(cyl('y', 2.2, 14, 34, 89, 500))), G,
        'steel block beside the top of the ear', 'z', 'spindle')
    add('Spindle_roll_screw_' + T, m(fuse(cyl('x', 2.5, 78, 104, 24, 489), cyl('x', 4.5, 98, 102, 24, 489))), G,
        'M5x0.5 opposed push screw on the ear side, 137 above the pivot: roll. 10 deg = 101 urad', 'z', 'spindle')
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
            add('%s_side_screw_%s%d' % (prefix, side, i), fuse(hd, sh), G, 'side screw opposite the pin', motion, 'rails'); cut(parent, sh)
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

# ================================================================ removable alignment kit
KIT_RX = r'^(Yaw_push|Yaw_pull|Yaw_block_bolt|X_roll_bracket|X_roll_jack|Z_face_screw|Z_roll_block|Z_roll_screw|Spindle_roll_block|Spindle_roll_screw)'
G_KIT = doc.addObject('App::DocumentObjectGroup', 'Kit'); G_KIT.Label = '09 Alignment kit'
KIT = [l for l in NEW if re.match(KIT_RX, l)]
for l in KIT:
    o = O(l); GROUPS[G].removeObject(o); G_KIT.addObject(o); prop(o, 'Kit', 'removable')

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v12.FCStd'))
L = ['v12 = v10 + owner architecture.  new parts: %d, alignment kit: %d, epoxy pads: %d' % (len(NEW), len(KIT), sum(1 for l in NEW if 'epoxy' in l)), '']
for l in ['Column_foot_R', 'X_base_plate', 'X_carriage_plate', 'Spindle_clamp', 'Spindle_body'] + NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s %-2s %-8s %-4s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, getattr(o, 'Motion', '') or '-', getattr(o, 'Adj', '') or '-',
             'KIT' if l in KIT else '', b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v12_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
