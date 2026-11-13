# -*- coding: utf-8 -*-
"""v5 from v4: the X head rides on a FRONT and a REAR rail (saddle over a box beam), so the head's moment is taken
by the front/rear rail pair instead of twisting the single X base plate.
  - box beam: v4 X base plate (front, slot kept) + rear plate + top plate + bottom plate (all t20 steel)
  - rails: front upper rail kept (z 470), front lower rail + its 2 blocks removed, rear rail on the rear plate's
    rear face at the same height (mirror of the front rail, same MISUMI SX2RNL28-540)
  - saddle: bridge plate from the X carriage rear face over the box top to a rear plate carrying the 2 rear blocks
  - X screw / nut / C-TEK12 / X motor unchanged (inside the box, nut housing still through the front-plate slot)
  - electrics (panel + 3 drives) untouched for now: they collide with the rear plate/saddle -> relocate later
Run from the repository root:  freecadcmd freecad/v5/01_v5_saddle.py      Out: output/v5/CNC_v5.FCStd"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v5'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v4', 'CNC_v4.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def grp(p): return [g for g in doc.Objects if g.TypeId == 'App::DocumentObjectGroup' and g.Label.startswith(p)][0]
def meta(o, src, spec):
    for pn, val in (('Source', src), ('Spec', spec)):
        if pn not in o.PropertiesList: o.addProperty('App::PropertyString', pn, 'CNC')
        setattr(o, pn, val)
def new(name, shape, g, src, spec):
    o = doc.addObject('Part::Feature', name); o.Shape = shape; o.Label = name; meta(o, src, spec); grp(g).addObject(o); return o

# ---------------- key planes (from v4)
fp = O('X_base_plate').Shape.BoundBox            # front plate y 162..182, z 330..490
YF0, YF1, ZB0, ZB1, XB = fp.YMin, fp.YMax, fp.ZMin, fp.ZMax, fp.XMax
T = 20.0                                          # box plates t20
YR0 = 250.0                                       # rear plate front face (clears X motor block y<=242, nut <=230)
YR1 = YR0 + T                                     # rear plate rear face = rear rail base
r2 = O('X_rail_2').Shape.BoundBox                 # front upper rail y 146..162 (base on the plate front face)
ZRAIL = (r2.ZMin + r2.ZMax) / 2                   # 470
YMIR = (YF0 + YR1) / 2                            # mirror plane: front rail base y=YF0 <-> rear rail base y=YR1


def mirror_y(shape):
    m = App.Matrix(); m.A22 = -1; m.A24 = 2 * YMIR    # y' = 2*YMIR - y
    return shape.transformGeometry(m)


# ---------------- remove the lower front rail and its blocks
for l in ('X_rail_1', 'X_block_11', 'X_block_12'):
    doc.removeObject(O(l).Name)

# ---------------- box beam
new('Box_rear_plate', box(-XB, XB, YR0, YR1, ZB0, ZB1), '03', 'custom (machined)',
    'steel t20 %dx%d, rear face milled = rear X rail datum' % (2 * XB, ZB1 - ZB0))
new('Box_top_plate', box(-XB, XB, YF1, YR0, ZB1 - T, ZB1), '03', 'custom (machined)', 'steel t20, closes the box (top)')
new('Box_bottom_plate', box(-XB, XB, YF1, YR0, ZB0, ZB0 + T), '03', 'custom (machined)', 'steel t20, closes the box (bottom)')

# ---------------- rear rail + blocks (mirror of the front upper rail / blocks)
rr = new('X_rail_rear', mirror_y(O('X_rail_2').Shape), '04', 'MISUMI', 'SX2RNL28-540 rail on the box rear face (z %d)' % ZRAIL)
for f, n in (('X_block_21', 'X_block_R1'), ('X_block_22', 'X_block_R2')):
    new(n, mirror_y(O(f).Shape), '04', 'MISUMI', 'SX2RNL28 block, rear rail')

# ---------------- saddle: bridge over the box top + rear plate on the rear blocks
car = O('X_carriage_plate').Shape.BoundBox        # y 104..134
fb = O('X_block_21').Shape.BoundBox               # front blocks y 134..156, z 449..491
# mirrored B-spline bounding boxes are loose -> take the rear-block planes from the mirror formula
RB_FACE = 2 * YMIR - fb.YMin                      # rear block mount face (front block mount face y=134 mirrored)
ZBR0 = max(ZB1, fb.ZMax) + 4                      # 4 mm over the box top / block tops
BT = 20.0
YS1 = RB_FACE + 20                                 # rear saddle plate t20
new('X_saddle_bridge', box(car.XMin, car.XMax, car.YMax, YS1, ZBR0, ZBR0 + BT), '04', 'custom (machined)',
    'steel t20 bridge: X carriage rear face -> over the box top -> rear saddle plate')
new('X_saddle_rear', box(car.XMin, car.XMax, RB_FACE, YS1, fb.ZMin - 9, ZBR0), '04', 'custom (machined)',
    'steel t20 rear saddle plate carrying the 2 rear blocks')

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v5.FCStd'))
lines = ['front plate y[%.0f,%.0f] z[%.0f,%.0f]; rear plate y[%.0f,%.0f]; rail z %.0f; mirror y %.1f' % (YF0, YF1, ZB0, ZB1, YR0, YR1, ZRAIL, YMIR),
         'saddle bridge z[%.0f,%.0f] y[%.0f,%.0f]; rear saddle y[%.1f,%.1f]' % (ZBR0, ZBR0 + BT, car.YMax, YS1, RB_FACE, YS1)]
for l in ('X_rail_2', 'X_rail_rear', 'X_block_21', 'X_block_R1', 'X_saddle_bridge', 'X_saddle_rear', 'Box_rear_plate', 'Box_top_plate', 'Box_bottom_plate'):
    b = O(l).Shape.BoundBox
    lines.append('%-16s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f] vol %.0f' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, O(l).Shape.Volume))
open(os.path.join(OUT, 'logs', 'v5_build.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
