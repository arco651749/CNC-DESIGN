# -*- coding: utf-8 -*-
"""v14 on a coolant base, built as two assemblies:
  A  base: aluminium-extrusion frame (40x40) on 6 levelling feet, SUS304 coolant pan with silicone-sealed corners and a drain at the
     rear centre (floor slope 1:100), splash guards (sides, rear, low front lip, PC windows), 90 L tank on castors that slides out
     at the rear, 60-mesh filter basket, immersion pump, supply hose to a bulkhead at the guard top; 4 steel risers through the pan
     (sealed) carry the machine
  B  the v14 machine, unchanged except 4 mounting holes in the datum plate; 4 M12 bolts tie B to A
The table top stands about 900 mm above the floor (floor at z = -790 in machine coordinates).
Run:  freecadcmd freecad/v14/06_base_coolant_v14.py      Out: output/v14/CNC_v14_base.FCStd, output/v14/logs/v14_base_build.txt"""
import os, math
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v14')
doc = App.openDocument(os.path.join(OUT, 'CNC_v14.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
FLOOR = -790
NEW = []


def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cyl(ax, r, a0, a1, p, q):
    if ax == 'x': return Part.makeCylinder(r, a1 - a0, V(a0, p, q), V(1, 0, 0))
    if ax == 'y': return Part.makeCylinder(r, a1 - a0, V(p, a0, q), V(0, 1, 0))
    return Part.makeCylinder(r, a1 - a0, V(p, q, a0), V(0, 0, 1))
def seg(p0, p1, r):
    d = V(*p1) - V(*p0); return Part.makeCylinder(r, d.Length, V(*p0), d)
def fuse(*ss):
    r = ss[0]
    for x in ss[1:]: r = r.fuse(x)
    return r.removeSplitter()
def prop(o, n, v):
    if n not in o.PropertiesList: o.addProperty('App::PropertyString', n, 'CNC')
    setattr(o, n, v)

# ---------------- the two assemblies as groups
GB = doc.addObject('App::DocumentObjectGroup', 'B'); GB.Label = 'B CNC machine v14'
for g in [o for o in doc.Objects if o.TypeId == 'App::DocumentObjectGroup' and o.Label[:2].isdigit()]:
    GB.addObject(g)
GA = doc.addObject('App::DocumentObjectGroup', 'A'); GA.Label = 'A Base (extrusion + sheet metal + coolant)'
def add(label, shape, spec, motion=''):
    o = doc.addObject('Part::Feature', label); o.Label = label; o.Shape = shape
    prop(o, 'Spec', spec); prop(o, 'Motion', motion); prop(o, 'Adj', 'base'); GA.addObject(o); NEW.append(label); return o
_hfs = Part.read(os.path.join(ROOT, 'vendor', 'misumi', 'HFS8-4040-600', 'step', 'HFS8-4040-600.stp'))   # vendor STEP: along x 0..600, section in yz
HFS_SEC = Part.makeFace(_hfs.slice(V(1, 0, 0), 300.0), 'Part::FaceMakerBullseye'); HFS_SEC.translate(V(-300, 0, 0))   # section at x 0, centred
def ext(label, b):
    """MISUMI HFS8-4040 cut to length: the vendor section (slot 8, centre hole, 4 corner cavities) extruded along the long side of box b"""
    x0, x1, y0, y1, z0, z1 = b
    L = [x1 - x0, y1 - y0, z1 - z0]; ax = L.index(max(L))
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    f = HFS_SEC.copy()
    if ax == 0: f.translate(V(x0, cy, cz)); d = V(L[0], 0, 0)
    elif ax == 1: f.rotate(V(0, 0, 0), V(0, 0, 1), 90); f.translate(V(cx, y0, cz)); d = V(0, L[1], 0)
    else: f.rotate(V(0, 0, 0), V(0, 1, 0), 90); f.translate(V(cx, cy, z0)); d = V(0, 0, L[2])
    return add(label, f.extrude(d), 'MISUMI HFS8-4040-%d aluminium extrusion 40x40, slot 8, cut to length (section from the vendor STEP)' % round(max(L)))

# ---------------- A1 frame
W = 32.5                                                     # v14: machine 65 wider in X than v12 -> frame, pan and guards 32.5 wider per side
BX = 440 + W                                                 # leg axis x
LEGS = [(-BX, -580), (BX, -580), (-BX, 40), (BX, 40), (-BX, 560), (BX, 560)]
for i, (x, y) in enumerate(LEGS, 1):
    ext('Base_leg_%d' % i, (x - 20, x + 20, y - 20, y + 20, FLOOR + 60, -130))
    add('Base_foot_%d' % i, cyl('z', 40, FLOOR, FLOOR + 15, x, y).fuse(cyl('z', 8, FLOOR + 15, FLOOR + 60, x, y)), 'levelling foot M16, pad D80')
# top ring: the two side beams run full length on the 6 leg tops; front / rear / cross beams butt into the side beams. Low ring runs between
# the legs (no low rear beam: the tank slides out at the rear). Joints: hidden end-tap (M8 into the centre hole of the butting member, SHCS
# through a counterbored cross hole of the through member). Layout so that no two joint bolts meet inside one member: front / rear top beams
# 40 inside the corner legs (their bolts clear the vertical leg bolts), low front and the rear low sides 40 higher than the front low sides.
ext('Base_top_side_L', (-BX - 20, -BX + 20, -600, 580, -130, -90)); ext('Base_top_side_R', (BX - 20, BX + 20, -600, 580, -130, -90))
YF, YR = -540, 520                                           # front / rear top beam axes
ext('Base_top_front', (-BX + 20, BX - 20, YF - 20, YF + 20, -130, -90)); ext('Base_top_rear', (-BX + 20, BX - 20, YR - 20, YR + 20, -130, -90))
LZ = FLOOR + 90
ext('Base_low_front', (-BX + 20, BX - 20, -600, -560, LZ + 40, LZ + 80))
for T, x0, x1 in (('L', -BX - 20, -BX + 20), ('R', BX - 20, BX + 20)):
    ext('Base_low_side_%s1' % T, (x0, x1, -560, 20, LZ, LZ + 40)); ext('Base_low_side_%s2' % T, (x0, x1, 60, 540, LZ + 40, LZ + 80))
for k, y in enumerate((-120, 168), 1):                       # cross beams under the machine risers
    ext('Base_cross_%d' % k, (-BX + 20, BX - 20, y - 20, y + 20, -130, -90))
# hidden end-tap joints: M8x50 SHCS in a D14 x 8.5 counterbore + D9 cross hole through the 40 of the through member, into the M8 end tap
# (depth 22) of the butting member: 18.5 engaged (2.3 d in aluminium), tap 3.5 deeper than the bolt tip. Heads 0.5 below the face.
MACH = {}
def joint(thru, butt, ax, a_head, a_face, p, q):
    sg = 1 if a_face > a_head else -1
    def c(r, u0, u1):
        u0, u1 = sorted((a_head + sg * u0, a_head + sg * u1)); return cyl(ax, r, u0, u1, p, q)
    o = O(thru); o.Shape = o.Shape.cut(c(7, 0, 8.5)).cut(c(4.5, 8.5, 40))
    o = O(butt); o.Shape = o.Shape.cut(c(4, 40, 62))
    MACH.setdefault(thru, []).append('x'); MACH.setdefault(butt, []).append('t')
    k = len([n for n in NEW if n.startswith('Base_frame_bolt_')]) + 1
    add('Base_frame_bolt_%d' % k, fuse(c(6.5, 0.5, 8.5), c(4, 8.5, 58.5)),
        'M8x50 SHCS (DIN 912), hidden end-tap joint: through the counterbored cross hole (D14 x 8.5 + D9) of one extrusion into the M8 end tap '
        '(depth 22) of the butting one, 18.5 engaged')
for i, (x, y) in enumerate(LEGS, 1):                          # side beams on the leg tops (heads flush under the pan)
    joint('Base_top_side_%s' % ('L' if x < 0 else 'R'), 'Base_leg_%d' % i, 'z', -90, -130, x, y)
for T, sx in (('L', -1), ('R', 1)):
    for butt, y in (('Base_top_front', YF), ('Base_top_rear', YR), ('Base_cross_1', -120), ('Base_cross_2', 168)):
        joint('Base_top_side_' + T, butt, 'x', sx * (BX + 20), sx * (BX - 20), y, -110)
    i0 = 1 if sx < 0 else 2                                   # legs: 1/2 front, 3/4 middle, 5/6 rear (odd = left)
    joint('Base_leg_%d' % i0, 'Base_low_front', 'x', sx * (BX + 20), sx * (BX - 20), -580, LZ + 60)
    joint('Base_leg_%d' % i0, 'Base_low_side_%s1' % T, 'y', -600, -560, sx * BX, LZ + 20)
    joint('Base_leg_%d' % (i0 + 2), 'Base_low_side_%s1' % T, 'y', 60, 20, sx * BX, LZ + 20)
    joint('Base_leg_%d' % (i0 + 2), 'Base_low_side_%s2' % T, 'y', 20, 60, sx * BX, LZ + 60)
    joint('Base_leg_%d' % (i0 + 4), 'Base_low_side_%s2' % T, 'y', 580, 540, sx * BX, LZ + 60)
for n, m in MACH.items():                                     # MISUMI additional machining in the spec (BOM groups same length + machining)
    t, x_ = m.count('t'), m.count('x')
    prop(O(n), 'Spec', O(n).Spec.replace('cut to length', 'cut to length, machining: ' + ', '.join(
        ([('M8 end tap depth 22 x %d' % t)] if t else []) + ([('cross hole D9 + c-bore D14 x 8.5 x %d' % x_)] if x_ else []))))

# ---------------- A2 coolant pan (sheet SUS304 t1.5, corners folded and sealed with silicone)
PX_ = 455 + W                                                # pan half width
pan = box(-PX_, PX_, -595, 575, -90, -30).cut(box(-PX_ + 1.5, PX_ - 1.5, -593.5, 573.5, -88.5, -30)).cut(cyl('z', 20, -90, -88.5, 0, 470))
MOUNT = [(-340 - W, -120), (340 + W, -120), (-240 - W, 168), (240 + W, 168)]
for x, y in MOUNT:
    for dx in (-20, 20): pan = pan.cut(cyl('z', 4.5, -90, -88.5, x + dx, y))
add('Coolant_pan', pan, 'SUS304 t1.5 pan 1065x1170x60, floor slope 1:100 to the drain D40 at the rear centre; corners folded, sealed with silicone')
for i, (x, y) in enumerate(((-PX_ + 1.5, -593.5), (PX_ - 1.5, -593.5), (-PX_ + 1.5, 573.5), (PX_ - 1.5, 573.5)), 1):
    add('Coolant_silicone_%d' % i, cyl('z', 3, -88.5, -30, x, y).common(box(-PX_ + 1.5, PX_ - 1.5, -593.5, 573.5, -90, 0)), 'silicone bead in the pan corner')
# ---------------- A3 risers + the 4 bolts that join B to A
for i, (x, y) in enumerate(MOUNT, 1):
    r = box(x - 30, x + 30, y - 30, y + 30, -88.5, -20).cut(cyl('z', 6, -40, -20, x, y))
    for dx in (-20, 20): r = r.cut(cyl('z', 7, -29, -20, x + dx, y)).cut(cyl('z', 4.5, -88.5, -29, x + dx, y))
    add('Base_riser_%d' % i, r, 'steel riser 60x60x68.5 on the pan floor: M12 tap for the machine, 2 counterbored M8 holes to the cross beam; '
        'silicone ring under it seals the pan holes')
    add('Base_mount_bolt_%d' % i, cyl('z', 6, -40, 0, x, y).fuse(cyl('z', 9, 0, 12, x, y)), 'M12x40 SHCS: datum plate (B) into the riser tap (joins B to A)')
    for k, dx in enumerate((-20, 20), 1):
        add('Base_riser_bolt_%d_%d' % (i, k), cyl('z', 4, -99, -29, x + dx, y).fuse(cyl('z', 6.5, -29, -21, x + dx, y)),
            'M8x70 SHCS, counterbored in the riser, through the pan into a T-nut in the cross-beam slot')
    s = cyl('z', 6.5, -20, 0, x, y); o = O('Datum_base_plate'); o.Shape = o.Shape.cut(s)
# ---------------- A4 splash guards
for sx, T in ((1, 'R'), (-1, 'L')):
    GX = 450 + W
    side = box(GX if sx > 0 else -GX - 1.2, GX + 1.2 if sx > 0 else -GX, -590, 570, -60, 450).cut(box(-GX - 10, GX + 10, -300, 250, 120, 400))
    add('Guard_side_' + T, side, 'SUS304 t1.2 side guard, stands inside the pan wall (splash runs into the pan); window cut-out 550x280')
    add('Guard_window_' + T, box(GX + 1.2 if sx > 0 else -GX - 5.2, GX + 5.2 if sx > 0 else -GX - 1.2, -310, 260, 110, 410), 'PC t4 window, bolted with a rubber seal')
    for y in (-590, 550):
        add('Guard_post_%s_%d' % (T, y), box(GX - 20 if sx > 0 else -GX, GX if sx > 0 else -GX + 20, y, y + 20, -88.5, 450), 'extrusion 20x20 corner post, sealed with silicone to the panels')
add('Guard_rear', box(-GX, GX, 570, 571.2, -60, 450), 'SUS304 t1.2 rear guard')
add('Guard_front_lip', box(-GX, GX, -591.2, -590, -60, 60), 'SUS304 t1.2 low front lip (loading side open), 35 mm ahead of the Y rail ends at the load position')
# ---------------- A5 tank, filter, pump, hose
TZ0, TZ1 = FLOOR + 60, FLOOR + 360
tank = box(-300, 300, 0, 520, TZ0, TZ1).cut(box(-297, 297, 3, 517, TZ0 + 3, TZ1))
add('Coolant_tank', tank, 'SUS304 t3 tank 600x520x300, 90 L (fill 75 L), on castors, slides out at the rear (no rear low beam)')
add('Coolant_baffle', box(-297, 297, 259, 262, TZ0 + 3, TZ1 - 60), 'settling baffle, overflow at the top: dirty side (rear) -> clean side (front)')
for i, (x, y) in enumerate(((-260, 40), (260, 40), (-260, 480), (260, 480)), 1):
    add('Coolant_castor_%d' % i, cyl('z', 25, FLOOR, FLOOR + 60, x, y), 'castor D50')
add('Coolant_filter_basket', box(-80, 80, 400, 510, TZ1 - 60, TZ1).cut(box(-78, 78, 402, 508, TZ1 - 58, TZ1)), '60-mesh filter basket under the drain, lifts out')
add('Coolant_drain_pipe', cyl('z', 20, TZ1, -90, 0, 470).cut(cyl('z', 18, TZ1, -90, 0, 470)), 'drain pipe D40 from the pan into the filter basket')
add('Coolant_tank_lid', box(-300, 300, 0, 259, TZ1, TZ1 + 3).cut(cyl('z', 38, TZ1, TZ1 + 3, -200, 90)), 'SUS304 t3 lid over the clean side, carries the pump')
add('Coolant_pump', cyl('z', 35, TZ1 - 150, TZ1, -200, 90).fuse(box(-260, -140, 30, 150, TZ1 + 3, TZ1 + 9)).fuse(cyl('z', 55, TZ1 + 9, TZ1 + 130, -200, 90)),
    'MISUMI / TERAL VKP-055A immersion coolant pump, 3-phase 200-220 V, 60 W, 20 / 30 L/min at 50 / 60 Hz, total head 1.5-5 m, '
    'immersion about 150 mm (same as VKP-053A / 065A; confirm on the TERAL outline drawing). Flow trimmed with a ball valve and a bypass to the tank')
P0 = (-200, 90, TZ1 + 130)
HX = -475 - W
for k, (a, b) in enumerate(((P0, (-200, 90, -290)), ((-200, 90, -290), (HX, 90, -290)), ((HX, 90, -290), (HX, 90, 470)), ((HX, 90, 470), (HX + 35, 90, 470))), 1):
    add('Coolant_hose_%d' % k, seg(a, b, 6), 'supply hose 12 mm: pump -> up the left side outside the guard -> bulkhead at the guard top -> X drag chain -> nozzles')
# nozzles on the spindle clamp RIGHT face (v14: the camera is on the left, the probe bracket on the front); move with Z
SX0, SY = 32.5, -20.0
DZN = O('Spindle_clamp').Shape.BoundBox.ZMin - 331.0           # clamp height offset (Z assembly 25 lower)
XR = O('Spindle_clamp').Shape.BoundBox.XMax                    # clamp right face
for k, yc in enumerate((-40.0, 0.0), 1):                       # clear of the pinch-screw heads (y -57) on the same face
    add('Coolant_nozzle_block_%d' % k, box(XR, XR + 10, yc - 5, yc + 5, 360 + DZN, 380 + DZN).cut(cyl('x', 2.25, XR, XR + 10, yc, 370 + DZN)),
        'nozzle block on the right face of the spindle clamp (Loc-Line 1/4), 1 x M4 into the clamp', 'z')
    add('Coolant_nozzle_block_bolt_%d' % k, cyl('x', 3.5, XR + 10, XR + 14, yc, 370 + DZN).fuse(cyl('x', 2.0, XR - 8, XR + 10, yc, 370 + DZN)),
        'M4x18 SHCS, nozzle block to the spindle clamp right face (tap M4 depth 8, between the pinch screws)', 'z')
    o = O('Spindle_clamp'); o.Shape = o.Shape.cut(cyl('x', 2.0, XR - 8, XR, yc, 370 + DZN))
    pts = [(XR + 5, yc, 362 + DZN), (XR + 6, yc, 300 + DZN), (XR + 6, yc, 228 + DZN), (SX0 + 26, SY + (yc - SY) * 0.6, 208 + DZN)]
    add('Coolant_nozzle_%d' % k, fuse(seg(pts[0], pts[1], 4), seg(pts[1], pts[2], 3.5), seg(pts[2], pts[3], 3.5)),
        'segmented coolant nozzle 1/4, down beside the spindle (right) then in, aimed at the tool', 'z')

# feeder cables between the column-top electrical box and the base cabinet (owner 2026-11-27: protection parts in a base cabinet; both boxes
# drawn by the electrical session). Fixed runs, no drag chain, outside the machine and away from the moving conduits: entry plate on
# the box top plate rear flange (01) -> rear guard glands -> down behind the rear-left leg -> forward outside the left low side beams -> along the front
# low beam -> up into the base cabinet bottom. Power (F1-F3 + PE) and control (F4, shielded) in two conduits ~50 apart. KSS sizes: sketch.
def fillet(pts, R, n=6):                                       # polyline with each corner rounded to radius R (static conduit bends)
    P_ = [V(*p) for p in pts]; out = [P_[0]]
    for a_, b_, c_ in zip(P_[:-2], P_[1:-1], P_[2:]):
        u1 = (a_ - b_); u1.normalize(); u2 = (c_ - b_); u2.normalize()
        th = math.acos(max(-1.0, min(1.0, u1.dot(u2)))); t_ = R / math.tan(th / 2)
        p1, p2 = b_ + u1 * t_, b_ + u2 * t_; bis = u1 + u2; bis.normalize(); cc = b_ + bis * (R / math.sin(th / 2))
        for k in range(n + 1):
            v1 = p1 - cc; v2 = p2 - cc; f = k / n
            v = v1 * (1 - f) + v2 * f; v.normalize(); out.append(cc + v * R)
    out.append(P_[-1]); return [(q.x, q.y, q.z) for q in out]
def tube_(pts, D):
    return fuse(*([seg(a_, b_, D / 2) for a_, b_ in zip(pts[:-1], pts[1:]) if math.dist(a_, b_) > 1e-6] + [Part.makeSphere(D / 2, V(*q)) for q in pts[1:-1]]))
FEED = {   # name: (outer D, static bend R, route, spec); rear runs bend only after the guard, side runs outside the frame bolt heads
    'Feeder_power_conduit': (42.5, 70.0, [(-340, 506 + 1.2 * 47.0, 270), (-340, 645, 270), (-530, 645, 270), (-530, 645, -640), (-530, -640, -640), (-150, -640, -640), (-150, -640, -510 - 1.2 * 47.0)],
                             'KSS PA-36 nylon conduit (model AD 42.5, size to confirm from the PA page), ends in PAQ-3636 adaptors: F1 servo 5G2.5, F2 VFD 3G4, F3 supply 3G1.5, PE; column box -> base cabinet'),
    'Feeder_control_conduit': (21.2, 60.0, [(-260, 506 + 1.2 * 22.5, 270), (-260, 695, 270), (-530, 695, 270), (-530, 695, -690), (-530, -640, -690), (-90, -640, -690), (-90, -640, -510 - 1.2 * 22.5)],
                               'KSS PA-17 nylon conduit (model AD 21.2), ends in PAQ-1716 adaptors: F4 control 4x0.75 shielded (E-stop loop, contactor coil); 50 from the power run'),
    'Feeder_opbox_cable': (9.0, 30.0, [(300, -633, -330), (300, -633, -400), (200, -633, -400), (180, -625, -400)],
                           'operator box -> base cabinet right wall: 7G0.75 (S1 E-stop 2NC, S2 start NO), ~0.5 m, clipped to the right upright'),
}
for n_, (D_, R_, pts_, sp_) in FEED.items():
    add(n_, tube_(fillet(pts_, R_), D_), sp_ + '; model length %.0f mm' % sum(math.dist(a_, b_) for a_, b_ in zip(fillet(pts_, R_)[:-1], fillet(pts_, R_)[1:])))
g_ = O('Guard_rear')                                           # rear guard glands (outside the guard from here on)
g_.Shape = g_.Shape.cut(cyl('y', 42.5 / 2 + 2.5, 565, 576, -340, 270)).cut(cyl('y', 21.2 / 2 + 2.5, 565, 576, -260, 270))   # conduit through a grommet
for k, (x_, d_) in enumerate(((-340, 42.5), (-260, 21.2)), 1):
    add('Feeder_guard_gland_%d' % k, cyl('y', d_ / 2 + 2.5, 564, 578, x_, 270).cut(cyl('y', d_ / 2 + 0.5, 564, 578, x_, 270)),
        'rubber grommet in the rear guard (hole = conduit OD + 5) for the %s conduit' % ('power' if k == 1 else 'control'))
for k, (x_, tod, cd_, pn) in enumerate(((-150, 47.0, 42.5, 'PAQ-3636 (PG36)'), (-90, 22.5, 21.2, 'PAQ-1716 (PG16)')), 1):   # base cabinet bottom (box: electrical session)
    rb_ = max(tod / 2 + 5, cd_ / 2 + 4); z0_ = -510.0
    add('Feeder_cabinet_fitting_%d' % k, fuse(cyl('z', rb_, z0_ - 1.2 * tod, z0_, x_, -640), cyl('z', tod / 2, z0_, z0_ + 9, x_, -640), cyl('z', tod / 2 + 5, z0_ + 3, z0_ + 9, x_, -640))
        .cut(cyl('z', cd_ / 2 + 0.5, z0_ - 1.2 * tod - 5, z0_ + 10, x_, -640)),
        'KSS %s easy-type conduit adaptor with locknut in the base cabinet bottom, hole D%.1f (catalog); body size estimated' % (pn, tod + 0.3))
def clamp(n_, c, ax, D_, foot):                                # conduit fixing base (sketch): ring around the conduit + foot to the frame face
    r_ = D_ / 2 + 0.5; ring = cyl(ax, r_ + 4, -10, 10, 0, 0).cut(cyl(ax, r_, -10, 10, 0, 0))
    if ax == 'x': ring = Part.makeCylinder(r_ + 4, 20, V(c[0] - 10, c[1], c[2]), V(1, 0, 0)).cut(Part.makeCylinder(r_, 20, V(c[0] - 10, c[1], c[2]), V(1, 0, 0)))
    if ax == 'y': ring = Part.makeCylinder(r_ + 4, 20, V(c[0], c[1] - 10, c[2]), V(0, 1, 0)).cut(Part.makeCylinder(r_, 20, V(c[0], c[1] - 10, c[2]), V(0, 1, 0)))
    if ax == 'z': ring = Part.makeCylinder(r_ + 4, 20, V(c[0], c[1], c[2] - 10), V(0, 0, 1)).cut(Part.makeCylinder(r_, 20, V(c[0], c[1], c[2] - 10), V(0, 0, 1)))
    bore = {'x': Part.makeCylinder(r_, 60, V(c[0] - 30, c[1], c[2]), V(1, 0, 0)), 'y': Part.makeCylinder(r_, 60, V(c[0], c[1] - 30, c[2]), V(0, 1, 0)),
            'z': Part.makeCylinder(r_, 60, V(c[0], c[1], c[2] - 30), V(0, 0, 1))}[ax]
    add(n_, fuse(ring, *[box(*f_) for f_ in foot]).cut(bore), 'conduit fixing base for AD %.1f (KSS, sketch), M6 + T-nut into the HFS8 slot / M5 into the guard' % D_)
CL = [   # (centre, conduit axis, D, foot boxes toward the frame face); the control conduit rides on the power clamps where they run side by side
    ((-430, 645, 270), 'x', 42.5, [(-440, -420, 571.2, 620, 260, 280)]), ((-430, 695, 270), 'x', 21.2, [(-440, -420, 671, 685, 265, 275)]),
    ((-530, 645, 0), 'z', 42.5, [(-540, -520, 560, 621, -10, 10), (-520, -492.5, 560, 580, -10, 10)]),
    ((-530, 645, -400), 'z', 42.5, [(-540, -520, 560, 621, -410, -390), (-520, -492.5, 560, 580, -410, -390)]),
    ((-530, 695, 0), 'z', 21.2, [(-535, -525, 671, 685, -5, 5)]), ((-530, 695, -400), 'z', 21.2, [(-535, -525, 671, 685, -405, -395)]),
    ((-530, 300, -640), 'y', 42.5, [(-509, -492.5, 290, 310, -650, -630)]), ((-530, -150, -640), 'y', 42.5, [(-509, -492.5, -160, -140, -668, -630)]),
    ((-530, 250, -690), 'y', 21.2, [(-520, -492.5, 240, 260, -695, -660)]), ((-530, -100, -690), 'y', 21.2, [(-520, -492.5, -110, -90, -695, -685)]),
    ((-380, -640, -640), 'x', 42.5, [(-390, -370, -619, -600, -650, -630)]), ((-300, -640, -690), 'x', 21.2, [(-310, -290, -630, -600, -695, -660)]),
    ((240, -633, -400), 'x', 9.0, [(235, 245, -628.5, -600, -405, -395)]),
]
for k, (c_, ax_, d_, ft_) in enumerate(CL, 1): clamp('Feeder_clamp_%d' % k, c_, ax_, d_, ft_)
FS = [n_ for n_ in NEW if n_.startswith('Feeder_')]            # static clash check of the feeder parts against the base and the machine
fh = []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    for n_ in FS:
        if n_ == o.Label or (o.Label.startswith('Feeder_') and n_ > o.Label): continue
        fs_ = O(n_).Shape
        if not fs_.BoundBox.intersect(o.Shape.BoundBox): continue
        try: v_ = fs_.common(o.Shape).Volume
        except Exception: v_ = -1
        if v_ > 1 and not (n_.startswith('Feeder_clamp') or n_.startswith('Feeder_guard')): fh.append('%s x %s: %.0f mm3' % (n_, o.Label, v_))
        elif v_ > 1 and n_.startswith('Feeder_guard') and o.Label != 'Guard_rear': fh.append('%s x %s: %.0f mm3' % (n_, o.Label, v_))
        elif v_ > 1 and n_.startswith('Feeder_clamp'): fh.append('%s x %s: %.0f mm3 (clamp foot into the frame?)' % (n_, o.Label, v_))
FEED_LOG = ['feeder runs (column box <-> base cabinet): %d parts, static clashes %d' % (len(FS), len(fh))] + ['  ' + x for x in fh]

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v14_base.FCStd'))
L = ['v14 on coolant base: base parts %d (A), machine unchanged (B) + 4 datum-plate holes; floor z=%d, table top %d above the floor' % (len(NEW), FLOOR, 110 - FLOOR), '']
for l in NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v14_base_build.txt'), 'w', encoding='utf-8').write('\n'.join(FEED_LOG + [''] + L))
