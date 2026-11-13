# -*- coding: utf-8 -*-
"""v6 from v4: X base plate extended DOWN, lower X rail moved down, X drive (screw / nut / C-TEK12 / coupling /
motor / motor block) moved down close to the lower rail (no longer centred between the rails).
  - plate z 330..490 -> ZP0..490; lower rail z 350 -> Z_LOW (lowest the X carriage allows: blocks inside z>=272)
  - X drive axis z 410 -> Z_AX: nut housing (z +-26) must clear the lower blocks (top = Z_LOW + 21) by 3 mm
  - slot and the 7 mm motor pocket move with the drive
  - upper rail, carriage, Z axis, columns unchanged
Run from the repository root:  freecadcmd freecad/v6/01_v6_lower_rail.py      Out: output/v6/CNC_v6.FCStd"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v6'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v4', 'CNC_v4.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def moved(s, dz): s = s.copy(); s.translate(V(0, 0, dz)); return s
def spec(o, txt):
    if 'Spec' not in o.PropertiesList: o.addProperty('App::PropertyString', 'Spec', 'CNC')
    o.Spec = txt

car = O('X_carriage_plate').Shape.BoundBox          # z 272..710
r1 = O('X_rail_1').Shape.BoundBox                   # lower rail z 340..360
b11 = O('X_block_11').Shape.BoundBox                # lower block z 329..371 (width 42)
nb = O('X_nut_bracket').Shape.BoundBox              # z 384..436 (axis 410)
Z_AX0 = (nb.ZMin + nb.ZMax) / 2
HALF_BLK = (b11.ZMax - b11.ZMin) / 2                # 21
HALF_NB = (nb.ZMax - nb.ZMin) / 2                   # 26

Z_LOW = car.ZMin + HALF_BLK + 7                     # lower rail centre: blocks 7 mm inside the carriage bottom -> 300
DZ_RAIL = Z_LOW - (r1.ZMin + r1.ZMax) / 2           # -50
Z_AX = Z_LOW + HALF_BLK + 3 + HALF_NB               # drive axis: nut housing 3 mm over the lower blocks -> 350
DZ_AX = Z_AX - Z_AX0                                # -60
ZP0 = Z_LOW - (r1.ZMax - r1.ZMin) / 2 - 10          # plate bottom 10 mm under the lower rail -> 280

# ---------------- X base plate: new outline, slot + motor pocket moved with the drive
pl = O('X_base_plate'); pb = pl.Shape.BoundBox
removed = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax).cut(pl.Shape)   # slot (through) + pocket
newp = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, ZP0, pb.ZMax)
for s in removed.Solids:
    newp = newp.cut(moved(s, DZ_AX))
pl.Shape = newp.removeSplitter()
spec(pl, 'steel t20 %dx%d (z %d..%d) = gantry beam; front: X rails z %d / %d; rear: X drive axis z %d (near the lower rail)'
     % (pb.XLength, pb.ZMax - ZP0, ZP0, pb.ZMax, Z_LOW, (O('X_rail_2').Shape.BoundBox.ZMin + O('X_rail_2').Shape.BoundBox.ZMax) / 2, Z_AX))

# ---------------- lower rail + blocks down
for l in ('X_rail_1', 'X_block_11', 'X_block_12'):
    o = O(l); o.Shape = moved(o.Shape, DZ_RAIL)
# ---------------- X drive down
for l in ('X_ballscrew', 'X_ball_nut', 'X_nut_bracket', 'X_support_fixed', 'X_coupling', 'X_motor', 'X_motor_block'):
    o = O(l); o.Shape = moved(o.Shape, DZ_AX)

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v6.FCStd'))
L = ['plate z %d..%d (was %d..%d); lower rail z %.0f (dz %.0f); drive axis z %.0f (dz %.0f); rail spacing %.0f (was %.0f)'
     % (ZP0, pb.ZMax, pb.ZMin, pb.ZMax, Z_LOW, DZ_RAIL, Z_AX, DZ_AX,
        (O('X_rail_2').Shape.BoundBox.ZMin + O('X_rail_2').Shape.BoundBox.ZMax) / 2 - Z_LOW,
        (O('X_rail_2').Shape.BoundBox.ZMin + O('X_rail_2').Shape.BoundBox.ZMax) / 2 - (Z_LOW - DZ_RAIL))]
for l in ('X_base_plate', 'X_rail_1', 'X_block_11', 'X_rail_2', 'X_ballscrew', 'X_ball_nut', 'X_nut_bracket', 'X_support_fixed',
          'X_coupling', 'X_motor', 'X_motor_block', 'X_carriage_plate', 'Electrical_panel'):
    b = O(l).Shape.BoundBox
    L.append('%-16s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f]' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
open(os.path.join(OUT, 'logs', 'v6_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
