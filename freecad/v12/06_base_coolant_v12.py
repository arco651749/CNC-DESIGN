# -*- coding: utf-8 -*-
"""v12 on a coolant base, built as two assemblies:
  A  base: aluminium-extrusion frame (40x40) on 6 levelling feet, SUS304 coolant pan with silicone-sealed corners and a drain at the
     rear centre (floor slope 1:100), splash guards (sides, rear, low front lip, PC windows), 90 L tank on castors that slides out
     at the rear, 60-mesh filter basket, immersion pump, supply hose to a bulkhead at the guard top; 4 steel risers through the pan
     (sealed) carry the machine
  B  the v12 machine, unchanged except 4 mounting holes in the datum plate; 4 M12 bolts tie B to A
The table top stands about 900 mm above the floor (floor at z = -790 in machine coordinates).
Run:  freecadcmd freecad/v12/06_base_coolant_v12.py      Out: output/v12/CNC_v12_base.FCStd, output/v12/logs/v12_base_build.txt"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v12')
doc = App.openDocument(os.path.join(OUT, 'CNC_v12.FCStd'))
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
def prop(o, n, v):
    if n not in o.PropertiesList: o.addProperty('App::PropertyString', n, 'CNC')
    setattr(o, n, v)

# ---------------- the two assemblies as groups
GB = doc.addObject('App::DocumentObjectGroup', 'B'); GB.Label = 'B CNC machine v12'
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
LEGS = [(-440, -480), (440, -480), (-440, 40), (440, 40), (-440, 560), (440, 560)]
for i, (x, y) in enumerate(LEGS, 1):
    ext('Base_leg_%d' % i, (x - 20, x + 20, y - 20, y + 20, FLOOR + 60, -130))
    add('Base_foot_%d' % i, cyl('z', 40, FLOOR, FLOOR + 15, x, y).fuse(cyl('z', 8, FLOOR + 15, FLOOR + 60, x, y)), 'levelling foot M16, pad D80')
for zz, tag in ((-130, 'top'), (FLOOR + 90, 'low')):
    ext('Base_%s_side_L' % tag, (-460, -420, -460, 540, zz, zz + 40)); ext('Base_%s_side_R' % tag, (420, 460, -460, 540, zz, zz + 40))
    ext('Base_%s_front' % tag, (-460, 460, -500, -460, zz, zz + 40))
    if tag == 'top': ext('Base_top_rear', (-460, 460, 540, 580, zz, zz + 40))   # no low rear beam: the tank slides out at the rear
for k, y in enumerate((-120, 168), 1):                       # cross beams under the machine risers
    ext('Base_cross_%d' % k, (-420, 420, y - 20, y + 20, -130, -90))
# ---------------- A2 coolant pan (sheet SUS304 t1.5, corners folded and sealed with silicone)
pan = box(-455, 455, -495, 575, -90, -30).cut(box(-453.5, 453.5, -493.5, 573.5, -88.5, -30)).cut(cyl('z', 20, -90, -88.5, 0, 470))
MOUNT = [(-340, -120), (340, -120), (-240, 168), (240, 168)]
for x, y in MOUNT: pan = pan.cut(cyl('z', 6.5, -90, -88.5, x, y))
add('Coolant_pan', pan, 'SUS304 t1.5 pan 910x1070x60, floor slope 1:100 to the drain D40 at the rear centre; corners folded, sealed with silicone')
for i, (x, y) in enumerate(((-453.5, -493.5), (453.5, -493.5), (-453.5, 573.5), (453.5, 573.5)), 1):
    add('Coolant_silicone_%d' % i, cyl('z', 3, -88.5, -30, x, y).common(box(-453.5, 453.5, -493.5, 573.5, -90, 0)), 'silicone bead in the pan corner')
# ---------------- A3 risers + the 4 bolts that join B to A
for i, (x, y) in enumerate(MOUNT, 1):
    add('Base_riser_%d' % i, box(x - 30, x + 30, y - 30, y + 30, -88.5, -20).cut(cyl('z', 6.5, -88.5, -20, x, y)),
        'steel riser 60x60x68.5 on the pan floor, bolted through to the cross beam; silicone ring under it seals the pan hole')
    add('Base_mount_bolt_%d' % i, cyl('z', 6, -128, 0, x, y).fuse(cyl('z', 9, 0, 12, x, y)),
        'M12x130 SHCS: datum plate (B) + riser + pan + cross beam, into a T-nut (joins B to A)')
    s = cyl('z', 6.5, -20, 0, x, y); o = O('Datum_base_plate'); o.Shape = o.Shape.cut(s)
# ---------------- A4 splash guards
for sx, T in ((1, 'R'), (-1, 'L')):
    side = box(450 if sx > 0 else -451.2, 451.2 if sx > 0 else -450, -490, 570, -60, 450).cut(box(-460, 460, -300, 250, 120, 400))
    add('Guard_side_' + T, side, 'SUS304 t1.2 side guard, stands inside the pan wall (splash runs into the pan); window cut-out 550x280')
    add('Guard_window_' + T, box(451.2 if sx > 0 else -455.2, 455.2 if sx > 0 else -451.2, -310, 260, 110, 410), 'PC t4 window, bolted with a rubber seal')
    for y in (-490, 550):
        add('Guard_post_%s_%d' % (T, y), box(430 if sx > 0 else -450, 450 if sx > 0 else -430, y, y + 20, -88.5, 450), 'extrusion 20x20 corner post, sealed with silicone to the panels')
add('Guard_rear', box(-450, 450, 570, 571.2, -60, 450), 'SUS304 t1.2 rear guard')
add('Guard_front_lip', box(-450, 450, -491.2, -490, -60, 60), 'SUS304 t1.2 low front lip (loading side open)')
# ---------------- A5 tank, filter, pump, hose
TZ0, TZ1 = FLOOR + 60, FLOOR + 360
tank = box(-300, 300, 0, 520, TZ0, TZ1).cut(box(-297, 297, 3, 517, TZ0 + 3, TZ1))
add('Coolant_tank', tank, 'SUS304 t3 tank 600x520x300, 90 L (fill 75 L), on castors, slides out at the rear (no rear low beam)')
add('Coolant_baffle', box(-297, 297, 259, 262, TZ0 + 3, TZ1 - 60), 'settling baffle, overflow at the top: dirty side (rear) -> clean side (front)')
for i, (x, y) in enumerate(((-260, 40), (260, 40), (-260, 480), (260, 480)), 1):
    add('Coolant_castor_%d' % i, cyl('z', 25, FLOOR, FLOOR + 60, x, y), 'castor D50')
add('Coolant_filter_basket', box(-80, 80, 400, 510, TZ1 - 60, TZ1).cut(box(-78, 78, 402, 508, TZ1 - 58, TZ1)), '60-mesh filter basket under the drain, lifts out')
add('Coolant_drain_pipe', cyl('z', 20, TZ1, -90, 0, 470).cut(cyl('z', 18, TZ1, -90, 0, 470)), 'drain pipe D40 from the pan into the filter basket')
add('Coolant_pump', cyl('z', 45, TZ1 - 160, TZ1, -200, 90).fuse(cyl('z', 55, TZ1, TZ1 + 110, -200, 90)), 'immersion pump 90 W, 25 L/min, 0.2 MPa, clean side')
P0 = (-200, 90, TZ1 + 110)
for k, (a, b) in enumerate(((P0, (-200, 90, -330)), ((-200, 90, -330), (-475, 90, -330)), ((-475, 90, -330), (-475, 90, 470)), ((-475, 90, 470), (-440, 90, 470))), 1):
    add('Coolant_hose_%d' % k, seg(a, b, 6), 'supply hose 12 mm: pump -> up the left side outside the guard -> bulkhead at the guard top -> X drag chain -> nozzles')
# nozzles on the spindle clamp block (move with Z)
add('Coolant_nozzle_block', box(-58, -48, -52, -32, 372, 392), 'nozzle block on the left face of the spindle clamp (2 x Loc-Line 1/4)', 'z')
for k, dy in enumerate((-6, 6), 1):
    pts = [(-53, -42 + dy, 372), (-38, -34 + dy, 300), (-16, -24 + dy, 215)]
    s = seg(pts[0], pts[1], 4).fuse(seg(pts[1], pts[2], 3.5))
    add('Coolant_nozzle_%d' % k, s, 'segmented coolant nozzle 1/4, aimed at the tool', 'z')

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v12_base.FCStd'))
L = ['v12 on coolant base: base parts %d (A), machine unchanged (B) + 4 datum-plate holes; floor z=%d, table top %d above the floor' % (len(NEW), FLOOR, 110 - FLOOR), '']
for l in NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v12_base_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
