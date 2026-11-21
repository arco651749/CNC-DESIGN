# -*- coding: utf-8 -*-
"""v13 from v12 (frozen): tool-head module + wider X.

  1 Wider X     X travel +-150 -> +-227.5 (+155). The gantry is stretched 77.5 per side: columns, feet, yaw / X-level adjusters,
                X motor end move out; datum plate, X plate, X rails (SX2RNL28-540 -> -695, holes kept on the 60 pitch, +-270 / +-330
                added) and X screw (C-KBS1505-458 -> -613) are lengthened. Y axis, table, Z axis unchanged.
  2 Tool head   one module on the Z slide: camera, spindle, probe in one line along X (all centres at y -20).
                Spindle at x -7.5 (7.5 left of the Z centre), camera 70 left of it (x -77.5), probe 85 right of it (x +77.5):
                the module is symmetric about the Z slide and each tool still covers the 300 x 300 work area
                (spindle reach x -235..220, camera -305..150, probe -150..305).
                Module plate = the v12 spindle back plate made wider (216 at the bottom): same RBPB8 pivot, shim packs and differential
                screws, used for spindle tram ONLY; camera and probe offsets are calibrated after tramming. Shim bolts and the
                bottom face screws are moved so they stay reachable from the front (between the tools).
                Camera: lens front 40 above the tool tip (path 40 + 70 = 110 = WD), 4 above the spindle nose.
  3 Prism       folds the view +X; holder on the table T-slot x -160 at the rear-left corner (prism x -195, y +200), outside
                the work area. Tool measured at X -117.5, table -220, Z -40.
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
LOG.append('moved out: %d parts (+x %d, -x %d); static parts crossing x+-255 not handled: %s'
           % (len(moved), sum(1 for d in moved.values() if d > 0), sum(1 for d in moved.values() if d < 0), warn or 'none'))
# X rails: two more holes per side on the 60 pitch (rail ends at +-347.5, end distance 17.5), tapped into the X plate
for r, z in ((1, 250), (2, 470)):
    for x in (-330, -270, 270, 330):
        cut('X_rail_%d' % r, cyl('y', 4.5, 146, 155, x, z), cyl('y', 2.75, 155, 162, x, z))
        hole('X_base_plate', cyl('y', 2.5, 162, 171, x, z))
        add('X_rail_bolt_%d_%d' % (r, x), fuse(cyl('y', 4.25, 150, 155, x, z), cyl('y', 2.5, 155, 171, x, z)), G,
            'M5x16 SHCS in the rail counterbore, tapped 9 into the X plate', '', 'fasten')
spec('X_rail_1', 'SX2RNL28-695 rail (between the columns), holes on the 60 pitch x+-30..+-330')
spec('X_rail_2', 'SX2RNL28-695 rail (between the columns), holes on the 60 pitch x+-30..+-330')
spec('X_ballscrew', 'C-KBS1505-613: thread to the C-TEK12 face, D12x36 (bearing + lock nut) + D10x27 (coupling), fixed-free. '
     'X travel +-227.5; check the critical speed of the 613 fixed-free screw (add a free-end support if needed)')
spec('X_base_plate', 'steel t20 875x260 (z 230..490); X rails z 250 / 470 (spacing 220); X drive axis z 360 = midway between the rails. '
     'Front face stepped 1 mm down outside x+-349.5: stands 1 mm off the columns, joined by 8 epoxy pads')
spec('Datum_base_plate', 'Q235 t20 875x327 datum plate, top face ground (Y block seats): Y blocks, Y nut seat, column feet')

# ================================================================ 2. tool-head module
for gl in ('11 Camera', '12 Probe'):                          # v12 camera and probe are replaced
    for o in list(GROUPS[gl].Group): doc.removeObject(o.Name)
z = O('Z_slide_plate')                                        # fill the v12 probe-bracket taps in the Z slide
z.Shape = fuse(z.Shape, *[cyl('y', 2.5, 34, 44, x, zz) for x in (89, 101) for zz in (340, 380)])

SX0, SY = -7.5, -20.0                                         # spindle axis
CX, PX = SX0 - 70.0, SX0 + 85.0                               # camera, probe axes (-77.5, +77.5)
for l in ('Spindle_body', 'Spindle_fan_cover', 'Spindle_plug', 'Spindle_nose', 'ER11_nut', 'Tool_D5',
          'Spindle_pinch_screw_1', 'Spindle_pinch_screw_2') + tuple('Spindle_clamp_bolt_%d' % k for k in range(1, 5)):
    move(l, SX0)
TIP = O('Tool_D5').Shape.BoundBox.ZMin                         # 180 at home
# clamp block (same as v12, moved with the spindle)
CB = [(SX0 - 41, 340), (SX0 + 41, 340), (SX0 - 41, 396), (SX0 + 41, 396)]
c = box(SX0 - 48, SX0 + 48, -63, 20, 331, 405).cut(cyl('z', 32.5, 331, 405, SX0, SY)).cut(box(SX0 - 1, SX0 + 1, -63, SY, 331, 405))
for zz in (355, 381): c = c.cut(cyl('x', 3, SX0 - 48, SX0 + 30, -57, zz)).cut(cyl('x', 5.5, SX0 + 30, SX0 + 48, -57, zz))
for x, zz in CB: c = c.cut(cyl('y', 3.25, -57, 20, x, zz)).cut(cyl('y', 5.5, -63, -57, x, zz))
O('Spindle_clamp').Shape = c
spec('Spindle_clamp', '6061 clamp block 96x83x74: bore D65 H7 at (x-7.5, y-20), rear wall 7.5, front split with 2 M6 pinch screws; bolted to the '
     'module plate with 4 M6x80 from the front')
# module plate: v12 back plate (156 wide, z 319..500) + a wide lower band (216 wide, z 288..465) for the camera and probe brackets
SB = (0, 366)                                                 # pivot (RBPB8 in the Z slide, unchanged)
BOLTS = [(-50, 420), (50, 420), (-50, 455), (50, 455)]        # shim bolts: between the spindle and the camera / probe (front access)
SCREWS = [('TC', 0, 490), ('BL', -103, 330), ('BR', 103, 330)]  # differential face screws: outside the camera and the probe
CAMB = [(CX - 10, 300), (CX + 10, 300)]                       # camera bracket: 2 x M5 low-head from the plate back
PRB = [(66, 300), (89, 300), (66, 445), (89, 445)]           # probe bracket: 4 x M5 low-head from the plate back
pl = fuse(box(-78, 78, 20, 32, 319, 500), box(-108, 108, 20, 32, 288, 465))
for x, zz in BOLTS: pl = pl.cut(cyl('y', 3.5, 20, 32, x, zz))
for _, x, zz in SCREWS: pl = pl.cut(cyl('y', 4, 20, 32, x, zz))
for x, zz in CB: pl = pl.cut(cyl('y', 3, 20, 32, x, zz))
for x, zz in CAMB + PRB: pl = pl.cut(cyl('y', 2.75, 20, 28, x, zz)).cut(cyl('y', 5, 28, 32, x, zz))
pl = pl.cut(cyl('y', 3, 20, 32, *SB))
O('Spindle_mount_plate').Shape = pl
spec('Spindle_mount_plate', 'tool-head module plate, flat steel t12 (156 wide z 319..500 + 216 wide z 288..465), ground both faces, all holes from '
     'the front except 6 counterbores on the back: M6 tap for the pivot stud, 4 shim-bolt holes, 3 differential-screw taps, 4 M6 taps for the '
     'clamp block, 6 x M5 low-head holes (counterbored from the back) for the camera and probe brackets. Stands 2 mm off the slide on 4 shim packs')
for k, (x, zz) in enumerate(BOLTS, 1):
    o = O('Spindle_shim_%d' % k)
    o.Shape = box(x - 11, x + 11, 32, 34, zz - 8, zz + 8).cut(box(x - 3.5, x + 3.5, 32, 34, zz - 8, zz)).cut(cyl('y', 3.5, 32, 34, x, zz))
    O('Spindle_bolt_%d' % k).Shape = fuse(cyl('y', 5, 14, 20, x, zz), cyl('y', 3, 20, 46, x, zz))
z = O('Z_slide_plate')                                        # move the shim-bolt taps: fill the v12 ones, tap the new ones
z.Shape = fuse(z.Shape, *[cyl('y', 3, 34, 46, x, zz) for x in (-63, 63) for zz in (420, 455)])
for x, zz in BOLTS: hole('Z_slide_plate', cyl('y', 3, 34, 46, x, zz))
for nm, x, zz in SCREWS:
    O('Spindle_face_screw_' + nm).Shape = fuse(cyl('y', 4, 14, 34, x, zz), cyl('y', 6.5, 14, 20, x, zz))
spec('Spindle_face_screw_BL', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate, tip on the slide face, outside the '
     'camera: the three set the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')
spec('Spindle_face_screw_BR', 'differential push screw (M8x0.75 / M6x0.5 = 0.25 mm/rev) through the module plate, tip on the slide face, outside the '
     'probe: the three set the 2 mm gap; top vs bottom pair = nod (lever 160, 10 deg = 43 urad)')

# ---------------------------------------------------------------- camera (left)
import math
gl = '11 Camera'
ZF = TIP + (110.0 - (SX0 - CX))                               # lens front: tip + 40
def place(shape, rx180=True, rz=0.0, t=(0, 0, 0)):
    s = shape.copy()
    if rx180: s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    if rz: s.rotate(V(0, 0, 0), V(0, 0, 1), rz)
    s.translate(V(*t)); return s
lens = Part.read(os.path.join(ROOT, 'vendor', 'moritex', 'MML05-HR110D', 'MML05-HR110D.step'))  # front z+91.47, C flange z-43.64, port +Y
add('Camera_lens', place(lens, True, -90, (CX, SY, ZF + 91.47)), gl,
    'Moritex MML05-HR110D telecentric 0.5x, WD 110+-5.5, DOF 3, C-mount, coaxial light port D8 H7 toward -X (vendor STEP)', 'z', 'camera')
ZC = ZF + 91.47 + 43.64
ring5 = Part.makeCylinder(15.0, 5.026, V(0, 0, 0)).cut(Part.makeCylinder(12.7, 5.026, V(0, 0, 0)))
add('Camera_CS_C_adapter', place(ring5, False, 0, (CX, SY, ZC)), gl, 'Basler CS-mount to C-mount adapter ring 5 mm (2200002382)', 'z', 'camera')
cam = Part.read(os.path.join(ROOT, 'vendor', 'basler', 'daA2448-70uc', 'daA2448-70uc_CS_from_drawing.step'))
add('Camera_body', place(cam, True, -180, (CX, SY, ZC + 5.026)), gl,
    'Basler dart R daA2448-70uc (CS-Mount), IMX548 1/1.8" 5 MP, USB3 toward -X (outside); sensor long side along X '
    '(= along the tool axis in the folded view); model from the Basler dimension drawing', 'z', 'camera')
PZ = ZF + 91.47 - 6.55                                          # coaxial port bore centre height (vendor STEP)
add('Camera_light_guide', fuse(cyl('x', 3.98, CX - 26, CX - 10.5, SY, PZ), cyl('x', 7.0, CX - 46, CX - 20, SY, PZ),
                               cyl('x', 5.5, CX - 86, CX - 46, SY, PZ)), gl,
    'light guide (fibre) D8 ferrule pushed 8 into the coaxial port D8 H7, locked by its screw; cable to the LED light source', 'z', 'camera')
# bracket (CNC, 6061): split ring on the D22 lens tube, web back to a flange on the module plate (2 x M5 from the plate back)
RZ0, RZ1 = ZF + 106, ZF + 126
PZM = (RZ0 + RZ1) / 2
br = fuse(cyl('z', 18, RZ0, RZ1, CX, SY), box(CX - 8, CX + 8, SY - 32, SY - 16, RZ0 + 2, RZ1 - 2),       # ring + pinch lug (front)
          box(CX - 10, CX + 10, SY + 12, 8, RZ0, RZ1), box(CX - 10, CX + 10, -1, 8, 312, RZ0),         # web (above the D35 lens body)
          box(CX - 17.5, CX + 17.5, 8, 20, 288, 322))                                                   # flange on the module plate
br = br.cut(cyl('z', 11.05, RZ0, RZ1, CX, SY)).cut(box(CX - 0.5, CX + 0.5, SY - 33, SY - 10, RZ0, RZ1))
br = br.cut(cyl('x', 2.25, CX - 8, CX - 0.5, SY - 24, PZM)).cut(cyl('x', 2.0, CX + 0.5, CX + 8, SY - 24, PZM))
add('Camera_bracket', br, gl, 'camera bracket (CNC, 6061): flange on the module plate (2 x M5 low-head from the plate back), split ring D22 on the '
    'lens tube, M4 pinch screw', 'z', 'camera')
add('Camera_pinch_bolt', fuse(cyl('x', 3.5, CX - 12, CX - 8, SY - 24, PZM), cyl('x', 2.0, CX - 8, CX + 6, SY - 24, PZM)), gl,
    'M4x14 SHCS, ring pinch screw', 'z', 'fasten')
for i, (x, zz) in enumerate(CAMB, 1):
    hole('Camera_bracket', cyl('y', 2.5, 8.5, 20, x, zz))
    add('Camera_bracket_bolt_%d' % i, fuse(cyl('y', 4.25, 28.5, 32, x, zz), cyl('y', 2.5, 9, 28.5, x, zz)), gl,
        'M5x20 low-head (DIN 7984) from the module plate back into the bracket flange (tap M5); fitted on the bench before the module goes on', 'z', 'fasten')
# prism on the table (moves in Y): mirror-coated hypotenuse used from outside, folds the view +X onto the tool 70 to the right
TT = O('Work_table').Shape.BoundBox
SX = -160.0                                                     # T-slot used (left slot)
MX, MY, MZ = -195.0, 200.0, TT.ZMax + 30.0                       # fold point, rear-left corner outside the 300 x 300 work area
ZB = MZ - 10
pr = Part.Face(Part.makePolygon([V(MX - 10, MY - 10, ZB), V(MX - 10, MY - 10, ZB + 20), V(MX + 10, MY - 10, ZB), V(MX - 10, MY - 10, ZB)])).extrude(V(0, 20, 0))
add('Tool_mirror', pr, gl, 'right-angle prism 20x20x20, mirror-coated hypotenuse used from outside (front-surface mirror), glued: bottom face on '
    'the holder base, left face against the lip; folds the view +X', 'y', 'camera')
mb = fuse(box(MX - 14, SX + 15, MY - 14, MY + 14, TT.ZMax, ZB),                    # base (ground bottom), prism glued on top
          box(SX - 6.95, SX + 6.95, MY - 14, MY + 14, TT.ZMax - 4, TT.ZMax),        # tenon key in the 14 mm slot
          box(MX - 14, MX - 10, MY - 12, MY + 12, ZB, ZB + 12))                      # lip: the prism's left face leans on it
mb = mb.cut(cyl('z', 6.75, TT.ZMax - 4, ZB, SX, MY)).cut(cyl('z', 10, ZB - 12, ZB, SX, MY))
add('Mirror_bracket', mb, gl, 'prism holder (CNC, steel, base ground): on the table T-slot x -160 at the rear-left corner (tenon key 14 h7, 1 x M12 + '
    'T-nut, head flush under the reflected beam), prism centre at x -195; top face and left lip locate the glued 20 mm prism', 'y', 'camera')
add('Mirror_bracket_bolt_1', fuse(cyl('z', 9, ZB - 12, ZB, SX, MY), cyl('z', 6, TT.ZMax - 12, ZB - 12, SX, MY)), gl,
    'M12x30 SHCS + T-nut (DIN 508, slot 14) into the table T-slot', 'y', 'fasten')
MEAS = (MX - CX, SY - MY, MZ - TIP)                               # carriage dx, table dy, dz at the measuring pose
LOG.append('CAMERA (%.1f, %.0f), lens front z %.1f, tip %.1f, prism fold (%.0f, %.0f, %.0f), air path %.1f; measure at X %+.1f, table %+.0f, Z %+.0f'
           % (CX, SY, ZF, TIP, MX, MY, MZ, (ZF - TIP) + (SX0 - CX), *MEAS))

# ---------------------------------------------------------------- probe (right)
gp = '12 Probe'
STROKE = 60.0
TIPR = TIP - 10.0 + STROKE                                      # retracted ball bottom (tool tip + 50)
BB0 = TIPR + 26.0
pb = fuse(cyl('z', 16.5, BB0, BB0 + 21, PX, SY), cyl('z', 3.0, BB0 + 21, BB0 + 41, PX, SY), cyl('z', 2.5, BB0 - 4, BB0, PX, SY),
          cyl('z', 0.75, TIPR + 1, BB0 - 4, PX, SY), Part.makeSphere(1.0, V(PX, SY, TIPR + 1)))
add('Probe_body', pb, gp, 'touch probe: shank D6x20, body D33x21, stylus 26 / ball D2 (M2.5), DC5-24V NPN NO; to the servo amplifier MSD input (CN1-10)', 'z', 'probe')
ZBK = BB0 + 41 - 2                                              # guide block bottom (retracted)
SYS = -10.5                                                     # solenoid axis y
br = fuse(box(56, 95, 12, 20, 213, 460), box(56, 59.5, 3, 12, 213, 330), box(91.5, 95, 3, 12, 213, 330),   # plate + 2 ribs
          box(PX - 9, PX + 9, -4, 12, 213, 223))                                                         # hard-stop block under the rail
add('Probe_bracket', br, gp, 'probe slide bracket (CNC, 6061) t8 on the module plate (4 x M5 low-head from the plate back): rail face y12, solenoid '
    'face, hard-stop block', 'z', 'probe')
for i, (x, zz) in enumerate(PRB, 1):
    hole('Probe_bracket', cyl('y', 2.5, 12.5, 20, x, zz))
    add('Probe_bracket_bolt_%d' % i, fuse(cyl('y', 4.25, 28.5, 32, x, zz), cyl('y', 2.5, 13, 28.5, x, zz)), gp,
        'M5x16 low-head (DIN 7984) from the module plate back into the bracket (tap M5); fitted on the bench', 'z', 'fasten')
RZ0P = 228.0
RL = ZBK + 32 - RZ0P
add('Probe_rail', box(PX - 6, PX + 6, 4, 12, RZ0P, RZ0P + RL), gp, 'miniature linear guide rail, width 12, L%.0f (MISUMI miniature series), M3' % RL, 'z', 'probe')
add('Probe_block', box(PX - 13, PX + 13, -2, 10, ZBK, ZBK + 30).cut(box(PX - 6, PX + 6, 4, 12, ZBK, ZBK + 30)), gp, 'miniature linear guide block, width 26, L30', 'z', 'probe')
hd = fuse(box(PX - 14, PX + 14, -7, -2, BB0 + 25, ZBK + 34), box(PX - 17, PX + 17, SY - 18, -2, BB0 + 25, BB0 + 39),
          box(PX - 10, PX + 10, -18, 2, ZBK + 34, ZBK + 40))
hd = hd.cut(cyl('z', 3.0, BB0 + 25, BB0 + 39, PX, SY)).cut(box(PX - 0.5, PX + 0.5, SY - 18, SY, BB0 + 25, BB0 + 39))
hd = hd.cut(cyl('z', 3.0, ZBK + 34, ZBK + 40, PX, SYS))
hd = hd.cut(cyl('x', 2.25, PX - 17, PX - 0.5, SY - 10, BB0 + 32)).cut(cyl('x', 2.0, PX + 0.5, PX + 6, SY - 10, BB0 + 32))
add('Probe_holder', hd, gp, 'probe holder (CNC, 6061): on the guide block, split D6 H7 clamp for the shank (M4 pinch), M6 tap for the solenoid stud', 'z', 'probe')
add('Probe_pinch_bolt', fuse(cyl('x', 3.5, PX - 21, PX - 17, SY - 10, BB0 + 32), cyl('x', 2.0, PX - 17, PX + 6, SY - 10, BB0 + 32)), gp, 'M4x20 SHCS, shank clamp', 'z', 'fasten')
SZ0 = ZBK + 44
sol = fuse(box(PX - 20, PX + 20, 12 - 45, 12, SZ0, SZ0 + 110), cyl('z', 6, SZ0 + 110, SZ0 + 170, PX, SYS), cyl('z', 10, SZ0 + 166, SZ0 + 170, PX, SYS),
           cyl('z', 3.0, ZBK + 36, SZ0, PX, SYS))
add('Probe_solenoid', sol, gp, 'push-pull frame solenoid 40 x 45 x 110 (40 along X), stroke 60, spring end up, rear M6 stud down into the holder: '
    'off = retracted by the spring (fail-safe), on = probe down onto the hard stop; mounted 4 x M4 on the bracket', 'z', 'probe')
add('Probe_stop_screw', fuse(cyl('z', 2.5, 207, ZBK - STROKE, PX, 1), cyl('z', 4.6, 209, 213, PX, 1)), gp,
    'M5 stop screw + jam nut: sets the extended probe height (block bottom lands on it)', 'z', 'probe')
hole('Probe_bracket', cyl('z', 2.5, 213, 223, PX, 1))
LOG.append('PROBE (%.1f, %.0f), ball retracted z %.1f (tool tip %+.0f), extended z %.1f (tool tip %+.0f), stroke %.0f, rail L%.0f'
           % (PX, SY, TIPR, TIPR - TIP, TIPR - STROKE, TIPR - STROKE - TIP, STROKE, RL))
LOG.append('SPINDLE x %.1f, camera %.1f (D %.0f), probe %.1f (P %.0f); X travel +-%.1f: spindle reach %.1f..%.1f, camera %.1f..%.1f, probe %.1f..%.1f'
           % (SX0, CX, SX0 - CX, PX, PX - SX0, 150 + W, SX0 - 150 - W, SX0 + 150 + W, CX - 150 - W, CX + 150 + W, PX - 150 - W, PX + 150 + W))

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
