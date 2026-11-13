# -*- coding: utf-8 -*-
"""v7 from v6: X base plate height +50% (210 -> 315 mm), extended DOWN (top stays at z 490).
Rails, X drive, slot and motor pocket stay where they are in v6 (the X carriage bottom z 272 limits the lower rail).
Run from the repository root:  freecadcmd freecad/v7/01_v7_taller_plate.py      Out: output/v7/CNC_v7.FCStd"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v7'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v6', 'CNC_v6.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

SCALE = 1.5
pl = O('X_base_plate'); pb = pl.Shape.BoundBox                    # v6: z 280..490 (210)
H6 = pb.ZMax - pb.ZMin
H7 = round(H6 * SCALE)                                             # 315
ZP0 = pb.ZMax - H7                                                 # 175
removed = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax).cut(pl.Shape)   # slot + motor pocket (v6 places)
newp = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, ZP0, pb.ZMax)
for s in removed.Solids:
    newp = newp.cut(s)
pl.Shape = newp.removeSplitter()
if 'Spec' not in pl.PropertiesList: pl.addProperty('App::PropertyString', 'Spec', 'CNC')
pl.Spec = 'steel t20 %dx%d (z %d..%d) = gantry beam (v6 height x1.5, extended down); rails / X drive as v6' % (pb.XLength, H7, ZP0, pb.ZMax)

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v7.FCStd'))
tt = O('Work_table').Shape.BoundBox
b = pl.Shape.BoundBox
open(os.path.join(OUT, 'logs', 'v7_build.txt'), 'w', encoding='utf-8').write(
    'X_base_plate z[%.0f,%.0f] height %.0f (v6 %.0f); mass %.2f kg (v6 %.2f kg); table top z %.0f -> gap %.0f mm'
    % (b.ZMin, b.ZMax, b.ZLength, H6, pl.Shape.Volume * 7.85e-6, (box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax).Volume - removed.Volume) * 7.85e-6,
       tt.ZMax, b.ZMin - tt.ZMax))
