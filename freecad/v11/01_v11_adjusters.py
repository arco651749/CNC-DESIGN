# -*- coding: utf-8 -*-
"""v11 from v10 (frozen): every geometric relation that has to be set at assembly has an adjuster in the model.
Three layers, set in this order; later layers never disturb earlier ones:

  1 gantry  pitch  Z travel perp Y, per column   1:10 wedge under each foot flange, M5x0.5 drive from the outer side;
                                                 the foot pivots on a 10 mm rib at the rear
            yaw    X perp Y                      push-pull screws (M6x0.75) in front of each foot flange, columns 640 apart
  2 Z plate ztram  Z travel perp X               carriage = saddle (on the X blocks) + Z plate; D10 pivot low, push screws high
  3 clamp   spindle // Z (nod and roll)          3-point carrier: crowned bar at the bottom, one 1:20 wedge at the top
                                                 (set AFTER the bolts are at final torque, disc springs follow), D8 roll pin
                                                 on the bar line, 1:15 side wedge for roll; spindle axis moved to y-13

  rails   rail // rail    reference pins (master), eccentric pins (slave), side screws OPPOSITE the pins; under 5.5 mm high
  pins    lock            match-reamed dowels on layers 1 and 2 only (foot flange / datum plate, Z plate / saddle).
                          The clamp is NOT dowelled: its setting belongs to one spindle and is redone after a spindle change.
  measure                 fixture plate skimmed by the machine (its top is the X-Y motion plane); indicator on the spindle axis

The X base plate is set on the columns by fixture (no level adjuster).
Hardware is modelled as solids and its holes are cut in the parts, so the collision sweep stays meaningful.
Run:  freecadcmd freecad/v11/01_v11_adjusters.py      Out: output/v11/CNC_v11.FCStd, output/v11/logs/v11_build.txt"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v11'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v10', 'CNC_v10.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
GROUPS = {g.Label: g for g in doc.Objects if g.TypeId == 'App::DocumentObjectGroup'}
NEW = []


def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cyl(ax, r, a0, a1, p, q):
    """cylinder along axis ax from a0 to a1; (p, q) are the other two coordinates in x,y,z order"""
    if ax == 'x': return Part.makeCylinder(r, a1 - a0, V(a0, p, q), V(1, 0, 0))
    if ax == 'y': return Part.makeCylinder(r, a1 - a0, V(p, a0, q), V(0, 1, 0))
    return Part.makeCylinder(r, a1 - a0, V(p, q, a0), V(0, 0, 1))
def prism_xz(pts, y0, y1):
    w = Part.makePolygon([V(x, y0, z) for x, z in pts] + [V(pts[0][0], y0, pts[0][1])])
    return Part.Face(w).extrude(V(0, y1 - y0, 0))
def prism_yz(pts, x0, x1):
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))
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


G_ADJ = doc.addObject('App::DocumentObjectGroup', 'Adjusters'); G_ADJ.Label = '08 Adjusters'; GROUPS['08 Adjusters'] = G_ADJ
G = '08 Adjusters'

# ================================================================ layer 1: gantry feet (pitch wedge, yaw push-pull)
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    foot = O('Column_foot_' + T)
    f = box(280, 360, -48, 182, 0, 18)
    f = f.cut(box(280, 360, -48, 167, 0, 0.5)).cut(box(280, 360, 177, 182, 0, 0.5))           # rib y167..177 is the pivot
    f = f.cut(prism_xz([(296, 0), (362, 0), (362, 8.4), (296, 1.8)], -46, -22))                 # 1:10 wedge seat, open at the outer side
    foot.Shape = m(f)
    prop(foot, 'Spec', 'steel foot t18, 80x230 with a front flange 50. Underside relieved 0.5 except a 10 mm rib at y167..177 '
                       '(the pitch pivot, with the two rear bolts on it). Inclined 1:10 seat under the flange for the pitch wedge')
    tag('Column_foot_' + T, 'pitch')
    add('Foot_wedge_' + T, m(prism_xz([(304, 0), (352, 0), (352, 7.4), (304, 2.6)], -45, -23).cut(cyl('x', 2.5, 340, 352, -34, 3.7))), G,
        'hardened steel 1:10 wedge 48x22, 2.6..7.4 thick, slides along X on the datum plate under the foot flange (pushed inward = foot lifts). '
        'Travel +-4 = +-0.4 mm rise = +-1.9 mrad pitch', '', 'pitch')
    add('Foot_wedge_block_' + T, m(box(360, 372, -44, -24, 1, 17).cut(cyl('x', 2.5, 360, 372, -34, 3.7))
                                 .cut(cyl('x', 2, 360, 372, -40, 13)).cut(cyl('x', 2, 360, 372, -28, 13))), G,
        'steel block 12x20x16 on the outer side face of the foot, carries the wedge drive screw', '', 'pitch')
    add('Foot_wedge_screw_' + T, m(fuse(cyl('x', 2.5, 346, 380, -34, 3.7), cyl('x', 4.5, 380, 385, -34, 3.7))), G,
        'M5x0.5 drive screw, captive in the wedge end: 10 deg = 1.4 um rise = 6.7 urad pitch (lever 206 to the rib)', '', 'pitch')
    cut(foot.Label)
    for k, y in enumerate((-40, -28), 1):
        add('Foot_wedge_block_bolt_%s%d' % (T, k), m(fuse(cyl('x', 2, 350, 372, y, 13), cyl('x', 3.5, 372, 376, y, 13))), G, 'M4 SHCS', '', 'pitch')
        cut(foot.Label, m(cyl('x', 2, 350, 360, y, 13)))
    s = m(fuse(cyl('z', 4, -14, 18, 320, -16), cyl('z', 6.5, 18, 26, 320, -16)))           # front hold-down
    add('Foot_bolt_front_' + T, s, G, 'M8 SHCS hold-down beside the wedge, hole D9.5 for adjustment', '', 'pitch')
    cut(foot.Label, m(cyl('z', 4.75, 0, 18, 320, -16))); cut('Datum_base_plate', m(cyl('z', 4, -14, 0, 320, -16)))
    s = m(cyl('z', 4, -10, 20, 345, -10))                                                   # dowel
    add('Foot_dowel_' + T, s, G, 'dowel D8x30, drilled and reamed through the flange into the datum plate AFTER alignment', '', 'pins')
    cut(foot.Label, s); cut('Datum_base_plate', s)
    for k, x in enumerate((300, 340), 1):                                                    # rear hold-down on the pivot rib
        s = m(fuse(cyl('z', 3, -12, 18, x, 172), cyl('z', 5, 18, 24, x, 172)))
        add('Foot_bolt_rear_%s%d' % (T, k), s, G, 'M6 SHCS on the pivot rib (loosen before turning the wedge)', '', 'pitch')
        cut(foot.Label, m(cyl('z', 3.5, 0, 18, x, 172))); cut('Datum_base_plate', m(cyl('z', 3, -12, 0, x, 172)))
    for k, (x, y) in enumerate(((300, 22), (340, 22), (300, 142), (340, 142)), 1):              # foot to column end taps
        s = m(fuse(cyl('z', 6.5, 1, 9, x, y), cyl('z', 4, 9, 38, x, y)))
        add('Foot_col_bolt_%s%d' % (T, k), s, G, 'M8 SHCS from below into the column end tap (foot is bolted to the column first)', '', '')
        cut(foot.Label, m(cyl('z', 7, 0.5, 9.5, x, y)), m(cyl('z', 4.5, 9.5, 18, x, y))); cut('Gantry_column_' + T, m(cyl('z', 4, 18, 38, x, y)))
    # yaw: push-pull pair in one block in front of the flange
    blk = box(300, 340, -84, -58, 0, 25).cut(cyl('y', 3, -84, -58, 312, 12)).cut(cyl('y', 3.5, -84, -58, 328, 12))
    for x in (304, 336): blk = blk.cut(cyl('z', 2.75, 0, 25, x, -71))
    add('Yaw_push_block_' + T, m(blk), G, 'steel block 40x26x25 on the datum plate in front of the foot flange: one push and one pull screw', '', 'yaw')
    add('Yaw_push_screw_' + T, m(fuse(cyl('y', 3, -94, -48, 312, 12), cyl('y', 5.5, -89, -84, 312, 12))), G,
        'M6x0.75 push screw + jam nut, tip on the flange front face', '', 'yaw')
    add('Yaw_pull_screw_' + T, m(fuse(cyl('y', 3, -84, -36, 328, 12), cyl('y', 5, -90, -84, 328, 12))), G,
        'M6x0.75 pull screw through the block into a tap in the flange: corrects an overshoot without walking the gantry', '', 'yaw')
    cut(foot.Label, m(cyl('y', 3, -48, -36, 328, 12)))
    for k, x in enumerate((304, 336), 1):
        add('Yaw_block_bolt_%s%d' % (T, k), m(fuse(cyl('z', 2.5, -10, 25, x, -71), cyl('z', 4.25, 25, 30, x, -71))), G, 'M5 SHCS', '', 'yaw')
        cut('Datum_base_plate', m(cyl('z', 2.5, -10, 0, x, -71)))
    for k, (x, z) in enumerate(((300, 270), (340, 270), (300, 450), (340, 450)), 1):           # X plate to column, set by fixture
        add('X_plate_bolt_%s%d' % (T, k), m(fuse(cyl('y', 4, 157, 182, x, z), cyl('y', 6.5, 182, 190, x, z))), G,
            'M8 SHCS + T-nut, X plate to column; the plate is positioned by a fixture, hole D9', '', '')
        cut('X_base_plate', m(cyl('y', 4.5, 162, 182, x, z)))

# ================================================================ layer 2: Z tram (saddle + Z plate)
zp = O('X_carriage_plate')
zp.Shape = box(-120, 120, 104, 122, 222, 710)
prop(zp, 'Spec', 'Z plate, steel t18 240x488: carries the Z rails, Z screw, Z motor plate. Rotates about the pivot pin on the saddle '
                 '(Z perp X), clamped by 6xM6 outside the Z-slide sweep')
tag('X_carriage_plate', 'ztram')
sad = fuse(box(-120, 120, 122, 134, 222, 706), box(120, 142, 122, 134, 652, 706), box(-142, -120, 122, 134, 652, 706))
add('X_saddle_plate', sad, '04 X-axis', 'saddle, steel t12 240x484 with two ears above the columns: bolted to the 4 X blocks and the X nut bracket; '
    'top 4 mm below the Z motor plate lip', 'x', 'ztram')
s = cyl('y', 5, 104, 134, 0, 250)
add('Z_tram_pivot_pin', s, G, 'dowel D10x30, pivot of the Z plate on the saddle (bottom centre)', 'x', 'ztram'); cut('X_carriage_plate', s); cut('X_saddle_plate', s)
s = cyl('y', 3, 104, 134, -108, 658)
add('Z_tram_lock_dowel', s, G, 'dowel D6x30, reamed through Z plate into saddle AFTER the tram is set', 'x', 'pins'); cut('X_carriage_plate', s); cut('X_saddle_plate', s)
k = 0
for x in (-108, 108):
    for z in (240, 620, 696):
        k += 1
        add('Z_tram_bolt_%d' % k, fuse(cyl('y', 5, 98, 104, x, z), cyl('y', 3, 104, 132, x, z)), G, 'M6 SHCS, Z plate to saddle; plate hole D7', 'x', 'ztram')
        cut('X_carriage_plate', cyl('y', 3.5, 104, 122, x, z)); cut('X_saddle_plate', cyl('y', 3, 122, 132, x, z))
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    add('Z_tram_block_' + T, m(box(124, 142, 104, 122, 664, 696).cut(cyl('x', 3, 124, 142, 113, 680)).cut(cyl('y', 2.75, 104, 122, 133, 670)).cut(cyl('y', 2.75, 104, 122, 133, 690))),
        G, 'steel block 18x18x32 on the saddle ear, beside the Z plate edge', 'x', 'ztram')
    add('Z_tram_screw_' + T, m(fuse(cyl('x', 3, 120, 150, 113, 680), cyl('x', 5.5, 142, 147, 113, 680))), G,
        'M6x0.5 push screw + jam nut, tip on the Z plate side edge, 430 above the pivot', 'x', 'ztram')
    for k, z in enumerate((670, 690), 1):
        add('Z_tram_block_bolt_%s%d' % (T, k), m(fuse(cyl('y', 4.25, 99, 104, 133, z), cyl('y', 2.5, 104, 132, 133, z))), G, 'M5 SHCS', 'x', 'ztram')
        cut('X_saddle_plate', m(cyl('y', 2.5, 122, 132, 133, z)))

# ================================================================ layer 3: spindle 3-point carrier
DY = -13                                                       # spindle axis moves forward
for l in ('Spindle_body', 'Spindle_fan_cover', 'Spindle_plug', 'Spindle_nose', 'ER11_nut', 'Tool_D5'):
    o = O(l); s = o.Shape.copy(); s.translate(V(0, DY, 0)); o.Shape = s; tag(l, 'spindle')
BOLTS = [(-64, 327), (64, 327), (50, 396)]                     # B1, B2 on the bar line, B3 on the nod wedge
PIN = (50, 327)                                                # roll pivot on the bar line, under the nod wedge
cl = O('Spindle_clamp')
c = fuse(box(-40, 40, -60, 26, 318, 406), box(40, 78, -14, 26, 318, 406), box(-78, -40, -14, 26, 318, 406))
c = c.cut(cyl('z', 32.5, 318, 406, 0, DY)).cut(box(-1, 1, -60, DY, 318, 406))
for z in (340, 384): c = c.cut(cyl('x', 3, -40, 30, -52, z)).cut(cyl('x', 5.5, 26, 40, -52, z))
for x, z in BOLTS: c = c.cut(cyl('y', 3.75, 0, 26, x, z)).cut(cyl('y', 7.5, -60, 0, x, z))
c = c.cut(cyl('y', 4, 20, 26, *PIN))
cl.Shape = c
prop(cl, 'Spec', '6061-T6 split clamp 156x86x88, bore D65 H7 at (x0, y-13), rear face milled in the same set-up as the bore, rear wall 6.5. '
                 'Stands 8 mm off the slide on 3 points: crowned bar (bottom line), nod wedge (top, x50). 3xM6 from the front with disc springs')
tag('Spindle_clamp', 'spindle')
for k, z in enumerate((340, 384), 1):
    add('Spindle_pinch_screw_%d' % k, fuse(cyl('x', 3, -30, 30, -52, z), cyl('x', 5, 30, 36, -52, z)), G,
        'M6 pinch screw across the front split; tighten to a fixed torque BEFORE tramming', 'z', 'spindle')
bar = box(-80, 80, 26, 34, 321, 333).cut(box(-44, 44, 26, 26.3, 321, 333))
for x, z in BOLTS[:2]: bar = bar.cut(cyl('y', 3.5, 26, 34, x, z))
bar = bar.cut(cyl('y', 4.25, 26, 34, *PIN))
for x in (-20, 20): bar = bar.cut(cyl('y', 2, 26, 34, x, 327))
add('Spindle_bar', bar, G, 'C45 ground bar 160x8x12, front face crowned R100 about X (apex z327) = the nod pivot line; relieved 0.3 over x+-44 '
    'so it touches only under the clamp lugs', 'z', 'spindle')
for k, x in enumerate((-20, 20), 1):
    add('Spindle_bar_screw_%d' % k, cyl('y', 2, 26.5, 42, x, 327), G, 'M4 countersunk, bar to slide', 'z', 'spindle')
    cut('Z_slide_plate', cyl('y', 2, 34, 42, x, 327))
s = cyl('y', 4, 20, 46, *PIN)
add('Spindle_roll_pin', s, G, 'D8 m6 hardened pin pressed 12 into the slide; engages the clamp 6 (barrelled end): roll pivot, on the nod line', 'z', 'spindle')
cut('Z_slide_plate', s)
base = prism_yz([(34, 378), (34, 414), (29.1, 414), (30.9, 378)], 38, 62).cut(cyl('y', 3.5, 29, 34, 50, 396))
add('Spindle_nod_wedge_base', base, G, '1.2510 hardened 1:20 wedge 24x36, 3.1..4.9 thick, fixed on the slide face', 'z', 'spindle')
sl = fuse(prism_yz([(26, 378), (26, 414), (29.1, 414), (30.9, 378)], 38, 62), box(38, 62, 26, 29.1, 414, 424), box(44, 56, 14, 26, 412, 424))
sl = sl.cut(box(46.7, 53.3, 25, 32, 387.5, 404.5)).cut(cyl('z', 2.5, 412, 424, 50, 20))
add('Spindle_nod_wedge', sl, G, '1.2510 hardened 1:20 slider, front face crowned R100, slot 6.6x17 for B3; moved along Z by the nod screw. '
    'Travel +-5 = +-0.25 mm = +-3.6 mrad nod', 'z', 'spindle')
add('Spindle_nod_bracket', box(40, 60, 14, 34, 430, 442).cut(cyl('z', 2.5, 430, 442, 50, 20)).cut(cyl('y', 2, 14, 34, 44, 436)).cut(cyl('y', 2, 14, 34, 56, 436)),
    G, 'steel bracket 20x20x12 on the slide face above the clamp, carries the nod screw', 'z', 'spindle')
for k, x in enumerate((44, 56), 1):
    add('Spindle_nod_bracket_bolt_%d' % k, fuse(cyl('y', 3.5, 10, 14, x, 436), cyl('y', 2, 14, 44, x, 436)), G, 'M4 SHCS', 'z', 'spindle')
    cut('Z_slide_plate', cyl('y', 2, 34, 44, x, 436))
add('Spindle_nod_screw', fuse(cyl('z', 2.5, 416, 448, 50, 20), cyl('z', 4.5, 448, 452, 50, 20)), G,
    'M5x0.5 nod screw from the top, captive in the slider tab: 1 turn = 25 um = 0.36 mrad; 10 deg = 10 urad (0.001/100)', 'z', 'spindle')
for k, (x, z) in enumerate(BOLTS, 1):
    add('Spindle_bolt_%d' % k, fuse(cyl('y', 5, -11, -5, x, z), cyl('y', 3, -5, 46, x, z)), G,
        'M6x50 SHCS from the front, through the support it loads; 6 Nm', 'z', 'spindle')
    add('Spindle_disc_springs_%d' % k, cyl('y', 7, -5, 0, x, z).cut(cyl('y', 3.6, -5, 0, x, z)), G,
        'hardened washer + 4 parallel DIN 2093 A14 disc springs (about 23 N/um): the joint can be adjusted at final preload', 'z', 'spindle')
    cut('Z_slide_plate', cyl('y', 3, 34, 46, x, z))
rb = box(-106, -79, 12, 34, 376, 420).cut(prism_xz([(-79, 380), (-79, 412), (-84.27, 412), (-82.13, 380)], 14, 30))
rb = rb.cut(cyl('z', 2.5, 410, 420, -81.5, 22))
for z in (384, 412): rb = rb.cut(cyl('y', 2.5, 12, 34, -98, z))
add('Spindle_roll_block', rb, G, 'C45 block 27x22x44 on the slide face left of the clamp, holds the roll wedge', 'z', 'spindle')
add('Spindle_roll_wedge', prism_xz([(-78, 384), (-78, 408), (-84, 408), (-82.4, 384)], 14, 30).cut(cyl('z', 2.5, 404, 408, -81.5, 22)), G,
    'hardened 1:15 side wedge, crowned face on the clamp lug side x-78 at z396 (69 above the roll pin). Travel +-4 = +-3.9 mrad', 'z', 'spindle')
add('Spindle_roll_screw', fuse(cyl('z', 2.5, 404, 428, -81.5, 22), cyl('z', 4.5, 428, 432, -81.5, 22)), G,
    'M5x0.5 roll screw from the top: 1 turn = 33 um = 0.48 mrad; 10 deg = 13 urad', 'z', 'spindle')
for k, z in enumerate((384, 412), 1):
    add('Spindle_roll_block_bolt_%d' % k, fuse(cyl('y', 4.25, 8, 12, -98, z), cyl('y', 2.5, 12, 46, -98, z)), G, 'M5 SHCS', 'z', 'spindle')
    cut('Z_slide_plate', cyl('y', 2.5, 34, 46, -98, z))
fb = box(80, 104, 12, 34, 384, 408).cut(cyl('x', 3, 80, 104, 22, 396))
for z in (388, 404): fb = fb.cut(cyl('y', 2.5, 12, 34, 96, z))
add('Spindle_follower_block', fb, G, 'steel block 24x22x24 on the slide face right of the clamp', 'z', 'spindle')
add('Spindle_follower_screw', fuse(cyl('x', 3, 78, 106, 22, 396), cyl('x', 5, 104, 108, 22, 396)), G,
    'M6x0.5 brass-tipped follower + jam nut, holds the clamp against the roll wedge (0.3 Nm)', 'z', 'spindle')
for k, z in enumerate((388, 404), 1):
    add('Spindle_follower_bolt_%d' % k, fuse(cyl('y', 4.25, 8, 12, 96, z), cyl('y', 2.5, 12, 46, 96, z)), G, 'M5 SHCS', 'z', 'spindle')
    cut('Z_slide_plate', cyl('y', 2.5, 34, 46, 96, z))

# ================================================================ rail references (all under 5.5 mm high: the blocks pass over them)
def refs(prefix, face, pin_r, ecc_r, scr_r, master, slave, at, pin_h, parent, motion):
    """face = mounting face coordinate (parts stick out towards -normal); master/slave = (pin side, screw side) across the rail.
    The side screws sit exactly opposite the pins, so they press the rail onto the pin without bending it."""
    a0, a1, b0, b1 = face - pin_h, face, face, face + 8
    def stud(r_head, r_shank, c, t, h=None):
        h0 = a0 if h is None else face - h
        return _c(r_head, h0, a1, c, t), _c(r_shank, b0, b1, c, t)
    for i, t in enumerate(at, 1):
        hd, sh = stud(pin_r, pin_r, master[0], t)
        add('%s_ref_pin_%d' % (prefix, i), fuse(hd, sh), G, 'reference dowel D%d pressed in, master rail leans on it' % (2 * pin_r), motion, 'rails'); cut(parent, sh)
        hd, sh = stud(ecc_r, pin_r, slave[0], t)
        add('%s_ecc_pin_%d' % (prefix, i), fuse(hd, sh), G, 'eccentric pin (head D%d, 0.25 offset, locked by a set screw), shifts the slave rail' % (2 * ecc_r), motion, 'rails'); cut(parent, sh)
        for side, c in (('M', master[1]), ('S', slave[1])):
            hd, sh = stud(scr_r, scr_r / 2.0, c, t, 2.5)
            add('%s_side_screw_%s%d' % (prefix, side, i), fuse(hd, sh), G, 'flat-head screw opposite the pin: its cone presses the rail onto the pin', motion, 'rails'); cut(parent, sh)

_c = lambda r, h0, h1, c, t: cyl('y', r, h0, h1, t, c)          # X rails on the X plate front face (y162)
refs('X', 162, 3, 5, 4, (237, 264), (455, 484), (-240, 0, 240), 4.5, 'X_base_plate', '')
_c = lambda r, h0, h1, c, t: cyl('y', r, h0, h1, c, t)          # Z rails on the Z plate front face (y104)
refs('Z', 104, 3, 5, 4, (-67, -94), (65, 94), (300, 462, 624), 4.5, 'X_carriage_plate', 'x')
_c = lambda r, h0, h1, c, t: cyl('z', r, h0, h1, c, t)          # Y rails on the table underside (z70)
refs('Y', 70, 4, 6, 6, (-133.5, -188.5), (131.5, 188.5), (-150, 50, 250), 7.0, 'Work_table', 'y')
for i, y in enumerate((-130, -30, 30, 130), 1):                   # master-side Y blocks on the datum plate
    add('Y_block_ref_pin_%d' % i, cyl('z', 4, -8, 12, -207, y), G, 'reference dowel D8 in the datum plate, master-side Y blocks lean on it', '', 'rails')
    cut('Datum_base_plate', cyl('z', 4, -8, 0, -207, y))

# ================================================================ measuring reference
add('Fixture_plate', box(-150, 150, 13 * -1 - 150, 237, 110, 135), '02 Y-axis',
    'Al fixture plate 300x400 t25 on the table (13 forward, under the moved spindle): skimmed by the machine itself, so its top is the '
    'X-Y motion plane. Skim once early (after the gantry is seated) and once at the end', 'y', 'measure')

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v11.FCStd'))

res = lambda lead_mm, lever: lead_mm / 36.0 / lever * 1e6       # urad per 10 deg of screw turn
L = ['v11 = v10 + adjusters.  new parts: %d' % len(NEW), '', 'ADJUSTER RESOLUTION (per 10 deg of screw turn):']
for name, lead, lever in (('1 pitch   1:10 wedge, M5x0.5, lever 206 to the rib', .5 / 10, 206),
                          ('1 yaw     M6x0.75 push-pull, columns 640 apart', .75, 640),
                          ('2 ztram   M6x0.5 push, 430 above the pivot', .5, 430),
                          ('3 nod     1:20 wedge, M5x0.5, lever 69', .5 / 20, 69),
                          ('3 roll    1:15 wedge, M5x0.5, lever 69', .5 / 15, 69)):
    r = res(lead, lever); L.append('  %-48s %5.1f urad  = %.4f mm / 100' % (name, r, r * 1e-4))
L.append('')
for l in ['Column_foot_R', 'X_carriage_plate', 'Spindle_clamp', 'Spindle_body', 'Tool_D5'] + NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-28s %-3s %-8s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, getattr(o, 'Motion', '') or '-', getattr(o, 'Adj', '') or '-',
             b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v11_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
