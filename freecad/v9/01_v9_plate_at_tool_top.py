# -*- coding: utf-8 -*-
"""v9 from v8: X base plate bottom raised to the highest tool-tip position (tool tip at Z +50), top stays z 490.
Lower X rail, X carriage bottom and X drive follow with the same rules as v6/v8:
  lower rail 10 mm above the plate bottom; carriage bottom 7 mm under the lower blocks;
  X drive axis = nut housing 3 mm over the lower blocks.  Slot + motor pocket follow the drive.
Run from the repository root:  freecadcmd freecad/v9/01_v9_plate_at_tool_top.py      Out: output/v9/CNC_v9.FCStd"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v9'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v8', 'CNC_v8.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def moved(s, dz): s = s.copy(); s.translate(V(0, 0, dz)); return s
def spec(o, txt):
    if 'Spec' not in o.PropertiesList: o.addProperty('App::PropertyString', 'Spec', 'CNC')
    o.Spec = txt

Z_TRAVEL_UP = 50.0
TOOL_TOP = O('Tool_D5').Shape.BoundBox.ZMin + Z_TRAVEL_UP     # highest tool-tip position -> 230
pl = O('X_base_plate'); pb = pl.Shape.BoundBox                # v8: z 175..490
r1 = O('X_rail_1').Shape.BoundBox; b11 = O('X_block_11').Shape.BoundBox; nb = O('X_nut_bracket').Shape.BoundBox
car = O('X_carriage_plate'); cb = car.Shape.BoundBox
RW = r1.ZMax - r1.ZMin; HB = (b11.ZMax - b11.ZMin) / 2; HN = (nb.ZMax - nb.ZMin) / 2
ZR2 = (O('X_rail_2').Shape.BoundBox.ZMin + O('X_rail_2').Shape.BoundBox.ZMax) / 2

ZP0 = TOOL_TOP                                                # plate bottom
Z_LOW = ZP0 + 10 + RW / 2                                     # 250
DZ_RAIL = Z_LOW - (r1.ZMin + r1.ZMax) / 2
Z_AX = Z_LOW + HB + 3 + HN                                    # 300
DZ_AX = Z_AX - (nb.ZMin + nb.ZMax) / 2
ZC0 = Z_LOW - HB - 7                                          # 222

removed = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax).cut(pl.Shape)
newp = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, ZP0, pb.ZMax)
for s in removed.Solids:
    newp = newp.cut(moved(s, DZ_AX))
pl.Shape = newp.removeSplitter()
spec(pl, 'steel t20 %dx%d (z %d..%d, bottom = highest tool tip); X rails z %d / %d (spacing %d); X drive axis z %d'
     % (pb.XLength, pb.ZMax - ZP0, ZP0, pb.ZMax, Z_LOW, ZR2, ZR2 - Z_LOW, Z_AX))
car.Shape = car.Shape.common(box(cb.XMin - 1, cb.XMax + 1, cb.YMin - 1, cb.YMax + 1, ZC0, cb.ZMax + 1)).removeSplitter()
spec(car, 'steel t30, %dx%d (z %d..%d)' % (cb.XLength, cb.ZMax - ZC0, ZC0, cb.ZMax))
for l in ('X_rail_1', 'X_block_11', 'X_block_12'):
    o = O(l); o.Shape = moved(o.Shape, DZ_RAIL)
for l in ('X_ballscrew', 'X_ball_nut', 'X_nut_bracket', 'X_support_fixed', 'X_coupling', 'X_motor', 'X_motor_block'):
    o = O(l); o.Shape = moved(o.Shape, DZ_AX)

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v9.FCStd'))
L = ['tool top z %.0f -> plate z %.0f..%.0f (%.0f); lower rail z %.0f (spacing %.0f); drive axis z %.0f; carriage z %.0f..%.0f; plate %.2f kg'
     % (TOOL_TOP, ZP0, pb.ZMax, pb.ZMax - ZP0, Z_LOW, ZR2 - Z_LOW, Z_AX, ZC0, cb.ZMax, pl.Shape.Volume * 7.85e-6)]
for l in ('X_base_plate', 'X_carriage_plate', 'X_rail_1', 'X_block_11', 'X_nut_bracket', 'X_support_fixed', 'X_motor',
          'X_motor_block', 'Tool_D5', 'Work_table'):
    b = O(l).Shape.BoundBox
    L.append('%-16s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f]' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
open(os.path.join(OUT, 'logs', 'v9_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
