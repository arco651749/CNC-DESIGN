# -*- coding: utf-8 -*-
"""v14 from v12 (frozen), same build as v13 but with the tool head laid out as an L (owner: option B):
  1 X           X travel +-150 -> +-182.5 (+65, v13 was +155). Camera and spindle stay in one line along X (D 65, the optics and
                the prism station are unchanged); the probe moves in front of the spindle (-Y), so only the camera offset adds to X.
                The gantry is stretched 32.5 per side: columns, feet, yaw / X-level adjusters, X motor end move out; datum plate, X plate,
                X rails (SX2RNL28-540 -> -605, holes on the 60 pitch, +-270 added) and X screw (C-KBS1505-458 -> about 523, fixed-supported
                with a C-TEF12) are lengthened. Y axis (travel 400) and Z axis unchanged.
  2 Tool head   one module on the Z slide: camera x -32.5 and spindle x +32.5 (centred on the Z slide), probe on the spindle clamp
                front at (-11, -73): its X offset lies between camera and spindle, so it adds no X travel; its Y offset 53 uses the
                Y travel that the prism station already needs (table +97..-203 vs +150..-250).
                Module plate = the v12 spindle back plate made wider (216 at the bottom): same RBPB8 pivot, shim packs and differential
                screws, used for spindle tram ONLY; camera and probe offsets are calibrated after tramming. Bottom shim bolts at x -70 / +95,
                outside the spindle and the camera, reachable from the front.
                Camera: Moritex MML04-HR120D (WD 120), 65 from the spindle, lens front 55 above the tool tip (path 55 + 65 = 120 = WD).
                Probe: SMC MXH10-60Z, side face bolted straight onto the spindle clamp front (left of the split, 2 x M4), the probe on a plate + stem under its rod-end plate;
                the clamp is bolted to the module plate from the plate back. Ball retracted at tool tip + 35, extended 25 below the tip.
  3 Prism       folds the view +X; holder on the table T-slot x -130 at the rear-left corner (prism x -195, y +228), outside
                the work area, with a pneumatic sliding cover. v14: fold point 10 above the table (prism through the base onto the table,
                cover cylinder on the table), station top 25: 5 below the retracted probe ball and 11 below the spindle body at Z -50.
  4 v13 freeze fixes kept: C-TEK12 mounting holes, table T-slots DIN 650, clamp bolts + dowels (v14: spindle plug faces +X again),
                lens air ring, rail holes to the vendor size, vendor STEP for the SMC parts and fittings.
  5 Z assembly 25 lower on the saddle: tool tip range -5..95 above the table (Z -50 reaches the table top), camera sees work tops 0..25.
Run:  freecadcmd freecad/v14/01_v14_toolhead.py      Out: output/v14/CNC_v14.FCStd, output/v14/logs/v14_build.txt"""
import os, re
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v14'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
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
def shrink(label, x0, d):
    """narrow a plate by d per side: drop the plain band x0..x0+d on each side, move the outer parts in (inverse of stretch)"""
    o = O(label); s_ = o.Shape; b = s_.BoundBox
    big = lambda a0, a1: box(a0, a1, b.YMin - 1, b.YMax + 1, b.ZMin - 1, b.ZMax + 1)
    sec = lambda x: round(s_.slice(V(1, 0, 0), x)[0].BoundBox.ZLength if s_.slice(V(1, 0, 0), x) else 0, 3)
    R = s_.common(big(x0 + d, b.XMax + 1)); R.translate(V(-d, 0, 0))
    L = s_.common(big(b.XMin - 1, -x0 - d)); L.translate(V(d, 0, 0))
    o.Shape = fuse(s_.common(big(-x0, x0)), R, L)
    LOG.append('shrink %-18s band +-%.0f..%.0f: x %.1f..%.1f -> %.1f..%.1f' % (label, x0, x0 + d, b.XMin, b.XMax, o.Shape.BoundBox.XMin, o.Shape.BoundBox.XMax))
def inward(label, d):
    o = O(label); s_ = o.Shape.copy(); c = (s_.BoundBox.XMin + s_.BoundBox.XMax) / 2; s_.translate(V(-d if c > 0 else d, 0, 0)); o.Shape = s_
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
# ================================================================ 1. wider X: stretch the gantry 32.5 per side (v13: 77.5)
W = 32.5
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
    RE = 270 + W - 15                                          # plain section from here to the rail end (270 + W)
    o.Shape = fuse(s_.common(box(-RE, RE, b_.YMin - 1, b_.YMax + 1, b_.ZMin - 1, b_.ZMax + 1)), sec_(RE).extrude(V(15, 0, 0)), sec_(-RE).extrude(V(-15, 0, 0)))
# X rails: more holes on the 60 pitch where the longer rail has room (end distance >= 17.5), vendor hole D6 / c-bore D9.5, tapped into the X plate
for r, z in ((1, 250), (2, 470)):
    for x in [x for x in (-330, -270, 270, 330) if abs(x) <= 270 + W - 17.5]:
        cut('X_rail_%d' % r, cyl('y', 4.75, 146, 155, x, z), cyl('y', 3.0, 155, 162, x, z))
        hole('X_base_plate', cyl('y', 2.5, 162, 171, x, z))
        add('X_rail_bolt_%d_%d' % (r, x), fuse(cyl('y', 4.25, 150, 155, x, z), cyl('y', 2.5, 155, 171, x, z)), G,
            'M5x16 SHCS in the rail counterbore, tapped 9 into the X plate', '', 'fasten')
# X screw: free end now supported (C-TEF12 on the X plate rear face, like the C-TEK12 at the motor end) -> fixed-supported
XF = -(150 + W) - 41                                          # support centre: 5 clear of the nut bracket at the X travel end, base past the slot end
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
RL, HX_ = round(540 + 2 * W), max(x for x in (210, 270, 330) if x <= 270 + W - 17.5)
for r in (1, 2): spec('X_rail_%d' % r, 'SX2RNL28-%d rail (between the columns), holes on the 60 pitch x+-30..+-%d' % (RL, HX_))
SL = round(O('X_ballscrew').Shape.BoundBox.XLength)
spec('X_ballscrew', 'C-KBS1505-%d, both ends machined: motor end D12x36 (C-TEK12 bearing + lock nut) + D10x27 (coupling), '
     'other end D10x17 (C-TEF12 bearing + snap ring); fixed-supported, X travel +-%.1f. Critical speed above the v13 value (5800 rpm, 616 long): '
     'span %d shorter' % (SL, 150 + W, 616 - SL))
PW = round(720 + 2 * W)
spec('X_base_plate', 'steel t20 %dx260 (z 230..490); X rails z 250 / 470 (spacing 220); X drive axis z 360 = midway between the rails. '
     'Through-slot x %.1f..%.1f, z 330..390 for the X nut bracket. Front face stepped 1 mm down outside x+-%.1f: stands 1 mm off the columns, '
     'joined by 8 epoxy pads' % (PW, -181 - W, 166 + W, 272 + W))
spec('Datum_base_plate', 'Q235 t20 %dx327 datum plate, top face ground (Y block seats): Y blocks, Y nut seat, column feet' % PW)

# ================================================================ 2. tool-head module
for gl in ('11 Camera', '12 Probe'):                          # v12 camera and probe are replaced
    for o in list(GROUPS[gl].Group): doc.removeObject(o.Name)
z = O('Z_slide_plate')                                        # fill the v12 probe-bracket taps in the Z slide
z.Shape = fuse(z.Shape, *[cyl('y', 2.5, 34, 44, x, zz) for x in (89, 101) for zz in (340, 380)])

SX0, SY = 32.5, -20.0                                         # spindle axis (v14: camera / spindle pair centred on the Z slide)
CX = SX0 - 65.0                                               # camera (D 65, MML04-HR120D: Ø45 nose vs spindle, taper vs clamp)
PX, PY = -11.0, -73.0                                         # probe axis (set again from the build below): under the probe stem, between camera and spindle
for l in ('Spindle_body', 'Spindle_fan_cover', 'Spindle_plug', 'Spindle_nose', 'ER11_nut', 'Tool_D5',
          'Spindle_pinch_screw_1', 'Spindle_pinch_screw_2') + tuple('Spindle_clamp_bolt_%d' % k for k in range(1, 5)):
    move(l, SX0)
# v14: no 90 deg turn: the plug faces +X (right) as in v12; the front is taken by the probe slide, the right side is free above the clamp
TIP = O('Tool_D5').Shape.BoundBox.ZMin                         # 180 at home
# clamp block (same as v12, moved with the spindle)
CB = [(SX0 - 41, 340), (SX0 + 41, 340), (SX0 - 41, 396), (SX0 + 41, 396)]
c = box(SX0 - 48, SX0 + 48, -63, 20, 331, 405).cut(cyl('z', 32.5, 331, 405, SX0, SY)).cut(box(SX0 - 1, SX0 + 1, -63, SY, 331, 405))
for zz in (355, 381): c = c.cut(cyl('x', 3, SX0 - 48, SX0 + 30, -57, zz)).cut(cyl('x', 5.5, SX0 + 30, SX0 + 48, -57, zz))
for x, zz in CB: c = c.cut(cyl('y', 3, 6, 20, x, zz))      # v14: M6 tap depth 14 in the rear face (bolts from the module-plate back)
DW = [(SX0 - 41, 368), (SX0 + 41, 368)]                       # 2 dowels clamp -> module plate: offsets / tram repeat after removal
for x, zz in DW: c = c.cut(cyl('y', 3, 10, 20, x, zz))
O('Spindle_clamp').Shape = c
for k, (x, zz) in enumerate(CB, 1):
    O('Spindle_clamp_bolt_%d' % k).Shape = fuse(cyl('y', 5, 28, 31.5, x, zz), cyl('y', 3, 8, 28, x, zz))
    spec('Spindle_clamp_bolt_%d' % k, 'M6x20 low-head (DIN 7984) from the module-plate back (c-bore D11 x 4) into the clamp rear face (tap M6 depth 14, '
         '12 engaged); the probe slide covers the clamp front, the module is assembled on the bench')
spec('Spindle_clamp', '6061 clamp block 96x83x74: bore D65 H7 at (x%+.1f, y-20), rear wall 7.5, front split with 2 M6 pinch screws (heads on the right '
     'face); bolted to the module plate with 4 M6x20 from the plate back (M6 tap depth 14 in the rear face), located by 2 dowels D6 (H7 / m6) at '
     '(x%+.1f / %+.1f, z 368); spindle plug faces +X (right, above the clamp). Front face left of the split: 2 x M4 tap depth 11 for the probe slide' % (SX0, SX0 - 41, SX0 + 41))
# module plate: v12 back plate (156 wide, z 319..500) + a wide lower band (216 wide, z 288..465) for the camera and probe brackets
SB = (0, 366)                                                 # pivot (RBPB8 in the Z slide, unchanged)
BOLTS = [(-75, 300), (75, 300), (-45, 490), (45, 490)]        # shim bolts 190 apart in z; bottom pair outside the camera and the spindle (front access)
SCREWS = [('TC', 0, 490), ('BL', -80, 320), ('BR', 80, 320)]    # differential face screws: outside the camera and below / beside the spindle clamp
CAMB = [(CX + 9, 315), (CX + 21, 315)]                        # camera bracket base: 2 x M5 low-head from the plate back (upper row of the block)
pl = fuse(box(-58, 58, 20, 32, 288, 500), box(-88, 88, 20, 32, 288, 405))   # v14: narrowed with the Z slide (upper +-58 for the roll blocks, lower +-88)
for x, zz in BOLTS: pl = pl.cut(cyl('y', 3.5, 20, 32, x, zz))
for _, x, zz in SCREWS: pl = pl.cut(cyl('y', 4, 20, 32, x, zz))
for x, zz in CB: pl = pl.cut(cyl('y', 3.3, 20, 32, x, zz)).cut(cyl('y', 5.5, 28, 32, x, zz))   # clamp bolts from the back
for x, zz in CAMB: pl = pl.cut(cyl('y', 2.75, 20, 28, x, zz)).cut(cyl('y', 5, 28, 32, x, zz))
pl = pl.cut(cyl('y', 3, 20, 32, *SB))
for x, zz in DW: pl = pl.cut(cyl('y', 3, 20, 30, x, zz))
O('Spindle_mount_plate').Shape = pl
spec('Spindle_mount_plate', 'tool-head module plate, flat steel t12 (116 wide z 288..500 + 176 wide z 288..405), not ground (no guide face; owner: only the Y slide table is ground on both faces), all holes from '
     'the front except 6 counterbores on the back: M6 tap for the pivot stud, 4 shim-bolt holes, 3 differential-screw taps, 4 M6 taps for the '
     'clamp block (from the back, c-bored) + 2 dowel holes D6 H7, 2 x M5 low-head holes (counterbored from the back) for the camera bracket. Stands 2 mm off the '
     'slide on 4 shim packs at z 305 / 490 (185 apart)')
for k, (x, zz) in enumerate(BOLTS, 1):
    o = O('Spindle_shim_%d' % k)
    o.Shape = box(x - 11, x + 11, 32, 34, zz - 8, zz + 8).cut(box(x - 3.5, x + 3.5, 32, 34, zz - 8, zz)).cut(cyl('y', 3.5, 32, 34, x, zz))
    O('Spindle_bolt_%d' % k).Shape = fuse(cyl('y', 5, 14, 20, x, zz), cyl('y', 3, 20, 46, x, zz))
z = O('Z_slide_plate')                                        # move the shim-bolt taps: fill the v12 ones, tap the new ones; 30 longer at the bottom
z.Shape = fuse(z.Shape, box(-110, 110, 34, 62, 287, 317))
prop(z, 'Spec', z.Spec + '; v13: 30 longer at the bottom (z 287..547 at home) for the lower shim bolts')
z.Shape = fuse(z.Shape, *[cyl('y', 3, 34, 46, x, zz) for x in (-63, 63) for zz in (420, 455)])
# v14 (owner): Z axis narrowed with the trimmed nut housing: Z rails +-80 -> +-60, Z slide 220 -> 180 (plain band 38..58 removed), the parts on
# it move in by 20: Z blocks + bolts, spacers, spindle roll blocks / screws / bolts (they push the narrower upper module plate, +-58)
ZD = 20.0
shrink('Z_slide_plate', 38, ZD)
for o in [o for o in doc.Objects if o.TypeId == 'Part::Feature' and o.Label.startswith(('Z_block', 'Z_spacer', 'Spindle_roll_block', 'Spindle_roll_screw'))]:
    inward(o.Label, ZD)
for x, zz in BOLTS: hole('Z_slide_plate', cyl('y', 3, 34, 46, x, zz))
for k, (x, zz) in enumerate(DW, 1):
    add('Spindle_clamp_dowel_%d' % k, cyl('y', 3, 10, 30, x, zz), G, 'dowel D6 m6x20 (ISO 8734): spindle clamp to module plate', 'z', 'pins')
for nm, x, zz in SCREWS:
    O('Spindle_face_screw_' + nm).Shape = fuse(cyl('y', 4, 14, 34, x, zz), cyl('y', 6.5, 14, 20, x, zz))
spec('Spindle_face_screw_BL', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate, tip on the slide face, outside the '
     'camera: the three set the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')
spec('Spindle_face_screw_BR', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate, tip on the slide face, outside the '
     'spindle clamp: the three set the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')
spec('Spindle_face_screw_TC', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate top, tip on the slide face: '
     'with BL / BR sets the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')
spec('Z_face_screw_B', 'differential push screw (M8x0.75 outer / M6x0.5 inner = 0.25 mm/rev) at the bottom centre, 230 below the bearing: with the '
     'two top screws it holds the Y gap; top pair vs this one = nod about X. 10 deg = 30 urad')
spec('Yaw_push_screw', 'M6x0.75 push screw + jam nut: 10 deg = 30 urad (lever about 702, v14 gantry 65 wider than v12)')
spec('X_roll_jack', 'M8x0.75 jack + jam nut under the right end of the X plate: 10 deg = 30 urad (lever 705, v14 gantry 65 wider than v12)')

# Z nut housing (owner, v14): trimmed to the nut flange outline (52 x 45.6, the v12 wings x+-44 removed); 4 x M6 from the slide front now go
# into the housing front face at x +-19 (inside the nut pocket), clear of the nut bore (D28.2) and of the 6 flange taps (PCD 38, from the top)
zh = O('Z_nut_housing'); zb = zh.Shape.BoundBox
FT = [((O('Z_nut_flange_bolt_%d' % k).Shape.BoundBox.XMin + O('Z_nut_flange_bolt_%d' % k).Shape.BoundBox.XMax) / 2,
       (O('Z_nut_flange_bolt_%d' % k).Shape.BoundBox.YMin + O('Z_nut_flange_bolt_%d' % k).Shape.BoundBox.YMax) / 2) for k in range(1, 7)]
zh.Shape = box(-26, 26, 56, 101.6, zb.ZMin, zb.ZMax).cut(cyl('z', 14.1, zb.ZMin, zb.ZMax, 0, 79))
for x, y in FT: hole('Z_nut_housing', cyl('z', 2.5, zb.ZMax - 10, zb.ZMax, x, y))
ZNB = [(x, z) for z in (zb.ZMin + 6, zb.ZMin + 18) for x in (-19, 19)]   # top row 1 below the flange taps (depth 10)
zs = O('Z_slide_plate'); zs.Shape = fuse(zs.Shape, *[cyl('y', 5.5, 34, 62, x, z) for x in (-36, 36) for z in (zb.ZMin + 7, zb.ZMin + 25)])   # fill the v12 holes
for x, z in ZNB:
    hole('Z_nut_housing', cyl('y', 3, 56, 76, x, z))
    cut('Z_slide_plate', cyl('y', 3.3, 38.5, 54, x, z), cyl('y', 5.5, 34, 38.5, x, z))
for k, (x, z) in enumerate(ZNB, 1):
    O('Z_nut_mount_bolt_%d' % k).Shape = fuse(cyl('y', 5, 34.5, 38.5, x, z), cyl('y', 3, 38.5, 73.5, x, z))
    spec('Z_nut_mount_bolt_%d' % k, 'M6x35 low-head (DIN 7984) from the slide front (head sunk), through the slide into the Z nut housing front face '
         '(tap M6 depth 20, 17.5 engaged); fit before the spindle plate')
spec('Z_nut_housing', 'Z nut housing (CNC, steel) 52 x 45.6 x 32 = the nut flange outline: bore D28.2 for the nut body, nut flange on its top face '
     '(6 x M5, PCD 38), front part in the slide pocket, 4 x M6 from the slide front into its front face at x+-19')

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
ar = fuse(cyl('z', 25.5, ZF - 2, ZF + 8, CX, SY), box(CX - 29.5, CX - 24, SY - 6, SY + 6, ZF - 2, ZF + 8))   # ring + port boss on the -X side (v14: the probe is in front)
ar = ar.cut(cyl('z', 22.6, ZF - 2, ZF + 8, CX, SY)).cut(cyl('z', 24.0, ZF - 2, ZF + 4, CX, SY))                # bore + air gallery
ar = ar.cut(cyl('x', 2.0, CX - 25.5, CX - 22, SY, ZF + 3))           # D4 drill below the M5 tap into the gallery
add('Camera_air_ring', ar, gl, 'lens air ring (CNC, 6061) on the D45 lens nose, 2 x M3 set screws, port boss 12 x 12 with M5 tap depth 4: clean dry air from an M5 push-in fitting blows across '
    'the front glass (keeps coolant mist and chips off); no window, WD unchanged', 'z', 'camera')
fit_, tub_, port_ = push_in('x', -1, SY, ZF + 3, CX - 29.5); hole('Camera_air_ring', port_)
add('Camera_air_fitting', fit_, gl, 'SMC KQ2H04-M5A push-in fitting (M5, tube D4) on the lens air ring, pointing -X (outside, clear of the probe)', 'z', 'camera')
add('Camera_air_tube', tub_, gl, 'polyurethane tube D4 (stub)', 'z', 'camera')
# bracket (CNC, 6061), v14: split block in two prismatic parts (made as one block, sawn, bored D45 together; 0.5 split gap for clamping):
# base on the spindle side of the lens, bolted to the module plate (2 x M5 from the plate back); cap on the outer (-X) side, 2 x M5 from the cap
# side into the base. Lens set into the base seat from the front, cap tightened from the left (no ring to thread over the lens).
RZ0, RZ1 = ZF + 60, ZF + 88
PZM = RZ0 + 8                                                   # cap screws in the lower row (plate bolts in the upper row)
YB0 = SY - 33.5                                                 # front face of base and cap
br = box(CX + 0.25, CX + 28, YB0, 20, RZ0, RZ1).cut(cyl('z', 22.55, RZ0, RZ1, CX, SY))
cp = box(CX - 31, CX - 0.25, YB0, SY + 33.5, RZ0, RZ1).cut(cyl('z', 22.55, RZ0, RZ1, CX, SY))
CPB = [SY - 27.5, SY + 27.5]                                    # cap screws along X, front and back of the bore
for y in CPB:
    cp = cp.cut(cyl('x', 2.75, CX - 31, CX - 0.25, y, PZM)); br = br.cut(cyl('x', 2.5, CX + 0.25, CX + 12, y, PZM))
add('Camera_bracket', br, gl, 'camera bracket base (CNC, 6061 block 27.75 x 73.5 x 28) on the spindle side of the lens: half seat D45 H7, bolted to the '
    'module plate with 2 x M5 low-head from the plate back (tap M5 depth 12), 2 x M5 taps for the cap', 'z', 'camera')
add('Camera_bracket_cap', cp, gl, 'camera bracket cap (CNC, 6061 block 30.75 x 67 x 28) on the outer side of the lens: half seat D45, 2 x M5 clearance; '
    'base and cap made as one block, sawn apart and bored together (split gap 0.5)', 'z', 'camera')
for i, y in enumerate(CPB, 1):
    add('Camera_cap_bolt_%d' % i, fuse(cyl('x', 4.25, CX - 36, CX - 31, y, PZM), cyl('x', 2.5, CX - 31, CX + 9, y, PZM)), gl,
        'M5x40 SHCS, cap into the bracket base (tap M5 depth 11.75, 8.75 engaged), head on the outer side (reachable from the left)', 'z', 'fasten')
for i, (x, zz) in enumerate(CAMB, 1):
    hole('Camera_bracket', cyl('y', 2.5, 8, 20, x, zz))
    add('Camera_bracket_bolt_%d' % i, fuse(cyl('y', 4.25, 28.5, 32, x, zz), cyl('y', 2.5, 8.5, 28.5, x, zz)), gl,
        'M5x20 low-head (DIN 7984) from the module plate back into the bracket base (tap M5 depth 12, tip 0.5 short); fitted on the bench before the module goes on', 'z', 'fasten')
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
# The station must stay below the spindle body (36 above the table at Z -50) and, v14, below the retracted probe ball (30 at Z -50):
# fold point 10 above the table, prism through the base onto the table, cylinder straight on the table, sliding cover. Station top 25.
MX, MY, MZ = -195.0, 228.0, TT.ZMax + 10.0                       # fold point, rear-left corner outside the 300 x 300 work area (table -248 to measure)
ZB = MZ - 10                                                    # prism bottom (on the table top, through the base)
BT = TT.ZMax + 8                                                # base top
pr = Part.Face(Part.makePolygon([V(MX - 10, MY - 10, ZB), V(MX - 10, MY - 10, ZB + 20), V(MX + 10, MY - 10, ZB), V(MX - 10, MY - 10, ZB)])).extrude(V(0, 20, 0))
add('Tool_mirror', pr, gl, 'right-angle prism 20x20x20, mirror-coated hypotenuse used from outside (front-surface mirror), glued: bottom face in the '
    'table top in the holder window, left face against the lip; folds the view +X', 'y', 'camera')
XC = MX - 22                                                     # cover cylinder axis x (outside the lip and the cover skirt)
mb = fuse(box(MX - 14, SX + 15, MY - 50, MY + 18, TT.ZMax, BT),                    # base t8 (ground bottom)
          box(XC - 16.5, XC + 16.5, MY - 83.5, MY - 77.5, TT.ZMax, TT.ZMax + 25),     # end plate t6 for the cylinder (2 x M3 tapped through)
          box(SX - 6.95, SX + 6.95, MY - 50, MY + 18, TT.ZMax - 4, TT.ZMax),        # tenon key in the 14 mm slot neck
          box(MX - 14, MX - 10, MY - 12, MY + 12, BT, BT + 9))                       # lip: the prism's left face leans on it
mb = mb.cut(box(XC - 16.5, XC + 16.5, MY - 77.5, MY - 19.5, TT.ZMax, BT))           # cylinder pocket (the cylinder stands on the table)
ZCY = TT.ZMax + 12.5                                            # cylinder axis: body square 25 on the table top
CYH = [(XC - 7.78, ZCY + 7.78), (XC + 7.78, ZCY - 7.78)]   # CDQ2B12 through-holes on the body diagonal (M 22)
for x_, z_ in CYH: mb = mb.cut(cyl('y', 1.5, MY - 83.5, MY - 77.5, x_, z_))           # 2 x M3 tapped through the end plate (t6)
mb = mb.cut(box(MX - 10, MX + 10, MY - 10, MY + 10, ZB, BT))                         # prism window through the base
MBB = [(SX, MY - 16), (SX, MY - 44)]                             # 2 x M6 low-head + T-nut, heads flush, off the beam band
mb = mb.cut(box(MX + 10, SX, MY - 9, MY + 9, TT.ZMax, BT))   # window under the across beam, through the base (fold 10, FOV 16.8 high: beam bottom 1.6 above the table)
for x, y in MBB: mb = mb.cut(cyl('z', 3.3, TT.ZMax - 4, BT, x, y)).cut(cyl('z', 5.5, BT - 4, BT, x, y))
add('Mirror_bracket', mb, gl, 'prism holder (CNC, steel t8, base ground): on the table T-slot x -130 at the rear-left corner (tenon key 14 h7, 2 x M6 low-head '
    '+ T-nut, heads flush), prism centre x -195; window through the base (prism glued on the table top) and the left lip locate the 20 mm prism, a slot 18 wide through the base under the light path to the tool; station top 25 above the table', 'y', 'camera')
for k, (x, y) in enumerate(MBB, 1):
    add('Mirror_bracket_bolt_%d' % k, fuse(cyl('z', 5, BT - 4, BT, x, y), cyl('z', 3, TT.ZMax - 14, BT - 4, x, y)), gl,
        'M6x20 low-head (DIN 7984) + T-nut (DIN 508, slot 14) into the table T-slot', 'y', 'fasten')
CZ = BT + 16.5                                                  # cover lid top 24.5 (the cylinder top, 25, is the station top)
cv = fuse(box(MX - 16, MX + 14, MY - 16, MY + 12, CZ - 2.5, CZ), box(MX - 16, MX - 14, MY - 16, MY + 12, BT + 9.5, CZ),
          box(MX + 12, MX + 14, MY - 16, MY + 12, BT + 2, CZ), box(XC - 4, MX - 16, MY - 16, MY - 12, BT, CZ))   # + side arm to the rod
add('Mirror_cover', cv, gl, 'prism cover (SUS t2, bent: lid + skirts on both X sides, side arm to the cylinder rod), drawn closed: keeps coolant and '
    'chips off the coated hypotenuse (top and +X); slides 30 toward +Y, clear of the light path, only during tool setting', 'y', 'camera')
cq = Part.read(os.path.join(ROOT, 'vendor', 'smc', 'CDQ2B12-30DZ', 'CDQ2B12-30DZ.stp'))   # axis z, body z -29..29, rod end +z, ports on +x
cq.rotate(V(0, 0, 0), V(0, 0, 1), 180); cq.rotate(V(0, 0, 0), V(1, 0, 0), -90)          # -> rod toward +Y, ports on the -X face
cq.translate(V(XC, MY - 48.5, ZCY))
add('Mirror_cover_actuator', cq, gl,
    'SMC CDQ2B12-30DZ compact cylinder bore 12 stroke 30 with magnet, vendor STEP (catalog p.787: square 25, body 58 = B 28 + stroke, rod D6 '
    'protrudes 3.5, M3 internal thread depth 6, 2 x D3.5 through-holes with D6.5 c-bores both ends on the diagonal (M 22), ports M5 at 11 from '
    'the rod end / 6.5 from the head end); body on the table top, head end on the holder end plate (2 x M3 through the body), rod on the cover arm, ports on the outer '
    '(-X) face; auto switch D-M9 = cover open; air via the Y drag chain', 'y', 'camera')
for k, (x_, z_) in enumerate(CYH, 1):
    add('Mirror_cover_cyl_bolt_%d' % k, fuse(cyl('y', 2.75, MY - 23, MY - 20, x_, z_), cyl('y', 1.5, MY - 83, MY - 23, x_, z_)), gl,
        'M3x60 SHCS through the cylinder (head in the rod-end c-bore) into the holder end plate (M3 tapped through t6, 6 engaged)', 'y', 'fasten')
for k, yy in enumerate((MY - 77.5 + 6.5, MY - 19.5 - 11), 1):   # ports in the vendor STEP (M5, 5.5 deep)
    fit_, tub_, port_ = push_in('x', -1, yy, ZCY, XC - 12.5)
    add('Mirror_cover_fitting_%d' % k, fit_, gl, 'SMC KQ2H04-M5A push-in fitting (M5, tube D4) on the cover cylinder port (outer face), vendor STEP', 'y', 'camera')
    add('Mirror_cover_tube_%d' % k, tub_, gl, 'polyurethane tube D4 (stub; to the Y drag chain)', 'y', 'camera')
MEAS = (MX - CX, SY - MY, MZ - TIP)                               # carriage dx, table dy, dz at the measuring pose
LOG.append('CAMERA (%.1f, %.0f), lens front z %.1f, tip %.1f, prism fold (%.0f, %.0f, %.0f), air path %.1f; measure at X %+.1f, table %+.0f, Z %+.0f'
           % (CX, SY, ZF, TIP, MX, MY, MZ, (ZF - TIP) + (SX0 - CX), *MEAS))

# ---------------------------------------------------------------- probe (MXH10 bolted straight onto the spindle clamp front, left of the split)
# v14: the slide's side face sits on the clamp front face (2 x M4 through the body, the two holes of one row, 60 apart). The probe hangs from
# two flat parts (owner, inverted T): a plate under the rod-end plate (its 4 x M4 front-mounting taps) and a stem below it with the shank clamp;
# the probe force goes straight along the stroke into the rod-end plate. Table top toward -X (camera side), probe between camera and spindle in X. Built in the v13 frame (slide width along Y, mounting face y 12, table top x 48.5 facing -X), then moved
# DXP / DYP onto the clamp front (no mirror). Heights: retracted ball 6 below the spindle body bottom (tool tip + 35), extended (stroke 60)
# 25 below the tool tip; the slide sits where its holes land on the 74 high clamp face, the plate bridges the height.
gp = '12 Probe'
STROKE = 60.0
DXP, DYP = -68.0, None                                          # v13 frame -> machine: x - 68 (table top 48.5 -> -19.5), y onto the clamp front
CF = O('Spindle_clamp').Shape.BoundBox                          # clamp z 331..405, front face y -63
TIPR = O('Spindle_body').Shape.BoundBox.ZMin - 6.0              # retracted ball: spindle body bottom - 6 = tool tip + 35
BB0 = TIPR + 26.0
T0 = (CF.ZMin + CF.ZMax) / 2 - 46.5                             # rod-end plate face: slide holes at T0 + 16.5 / 76.5, 4.5 inside the clamp edges
XB, XT = 48.5, 95.5                                             # table top face / body bottom face (x, v13 frame)
YS0, YS1 = -8.0, 12.0                                           # slide width along Y (mounting face y 12, v13 frame)
DYP = CF.YMin - YS1
PXV, PYV = XB + 8.5, 2.0                                        # probe axis (v13 frame): stem centre, between the table edge and the first plate-bolt row
pb = fuse(cyl('z', 16.5, BB0, BB0 + 21, PXV, PYV), cyl('z', 3.0, BB0 + 21, BB0 + 41, PXV, PYV), cyl('z', 2.5, BB0 - 4, BB0, PXV, PYV),
          cyl('z', 0.75, TIPR + 1, BB0 - 4, PXV, PYV), Part.makeSphere(1.0, V(PXV, PYV, TIPR + 1)))
add('Probe_body', pb, gp, 'touch probe XUNKUANER (Amazon ASIN B0FWXWX7CT): shank D6x20, body D33x21, stylus 26 / ball D2, DC 5-24 V, NPN NO, to the grblHAL probe input '
    '(two-pass probing; NO cannot detect a broken wire: use an NC version if available, else check the input before each cycle). Not to the MR-J4: its MSD latch needs point-table mode, which cannot take the pulse train. '
    'Ball retracted 6 below the spindle body bottom (tool tip + 35, still 13 above the ER11 nut), extended 25 below the tool tip', 'z', 'probe')
MXH = Part.read(os.path.join(ROOT, 'vendor', 'smc', 'MXH10-60Z', 'MXH10-60Z.step')).Solids   # body, table; table top x -30.5, body bottom x 16.5,
for so in MXH:                                                  # rod-end plate face z 59, head end z -47.5 -> x + 79, y 2 - y, z T0 + 59 - z
    so.rotate(V(0, 0, 0), V(1, 0, 0), 180); so.translate(V(79, 2, T0 + 59))
mxb, mxt = MXH
ZB0, ZB1 = T0 + 11.5, T0 + 106.5                                 # body (fixed)
SLB = [(XT - 28, T0 + 16.5), (XT - 28, T0 + 76.5)]              # 2 body through-taps of one row, 60 apart, used as through holes for M4
EPH = [(XB + 21.5, 2 - 5.5), (XB + 21.5, 2 + 5.5), (XB + 39.5, 2 - 5.5), (XB + 39.5, 2 + 5.5)]   # rod-end plate M4 taps (rows from the table side)
for x, y in EPH: mxt = mxt.cut(cyl('z', 2.0, T0, T0 + 7.3, x, y))  # to nominal
add('Probe_slide_body', mxb, gp,
    'SMC MXH10-60Z-M9NW compact slide, bore 10, stroke 60, vendor STEP (catalog MXH p.31: section 20 x 47, body 95, overall 106.5 retracted, '
    'table 99 x 19); side face bolted straight onto the spindle clamp front, left of the split (2 x M4 through the body, one row, 60 apart), '
    'table toward -X, ports up; extended = end of stroke (rubber bumper), the probe height is set in the stem clamp; 5/2 single-solenoid valve, '
    'spring return = retract on power loss', 'z', 'probe')
add('Probe_slide_table', mxt, gp,
    'SMC MXH10-60Z table + rod-end plate (part of the slide, vendor STEP; moves 60 down to extend the probe); the probe plate under the rod-end plate (4 x M4)', 'z', 'probe')
for k, zz in enumerate((ZB1 - 32, ZB1 - 14), 1):
    add('Probe_reed_%d' % k, box(XT - 25.5, XT - 7.5, YS0 - 2.5, YS0, zz - 6, zz + 6), gp,
        ('auto switch D-M9NW (retracted): spindle enable + feed hold interlock' if k == 2 else 'auto switch D-M9NW (extended)'), 'z', 'probe')
    fit_, tub_, port_ = push_in('z', 1, (XT - 6.5, XT - 26.5)[k - 1], 2.0, ZB1); cut('Probe_slide_body', port_)
    add('Probe_air_fitting_%d' % k, fit_, gp, 'SMC KQ2H04-M5A push-in fitting (M5, tube D4) on the MXH head-end port (catalog: 6.5 / 26.5 from the body bottom), vendor STEP', 'z', 'probe')
    add('Probe_air_tube_%d' % k, tub_, gp, 'polyurethane tube D4 (stub; routed up to the Z drag chain)', 'z', 'probe')
for k_, (x, zz) in enumerate(SLB, 1):                           # head in the slide's front c-bore (D7.5 x 4.4), through the body, into the clamp
    add('Probe_slide_bolt_%d' % k_, fuse(cyl('y', 3.5, YS0 + 1.6, YS0 + 4.4, x, zz), cyl('y', 2.0, YS0 + 4.4, YS0 + 29.4, x, zz)), gp,
        'M4x25 low-head (DIN 7984) through the MXH10 body (head in the 4.4 c-bore, shank through the D4.2 pilot of the M5 tap) into the '
        'spindle clamp front (tap M4 depth 11, 9.4 engaged); fitted on the bench', 'z', 'fasten')
# probe holder in two flat parts: plate 6061 t10 46 x 19 under the rod-end plate + stem 6061 15 x 19 below it with the split shank clamp
PZ0 = T0 - 10                                                    # plate bottom
SX0_, SX1_ = XB + 1, XB + 16                                     # stem x (v13 frame), clear of the first plate-bolt row (XB + 21.5)
CZ0 = BB0 + 28                                                   # stem bottom: shank 13 deep in its clamp
hd = box(XB, XB + 46, PYV - 9.5, PYV + 9.5, PZ0, T0)
STB = [(PXV, PYV - 5.5), (PXV, PYV + 5.5)]                       # 2 x M4 from the plate top into the stem (fitted before the plate goes on)
for x, y in EPH: hd = hd.cut(cyl('z', 3.75, PZ0, PZ0 + 4.5, x, y)).cut(cyl('z', 2.25, PZ0 + 4.5, T0, x, y))
for x, y in STB: hd = hd.cut(cyl('z', 3.75, T0 - 4.5, T0, x, y)).cut(cyl('z', 2.25, PZ0, T0 - 4.5, x, y))
add('Probe_holder', hd, gp, 'probe plate (CNC, 6061 t10, 46 x 19) under the MXH10 rod-end plate (front mounting face, 4 x M4x12 from below, heads in '
    '4.5 c-bores); 2 x M4 c-bored from its top hold the stem', 'z', 'probe')
st = box(SX0_, SX1_, PYV - 9.5, PYV + 9.5, CZ0, PZ0)
st = st.cut(cyl('z', 3.0, CZ0, CZ0 + 20, PXV, PYV)).cut(box(PXV - 0.5, PXV + 0.5, PYV - 9.5, PYV, CZ0, CZ0 + 20))   # D6 H7 bore + slit (front half)
PZ7 = CZ0 + 6.5                                                  # pinch screw: middle of the 13 clamped shank length
st = st.cut(cyl('x', 2.25, SX0_, PXV - 0.5, PYV - 5.5, PZ7)).cut(cyl('x', 2.0, PXV + 0.5, SX1_, PYV - 5.5, PZ7))
for x, y in STB: st = st.cut(cyl('z', 2.0, PZ0 - 9, PZ0, x, y))
add('Probe_stem', st, gp, 'probe stem (CNC, 6061 flat 15 x 19, %.0f long) under the probe plate (2 x M4 tap depth 9 in its top), split D6 H7 bore in '
    'its bottom 20 for the shank (M4 pinch from the camera side): the probe height is set here' % (PZ0 - CZ0), 'z', 'probe')
add('Probe_pinch_bolt', fuse(cyl('x', 3.5, SX0_ - 4, SX0_, PYV - 5.5, PZ7), cyl('x', 2.0, SX0_, PXV + 6, PYV - 5.5, PZ7)), gp,
    'M4x14 SHCS, shank clamp (head on the camera side, reachable from the front-left)', 'z', 'fasten')
for i_, (x, y) in enumerate(EPH, 1):
    add('Probe_holder_bolt_%d' % i_, fuse(cyl('z', 3.5, PZ0 + 0.5, PZ0 + 4.5, x, y), cyl('z', 2.0, PZ0 + 4.5, T0 + 6.5, x, y)), gp,
        'M4x12 SHCS from below, probe plate into the MXH10 rod-end plate (tap M4 depth 7.5, 6.5 engaged)', 'z', 'fasten')
for i_, (x, y) in enumerate(STB, 1):
    add('Probe_stem_bolt_%d' % i_, fuse(cyl('z', 3.5, T0 - 4.5, T0 - 0.5, x, y), cyl('z', 2.0, PZ0 - 6.5, T0 - 4.5, x, y)), gp,
        'M4x12 SHCS from the plate top into the stem (tap depth 9, 6.5 engaged), head 0.5 under the plate top', 'z', 'fasten')
ZBK = T0
for o in GROUPS[gp].Group:                                      # move onto the clamp front (no mirror)
    s_ = o.Shape.copy(); s_.translate(V(DXP, DYP, 0)); o.Shape = s_
for x, zz in SLB: hole('Spindle_clamp', cyl('y', 2.0, CF.YMin, CF.YMin + 11, x + DXP, zz))   # M4 taps in the clamp front wall
PX, PY = PXV + DXP, PYV + DYP
LOG.append('PROBE (%.1f, %.0f) on an air slide bolted to the spindle clamp front, ball retracted z %.1f (tool tip %+.0f), extended z %.1f (tool tip %+.0f), '
           'stroke %.0f, stem %.0f long, slide holes z %.1f / %.1f on the clamp z %.0f..%.0f'
           % (PX, PY, TIPR, TIPR - TIP, TIPR - STROKE, TIPR - STROKE - TIP, STROKE, PZ0 - CZ0, T0 + 16.5, T0 + 76.5, CF.ZMin, CF.ZMax))
LOG.append('SPINDLE x %.1f, camera %.1f (D %.0f), probe (%.1f, %.0f); X travel +-%.1f: spindle reach %.1f..%.1f, camera %.1f..%.1f, probe %.1f..%.1f; '
           'probe needs table %+.0f..%+.0f (travel +150..-250)'
           % (SX0, CX, SX0 - CX, PX, PY, 150 + W, SX0 - 150 - W, SX0 + 150 + W, CX - 150 - W, CX + 150 + W, PX - 150 - W, PX + 150 + W,
              PY - (-170), PY - 130))

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

# v14: Z plate (X_carriage_plate) 240 -> 200 (plain band 56..76 removed); rails, rail bolts, datum pins, side screws, clamp bolts, epoxy pads,
# top face screws and the roll blocks on the saddle ears move in by 20; pin holes re-cut, saddle taps for clamp / roll-block bolts moved
shrink('X_carriage_plate', 56, ZD)
sd = O('X_saddle_plate'); sb0 = sd.Shape
old = [o.Shape.copy() for o in doc.Objects if o.TypeId == 'Part::Feature' and o.Label.startswith(('Z_clamp_bolt', 'Z_roll_block_bolt'))]
sd.Shape = fuse(sd.Shape, *[sh.common(box(-200, 200, 122, 134, 0, 900)) for sh in old if sh.common(box(-200, 200, 122, 134, 0, 900)).Volume > 0])   # fill the old taps
for o in [o for o in doc.Objects if o.TypeId == 'Part::Feature' and o.Label.startswith(('Z_rail', 'Z_ref_pin', 'Z_ecc_pin', 'Z_side_screw', 'Z_clamp_bolt',
          'Z_epoxy_pad', 'Z_face_screw_L', 'Z_face_screw_R', 'Z_roll_block', 'Z_roll_screw'))]:
    inward(o.Label, ZD)
for o in [o for o in doc.Objects if o.TypeId == 'Part::Feature' and o.Label.startswith(('Z_ref_pin', 'Z_ecc_pin'))]:
    cut('X_carriage_plate', o.Shape)                            # datum-pin holes at the new rail positions
for o in [o for o in doc.Objects if o.TypeId == 'Part::Feature' and o.Label.startswith(('Z_clamp_bolt', 'Z_roll_block_bolt'))]:
    t_ = o.Shape.common(box(-200, 200, 122, 134, 0, 900))
    if t_.Volume > 0: cut('X_saddle_plate', t_)                 # taps at the new positions
spec('X_carriage_plate', O('X_carriage_plate').Spec.replace('240x488', '200x488') + '; v14: 40 narrower (Z rails +-60)')
spec('Z_slide_plate', O('Z_slide_plate').Spec + '; v14: 180 wide (Z rails +-60, nut housing trimmed to the flange)')
LOG.append('Z axis narrowed: rails x %.1f..%.1f, slide x %.1f..%.1f, Z plate x %.1f..%.1f, module plate x %.1f..%.1f'
           % (O('Z_rail_R').Shape.BoundBox.XMin, O('Z_rail_R').Shape.BoundBox.XMax, O('Z_slide_plate').Shape.BoundBox.XMin, O('Z_slide_plate').Shape.BoundBox.XMax,
              O('X_carriage_plate').Shape.BoundBox.XMin, O('X_carriage_plate').Shape.BoundBox.XMax,
              O('Spindle_mount_plate').Shape.BoundBox.XMin, O('Spindle_mount_plate').Shape.BoundBox.XMax))

# v14: column-top electrical box (owner 2026-11-26: all electrics in a box on the gantry columns, parts facing down; the box and its
# contents are drawn by the electrical session, column_box/column_box.step, and checked by 24). The old back plate (20_panel) is
# removed. Mechanical side: the box top plate, SPHC t3 bent, sitting on 1 mm shims on the two column tops (1 mm clear of the X base
# plate top edge, so the rail plate carries nothing), covering the gap over the X drive and the whole box; the box (assembled and
# wired on the bench) hangs under it on 20 x M5 countersunk screws into rivet nuts in its mounting plate. The X conduit loop rolls on it.
for o in list(GROUPS['07 Electrics'].Group): doc.removeObject(o.Name)
TP, ZP0 = 3.0, 491.0; ZP1 = ZP0 + TP                         # plate z 491..494 (column tops z 490 + shim 1)
XE, YF, YR, FL = 392.5, 2.0, 500.0, 20.0                     # outer x, front (column front), rear (box back wall), flange depth
COLB = [(sx * x, y) for sx in (-1, 1) for x in (332.5, 372.5) for y in (22.0, 142.0)]   # column end taps (as the foot bolts, v12)
HANG = ([(x, 272.0) for x in (-350, -250, -150, -50, 50, 150, 250, 350)]   # front row y 272: clear of the L-plate bend (electrical session)
 + [(x, 490.0) for x in (-350, -250, -150, -50, 50, 100, 250, 350)]
        + [(sx * 376.0, y) for sx in (-1, 1) for y in (365.0, 435.0)])   # rear x 100: clear of the exhaust louvre; sides between the box roof DIN rails
GLAND_X = (0.0, 390.0, 45.0)                                 # X conduit cables drop through the plate here (adaptor on a tab at x 47..50), hole D45
pl = box(-XE, XE, YF, YR, ZP0, ZP1).cut(box(-312.5, 312.5, YF - 1, 162.0, ZP0 - 1, ZP1 + 1))   # open between the columns: X carriage
pl = pl.fuse(box(-XE, XE, YR, YR + TP, ZP1 - FL, ZP1))       # rear flange, outside the box back wall
for sx in (-1, 1): pl = pl.fuse(box(XE - TP, XE, 185.0, YR + TP, ZP1 - FL, ZP1) if sx > 0 else box(-XE, -XE + TP, 185.0, YR + TP, ZP1 - FL, ZP1))
pl = pl.cut(box(120.0, 220.0, YR - 1, YR + TP + 1, ZP1 - FL - 1, ZP0))   # rear flange notch: box exhaust louvre (x 125..215, z 460..485)
pl = pl.cut(Part.makeCylinder(GLAND_X[2] / 2, 10, V(GLAND_X[0], GLAND_X[1], ZP0 - 3)))
for x, y in COLB: pl = pl.cut(Part.makeCylinder(4.5, 10, V(x, y, ZP0 - 3)))
for x, y in HANG: pl = pl.cut(Part.makeCylinder(2.75, 10, V(x, y, ZP0 - 3))).cut(Part.makeCone(2.75, 5.25, 2.5, V(x, y, ZP1 - 2.5)))
add('Box_top_plate', pl, '07 Electrics', 'SPHC t3 laser cut + bent: 785 x 498, rear and side flanges 20 down (rear notch x 120..220 for the box exhaust); '
    'on the two column tops (8 x M8), carries the column electrical box (20 x M5 countersunk into rivet nuts) and the X conduit loop; '
    'X conduit gland hole D45 at (50, 390); open between the columns for the X carriage; PE: M5 earth stud at (-360, 480) on a spot masked from the powder coat (strap to the box PE stud)', '', 'electrics')
for sx, T in ((-1, 'L'), (1, 'R')):
    sh_ = box(312.5, 392.5, YF, 162.0, ZP0 - 1, ZP0) if sx > 0 else box(-392.5, -312.5, YF, 162.0, ZP0 - 1, ZP0)
    for x, y in COLB:
        if x * sx > 0: sh_ = sh_.cut(Part.makeCylinder(4.5, 4, V(x, y, ZP0 - 2)))
    add('Box_top_shim_%s' % T, sh_, '07 Electrics', 'stainless shim t1, 80 x 160, 4 x D9: lifts the box top plate 1 mm off the X base plate top edge', '', 'electrics')
for k, (x, y) in enumerate(COLB, 1):
    add('Box_top_bolt_%d' % k, fuse(Part.makeCylinder(4, 20, V(x, y, ZP1 - 20)), Part.makeCylinder(6.5, 8, V(x, y, ZP1))), '07 Electrics',
        'M8x20 SHCS: box top plate + shim into the column end tap (M8, 20 deep; engagement 16 = 2d)', '', 'electrics')
    cl_ = 'Gantry_column_' + ('L' if x < 0 else 'R'); th_ = Part.makeCylinder(4.0, 20, V(x, y, 470.0)).cut(Part.makeCylinder(3.4, 20, V(x, y, 470.0)))
    CHK.append((cl_ + ' M8 tap in screw port', th_.common(O(cl_).Shape).Volume / th_.Volume))   # the extrusion screw port is the tap core (D6.8)
    cut(cl_, Part.makeCylinder(4.0, 20, V(x, y, 470.0)))       # M8 thread (modelled at the major diameter, as the other taps)
for k, (x, y) in enumerate(HANG, 1):
    add('Box_hang_screw_%d' % k, fuse(Part.makeCone(2.5, 5.0, 2.5, V(x, y, ZP1 - 2.5)), Part.makeCylinder(2.5, 12, V(x, y, ZP1 - 12))), '07 Electrics',
        'M5x12 flat head (ISO 10642): box top plate into an M5 rivet nut in the box mounting plate (electrical session)', '', 'electrics')
LOG.append('box top plate: z %.1f..%.1f, %d column bolts, %d hang screws, X gland (%g, %g)' % (ZP0, ZP1, len(COLB), len(HANG), GLAND_X[0], GLAND_X[1]))

# v14: conduit hardware (owner: PA corrugated conduit, KSS). One continuous conduit per run, held by brackets; the conduit shapes
# themselves are drawn and checked by 22. Clamp / end-fitting envelopes are placeholders until the KSS catalog sizes are confirmed.
if '09 Conduits' not in GROUPS:
    GROUPS['09 Conduits'] = doc.addObject('App::DocumentObjectGroup', '09 Conduits'); GROUPS['09 Conduits'].Label = '09 Conduits'
GC = '09 Conduits'
TB = 3.0                                                     # bracket sheet SPHC t3
def bolts_into(part, label, pts, ax, face, sgn, L=10.0, sp='M5x10 SHCS'):   # M5 screws through a t3 bracket into tapped holes in part
    for k, p_ in enumerate(pts, 1):                          # face: the part face the bracket sits on; sgn: screw direction into the part
        d_ = V(*[sgn if a == ax else 0 for a in 'xyz'])
        c_ = V(*[face if a == ax else p_['xyz'.index(a)] for a in 'xyz'])
        sh_ = fuse(Part.makeCylinder(2.5, L, c_ - d_ * TB, d_), Part.makeCylinder(4.25, 5, c_ - d_ * (TB + 5), d_))
        add('%s_bolt_%d' % (label, k), sh_, GC, sp + ' into ' + part + ' (M5 tapped 12 deep)', O(label).Motion, '')
        hole(part, Part.makeCylinder(2.1, 12, c_, d_))      # tap drill D4.2 x 12 checked in material
        cut(part, Part.makeCylinder(2.5, 12, c_, d_))       # thread at the major diameter
# KSS PAQ easy-type conduit adaptors (vendor/kss, catalog p.152): PG thread through the sheet with a locknut, body on the conduit side.
# Thread OD and sheet hole from the catalog; body length (1.2 x thread OD) and diameter are estimated (the page gives no body size).
PAQ = {'PA-17': ('PAQ-1716', 'PG16', 22.5, 0.2, 21.2), 'PA-23': ('PAQ-2321', 'PG21', 28.3, 0.3, 28.5),
       'PA-29': ('PAQ-2929', 'PG29', 37.0, 0.3, 34.5), 'PA-36': ('PAQ-3636', 'PG36', 47.0, 0.3, 42.5)}
def paq_hole(size): return (PAQ[size][2] + PAQ[size][3]) / 2                     # sheet hole radius
def paq_len(size): return 1.2 * PAQ[size][2]                                    # body length: the conduit starts this far from the sheet
def paq(label, size, c, d, motion, group=None):
    pn, pg, t_, _, cd = PAQ[size]; c = V(*c); d = V(*d); rb = max(t_ / 2 + 5, cd / 2 + 4)
    sh = fuse(Part.makeCylinder(rb, paq_len(size), c, d), Part.makeCylinder(t_ / 2, TB + 6, c - d * (TB + 6), d),
              Part.makeCylinder(t_ / 2 + 5, 6, c - d * (TB + 6), d)).cut(Part.makeCylinder(cd / 2 + 0.5, paq_len(size) + 20, c - d * 10, d))
    add(label, sh, group or GC, 'KSS %s easy-type conduit adaptor (%s, NYLON 66, with locknut) for %s; sheet hole D%.1f (catalog); body size estimated'
        % (pn, pg, size, 2 * paq_hole(size)), motion, '')
# Y run: bracket on the Y motor block top (moves with the table), arm back over the motor to the conduit end at (0, 395), z 188
YA = 200.0 - paq_len('PA-23')                                  # arm top: the adaptor body ends at the conduit end z 200
yb = fuse(box(-40, 40, 265.0, 279.5, 110.0, 110.0 + TB), box(-25, 25, 279.5 - TB, 279.5, 110.0, YA), box(-25, 25, 279.5 - TB, 412.0, YA - TB, YA),
          box(-25, -25 + TB, 290.0, 412.0, YA - 18, YA), box(25 - TB, 25, 290.0, 412.0, YA - 18, YA))   # foot, web, arm with side flanges
yb = yb.cut(Part.makeCylinder(paq_hole('PA-23'), 10, V(0, 395, YA - 8))).cut(Part.makeCylinder(2.75, 10, V(-30, 272, 105))).cut(Part.makeCylinder(2.75, 10, V(30, 272, 105)))
add('Conduit_Y_bracket', yb, GC, 'SPHC t3 bent: Y conduit end bracket on the Y motor block top (2 x M5), arm 135 back over the motor, '
    'PAQ-2321 hole D28.6 at (0, 395)', 'y', '')
bolts_into('Y_motor_block', 'Conduit_Y_bracket', [(-30, 272, 0), (30, 272, 0)], 'z', 110.0, -1)
paq('Conduit_Y_end_fitting', 'PA-23', (0, 395, YA), (0, 0, 1), 'y')
# Z run moving end: bracket on the spindle clamp front face (right half, beside the probe slide), arm at z 455 to the end at (110, -80)
HA = 470.0 - paq_len('PA-29')                                  # arm top: the adaptor body ends at the conduit end z 470
hb = fuse(box(40, 78, -63.0 - TB, -63.0, 310.0, HA), box(40, 136, -102.0, -63.0, HA - TB, HA), box(133, 136, -102.0, -63.0, HA - 18, HA))   # side flange clear of the adaptor
hb = hb.cut(Part.makeCylinder(paq_hole('PA-29'), 10, V(110, -80, HA - 8)))
for x_, z_ in ((56, 318), (56, 368), (72, 318), (72, 368)): hb = hb.cut(Part.makeCylinder(2.75, 10, V(x_, -70, z_), V(0, 1, 0)))
add('Conduit_head_bracket', hb, GC, 'SPHC t3 bent: Z conduit end bracket on the spindle clamp front face (4 x M5, right half; the probe slide is '
    'on the left half), arm to the conduit end, PAQ-2929 hole D37.3 at (110, -80)', 'z', '')
bolts_into('Spindle_clamp', 'Conduit_head_bracket', [(x_, 0, z_) for x_, z_ in ((56, 318), (56, 368), (72, 318), (72, 368))], 'y', -63.0, 1)   # x >= 56: wall to the spindle bore > 20
paq('Conduit_head_end_fitting', 'PA-29', (110, -80, HA), (0, 0, 1), 'z')
# X carriage: front bracket on the saddle ear front face (beside the Z roll block), shelf at z 697..700 with a conduit clamp at (110, 40)
cb = fuse(box(102, 118, 122.0 - TB, 122.0, 560.0, 650.0), box(102, 142, 122.0 - TB, 122.0, 640.0, 650.0), box(124, 142, 122.0 - TB, 122.0, 640.0, 700.0),
          box(90, 142, 22.0, 122.0, 697.0, 700.0))   # flange on the saddle body (x <= 120), around the Z roll block, shelf over the Z module
cb = cb.cut(Part.makeCylinder(18.0, 10, V(110, 40, 690)))
for z_ in (575, 630): cb = cb.cut(Part.makeCylinder(2.75, 10, V(110, 115, z_), V(0, 1, 0)))
add('Conduit_carriage_bracket', cb, GC, 'SPHC t3 bent: on the saddle ear front face (2 x M5, beside the Z roll block), shelf at z 697..700 over '
    'the Z module; the conduit passes down through a clamp at (110, 40) to the tool-head loop', 'x', '')
bolts_into('X_saddle_plate', 'Conduit_carriage_bracket', [(110, 0, 575), (110, 0, 630)], 'y', 122.0, 1)
add('Conduit_carriage_clamp', Part.makeCylinder(23, 14, V(110, 40, 700.0)).cut(Part.makeCylinder(17.5, 14, V(110, 40, 700.0))), GC,
    'conduit clamp for PA-29 (KSS 浪管固定座 / fixing head) on the carriage shelf - size to confirm from the KSS catalog', 'x', '')
# X carriage: rear arm on the saddle ear back face, over the X base plate and the box top plate, down to the loop's moving-leg clamp
ZT_ = 494.0 + 34.5 / 2 + 10.75                                # X loop centre height (roof adaptor body and nut clear of the plate)
ra = fuse(box(60, 118, 134.0, 134.0 + TB, 560.0, 703.0), box(45, 118, 134.0, 255.0, 700.0, 703.0), box(45, 100, 252.0, 255.0, 500.0, 703.0))
for x_, z_ in ((72, 580), (106, 580), (72, 640), (106, 640)): ra = ra.cut(Part.makeCylinder(2.75, 10, V(x_, 130, z_), V(0, 1, 0)))
add('Conduit_X_arm', ra, GC, 'SPHC t3 bent: X conduit carriage arm on the saddle ear back face (4 x M5), back over the box top plate, '
    'holds the moving leg of the rolling loop (clamp at x 60..100, y 230)', 'x', '')
bolts_into('X_saddle_plate', 'Conduit_X_arm', [(x_, 0, z_) for x_, z_ in ((72, 580), (106, 580), (72, 640), (106, 640))], 'y', 134.0, -1)
add('Conduit_X_arm_clamp', box(62, 98, 230 - 23, 252.0, ZT_ - 20, ZT_ + 23).cut(Part.makeCylinder(17.5, 40, V(60, 230, ZT_), V(1, 0, 0))), GC,
    'conduit clamp for PA-29 (KSS fixing base) on the carriage arm: moving end of the rolling loop - size to confirm', 'x', '')
# roof: 90 deg elbow connector in the box top plate gland (50, 390) and a clamp on the fixed leg
# roof: KSS has no 90 deg adaptor on the catalog page -> a bent tab on the box top plate carries a straight PAQ-2929 along +x (the fixed
# leg starts at its body end); the cables leave the adaptor toward -x and drop through the plate hole at (0, 390)
rt = fuse(box(25, 50, 365.0, 415.0, 494.0, 494.0 + TB), box(50 - TB, 50, 365.0, 415.0, 494.0, ZT_ + 30))
rt = rt.cut(Part.makeCylinder(paq_hole('PA-29'), 10, V(40, 390, ZT_), V(1, 0, 0)))
for y_ in (375.0, 405.0):
    rt = rt.cut(Part.makeCylinder(2.75, 10, V(32, y_, 490))); cut('Box_top_plate', Part.makeCylinder(2.75, 10, V(32, y_, 488)))
    add('Conduit_X_roof_tab_bolt_%d' % (1 if y_ < 390 else 2), fuse(Part.makeCylinder(2.5, 16, V(32, y_, 481.0)), Part.makeCylinder(4.25, 4, V(32, y_, 494.0 + TB))), GC,
        'M5x16 button head: roof adaptor tab through the box top plate and the L-plate flange into the nut under the flange (nut: electrical session)', '', '')
add('Conduit_X_roof_tab', rt, GC, 'SPHC t3 bent: tab on the box top plate (2 x M5) carrying the X conduit adaptor PAQ-2929 along +x, hole D37.3', '', '')
paq('Conduit_X_roof_connector', 'PA-29', (50, 390, ZT_), (1, 0, 0), '')
# Y run top end (owner 2026-11-27: the column electrical box is one open L plate, no covers): bracket on the L plate front face (y 255,
# below the X drive), shelf under the plate's lower edge holding the Y conduit end fitting at (-120, 330)
yt = fuse(box(-160, -80, 255.0 - TB, 255.0, 236.0, 281.0), box(-160, -80, 255.0 - TB, 365.0, 236.0, 239.0))
yt = yt.cut(Part.makeCylinder(paq_hole('PA-23'), 10, V(-120, 330, 230)))
for x_ in (-140, -100): yt = yt.cut(Part.makeCylinder(2.75, 10, V(x_, 250, 265), V(0, 1, 0)))
add('Conduit_Y_top_bracket', yt, GC, 'SPHC t3 bent: Y conduit top end, on the column box L-plate front face (2 x M5 + nut through the L plate, holes by the '
    'electrical session at x -140 / -100, z 265), shelf z 236..239 under the plate edge, PAQ-2321 hole D28.6 at (-120, 330)', '', '')
for k, x_ in enumerate((-140, -100), 1):
    add('Conduit_Y_top_bracket_bolt_%d' % k, fuse(Part.makeCylinder(2.5, 16, V(x_, 247.0, 265), V(0, 1, 0)), Part.makeCylinder(4.25, 5, V(x_, 247.0, 265), V(0, 1, 0)),
        Part.makeCylinder(4.6, 4, V(x_, 259.0, 265), V(0, 1, 0))), GC, 'M5x16 SHCS + nut: Y conduit top bracket through the L plate', '', '')
paq('Conduit_Y_top_fitting', 'PA-23', (-120, 330, 236.0), (0, 0, -1), '')
# feeder conduits (to the base cabinet): entry plate hung from the box top plate rear flange, outside the L plate; conduit connectors D50 / D28
fe = fuse(box(-390, -210, 503.0, 506.0, 250.0, 494.0), box(-390, -387, 506.0, 526.0, 250.0, 494.0), box(-213, -210, 506.0, 526.0, 250.0, 494.0))
fe = fe.cut(Part.makeCylinder(paq_hole('PA-36'), 10, V(-340, 500, 270), V(0, 1, 0))).cut(Part.makeCylinder(paq_hole('PA-17'), 10, V(-260, 500, 270), V(0, 1, 0)))
for kb_, x_ in enumerate((-370, -300, -230), 1):
    fe = fe.cut(Part.makeCylinder(2.75, 10, V(x_, 498, 484), V(0, 1, 0))); cut('Box_top_plate', Part.makeCylinder(2.75, 10, V(x_, 498, 484), V(0, 1, 0)))
    add('Feeder_entry_plate_bolt_%d' % kb_, fuse(Part.makeCylinder(2.5, 14, V(x_, 496.0, 484), V(0, 1, 0)), Part.makeCylinder(4.25, 4, V(x_, 496.0, 484), V(0, 1, 0)),
        Part.makeCylinder(4.6, 4, V(x_, 506.0, 484), V(0, 1, 0))), GC, 'M5x14 button head + nut: feeder entry plate to the box top plate rear flange', '', '')
add('Feeder_entry_plate', fe, GC, 'SPHC t3 bent: feeder conduit entry plate on the box top plate rear flange (3 x M5), side flanges 20; KSS conduit '
    'adaptors PAQ-3636 (power, D47.3, x -340) and PAQ-1716 (control, D22.7, x -260) at z 270', '', '')
paq('Feeder_entry_fitting_1', 'PA-36', (-340, 506.0, 270), (0, 1, 0), '')
paq('Feeder_entry_fitting_2', 'PA-17', (-260, 506.0, 270), (0, 1, 0), '')
LOG.append('conduit hardware: Y bracket, head bracket, carriage bracket + clamp, X arm + clamp, roof tab + PAQ-2929, Y top bracket, feeder entry plate (KSS PAQ adaptors per catalog p.152)')

bad = [(l, round(r, 3)) for l, r in CHK if r < 0.98]
LOG.append('HOLE_CHECK %d tools, not fully in material: %s' % (len(CHK), bad))
doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v14.FCStd'))
L = ['v14 = v12 + wider X (+65) + L-shaped tool-head module.  new parts: %d' % len(NEW)] + LOG + ['']
for l in ['Datum_base_plate', 'X_base_plate', 'X_rail_1', 'X_ballscrew', 'Gantry_column_L', 'Gantry_column_R', 'Spindle_mount_plate', 'Spindle_clamp'] + NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s %-2s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, getattr(o, 'Motion', '') or '-', b.XMin, b.XMax, b.YMin, b.YMax,
             b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v14_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(LOG))
