# -*- coding: utf-8 -*-
"""v13 from v12 (frozen): tool-head module + wider X.

  1 Wider X     X travel +-150 -> +-227.5 (+155). The gantry is stretched 77.5 per side: columns, feet, yaw / X-level adjusters,
                X motor end move out; datum plate, X plate, X rails (SX2RNL28-540 -> -695, holes kept on the 60 pitch, +-270 / +-330
                added) and X screw (C-KBS1505-458 -> -616, now fixed-supported with a C-TEF12) are lengthened. Y axis and Z axis unchanged.
  2 Tool head   one module on the Z slide: camera, spindle, probe in one line along X (all centres at y -20).
                Spindle at x -7.5 (7.5 left of the Z centre), camera 70 left of it (x -77.5), probe 85 right of it (x +77.5):
                the module is symmetric about the Z slide and each tool still covers the 300 x 300 work area
                (spindle reach x -235..220, camera -305..150, probe -150..305).
                Module plate = the v12 spindle back plate made wider (216 at the bottom): same RBPB8 pivot, shim packs and differential
                screws, used for spindle tram ONLY; camera and probe offsets are calibrated after tramming. Shim bolts and the
                bottom face screws are moved so they stay reachable from the front (between the tools).
                Camera: Moritex MML04-HR120D (WD 120), 65 from the spindle, lens front 55 above the tool tip (path 55 + 65 = 120 = WD).
  3 Prism       folds the view +X; holder on the table T-slot x -130 at the rear-left corner (prism x -195, y +200), outside
                the work area, with a pneumatic flip cover. Tool measured at X -117.5, table -220, Z -40.
  4 Freeze fixes (design reviews): C-TEK12 mounting holes (X/Y/Z), table T-slots moved to x 0/+-65/+-130 with a DIN 650 section
                (clear of the Y rail taps), spindle turned 90 deg (plug forward), clamp bolts M6x85 + 2 dowels, module shim bolts
                spread to z 305 / 490 (Z slide 30 longer at the bottom), probe on an air slide (retract switch = spindle interlock),
                lens air ring, rail holes to the vendor size, text fixes.
  5 Z assembly 25 lower on the saddle: tool tip range -5..95 above the table (Z -50 reaches the table top), camera sees work tops 0..25.
Run:  freecadcmd freecad/v13/01_v13_toolhead.py      Out: output/v13/CNC_v13.FCStd, output/v13/logs/v13_build.txt"""
import os, re
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v13'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v12', 'CNC_v12.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
GROUPS = {g.Label: g for g in doc.Objects if g.TypeId == 'App::DocumentObjectGroup'}
NEW, LOG = [], []


def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cyl(ax, r, a0, a1, p, q):
    if ax == 'x': return Part.makeCylinder(r, a1 - a0, V(a0, p, q), V(1, 0, 0))
    if ax == 'y': return Part.makeCylinder(r, a1 - a0, V(p, a0, q), V(0, 1, 0))
    return Part.makeCylinder(r, a1 - a0, V(p, q, a0), V(0, 0, 1))
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
CHK = []
def hole(label, *tools):                                    # cut + check the tool lies in material
    o = O(label)
    for t in tools: CHK.append((label, t.common(o.Shape).Volume / t.Volume))
    cut(label, *tools)
def move(label, dx):
    o = O(label); s = o.Shape.copy(); s.translate(V(dx, 0, 0)); o.Shape = s
def spec(label, text): prop(O(label), 'Spec', text)
KQ2 = Part.read(os.path.join(ROOT, 'vendor', 'smc', 'KQ2H04-M5A', 'KQ2H04-M5A.stp'))   # vendor STEP: axis +Y, seat face y 0, M5 thread y -3..0, top y 14.7
def push_in(ax, sgn, p, q, a0, tube=25.0, tdep=4.0):
    """SMC KQ2H04-M5A straight push-in fitting (vendor STEP: M5 thread 3 long, hex 8, release button D7.9, 14.7 above the seat) on an M5
    port face at a0 (axis ax, pointing sgn) + D4 tube stub. Returns (fitting, tube, port); port = the M5 tap (depth tdep > thread 3) to cut."""
    def c(r, u0, u1):
        u0, u1 = sorted((a0 + sgn * u0, a0 + sgn * u1)); return cyl(ax, r, u0, u1, p, q)
    d = {'x': V(sgn, 0, 0), 'y': V(0, sgn, 0), 'z': V(0, 0, sgn)}[ax]
    pt = {'x': V(a0, p, q), 'y': V(p, a0, q), 'z': V(p, q, a0)}[ax]
    f = KQ2.copy(); f.Placement = App.Placement(pt, App.Rotation(V(0, 1, 0), d))
    return f, c(2.0, 14.7, 14.7 + tube), c(2.5, -tdep, 0.0)

def cls(o):                                                 # motion class, same rules as the motion check
    n = o.Label
    if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''

G = '08 Adjusters'
# ================================================================ 1. wider X: stretch the gantry 77.5 per side
W = 77.5
def stretch(label, xs, w=W):
    """split at x = +-xs, move the outer parts out by w, fill the gaps with the cross-section extruded"""
    o = O(label); s = o.Shape; b = s.BoundBox
    big = lambda x0, x1: box(x0, x1, b.YMin - 1, b.YMax + 1, b.ZMin - 1, b.ZMax + 1)
    sec = lambda x: Part.makeFace(s.slice(V(1, 0, 0), x), 'Part::FaceMakerBullseye')
    L = s.common(big(b.XMin - 1, -xs)); L.translate(V(-w, 0, 0))
    R = s.common(big(xs, b.XMax + 1)); R.translate(V(w, 0, 0))
    parts = [L, R]
    if xs > 0:
        parts += [s.common(big(-xs, xs)), sec(xs).extrude(V(w, 0, 0)), sec(-xs).extrude(V(-w, 0, 0))]
    else:
        f = sec(0.0); f.translate(V(-w, 0, 0)); parts.append(f.extrude(V(2 * w, 0, 0)))
    o.Shape = fuse(*[p for p in parts if p.Volume > 0])
    LOG.append('stretch %-18s at x+-%.0f: x %.1f..%.1f -> %.1f..%.1f' % (label, xs, b.XMin, b.XMax, o.Shape.BoundBox.XMin, o.Shape.BoundBox.XMax))
STRETCH = {'Datum_base_plate': 250.0, 'X_base_plate': 255.0, 'X_rail_1': 255.0, 'X_rail_2': 255.0, 'X_ballscrew': 0.0}
XDRIVE = ('X_support', 'X_coupling', 'X_motor')            # fixed end of the X screw (right side)
KEEP = ('Y_', 'Work_table', 'Servo_amp', 'Electrical_panel')
moved, warn = {}, []
for o in [o for o in doc.Objects if o.TypeId == 'Part::Feature']:
    n = o.Label
    if n in STRETCH or n.startswith(KEEP) or cls(o): continue
    b = o.Shape.BoundBox
    if n.startswith(XDRIVE) or b.XMin >= 255: d = W
    elif b.XMax <= -255: d = -W
    else:
        if b.XMax > 255 or b.XMin < -255: warn.append(n)
        continue
    move(n, d); moved[n] = d
for n, xs in STRETCH.items(): stretch(n, xs)
cut('X_base_plate', box(-181 - W, 166 + W, 162, 182, 330, 390))   # X nut bracket through-slot (v12: x -181..166) for the longer travel
LOG.append('moved out: %d parts (+x %d, -x %d); static parts crossing x+-255 not handled: %s'
           % (len(moved), sum(1 for d in moved.values() if d > 0), sum(1 for d in moved.values() if d < 0), warn or 'none'))
# X rails: ends rebuilt from the plain section (the stretch carried the cut-off half hole of the 540 rail out to the ends)
for r in (1, 2):
    o = O('X_rail_%d' % r); s_ = o.Shape; b_ = s_.BoundBox
    sec_ = lambda x: Part.makeFace(s_.slice(V(1, 0, 0), x), 'Part::FaceMakerBullseye')
    o.Shape = fuse(s_.common(box(-332.5, 332.5, b_.YMin - 1, b_.YMax + 1, b_.ZMin - 1, b_.ZMax + 1)), sec_(332.5).extrude(V(15, 0, 0)), sec_(-332.5).extrude(V(-15, 0, 0)))
# X rails: two more holes per side on the 60 pitch (rail ends at +-347.5, end distance 17.5), vendor hole D6 / c-bore D9.5, tapped into the X plate
for r, z in ((1, 250), (2, 470)):
    for x in (-330, -270, 270, 330):
        cut('X_rail_%d' % r, cyl('y', 4.75, 146, 155, x, z), cyl('y', 3.0, 155, 162, x, z))
        hole('X_base_plate', cyl('y', 2.5, 162, 171, x, z))
        add('X_rail_bolt_%d_%d' % (r, x), fuse(cyl('y', 4.25, 150, 155, x, z), cyl('y', 2.5, 155, 171, x, z)), G,
            'M5x16 SHCS in the rail counterbore, tapped 9 into the X plate', '', 'fasten')
# X screw: free end now supported (C-TEF12 on the X plate rear face, like the C-TEK12 at the motor end) -> fixed-supported
XF = -268.5                                                   # support centre: 5 clear of the nut bracket at X -227.5, base past the slot end
tef = Part.read(os.path.join(ROOT, 'vendor', 'misumi', 'C-TEF12', 'step', 'C-TEF12.stp')).Solids   # housing x0..20, base y0, axis (y25, z0)
for k, so in enumerate(tef[:2]):                              # housing + bearing (the snap ring is left out)
    so = so.copy(); so.translate(V(-10, -25, 0)); so.translate(V(XF, 207, 360)); tef[k] = so
add('X_support_float', tef[0].fuse(tef[1]), '04 X-axis', 'MISUMI C-TEF12 support unit (supported side, bearing 6000ZZ, d10), vendor STEP: on the X plate rear '
    'face at the free end of the X screw, 2 x M8', '', '')
for k, zz in enumerate((334, 386), 1):
    hole('X_base_plate', cyl('y', 4, 164, 182, XF, zz))
    add('X_support_float_bolt_%d' % k, fuse(cyl('y', 6.5, 225, 233, XF, zz), cyl('y', 4, 170, 225, XF, zz)), G,
        'M8x55 SHCS through the C-TEF12 housing into the X plate rear face (tap M8 depth 18, 12 engaged)', '', 'fasten')
o = O('X_ballscrew'); sb = o.Shape.BoundBox
o.Shape = fuse(o.Shape.common(box(XF + 10, sb.XMax + 1, sb.YMin - 1, sb.YMax + 1, sb.ZMin - 1, sb.ZMax + 1)), cyl('x', 5, XF - 7, XF + 10, 207, 360))
LOG.append('X screw fixed-supported: C-TEF12 at x %.1f, screw x %.1f..%.1f (L %.0f), thread end %.1f' % (XF, O('X_ballscrew').Shape.BoundBox.XMin,
           O('X_ballscrew').Shape.BoundBox.XMax, O('X_ballscrew').Shape.BoundBox.XLength, XF + 10))
# C-TEK12 fixed supports: 2 x M8 each (housing holes D9 at +-26 from the axis) were missing on X, Y and Z since v12
def tek_bolts(sup, plate, motion, head_side, nm, dep=18):
    s_ = O(sup).Shape; b_ = s_.BoundBox
    cs = sorted({(round(f.Surface.Center.x, 1), round(f.Surface.Center.y, 1), round(f.Surface.Center.z, 1)) for f in s_.Faces
                 if f.Surface.__class__.__name__ == 'Cylinder' and abs(f.Surface.Radius - 4.5) < 0.3})
    for k, c in enumerate(cs, 1):
        ax, lo, hi = head_side                                  # axis, housing face on the plate, housing far face
        sg = 1 if hi > lo else -1
        p_ = {'x': (c[1], c[2]), 'y': (c[0], c[2]), 'z': (c[0], c[1])}[ax]
        a0, a1 = sorted((lo - sg * dep, lo)); hole(plate, cyl(ax, 4, a0, a1, *p_))
        h0, h1 = sorted((hi, hi + sg * 8)); t0, t1 = sorted((lo - sg * 12, hi))
        add('%s_bolt_%d' % (nm, k), fuse(cyl(ax, 6.5, h0, h1, *p_), cyl(ax, 4, t0, t1, *p_)), G,
            'M8x55 SHCS through the C-TEK12 housing into the %s (tap M8 depth %d, 12 engaged)' % (plate, dep), motion, 'fasten')
    return len(cs)
nt = [tek_bolts('X_support_fixed', 'X_base_plate', '', ('y', 182.0, 225.0), 'X_support_fixed'),
      tek_bolts('Y_support_fixed', 'Work_table', 'y', ('z', 70.0, 27.0), 'Y_support_fixed'),
      tek_bolts('Z_support_fixed', 'X_carriage_plate', 'x', ('y', 104.0, 61.0), 'Z_support_fixed', 14)]
LOG.append('C-TEK12 mounting bolts added (X, Y, Z): %s' % nt)
spec('X_rail_1', 'SX2RNL28-695 rail (between the columns), holes on the 60 pitch x+-30..+-330')
spec('X_rail_2', 'SX2RNL28-695 rail (between the columns), holes on the 60 pitch x+-30..+-330')
spec('X_ballscrew', 'C-KBS1505-616, both ends machined: motor end D12x36 (C-TEK12 bearing + lock nut) + D10x27 (coupling), '
     'other end D10x17 (C-TEF12 bearing + snap ring); fixed-supported, X travel +-227.5. Critical speed about 5800 rpm (x0.8 = 4600) > 3000 rpm motor')
spec('X_base_plate', 'steel t20 875x260 (z 230..490); X rails z 250 / 470 (spacing 220); X drive axis z 360 = midway between the rails. '
     'Through-slot x -258.5..243.5, z 330..390 for the X nut bracket. Front face stepped 1 mm down outside x+-349.5: stands 1 mm off the columns, joined by 8 epoxy pads')
spec('Datum_base_plate', 'Q235 t20 875x327 datum plate, top face ground (Y block seats): Y blocks, Y nut seat, column feet')

# ================================================================ 2. tool-head module
for gl in ('11 Camera', '12 Probe'):                          # v12 camera and probe are replaced
    for o in list(GROUPS[gl].Group): doc.removeObject(o.Name)
z = O('Z_slide_plate')                                        # fill the v12 probe-bracket taps in the Z slide
z.Shape = fuse(z.Shape, *[cyl('y', 2.5, 34, 44, x, zz) for x in (89, 101) for zz in (340, 380)])

SX0, SY = -7.5, -20.0                                         # spindle axis
CX, PX = SX0 - 65.0, SX0 + 85.0                               # camera (D 65, MML04-HR120D: Ø45 nose vs spindle, taper vs clamp), probe axes
for l in ('Spindle_body', 'Spindle_fan_cover', 'Spindle_plug', 'Spindle_nose', 'ER11_nut', 'Tool_D5',
          'Spindle_pinch_screw_1', 'Spindle_pinch_screw_2') + tuple('Spindle_clamp_bolt_%d' % k for k in range(1, 5)):
    move(l, SX0)
for l in ('Spindle_body', 'Spindle_fan_cover', 'Spindle_plug', 'Spindle_nose', 'ER11_nut', 'Tool_D5'):   # turn 90 deg: plug forward (-Y)
    o = O(l); s_ = o.Shape.copy(); s_.rotate(V(SX0, SY, 0), V(0, 0, 1), -90); o.Shape = s_
TIP = O('Tool_D5').Shape.BoundBox.ZMin                         # 180 at home
# clamp block (same as v12, moved with the spindle)
CB = [(SX0 - 41, 340), (SX0 + 41, 340), (SX0 - 41, 396), (SX0 + 41, 396)]
c = box(SX0 - 48, SX0 + 48, -63, 20, 331, 405).cut(cyl('z', 32.5, 331, 405, SX0, SY)).cut(box(SX0 - 1, SX0 + 1, -63, SY, 331, 405))
for zz in (355, 381): c = c.cut(cyl('x', 3, SX0 - 48, SX0 + 30, -57, zz)).cut(cyl('x', 5.5, SX0 + 30, SX0 + 48, -57, zz))
for x, zz in CB: c = c.cut(cyl('y', 3.25, -57, 20, x, zz)).cut(cyl('y', 5.5, -63, -57, x, zz))
DW = [(SX0 - 41, 368), (SX0 + 41, 368)]                       # 2 dowels clamp -> module plate: offsets / tram repeat after removal
for x, zz in DW: c = c.cut(cyl('y', 3, 10, 20, x, zz))
O('Spindle_clamp').Shape = c
for k, (x, zz) in enumerate(CB, 1):
    O('Spindle_clamp_bolt_%d' % k).Shape = fuse(cyl('y', 5, -63, -57, x, zz), cyl('y', 3, -57, 28, x, zz))
    spec('Spindle_clamp_bolt_%d' % k, 'M6x85 SHCS, clamp block to module plate (tap M6 thru the plate, 8 engaged)')
spec('Spindle_clamp', '6061 clamp block 96x83x74: bore D65 H7 at (x-7.5, y-20), rear wall 7.5, front split with 2 M6 pinch screws; bolted to the '
     'module plate with 4 M6x85 from the front, located by 2 dowels D6 (H7 / m6) at (x-48.5 / 33.5, z 368); spindle turned so its plug faces forward')
# module plate: v12 back plate (156 wide, z 319..500) + a wide lower band (216 wide, z 288..465) for the camera and probe brackets
SB = (0, 366)                                                 # pivot (RBPB8 in the Z slide, unchanged)
BOLTS = [(-50, 305), (42, 305), (-50, 490), (50, 490)]        # shim bolts spread 185 apart (v13 review: 35 was too short for nod), front access
SCREWS = [('TC', 0, 490), ('BL', -103, 330), ('BR', 103, 330)]  # differential face screws: outside the camera and the probe
CAMB = [(CX - 10, 305), (CX + 6, 305)]                        # camera bracket: 2 x M5 low-head from the plate back
PRB = [(78, 300), (78, 360), (56, 330), (56, 375)]           # probe bracket: 4 x M5 low-head from the plate back (clear of the slide screws)
pl = fuse(box(-78, 78, 20, 32, 319, 500), box(-108, 108, 20, 32, 288, 465))
for x, zz in BOLTS: pl = pl.cut(cyl('y', 3.5, 20, 32, x, zz))
for _, x, zz in SCREWS: pl = pl.cut(cyl('y', 4, 20, 32, x, zz))
for x, zz in CB: pl = pl.cut(cyl('y', 3, 20, 32, x, zz))
for x, zz in CAMB + PRB: pl = pl.cut(cyl('y', 2.75, 20, 28, x, zz)).cut(cyl('y', 5, 28, 32, x, zz))
pl = pl.cut(cyl('y', 3, 20, 32, *SB))
for x, zz in DW: pl = pl.cut(cyl('y', 3, 20, 30, x, zz))
O('Spindle_mount_plate').Shape = pl
spec('Spindle_mount_plate', 'tool-head module plate, flat steel t12 (156 wide z 319..500 + 216 wide z 288..465), ground both faces, all holes from '
     'the front except 6 counterbores on the back: M6 tap for the pivot stud, 4 shim-bolt holes, 3 differential-screw taps, 4 M6 taps for the '
     'clamp block + 2 dowel holes D6 H7, 6 x M5 low-head holes (counterbored from the back) for the camera and probe brackets. Stands 2 mm off the '
     'slide on 4 shim packs at z 305 / 490 (185 apart)')
for k, (x, zz) in enumerate(BOLTS, 1):
    o = O('Spindle_shim_%d' % k)
    o.Shape = box(x - 11, x + 11, 32, 34, zz - 8, zz + 8).cut(box(x - 3.5, x + 3.5, 32, 34, zz - 8, zz)).cut(cyl('y', 3.5, 32, 34, x, zz))
    O('Spindle_bolt_%d' % k).Shape = fuse(cyl('y', 5, 14, 20, x, zz), cyl('y', 3, 20, 46, x, zz))
z = O('Z_slide_plate')                                        # move the shim-bolt taps: fill the v12 ones, tap the new ones; 30 longer at the bottom
z.Shape = fuse(z.Shape, box(-110, 110, 34, 62, 287, 317))
prop(z, 'Spec', z.Spec + '; v13: 30 longer at the bottom (z 287..547 at home) for the lower shim bolts')
z.Shape = fuse(z.Shape, *[cyl('y', 3, 34, 46, x, zz) for x in (-63, 63) for zz in (420, 455)])
for x, zz in BOLTS: hole('Z_slide_plate', cyl('y', 3, 34, 46, x, zz))
for k, (x, zz) in enumerate(DW, 1):
    add('Spindle_clamp_dowel_%d' % k, cyl('y', 3, 10, 30, x, zz), G, 'dowel D6 m6x20 (ISO 8734): spindle clamp to module plate', 'z', 'pins')
for nm, x, zz in SCREWS:
    O('Spindle_face_screw_' + nm).Shape = fuse(cyl('y', 4, 14, 34, x, zz), cyl('y', 6.5, 14, 20, x, zz))
spec('Spindle_face_screw_BL', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate, tip on the slide face, outside the '
     'camera: the three set the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')
spec('Spindle_face_screw_BR', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate, tip on the slide face, outside the '
     'probe: the three set the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')
spec('Spindle_face_screw_TC', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate top, tip on the slide face: '
     'with BL / BR sets the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')
spec('Z_face_screw_B', 'differential push screw (M8x0.75 outer / M6x0.5 inner = 0.25 mm/rev) at the bottom centre, 230 below the bearing: with the '
     'two top screws it holds the Y gap; top pair vs this one = nod about X. 10 deg = 30 urad')
spec('Yaw_push_screw', 'M6x0.75 push screw + jam nut: 10 deg = 26 urad (lever 787, v13 wider gantry)')
spec('X_roll_jack', 'M8x0.75 jack + jam nut under the right end of the X plate: 10 deg = 26 urad (lever 795, v13 wider gantry)')

# ---------------------------------------------------------------- camera (left)
import math
gl = '11 Camera'
WDL = 120.0                                                     # lens working distance (MML04-HR120D)
ZF = TIP + (WDL - (SX0 - CX))                                   # lens front: tip + 55 (path 55 + 65 = 120)
def place(shape, rx180=True, rz=0.0, t=(0, 0, 0)):
    s = shape.copy()
    if rx180: s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    if rz: s.rotate(V(0, 0, 0), V(0, 0, 1), rz)
    s.translate(V(*t)); return s
lens = Part.read(os.path.join(ROOT, 'vendor', 'moritex', 'MML04-HR120D', 'MML04-HR120D.step'))  # front z+123.07, C flange z-51.03, port +Y at z 6.57
add('Camera_lens', place(lens, True, -90, (CX, SY, ZF + 123.07)), gl,
    'Moritex MML04-HR120D telecentric 0.4x, WD 120+-3.6, DOF 5.3, resolution 17.7 um, C-mount, coaxial light port D8 toward -X (vendor STEP). '
    'Field of view with the daA2448 about 16.8 x 14.0. Focus plane = lens front - 120: with Z +50 max the camera sees work tops 0..30 mm above the table', 'z', 'camera')
ZC = ZF + 174.1                                                 # C flange
ring5 = Part.makeCylinder(15.0, 5.026, V(0, 0, 0)).cut(Part.makeCylinder(12.7, 5.026, V(0, 0, 0)))
add('Camera_CS_C_adapter', place(ring5, False, 0, (CX, SY, ZC)), gl, 'Basler CS-mount to C-mount adapter ring 5 mm (2200002382)', 'z', 'camera')
cam = Part.read(os.path.join(ROOT, 'vendor', 'basler', 'daA2448-70uc', 'daA2448-70uc_CS_from_drawing.step'))
add('Camera_body', place(cam, True, -180, (CX, SY, ZC + 5.026)), gl,
    'Basler dart R daA2448-70uc (CS-Mount), IMX548 1/1.8" 5 MP, USB3 toward -X (outside); sensor long side along X '
    '(= along the tool axis in the folded view); model from the Basler dimension drawing', 'z', 'camera')
PZ = ZF + 123.07 - 6.57                                         # coaxial port centre height (vendor STEP)
add('Camera_light_guide', fuse(cyl('x', 3.98, CX - 27, CX - 11.5, SY, PZ), cyl('x', 7.0, CX - 47, CX - 27, SY, PZ),
                               cyl('x', 5.5, CX - 87, CX - 47, SY, PZ)), gl,
    'light guide (fibre) D8 ferrule pushed into the coaxial port D8 to its stop, locked by the M3 set screw; cable to the LED light source', 'z', 'camera')
ar = fuse(cyl('z', 25.5, ZF - 2, ZF + 8, CX, SY), box(CX - 6, CX + 6, SY - 29.5, SY - 24, ZF - 2, ZF + 8))   # ring + port boss (M5 tap 4 > thread 3)
ar = ar.cut(cyl('z', 22.6, ZF - 2, ZF + 8, CX, SY)).cut(cyl('z', 24.0, ZF - 2, ZF + 4, CX, SY))                # bore + air gallery
ar = ar.cut(cyl('y', 2.0, SY - 25.5, SY - 22, CX, ZF + 3))           # D4 drill below the M5 tap into the gallery
add('Camera_air_ring', ar, gl, 'lens air ring (CNC, 6061) on the D45 lens nose, 2 x M3 set screws, port boss 12 x 12 with M5 tap depth 4: clean dry air from an M5 push-in fitting blows across '
    'the front glass (keeps coolant mist and chips off); no window, WD unchanged', 'z', 'camera')
fit_, tub_, port_ = push_in('y', -1, CX, ZF + 3, SY - 29.5); hole('Camera_air_ring', port_)
add('Camera_air_fitting', fit_, gl, 'SMC KQ2H04-M5A push-in fitting (M5, tube D4) on the lens air ring', 'z', 'camera')
add('Camera_air_tube', tub_, gl, 'polyurethane tube D4 (stub)', 'z', 'camera')
# bracket (CNC, 6061): split ring on the D45 lens barrel (below the spindle clamp), web back to a flange on the module plate (2 x M5 from the plate back)
RZ0, RZ1 = ZF + 60, ZF + 80
PZM = (RZ0 + RZ1) / 2
br = fuse(cyl('z', 26, RZ0, RZ1, CX, SY), box(CX - 8, CX + 8, SY - 36, SY - 22, RZ0 + 2, RZ1 - 2),       # ring + pinch lug (front)
          box(CX - 10, CX + 10, 1, 8, RZ0, RZ1),                                                       # web
          box(CX - 17.5, CX + 15, 8, 20, RZ0 - 5, RZ1 + 5))                                             # flange on the module plate
br = br.cut(cyl('z', 22.55, RZ0, RZ1, CX, SY)).cut(box(CX - 0.5, CX + 0.5, SY - 37, SY - 20, RZ0, RZ1))
br = br.cut(cyl('x', 2.25, CX - 8, CX - 0.5, SY - 29, PZM)).cut(cyl('x', 2.0, CX + 0.5, CX + 8, SY - 29, PZM))
add('Camera_bracket', br, gl, 'camera bracket (CNC, 6061): flange on the module plate (2 x M5 low-head from the plate back), split ring D45 on the '
    'lens barrel, M4 pinch screw', 'z', 'camera')
add('Camera_pinch_bolt', fuse(cyl('x', 3.5, CX - 12, CX - 8, SY - 29, PZM), cyl('x', 2.0, CX - 8, CX + 6, SY - 29, PZM)), gl,
    'M4x14 SHCS, ring pinch screw', 'z', 'fasten')
for i, (x, zz) in enumerate(CAMB, 1):
    hole('Camera_bracket', cyl('y', 2.5, 8, 20, x, zz))
    add('Camera_bracket_bolt_%d' % i, fuse(cyl('y', 4.25, 28.5, 32, x, zz), cyl('y', 2.5, 8.5, 28.5, x, zz)), gl,
        'M5x20 low-head (DIN 7984) from the module plate back into the bracket flange (M5 tap thru, tip 0.5 below the front); fitted on the bench before the module goes on', 'z', 'fasten')
# prism on the table (moves in Y): mirror-coated hypotenuse used from outside, folds the view +X onto the tool 70 to the right
TT = O('Work_table').Shape.BoundBox
# table T-slots: v12 had 14x15 straight slots at x 0/+-80/+-160, the +-160 ones right over the Y rail M12 taps -> fill them, cut DIN 650
# slots (neck 14x12, head 24x11, depth 23) at x 0 / +-65 / +-130, clear of the rail taps (x+-160) and the ref pins (x+-132)
TSLOT = (-130.0, -65.0, 0.0, 65.0, 130.0)
t_ = O('Work_table'); s_ = fuse(t_.Shape, *[box(x - 7, x + 7, TT.YMin, TT.YMax, 95, 110) for x in (-160, -80, 0, 80, 160)])
for x in TSLOT: s_ = s_.cut(box(x - 7, x + 7, TT.YMin, TT.YMax, 98, 110)).cut(box(x - 12, x + 12, TT.YMin, TT.YMax, 87, 98))
t_.Shape = s_
prop(t_, 'Spec', t_.Spec.replace('5x T-slot 14', '5x T-slot 14 DIN 650 (neck 14x12, head 24x11, depth 23) at x 0 / +-65 / +-130'))
SX = -130.0                                                     # T-slot used (left slot)
# v13 (Z assembly 25 lower): the station must stay below the spindle body at Z -50 (36 above the table) -> fold point 15 above the
# table, prism in a 3 mm pocket, sliding cover (no flip: a rotary actuator on the hinge would stand too high). Station top 29.5.
MX, MY, MZ = -195.0, 228.0, TT.ZMax + 15.0                       # fold point, rear-left corner outside the 300 x 300 work area (table -248 to measure)
ZB = MZ - 10                                                    # prism bottom (in the pocket)
BT = TT.ZMax + 8                                                # base top
pr = Part.Face(Part.makePolygon([V(MX - 10, MY - 10, ZB), V(MX - 10, MY - 10, ZB + 20), V(MX + 10, MY - 10, ZB), V(MX - 10, MY - 10, ZB)])).extrude(V(0, 20, 0))
add('Tool_mirror', pr, gl, 'right-angle prism 20x20x20, mirror-coated hypotenuse used from outside (front-surface mirror), glued: bottom face in the '
    'holder pocket, left face against the lip; folds the view +X', 'y', 'camera')
XC = MX - 22                                                     # cover cylinder axis x (outside the lip and the cover skirt)
mb = fuse(box(MX - 14, SX + 15, MY - 50, MY + 18, TT.ZMax, BT),                    # base t8 (ground bottom)
          box(XC - 16.5, XC + 16.5, MY - 83.5, MY - 19.5, TT.ZMax, TT.ZMax + 3),     # cylinder seat t3 (overhangs the table edge)
          box(XC - 16.5, XC + 16.5, MY - 83.5, MY - 77.5, TT.ZMax + 3, TT.ZMax + 28),  # end plate t6 for the cylinder (2 x M3 tapped through)
          box(SX - 6.95, SX + 6.95, MY - 50, MY + 18, TT.ZMax - 4, TT.ZMax),        # tenon key in the 14 mm slot neck
          box(MX - 14, MX - 10, MY - 12, MY + 12, BT, BT + 9))                       # lip: the prism's left face leans on it
mb = mb.cut(box(XC - 16.5, XC + 16.5, MY - 77.5, MY - 19.5, TT.ZMax + 3, BT))       # cylinder pocket
CYH = [(XC - 7.78, TT.ZMax + 15.5 + 7.78), (XC + 7.78, TT.ZMax + 15.5 - 7.78)]   # CDQ2B12 through-holes on the body diagonal (M 22)
for x_, z_ in CYH: mb = mb.cut(cyl('y', 1.5, MY - 83.5, MY - 77.5, x_, z_))           # 2 x M3 tapped through the end plate (t6)
mb = mb.cut(box(MX - 10, MX + 10, MY - 10, MY + 10, ZB, BT))                         # prism pocket 3 deep
MBB = [(SX, MY - 16), (SX, MY - 44)]                             # 2 x M6 low-head + T-nut, heads flush, off the beam band
mb = mb.cut(box(MX + 10, SX + 15, MY - 9, MY + 9, BT - 4, BT))   # relief under the across beam (FOV 16.8 x 14 at 0.4x)
for x, y in MBB: mb = mb.cut(cyl('z', 3.3, TT.ZMax - 4, BT, x, y)).cut(cyl('z', 5.5, BT - 4, BT, x, y))
add('Mirror_bracket', mb, gl, 'prism holder (CNC, steel t8, base ground): on the table T-slot x -130 at the rear-left corner (tenon key 14 h7, 2 x M6 low-head '
    '+ T-nut, heads flush), prism centre x -195; 3 mm pocket and left lip locate the glued 20 mm prism; station top 29.5 above the table', 'y', 'camera')
for k, (x, y) in enumerate(MBB, 1):
    add('Mirror_bracket_bolt_%d' % k, fuse(cyl('z', 5, BT - 4, BT, x, y), cyl('z', 3, TT.ZMax - 14, BT - 4, x, y)), gl,
        'M6x20 low-head (DIN 7984) + T-nut (DIN 508, slot 14) into the table T-slot', 'y', 'fasten')
CZ = BT + 21.5                                                  # cover lid top (station top)
cv = fuse(box(MX - 16, MX + 14, MY - 16, MY + 12, CZ - 2.5, CZ), box(MX - 16, MX - 14, MY - 16, MY + 12, BT + 9.5, CZ),
          box(MX + 12, MX + 14, MY - 16, MY + 12, BT + 2, CZ), box(XC - 4, MX - 16, MY - 16, MY - 12, TT.ZMax + 11, CZ))   # + side arm to the rod
add('Mirror_cover', cv, gl, 'prism cover (SUS t2, bent: lid + skirts on both X sides, side arm to the cylinder rod), drawn closed: keeps coolant and '
    'chips off the coated hypotenuse (top and +X); slides 30 toward +Y, clear of the light path, only during tool setting', 'y', 'camera')
cq = Part.read(os.path.join(ROOT, 'vendor', 'smc', 'CDQ2B12-30DZ', 'CDQ2B12-30DZ.stp'))   # axis z, body z -29..29, rod end +z, ports on +x
cq.rotate(V(0, 0, 0), V(0, 0, 1), 180); cq.rotate(V(0, 0, 0), V(1, 0, 0), -90)          # -> rod toward +Y, ports on the -X face
cq.translate(V(XC, MY - 48.5, TT.ZMax + 15.5))
add('Mirror_cover_actuator', cq, gl,
    'SMC CDQ2B12-30DZ compact cylinder bore 12 stroke 30 with magnet, vendor STEP (catalog p.787: square 25, body 58 = B 28 + stroke, rod D6 '
    'protrudes 3.5, M3 internal thread depth 6, 2 x D3.5 through-holes with D6.5 c-bores both ends on the diagonal (M 22), ports M5 at 11 from '
    'the rod end / 6.5 from the head end); head end on the holder end plate (2 x M3 through the body), rod on the cover arm, ports on the outer '
    '(-X) face; auto switch D-M9 = cover open; air via the Y drag chain', 'y', 'camera')
for k, (x_, z_) in enumerate(CYH, 1):
    add('Mirror_cover_cyl_bolt_%d' % k, fuse(cyl('y', 2.75, MY - 23, MY - 20, x_, z_), cyl('y', 1.5, MY - 83, MY - 23, x_, z_)), gl,
        'M3x60 SHCS through the cylinder (head in the rod-end c-bore) into the holder end plate (M3 tapped through t6, 6 engaged)', 'y', 'fasten')
for k, yy in enumerate((MY - 77.5 + 6.5, MY - 19.5 - 11), 1):   # ports in the vendor STEP (M5, 5.5 deep)
    fit_, tub_, port_ = push_in('x', -1, yy, TT.ZMax + 15.5, XC - 12.5)
    add('Mirror_cover_fitting_%d' % k, fit_, gl, 'SMC KQ2H04-M5A push-in fitting (M5, tube D4) on the cover cylinder port (outer face), vendor STEP', 'y', 'camera')
    add('Mirror_cover_tube_%d' % k, tub_, gl, 'polyurethane tube D4 (stub; to the Y drag chain)', 'y', 'camera')
MEAS = (MX - CX, SY - MY, MZ - TIP)                               # carriage dx, table dy, dz at the measuring pose
LOG.append('CAMERA (%.1f, %.0f), lens front z %.1f, tip %.1f, prism fold (%.0f, %.0f, %.0f), air path %.1f; measure at X %+.1f, table %+.0f, Z %+.0f'
           % (CX, SY, ZF, TIP, MX, MY, MZ, (ZF - TIP) + (SX0 - CX), *MEAS))

# ---------------------------------------------------------------- probe (right)
gp = '12 Probe'
STROKE = 60.0
TIPR = O('Spindle_body').Shape.BoundBox.ZMin                    # retracted ball level with the spindle body bottom (tool tip + 41)
BB0 = TIPR + 26.0
pb = fuse(cyl('z', 16.5, BB0, BB0 + 21, PX, SY), cyl('z', 3.0, BB0 + 21, BB0 + 41, PX, SY), cyl('z', 2.5, BB0 - 4, BB0, PX, SY),
          cyl('z', 0.75, TIPR + 1, BB0 - 4, PX, SY), Part.makeSphere(1.0, V(PX, SY, TIPR + 1)))
add('Probe_body', pb, gp, 'touch probe XUNKUANER (Amazon ASIN B0FWXWX7CT): shank D6x20, body D33x21, stylus 26 / ball D2, DC 5-24 V, NPN NO, to the grblHAL probe input '
    '(two-pass probing; NO cannot detect a broken wire: use an NC version if available, else check the input before each cycle). Not to the MR-J4: its MSD latch needs point-table mode, which cannot take the pulse train. '
    'Ball retracted level with the spindle body bottom (tool tip + 41), extended 19 below the tool tip', 'z', 'probe')
# SMC MXH10-60Z compact slide (owner: MXH10-60Z instead of MXH2 10-60; vendor STEP, catalog MXH p.31, bore 10): section 20 wide x 47 high
# (table 6), body 35 + stroke = 95, overall 46.5 + stroke = 106.5 retracted, table LT 99 x 19 with 6 x M4 taps, body 3 x M5 through-taps
# (c-bore D7.5 depth 4.4 both sides), ports M5 (head end, 6.5 / 26.5 from the body bottom). Mounted on its SIDE (lateral):
# the 20 width along Y on the bracket, the height along X with the table facing -X (spindle side) and the body bottom with the cylinder
# ports facing +X (room for the fittings), length vertical, head end up; the table + rod-end plate move down 60 to extend the probe.
# The probe hangs under the rod-end plate (front mounting face, 4 x M4 depth 7.5, rows 11 x 18) on a small clamp block: the probe force goes
# straight along the stroke into the plate, no lever arm.
T0 = BB0 + 42                                                   # rod-end plate bottom face (retracted): the probe shank (top BB0+41) just below it
XB, XT = 48.5, 95.5                                             # table top face / body bottom face (x)
YS0, YS1 = -8.0, 12.0                                           # slide width along Y (back on the bracket front y 12)
MXH = Part.read(os.path.join(ROOT, 'vendor', 'smc', 'MXH10-60Z', 'MXH10-60Z.step')).Solids   # body, table; table top x -30.5, body bottom x 16.5,
for so in MXH:                                                  # rod-end plate face z 59, head end z -47.5 -> x + 79, y 2 - y, z T0 + 59 - z
    so.rotate(V(0, 0, 0), V(1, 0, 0), 180); so.translate(V(79, 2, T0 + 59))
mxb, mxt = MXH
ZB0, ZB1 = T0 + 11.5, T0 + 106.5                                 # body (fixed)
SLB = [(XT - 28, T0 + 16.5), (XT - 28, T0 + 76.5), (XT - 5, T0 + 16.5)]   # body through-taps (vendor STEP)
for x, zz in SLB: mxb = mxb.cut(cyl('y', 2.5, -3.6, 7.6, x, zz))   # M5 thread to nominal (STEP shows the D4.2 pilot)
for x, y in [(XB + 21.5, 2 - 5.5), (XB + 21.5, 2 + 5.5), (XB + 39.5, 2 - 5.5), (XB + 39.5, 2 + 5.5)]:
    mxt = mxt.cut(cyl('z', 2.0, T0, T0 + 7.3, x, y))           # rod-end plate M4 taps to nominal
add('Probe_slide_body', mxb, gp,
    'SMC MXH10-60Z-M9NW compact slide, bore 10, stroke 60, vendor STEP (catalog MXH p.31: section 20 x 47, body 95, overall 106.5 retracted, '
    'table 99 x 19); mounted on its side, table toward the spindle, ports up / outward (3 x M5 into the body through-taps from the bracket back); '
    'extended = end of stroke (rubber bumper), the probe height is set in the shank clamp; 5/2 single-solenoid valve, spring return = retract on power loss', 'z', 'probe')
add('Probe_slide_table', mxt, gp,
    'SMC MXH10-60Z table + rod-end plate (part of the slide, vendor STEP; moves 60 down to extend the probe); the probe hangs under the rod-end plate (4 x M4)', 'z', 'probe')
for k, zz in enumerate((ZB1 - 32, ZB1 - 14), 1):
    add('Probe_reed_%d' % k, box(XT - 25.5, XT - 7.5, YS0 - 2.5, YS0, zz - 6, zz + 6), gp,
        ('auto switch D-M9NW (retracted): spindle enable + feed hold interlock' if k == 2 else 'auto switch D-M9NW (extended)'), 'z', 'probe')
    fit_, tub_, port_ = push_in('z', 1, (XT - 6.5, XT - 26.5)[k - 1], 2.0, ZB1); cut('Probe_slide_body', port_)
    add('Probe_air_fitting_%d' % k, fit_, gp, 'SMC KQ2H04-M5A push-in fitting (M5, tube D4) on the MXH head-end port (catalog: 6.5 / 26.5 from the body bottom), vendor STEP', 'z', 'probe')
    add('Probe_air_tube_%d' % k, tub_, gp, 'polyurethane tube D4 (stub; routed up to the Z drag chain)', 'z', 'probe')
br = box(XB, 96.0, 12, 20, ZB0 - 6, ZB1 + 6)
add('Probe_bracket', br, gp, 'probe slide bracket (CNC, 6061) t8 on the module plate (4 x M5 low-head from the plate back); the MXH10 on its front '
    '(3 x M5 low-head from the back into the slide body through-taps)', 'z', 'probe')
for i_, (x, zz) in enumerate(PRB, 1):
    hole('Probe_bracket', cyl('y', 2.5, 12, 20, x, zz))
    add('Probe_bracket_bolt_%d' % i_, fuse(cyl('y', 4.25, 28.5, 32, x, zz), cyl('y', 2.5, 12.5, 28.5, x, zz)), gp,
        'M5x16 low-head (DIN 7984) from the module plate back into the bracket (M5 tap thru, tip 0.5 below the front); fitted on the bench', 'z', 'fasten')
for k_, (x, zz) in enumerate(SLB, 1):
    cut('Probe_bracket', cyl('y', 2.75, 12, 16.5, x, zz), cyl('y', 4.75, 16.5, 20, x, zz))
    add('Probe_slide_bolt_%d' % k_, fuse(cyl('y', 4.25, 16.5, 20, x, zz), cyl('y', 2.5, -3.5, 16.5, x, zz)), gp,
        'M5x20 low-head (DIN 7984) from the bracket back into the MXH10 body through-tap (past the 4.4 c-bore, 11 engaged)', 'z', 'fasten')
HT = 14.0                                                       # clamp block height
EPH = [(XB + 21.5, 2 - 5.5), (XB + 21.5, 2 + 5.5), (XB + 39.5, 2 - 5.5), (XB + 39.5, 2 + 5.5)]   # end-plate taps (rows from the table side)
hd = box(XB + 2, PX + 17, SY - 18, YS1, T0 - HT, T0)            # clamp block under the rod-end plate
hd = hd.cut(cyl('z', 3.0, T0 - HT, T0, PX, SY)).cut(box(PX - 0.5, PX + 0.5, SY - 18, SY, T0 - HT, T0))      # D6 H7 bore + slit
hd = hd.cut(cyl('x', 2.25, PX + 0.5, PX + 17, SY - 10, T0 - HT / 2)).cut(cyl('x', 2.0, PX - 6, PX - 0.5, SY - 10, T0 - HT / 2))   # pinch from +X (head outside)
for x, y in EPH: hd = hd.cut(cyl('z', 2.25, T0 - HT + 4.5, T0, x, y)).cut(cyl('z', 3.75, T0 - HT, T0 - HT + 4.5, x, y))
add('Probe_holder', hd, gp, 'probe clamp block (CNC, 6061) under the MXH10 rod-end plate (front mounting face, 4 x M4 from below), split D6 H7 bore for the '
    'shank (M4 pinch): the probe height is set here', 'z', 'probe')
add('Probe_pinch_bolt', fuse(cyl('x', 3.5, PX + 17, PX + 21, SY - 10, T0 - HT / 2), cyl('x', 2.0, PX - 6, PX + 17, SY - 10, T0 - HT / 2)), gp, 'M4x20 SHCS, shank clamp (head on the +X side)', 'z', 'fasten')
for i_, (x, y) in enumerate(EPH, 1):
    add('Probe_holder_bolt_%d' % i_, fuse(cyl('z', 3.5, T0 - HT + 0.5, T0 - HT + 4.5, x, y), cyl('z', 2.0, T0 - HT + 4.5, T0 + 6.5, x, y)), gp,
        'M4x16 SHCS from below, clamp block into the MXH10 rod-end plate (tap M4 depth 7.5)', 'z', 'fasten')
ZBK = T0
LOG.append('PROBE (%.1f, %.0f) on an air slide, ball retracted z %.1f (tool tip %+.0f), extended z %.1f (tool tip %+.0f), stroke %.0f'
           % (PX, SY, TIPR, TIPR - TIP, TIPR - STROKE, TIPR - STROKE - TIP, STROKE))
LOG.append('SPINDLE x %.1f, camera %.1f (D %.0f), probe %.1f (P %.0f); X travel +-%.1f: spindle reach %.1f..%.1f, camera %.1f..%.1f, probe %.1f..%.1f'
           % (SX0, CX, SX0 - CX, PX, PX - SX0, 150 + W, SX0 - 150 - W, SX0 + 150 + W, CX - 150 - W, CX + 150 + W, PX - 150 - W, PX + 150 + W))

# ================================================================ 5. Z assembly 25 lower (owner: the tool must reach the table top at Z -50)
# The Z plate (X_carriage_plate) drops 25 on the saddle with everything on it: Z rails / screw / support / motor, the Z slide and the
# tool-head module. Parts that tie the plate to the SADDLE keep their saddle positions where possible:
#   clamp bolts at z 240 / 620 and the bottom face screw stay (plate holes moved), the top clamp bolts and top face screws move with the
#   plate (696 -> 671, 700 -> 675: the plate top is now 685; saddle taps re-cut), the RBPB8 bearing and its pin stay in the saddle
#   (pin hole in the plate moved 25 up: the pivot is now 25 above the plate centre), the side roll blocks stay on the saddle ears.
DZA = -25.0
ZMOVE = ('X_carriage_plate', 'Z_rail', 'Z_ballscrew', 'Z_support_fixed', 'Z_coupling', 'Z_motor', 'Z_ref_pin', 'Z_ecc_pin', 'Z_side_screw',
         'Z_face_screw_L', 'Z_face_screw_R', 'Z_clamp_bolt_3', 'Z_clamp_bolt_6', 'Z_epoxy_pad_3', 'Z_epoxy_pad_6')
nz = 0
for o in [o for o in doc.Objects if o.TypeId == 'Part::Feature']:
    if cls(o) == 'z' or o.Label.startswith(ZMOVE):
        s_ = o.Shape.copy(); s_.translate(V(0, 0, DZA)); o.Shape = s_; nz += 1
zp = O('X_carriage_plate')                                      # plate holes for the parts that stayed with the saddle
zp.Shape = fuse(zp.Shape, *[cyl('y', 3.5, 104, 121, x, zz + DZA) for x in (-108, 108) for zz in (240, 620)],
                *[cyl('y', 1.5, 104, 121, x, zz + 8 + DZA) for x in (-108, 108) for zz in (240, 620)],
                cyl('y', 4, 104, 121, 0, 236 + DZA), cyl('y', 4, 104, 121, 0, 466 + DZA))
for x in (-108, 108):
    for zz in (240, 620): cut('X_carriage_plate', cyl('y', 3.5, 104, 121, x, zz), cyl('y', 1.5, 104, 121, x, zz + 8))
cut('X_carriage_plate', cyl('y', 4, 104, 121, 0, 236), cyl('y', 4, 104, 121, 0, 466))
sd = O('X_saddle_plate')                                        # saddle taps for the top clamp bolts follow the plate
sd.Shape = fuse(sd.Shape, *[cyl('y', 3, 122, 132, x, 696) for x in (-108, 108)])
for x in (-108, 108): hole('X_saddle_plate', cyl('y', 3, 122, 132, x, 696 + DZA))
zm = O('Z_motor_plate').Shape.BoundBox; sb_ = O('X_saddle_plate').Shape.BoundBox   # the Z motor plate now reaches over the saddle top
cut('X_saddle_plate', box(zm.XMin - 4, zm.XMax + 4, sb_.YMin - 1, sb_.YMax + 1, zm.ZMin - 4, sb_.ZMax + 1))
prop(sd, 'Spec', sd.Spec + '; v13: notch %.0f wide x %.0f deep in the top centre for the Z motor plate (4 clear)' % (zm.XLength + 8, sb_.ZMax - zm.ZMin + 4))
prop(zp, 'Spec', zp.Spec + '; v13: Z assembly 25 lower on the saddle (plate z 197..685): RBPB8 pin 25 above the plate centre')
LOG.append('Z assembly lowered %.0f: %d parts moved; tool tip z %.1f (table top %.0f -> Z -50 reaches %.1f below it), Z plate bottom z %.1f'
           % (-DZA, nz, O('Tool_D5').Shape.BoundBox.ZMin, TT.ZMax, TT.ZMax - (O('Tool_D5').Shape.BoundBox.ZMin - 50), zp.Shape.BoundBox.ZMin))
LOG.append('  after the drop: lens front z %.1f, tool-setting pose X %+.1f, table %+.0f, Z %+.1f' % (O('Camera_lens').Shape.BoundBox.ZMin, MEAS[0], MEAS[1], MZ - O('Tool_D5').Shape.BoundBox.ZMin))
spec('Camera_lens', O('Camera_lens').Spec.replace('sees work tops 0..50 mm above the table', 'sees work tops 0..25 mm above the table'))

bad = [(l, round(r, 3)) for l, r in CHK if r < 0.98]
LOG.append('HOLE_CHECK %d tools, not fully in material: %s' % (len(CHK), bad))
doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v13.FCStd'))
L = ['v13 = v12 + wider X + tool-head module.  new parts: %d' % len(NEW)] + LOG + ['']
for l in ['Datum_base_plate', 'X_base_plate', 'X_rail_1', 'X_ballscrew', 'Gantry_column_L', 'Gantry_column_R', 'Spindle_mount_plate', 'Spindle_clamp'] + NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s %-2s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, getattr(o, 'Motion', '') or '-', b.XMin, b.XMax, b.YMin, b.YMax,
             b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v13_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(LOG))
