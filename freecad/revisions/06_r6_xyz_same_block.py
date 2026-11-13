# -*- coding: utf-8 -*-
"""r5 -> r6: X and Y motor blocks the same way as Z, table 440x473.5
Run from the repository root:  freecadcmd freecad/revisions/06_r6_xyz_same_block.py
(steps 01..07 in order; each opens the previous output in output/v3/)"""
import os
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v3', 'logs'); os.makedirs(LOG, exist_ok=True)
import FreeCAD as App, Part
from FreeCAD import Vector as V
doc = App.openDocument(ROOT+'/output/v3/CNC_v3_r5.FCStd')
def box(x0,x1,y0,y1,z0,z1): return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cylx(x0,x1,y,z,r): return Part.makeCylinder(r,x1-x0,V(x0,y,z),V(1,0,0))
def cyly(y0,y1,x,z,r): return Part.makeCylinder(r,y1-y0,V(x,y0,z),V(0,1,0))
def cylz(z0,z1,x,y,r): return Part.makeCylinder(r,z1-z0,V(x,y,z0),V(0,0,1))
O=lambda l: doc.getObjectsByLabel(l)[0]
grp=lambda p: [g for g in doc.Objects if g.TypeId=='App::DocumentObjectGroup' and g.Label.startswith(p)][0]
def newpart(name,shape,src,spec,g):
    o=doc.addObject('Part::Feature',name); o.Shape=shape
    for pn,val in (('Source',src),('Spec',spec)): o.addProperty('App::PropertyString',pn,'CNC'); setattr(o,pn,val)
    grp(g).addObject(o); return o
out=[]
for n in ('Y_support_fixed','Y_journal','Y_coupling','Y_motor','Work_table','X_support_fixed','X_coupling','X_motor','Z_motor_plate','X_carriage_plate'):
    b=O(n).Shape.BoundBox; out.append('%-16s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f]'%(n,b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))
# ---- X: Z-style block on the X rail plate FRONT face (bolts along y), lip against the rail-plate end face; joint plate back to plain
jp=O('Gantry_joint_plate_R'); jp.Shape=box(320,332,207,367,230,490)
if 'Spec' in jp.PropertiesList: jp.Spec='Al plate t12, column + beam ends'
XZ=410.0
xb=box(288,332,122,192,375,445).fuse(box(320,332,192,205,375,445))
xb=xb.cut(cylx(287,333,167,XZ,22)).cut(cylx(329,333,167,XZ,25.05))
for xx in (296,312):
    for zz in (382,438): xb=xb.cut(cyly(121,193,xx,zz,3.3))
newpart('X_motor_block',xb.removeSplitter(),'custom (machined)','Z-style block: bolted to X rail plate FRONT face 4xM6 (same face as rails/TEK), lip against rail-plate end face carries the rear motor holes; bore D44, pilot D50x3','04')
# ---- Y: Z-style block on the TABLE UNDERSIDE (bolts along z, same face as C-HLG45 rails / C-TEK12), lip against table rear end face
TE=263.5                                   # table rear end (flange face 279.5 - 16 lip)
t=box(-220,220,-210,TE,70,110)
for xs in (-160,-80,0,80,160): t=t.cut(box(xs-7,xs+7,-211,TE+1,98,111))
wt=O('Work_table'); wt.Shape=t
if 'Spec' in wt.PropertiesList: wt.Spec='440x473.5x40 (53.5 longer at rear), 5x T-slot 14, work area 300x300; underside: Y rails, C-TEK12, Y motor block'
doc.removeObject(O('Y_motor_plate').Name)
YZ=45.0
yb=box(-60,60,241.5,279.5,15,70).fuse(box(-60,60,TE,279.5,70,110))     # front part under the table, lip behind the table end
yb=yb.cut(cyly(240,281,0,YZ,22)).cut(cyly(276.5,281,0,YZ,25.05))
for xx in (-50,-34,34,50): yb=yb.cut(cylz(14,71,xx,252.5,3.3))           # 4x M6 from below into the table underside
newpart('Y_motor_block',yb.removeSplitter(),'custom (machined)','Z-style block: bolted UP into table underside 4xM6 (same face as rails/TEK), lip against table rear end face carries the upper motor holes; bore D44, pilot D50x3','02')
doc.recompute(); doc.saveAs(ROOT+'/output/v3/CNC_v3_r6.FCStd')
open(LOG+'/r6.txt','w').write('\n'.join(out))
