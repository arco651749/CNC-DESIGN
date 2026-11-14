# -*- coding: utf-8 -*-
"""v11 from v10 (frozen): every geometric relation that has to be set at assembly now has an adjuster in the model.

  yaw     X perp Y        push blocks in front of the foot flanges (M6x0.75), columns 640 apart
  pitch   Z perp Y        two M8x0.75 jack screws in each foot flange, foot pivots on its rear pad
  xlevel  X // datum      one M8x0.75 jack under each end of the X base plate, on a bracket on the column
  ztram   Z perp X        carriage split into saddle (on the X blocks) + Z plate; pivot pin low, push screws high
  spindle spindle // Z    long clamp ears: 4 jack screws (nod), pivot pin + opposed push screws (roll)
  rails   rail // rail    reference pins (master), eccentric pins (slave), flat-head side screws; low profile
  pins    lock            match-reamed dowels: foot flange / datum plate, Z plate / saddle, clamp / slide
  measure                 fixture plate (skimmed by the machine), indicator holder on the Z slide

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

# ---------------------------------------------------------------- 1. feet: flange, jacks, hold-down, dowel, yaw push
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    foot = O('Column_foot_' + T)
    foot.Shape = m(box(280, 360, -48, 182, 0, 18).cut(box(280, 360, -48, 150, 0, 0.5)))
    prop(foot, 'Spec', 'steel foot t18, 80x230: front flange 50 (jacks, hold-down bolt, dowel); underside relieved 0.5 except '
                       'the rear pad y150..182, so the foot pivots on the rear pad when the front jacks are turned')
    tag('Column_foot_' + T, 'pitch')
    for k, x in enumerate((300, 340), 1):                                      # jack screws
        s = m(cyl('z', 4, 0, 16, x, -34))
        add('Foot_jack_%s%d' % (T, k), s, G, 'M8x0.75 flat-point set screw, bears on the datum plate', '', 'pitch'); cut(foot.Label, s)
    s = m(fuse(cyl('z', 4, -14, 18, 320, -16), cyl('z', 6.5, 18, 26, 320, -16)))  # front hold-down
    add('Foot_bolt_front_' + T, s, G, 'M8 SHCS hold-down next to the jacks (push-pull), hole D9.5 for adjustment', '', 'pitch')
    cut(foot.Label, m(cyl('z', 4.75, 0, 18, 320, -16))); cut('Datum_base_plate', m(cyl('z', 4, -14, 0, 320, -16)))
    s = m(cyl('z', 4, -10, 20, 320, -34))                                      # dowel
    add('Foot_dowel_' + T, s, G, 'dowel D8x30, drilled and reamed through flange into datum plate AFTER alignment', '', 'pins')
    cut(foot.Label, s); cut('Datum_base_plate', s)
    for k, x in enumerate((300, 340), 1):                                      # rear hold-down (under the X plate, L-key from behind)
        s = m(fuse(cyl('z', 3, -12, 18, x, 172), cyl('z', 5, 18, 24, x, 172)))
        add('Foot_bolt_rear_%s%d' % (T, k), s, G, 'M6 SHCS hold-down on the rear pad', '', 'pitch')
        cut(foot.Label, m(cyl('z', 3.5, 0, 18, x, 172))); cut('Datum_base_plate', m(cyl('z', 3, -12, 0, x, 172)))
    for k, (x, y) in enumerate(((300, 22), (340, 22), (300, 142), (340, 142)), 1):   # foot to column end taps, from below
        s = m(fuse(cyl('z', 6.5, 1, 9, x, y), cyl('z', 4, 9, 38, x, y)))
        add('Foot_col_bolt_%s%d' % (T, k), s, G, 'M8 SHCS from below into the column end tap (foot is bolted to the column first)', '', '')
        cut(foot.Label, m(cyl('z', 7, 0, 9.5, x, y)), m(cyl('z', 4.5, 9.5, 18, x, y))); cut('Gantry_column_' + T, m(cyl('z', 4, 18, 38, x, y)))
    blk = m(box(300, 340, -84, -58, 0, 25))                                    # yaw push block
    scr = m(fuse(cyl('y', 3, -94, -48, 320, 10), cyl('y', 5.5, -89, -84, 320, 10)))
    bolts = [m(fuse(cyl('z', 2.5, -10, 25, x, -71), cyl('z', 4.25, 25, 30, x, -71))) for x in (308, 332)]
    add('Yaw_push_block_' + T, blk.cut(m(cyl('y', 3, -84, -58, 320, 10))).cut(m(cyl('z', 2.75, 0, 25, 308, -71))).cut(m(cyl('z', 2.75, 0, 25, 332, -71))),
        G, 'steel block 40x26x25 on the datum plate, in front of the foot flange', '', 'yaw')
    add('Yaw_push_screw_' + T, scr, G, 'M6x0.75 push screw + jam nut, tip on the flange front face', '', 'yaw')
    for k, b in enumerate(bolts, 1):
        add('Yaw_block_bolt_%s%d' % (T, k), b, G, 'M5 SHCS', '', 'yaw'); cut('Datum_base_plate', m(cyl('z', 2.5, -10, 0, (308, 332)[k - 1], -71)))

    # ------------------------------------------------------------ 2. X level: bracket on the column rear face, jack under the X plate edge
    br = m(box(290, 350, 162, 186, 192, 224))
    jk = m(fuse(cyl('z', 4, 184, 230, 320, 172), cyl('z', 6.5, 186, 192, 320, 172)))
    add('X_level_bracket_' + T, br.cut(m(cyl('z', 4, 192, 224, 320, 172))).cut(m(cyl('y', 3.3, 162, 186, 300, 208))).cut(m(cyl('y', 3.3, 162, 186, 340, 208))),
        G, 'steel block 60x24x32 on the column rear face (T-slots), under the X base plate', '', 'xlevel')
    add('X_level_jack_' + T, jk, G, 'M8x0.75 jack screw + jam nut, tip on the X plate bottom edge (carries the plate while its bolts are loose)', '', 'xlevel')
    for k, x in enumerate((300, 340), 1):
        add('X_level_bolt_%s%d' % (T, k), m(fuse(cyl('y', 3, 157, 186, x, 208), cyl('y', 5, 186, 192, x, 208))), G, 'M6 SHCS + T-nut', '', 'xlevel')
    for k, (x, z) in enumerate(((300, 270), (340, 270), (300, 450), (340, 450)), 1):   # X plate to column
        add('X_plate_bolt_%s%d' % (T, k), m(fuse(cyl('y', 4, 157, 182, x, z), cyl('y', 6.5, 182, 190, x, z))), G,
            'M8 SHCS + T-nut, X plate to column; plate hole D9.5 (level adjustment range)', '', 'xlevel')
        cut('X_base_plate', m(cyl('y', 4.75, 162, 182, x, z)))
tag('X_base_plate', 'xlevel')

# ---------------------------------------------------------------- 3. Z tram: carriage = saddle (on X blocks) + Z plate
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

# ---------------------------------------------------------------- 4. spindle tram: ears on the clamp
cl = O('Spindle_clamp')
cl.Shape = fuse(cl.Shape, box(48, 78, 16, 34, 319, 500), box(-78, -48, 16, 34, 319, 500))
prop(cl, 'Spec', 'split clamp D65, Al, with two mounting ears 30x18x181 (long on purpose: lever for the tram screws): 6xM6 to the slide, 4 jack screws (nod), pivot pin + 2 push screws (roll)')
tag('Spindle_clamp', 'spindle')
k = 0
for x in (-70, 70):
    for z in (339, 410, 480):
        k += 1
        add('Spindle_clamp_bolt_%d' % k, fuse(cyl('y', 5, 10, 16, x, z), cyl('y', 3, 16, 50, x, z)), G, 'M6 SHCS, clamp ear to Z slide; ear hole D6.8', 'z', 'spindle')
        cut('Spindle_clamp', cyl('y', 3.4, 16, 34, x, z)); cut('Z_slide_plate', cyl('y', 3, 34, 50, x, z))
k = 0
for x in (-56, 56):
    for z in (325, 494):
        k += 1
        s = cyl('y', 3, 15, 34, x, z)
        add('Spindle_nod_jack_%d' % k, s, G, 'M6x0.5 flat-point set screw through the ear, bears on the slide face (169 apart in Z)', 'z', 'spindle'); cut('Spindle_clamp', s)
s = cyl('y', 3, 16, 46, -70, 325)
add('Spindle_pivot_pin', s, G, 'dowel D6x30, roll pivot of the clamp on the slide', 'z', 'spindle'); cut('Spindle_clamp', s); cut('Z_slide_plate', s)
for sgn, T in ((1, 'R'), (-1, 'L')):
    m = lambda s: mir(s, sgn)
    add('Spindle_roll_block_' + T, m(box(80, 98, 14, 34, 474, 504).cut(cyl('x', 2.5, 80, 98, 24, 484)).cut(cyl('y', 2.2, 14, 34, 89, 497))), G,
        'steel block 18x20x30 on the slide face, beside the top of the clamp ear', 'z', 'spindle')
    add('Spindle_roll_screw_' + T, m(fuse(cyl('x', 2.5, 78, 104, 24, 484), cyl('x', 4.5, 98, 102, 24, 484))), G,
        'M5x0.5 push screw + jam nut, tip on the ear side face, 159 above the pivot pin', 'z', 'spindle')
    add('Spindle_roll_block_bolt_' + T, m(fuse(cyl('y', 3.5, 10, 14, 89, 497), cyl('y', 2, 14, 46, 89, 497))), G, 'M4 SHCS', 'z', 'spindle')
    cut('Z_slide_plate', m(cyl('y', 2, 34, 46, 89, 497)))

# ---------------------------------------------------------------- 5. rail references (all under 5.5 mm high: the blocks pass over them)
def refs(prefix, ax, face, sgn, pin_r, ecc_r, scr_r, master, slave, pin_at, scr_at, pin_h, parent, motion):
    """ax = rail direction; face = mounting face coordinate; sgn = +1 if parts stick out towards +normal.
    master/slave = (reference side coordinate, screw side coordinate) across the rail."""
    a0, a1 = (face, face + sgn * pin_h) if sgn > 0 else (face - pin_h, face)       # the visible part
    b0, b1 = (face - 8, face) if sgn > 0 else (face, face + 8)                     # the part in the plate
    def stud(r_head, r_shank, c, t, h=None):
        h0, h1 = (a0, a1) if h is None else ((face, face + sgn * h) if sgn > 0 else (face - h, face))
        return _c(r_head, h0, h1, c, t), _c(r_shank, b0, b1, c, t)
    for i, t in enumerate(pin_at, 1):
        hd, sh = stud(pin_r, pin_r, master[0], t)
        add('%s_ref_pin_%d' % (prefix, i), fuse(hd, sh), G, 'reference dowel D%d pressed in, master rail leans on it' % (2 * pin_r), motion, 'rails'); cut(parent, sh)
        hd, sh = stud(ecc_r, pin_r, slave[0], t)
        add('%s_ecc_pin_%d' % (prefix, i), fuse(hd, sh), G, 'eccentric pin (head D%d, 0.25 offset), turned with a hex key to shift the slave rail' % (2 * ecc_r), motion, 'rails'); cut(parent, sh)
    for i, t in enumerate(scr_at):
        for side, c in (('M', master[1]), ('S', slave[1])):
            hd, sh = stud(scr_r, scr_r / 2.0, c, t, 2.5)
            add('%s_side_screw_%s%s' % (prefix, side, 'abcd'[i]), fuse(hd, sh), G, 'flat-head screw beside the rail: its cone presses the rail onto the pins', motion, 'rails'); cut(parent, sh)

# X rails on the X base plate front face (y162, parts stick out towards -y); rail 1 z240..260 master (rests on pins by gravity), rail 2 z460..480 slave
_c = lambda r, h0, h1, c, t: cyl('y', r, h0, h1, t, c)
refs('X', 'x', 162, -1, 3, 5, 4, (237, 264), (455, 484), (-240, 0, 240), (-210, -70, 70, 210), 4.5, 'X_base_plate', '')
# Z rails on the Z plate front face (y104, towards -y); rail L x-90..-70 master (pins on the inner side), rail R slave
_c = lambda r, h0, h1, c, t: cyl('y', r, h0, h1, c, t)
refs('Z', 'z', 104, -1, 3, 5, 4, (-67, -94), (65, 94), (300, 462, 624), (320, 420, 520, 600), 4.5, 'X_carriage_plate', 'x')
# Y rails on the table underside (z70, towards -z); rail L x-182.5..-137.5 master (pins on the inner side), rail R slave
_c = lambda r, h0, h1, c, t: cyl('z', r, h0, h1, c, t)
refs('Y', 'y', 70, -1, 4, 6, 6, (-133.5, -188.5), (131.5, 188.5), (-150, 50, 250), (-100, 20, 140, 240), 7.0, 'Work_table', 'y')
for i, y in enumerate((-130, -30, 30, 130), 1):                                   # master-side Y blocks on the datum plate
    s = cyl('z', 4, -8, 12, -207, y)
    add('Y_block_ref_pin_%d' % i, s, G, 'reference dowel D8 in the datum plate, master-side Y blocks lean on it', '', 'rails'); cut('Datum_base_plate', cyl('z', 4, -8, 0, -207, y))

# ---------------------------------------------------------------- 6. measuring aids
add('Fixture_plate', box(-150, 150, -150, 250, 110, 135), '02 Y-axis',
    'Al fixture plate 300x400 t25 on the table: skimmed by the machine itself, so its top is the X-Y motion plane (tool reaches 5 mm below its top)', 'y', 'measure')
add('Indicator_holder', box(-106, -82, 12, 34, 320, 345).cut(cyl('z', 4, 320, 345, -94, 22)), G,
    'block with a D8 stem bore on the Z slide: holds the test indicator on the spindle side for every squareness check', 'z', 'measure')

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v11.FCStd'))

L = ['v11 = v10 + adjusters.  new parts: %d' % len(NEW), '']
res = lambda pitch, lever, deg=10: pitch * deg / 360.0 / lever * 1e6
L += ['ADJUSTER RESOLUTION (per 10 deg of screw turn):',
      '  yaw     M6x0.75 push, columns 640 apart      %5.0f urad  -> %.4f mm over X 300' % (res(.75, 640), res(.75, 640) * 300e-6),
      '  pitch   M8x0.75 jack, 200 from the rear pad  %5.0f urad  -> %.4f mm over Z 100' % (res(.75, 200), res(.75, 200) * 100e-6),
      '  xlevel  M8x0.75 jack, 640 apart              %5.0f urad  -> %.4f mm over X 300' % (res(.75, 640), res(.75, 640) * 300e-6),
      '  ztram   M6x0.5 push, 430 above the pivot     %5.0f urad  -> %.4f mm over Z 100' % (res(.5, 430), res(.5, 430) * 100e-6),
      '  spindle nod  M6x0.5 jack, 169 apart          %5.0f urad  -> %.4f mm over 100' % (res(.5, 169), res(.5, 169) * 100e-6),
      '  spindle roll M5x0.5 push, 159 above the pin  %5.0f urad  -> %.4f mm over 100' % (res(.5, 159), res(.5, 159) * 100e-6), '']
for l in ['Column_foot_R', 'X_carriage_plate', 'Spindle_clamp'] + NEW:
    o = O(l); b = o.Shape.BoundBox
    L.append('%-26s %-7s %-7s x[%7.1f,%7.1f] y[%7.1f,%7.1f] z[%7.1f,%7.1f]  %s' % (l, getattr(o, 'Motion', '') or '-', getattr(o, 'Adj', '') or '-',
             b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, 'OK' if o.Shape.isValid() and o.Shape.Volume > 0 else 'INVALID'))
open(os.path.join(OUT, 'logs', 'v11_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
