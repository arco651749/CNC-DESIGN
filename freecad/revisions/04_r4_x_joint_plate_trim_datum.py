# -*- coding: utf-8 -*-
"""r3 -> r4: X motor on joint plate, datum plate 640x512
Run from the repository root:  freecadcmd freecad/revisions/04_r4_x_joint_plate_trim_datum.py
(steps 01..07 in order; each opens the previous output in output/v3/)"""
import os
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v3', 'logs'); os.makedirs(LOG, exist_ok=True)
import FreeCAD as App, Part
from FreeCAD import Vector as V
doc = App.openDocument(ROOT+'/output/v3/CNC_v3_r3.FCStd')
def box(x0,x1,y0,y1,z0,z1): return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cylx(x0,x1,y,z,r): return Part.makeCylinder(r,x1-x0,V(x0,y,z),V(1,0,0))
O=lambda l: doc.getObjectsByLabel(l)[0]
out=[]
# what sits on the datum plate -> its outline
for n in ('Y_block_L1','Y_block_R2','Y_nut_bracket','Column_foot_L','Column_foot_R'):
    b=O(n).Shape.BoundBox; out.append('%-14s x[%6.1f,%6.1f] y[%6.1f,%6.1f]'%(n,b.XMin,b.XMax,b.YMin,b.YMax))
# X: flat motor plate = right joint plate extended forward (like the Y end plate), drop the block
doc.removeObject(O('X_motor_block').Name)
jp=O('Gantry_joint_plate_R')
jp.Shape=box(320,332,122,367,230,490).cut(cylx(319,333,167,410,22)).cut(cylx(329,333,167,410,25.05))
if 'Spec' in jp.PropertiesList: jp.Spec='Al plate t12, column + beam + rail-plate ends; extended forward = X motor plate (bore D44, pilot recess D50x3, motor bolted from outside)'
# datum plate trimmed to what it carries: front = block body -139.5 (-5), rear/sides flush with column feet
DP=(-320,320,-145,367)
dp=O('Datum_base_plate'); dp.Shape=box(DP[0],DP[1],DP[2],DP[3],-30,0)
if 'Spec' in dp.PropertiesList: dp.Spec='Q235 t30 640x512 milled datum plate (single face): Y block seats, Y nut seat, column feet'
out.append('datum plate %dx%d (was 690x595)'%(DP[1]-DP[0],DP[3]-DP[2]))
doc.recompute(); doc.saveAs(ROOT+'/output/v3/CNC_v3_r4.FCStd')
open(LOG+'/r4.txt','w').write('\n'.join(out))
