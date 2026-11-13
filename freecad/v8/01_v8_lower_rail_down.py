# -*- coding: utf-8 -*-
"""v8 from v7: lower X rail moved down to the bottom of the (v7, 315 mm) X base plate, X carriage extended down so
the lower blocks stay on it, X drive (screw / nut / housing / C-TEK12 / coupling / motor / motor block) moved down
close to the lower rail again (same rule as v6: nut housing 3 mm over the lower blocks).  Slot + motor pocket follow.
Run from the repository root:  freecadcmd freecad/v8/01_v8_lower_rail_down.py      Out: output/v8/CNC_v8.FCStd"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v8'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v7', 'CNC_v7.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def moved(s, dz): s = s.copy(); s.translate(V(0, 0, dz)); return s
def spec(o, txt):
    if 'Spec' not in o.PropertiesList: o.addProperty('App::PropertyString', 'Spec', 'CNC')
    o.Spec = txt

pl = O('X_base_plate'); pb = pl.Shape.BoundBox        # v7: z 175..490
r1 = O('X_rail_1').Shape.BoundBox                     # v7 lower rail z 290..310
b11 = O('X_block_11').Shape.BoundBox                  # z 279..321
nb = O('X_nut_bracket').Shape.BoundBox                # z 324..376 (axis 350)
car = O('X_carriage_plate'); cb = car.Shape.BoundBox  # z 272..710
RW = r1.ZMax - r1.ZMin; HB = (b11.ZMax - b11.ZMin) / 2; HN = (nb.ZMax - nb.ZMin) / 2

Z_LOW = pb.ZMin + 10 + RW / 2                         # lower rail 10 mm above the plate bottom -> 195
DZ_RAIL = Z_LOW - (r1.ZMin + r1.ZMax) / 2             # -105
Z_AX = Z_LOW + HB + 3 + HN                            # drive axis -> 245
DZ_AX = Z_AX - (nb.ZMin + nb.ZMax) / 2                # -105
ZC0 = Z_LOW - HB - 7                                  # carriage bottom: blocks 7 mm inside -> 167

# plate: same outline, slot + pocket moved with the drive
removed = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax).cut(pl.Shape)
newp = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax)
for s in removed.Solids:
    newp = newp.cut(moved(s, DZ_AX))
pl.Shape = newp.removeSplitter()
spec(pl, 'steel t20 %dx%d (z %d..%d) = gantry beam; X rails z %d / 470 (spacing %d); X drive axis z %d'
     % (pb.XLength, pb.ZLength, pb.ZMin, pb.ZMax, Z_LOW, 470 - Z_LOW, Z_AX))
# carriage extended down
car.Shape = car.Shape.fuse(box(cb.XMin, cb.XMax, cb.YMin, cb.YMax, ZC0, cb.ZMin)).removeSplitter()
spec(car, 'steel t30, %dx%d (z %d..%d), extended down for the lower X blocks' % (cb.XLength, cb.ZMax - ZC0, ZC0, cb.ZMax))
for l in ('X_rail_1', 'X_block_11', 'X_block_12'):
    o = O(l); o.Shape = moved(o.Shape, DZ_RAIL)
for l in ('X_ballscrew', 'X_ball_nut', 'X_nut_bracket', 'X_support_fixed', 'X_coupling', 'X_motor', 'X_motor_block'):
    o = O(l); o.Shape = moved(o.Shape, DZ_AX)

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v8.FCStd'))
L = ['lower rail z %.0f (dz %.0f); rail spacing %.0f; drive axis z %.0f (dz %.0f); carriage z %.0f..%.0f (+%.1f kg)'
     % (Z_LOW, DZ_RAIL, 470 - Z_LOW, Z_AX, DZ_AX, ZC0, cb.ZMax, cb.XLength * cb.YLength * (cb.ZMin - ZC0) * 7.85e-6)]
for l in ('X_base_plate', 'X_carriage_plate', 'X_rail_1', 'X_block_11', 'X_nut_bracket', 'X_support_fixed', 'X_motor',
          'X_motor_block', 'Work_table', 'Z_slide_plate', 'Electrical_panel'):
    b = O(l).Shape.BoundBox
    L.append('%-16s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f]' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
open(os.path.join(OUT, 'logs', 'v8_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
