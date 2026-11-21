# -*- coding: utf-8 -*-
"""v13 on a coolant base, built as two assemblies:
  A  base: aluminium-extrusion frame (40x40) on 6 levelling feet, SUS304 coolant pan with silicone-sealed corners and a drain at the
     rear centre (floor slope 1:100), splash guards (sides, rear, low front lip, PC windows), 90 L tank on castors that slides out
     at the rear, 60-mesh filter basket, immersion pump, supply hose to a bulkhead at the guard top; 4 steel risers through the pan
     (sealed) carry the machine
  B  the v13 machine, unchanged except 4 mounting holes in the datum plate; 4 M12 bolts tie B to A
The table top stands about 900 mm above the floor (floor at z = -790 in machine coordinates).
Run:  freecadcmd freecad/v13/06_base_coolant_v13.py      Out: output/v13/CNC_v13_base.FCStd, output/v13/logs/v13_base_build.txt"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v13')
doc = App.openDocument(os.path.join(OUT, 'CNC_v13.FCStd'))
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
GB = doc.addObject('App::DocumentObjectGroup', 'B'); GB.Label = 'B CNC machine v13'
for g in [o for o in doc.Objects if o.TypeId == 'App::DocumentObjectGroup' and o.Label[:2].isdigit()]:
    GB.addObject(g)
GA = doc.addObject('App::DocumentObjectGroup', 'A'); GA.Label = 'A Base (extrusion + sheet metal + coolant)'
def add(label, shape, spec, motion=''):
    o = doc.addObject('Part::Feature', label); o.Label = label; o.Shape = shape
    prop(o, 'Spec', spec); prop(o, 'Motion', motion); prop(o, 'Adj', 'base'); GA.addObject(o); NEW.append(label); return o
def ext(label, b, spec='aluminium extrusion 40x40 (HFS8-4040), slot 8'):
    x0, x1, y0, y1, z0, z1 = b
    s = box(x0, x1, y0, y1, z0, z1)
    L = [x1 - x0, y1 - y0, z1 - z0]; ax = L.index(max(L))
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    for k in range(4):                                       # four T-slots along the long axis
        if ax == 2: sl = [box(cx - 4, cx + 4, y0, y0 + 9, z0, z1), box(cx - 4, cx + 4, y1 - 9, y1, z0, z1), box(x0, x0 + 9, cy - 4, cy + 4, z0, z1), box(x1 - 9, x1, cy - 4, cy + 4, z0, z1)][k]
        elif ax == 0: sl = [box(x0, x1, cy - 4, cy + 4, z0, z0 + 9), box(x0, x1, cy - 4, cy + 4, z1 - 9, z1), box(x0, x1, y0, y0 + 9, cz - 4, cz + 4), box(x0, x1, y1 - 9, y1, cz - 4, cz + 4)][k]
        else: sl = [box(cx - 4, cx + 4, y0, y1, z0, z0 + 9), box(cx - 4, cx + 4, y0, y1, z1 - 9, z1), box(x0, x0 + 9, y0, y1, cz - 4, cz + 4), box(x1 - 9, x1, y0, y1, cz - 4, cz + 4)][k]
        s = s.cut(sl)
    return add(label, s, spec)

# ---------------- A1 frame
W = 77.5                                                     # v13: machine 155 wider in X -> frame, pan and guards 77.5 wider per side
BX = 440 + W                                                 # leg axis x
LEGS = [(-BX, -580), (BX, -580), (-BX, 40), (BX, 40), (-BX, 560), (BX, 560)]
for i, (x, y) in enumerate(LEGS, 1):
    ext('Base_leg_%d' % i, (x - 20, x + 20, y - 20, y + 20, FLOOR + 60, -130))
    add('Base_foot_%d' % i, cyl('z', 40, FLOOR, FLOOR + 15, x, y).fuse(cyl('z', 8, FLOOR + 15, FLOOR + 60, x, y)), 'levelling foot M16, pad D80')
# top ring sits on the leg tops; low ring runs between the legs (no low rear beam: the tank slides out at the rear)
ext('Base_top_side_L', (-BX - 20, -BX + 20, -560, 540, -130, -90)); ext('Base_top_side_R', (BX - 20, BX + 20, -560, 540, -130, -90))
ext('Base_top_front', (-BX - 20, BX + 20, -600, -560, -130, -90)); ext('Base_top_rear', (-BX - 20, BX + 20, 540, 580, -130, -90))
LZ = FLOOR + 90
ext('Base_low_front', (-BX + 20, BX - 20, -600, -560, LZ, LZ + 40))
for T, x0, x1 in (('L', -BX - 20, -BX + 20), ('R', BX - 20, BX + 20)):
    ext('Base_low_side_%s1' % T, (x0, x1, -560, 20, LZ, LZ + 40)); ext('Base_low_side_%s2' % T, (x0, x1, 60, 540, LZ, LZ + 40))
for k, y in enumerate((-120, 168), 1):                       # cross beams under the machine risers
    ext('Base_cross_%d' % k, (-BX + 20, BX - 20, y - 20, y + 20, -130, -90))
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
# nozzles on the spindle clamp FRONT face (v13: the clamp sides face the camera and the probe); move with Z
SX0, SY = -7.5, -20.0
for k, sx in enumerate((-1, 1), 1):
    x0 = SX0 + 28 * sx
    add('Coolant_nozzle_block_%d' % k, box(x0 - 5, x0 + 5, -73, -63, 372, 392),
        'nozzle block on the front face of the spindle clamp, beside the split (Loc-Line 1/4)', 'z')
    pts = [(x0, -68, 372), (SX0 + 30 * sx, -64, 300), (SX0 + 30 * sx, -64, 228), (SX0 + 14 * sx, -40, 208)]
    add('Coolant_nozzle_%d' % k, fuse(seg(pts[0], pts[1], 4), seg(pts[1], pts[2], 3.5), seg(pts[2], pts[3], 3.5)),
        'segmented coolant nozzle 1/4, down in front of the spindle then in, aimed at the tool', 'z')

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v13_base.FCStd'))
L = ['v13 on coolant base: base parts %d (A), machine unchanged (B) + 4 datum-plate holes; floor z=%d, table top %d above the floor' % (len(NEW), FLOOR, 110 - FLOOR), '']
for l in NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v13_base_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
