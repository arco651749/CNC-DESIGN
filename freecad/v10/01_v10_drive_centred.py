# -*- coding: utf-8 -*-
"""v10 from v9: X drive (screw / nut / nut housing / C-TEK12 / coupling / motor / motor block) moved to the
neutral line midway between the two X rails, so the screw thrust adds no pitching moment on the carriage
(the Z-head moment is carried by the rails only).  Slot + motor pocket in the X base plate follow the drive.
Run from the repository root:  freecadcmd freecad/v10/01_v10_drive_centred.py      Out: output/v10/CNC_v10.FCStd"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v10'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v9', 'CNC_v9.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def moved(s, dz): s = s.copy(); s.translate(V(0, 0, dz)); return s
def spec(o, txt):
    if 'Spec' not in o.PropertiesList: o.addProperty('App::PropertyString', 'Spec', 'CNC')
    o.Spec = txt
zc = lambda l: (O(l).Shape.BoundBox.ZMin + O(l).Shape.BoundBox.ZMax) / 2

Z_LOW, Z_UP = zc('X_rail_1'), zc('X_rail_2')                  # 250 / 470
Z_AX_OLD = zc('X_nut_bracket')                                # 300
Z_AX = (Z_LOW + Z_UP) / 2                                     # 360 = neutral line
DZ = Z_AX - Z_AX_OLD

pl = O('X_base_plate'); pb = pl.Shape.BoundBox
removed = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax).cut(pl.Shape)   # slot + motor pocket
newp = box(pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax)
for s in removed.Solids:
    newp = newp.cut(moved(s, DZ))
pl.Shape = newp.removeSplitter()
spec(pl, 'steel t20 %dx%d (z %d..%d); X rails z %d / %d (spacing %d); X drive axis z %d = midway between the rails'
     % (pb.XLength, pb.ZLength, pb.ZMin, pb.ZMax, Z_LOW, Z_UP, Z_UP - Z_LOW, Z_AX))
for l in ('X_ballscrew', 'X_ball_nut', 'X_nut_bracket', 'X_support_fixed', 'X_coupling', 'X_motor', 'X_motor_block'):
    o = O(l); o.Shape = moved(o.Shape, DZ)

doc.recompute()
doc.saveAs(os.path.join(OUT, 'CNC_v10.FCStd'))
L = ['X rails z %.0f / %.0f -> drive axis z %.0f (was %.0f, dz %+.0f): offset from the rail mid-line %.1f mm'
     % (Z_LOW, Z_UP, Z_AX, Z_AX_OLD, DZ, zc('X_nut_bracket') - (Z_LOW + Z_UP) / 2)]
for l in ('X_base_plate', 'X_rail_1', 'X_rail_2', 'X_block_11', 'X_block_21', 'X_nut_bracket', 'X_ball_nut', 'X_support_fixed',
          'X_motor', 'X_motor_block', 'Electrical_panel', 'Servo_amp_X'):
    b = O(l).Shape.BoundBox
    L.append('%-16s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f]' % (l, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
open(os.path.join(OUT, 'logs', 'v10_build.txt'), 'w', encoding='utf-8').write('\n'.join(L))
