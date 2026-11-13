# -*- coding: utf-8 -*-
"""r2 -> r3: Z/X blocks on the base faces, Y table +57.5
Run from the repository root:  freecadcmd freecad/revisions/02_r3_blocks_table_ext.py
(steps 01..07 in order; each opens the previous output in output/v3/)"""
import os
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v3', 'logs'); os.makedirs(LOG, exist_ok=True)
import FreeCAD as App, Part
from FreeCAD import Vector as V
doc = App.openDocument(ROOT+'/output/v3/CNC_v3_r2.FCStd')
def box(x0,x1,y0,y1,z0,z1): return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cylz(z0,z1,x,y,r): return Part.makeCylinder(r,z1-z0,V(x,y,z0),V(0,0,1))
def cyly(y0,y1,x,z,r): return Part.makeCylinder(r,y1-y0,V(x,y0,z),V(0,1,0))
O=lambda l: doc.getObjectsByLabel(l)[0]
cp=O('X_carriage_plate'); cp.Shape=box(-120,120,104,134,172,610)
if 'Spec' in cp.PropertiesList: cp.Spec='steel t30, 240x438; ALL holes on the front face (Z rails, C-TEK12, Z motor block)'
zb = box(-60,60,44,134,588,626).cut(box(-61,61,104,135,587,610))      # front part 588-610 on carriage face, lip 610-626 rests on carriage top
zb = zb.cut(cylz(587,627,0,79,22)).cut(cylz(623,627,0,79,25.05))       # coupling bore D44, pilot recess D50x3
for x in (-50,-34,34,50): zb = zb.cut(cyly(43,105,x,599,3.3))          # 4x M6 clearance, bolts from the front into the carriage face
zb = zb.removeSplitter()
o=O('Z_motor_plate'); o.Shape=zb
if 'Spec' in o.PropertiesList: o.Spec='block 120x90x38: front part bolted to carriage FRONT face with 4xM6 (same face as rails/TEK), rear lip rests on carriage top edge and carries the rear motor holes; bore D44, pilot D50x3'

# ---- Y: table 57.5 longer at the rear; screw assembly back to its v3 position; motor plate on the new rear face
EXT=57.5
def move(o,d):
    sh=o.Shape.copy(); sh.translate(V(*d)); o.Shape=sh
t=box(-220,220,-210,210+EXT,70,110)
for xs in (-160,-80,0,80,160): t=t.cut(box(xs-7,xs+7,-211,211+EXT,98,111))
wt=O('Work_table'); wt.Shape=t
if 'Spec' in wt.PropertiesList: wt.Spec='440x477.5x40 (57.5 longer at rear for the Y motor plate), 5x T-slot 14, work area 300x300'
for n in ('Y_ballscrew','Y_ball_nut','Y_support_fixed','Y_journal','Y_coupling','Y_motor'): move(O(n),(0,EXT,0))
nb=O('Y_nut_bracket'); nb.Shape=box(-60,60,-129,-114,0,66).cut(cyly(-130,-113,0,45,18))
yp=O('Y_motor_plate'); yp.Shape=box(-70,70,267.5,279.5,12,110).cut(cyly(266,281,0,45,22)).cut(cyly(276.5,281,0,45,25.05))

# ---- X: motor block thickened toward C-TEK12, bolted to the X rail plate FRONT face; joint plate back to original
jp=O('Gantry_joint_plate_R'); jp.Shape=box(320,332,207,367,230,490)
if 'Spec' in jp.PropertiesList: jp.Spec='Al plate t12, column + beam ends'
XZ=410.0
xb=box(288,332,122,192,375,445).fuse(box(320,332,192,205,375,445))     # front part on rail plate face, rear lip beside rail plate end face
xb=xb.cut(Part.makeCylinder(22,46,V(287,167,XZ),V(1,0,0))).cut(Part.makeCylinder(25.05,4,V(329,167,XZ),V(1,0,0)))
for xx in (296,312):
    for zz in (382,438): xb=xb.cut(cyly(121,193,xx,zz,3.3))           # 4x M6 from the front into the rail plate face
xb=xb.removeSplitter()
xo=doc.addObject('Part::Feature','X_motor_block'); xo.Shape=xb
for pn,val in (('Source','custom (machined)'),('Spec','block 44x83x70: front part bolted to X rail plate FRONT face with 4xM6 (same face as rails/TEK), rear lip against rail-plate end carries the rear motor holes; bore D44, pilot D50x3')):
    xo.addProperty('App::PropertyString',pn,'CNC'); setattr(xo,pn,val)
[g for g in doc.Objects if g.TypeId=='App::DocumentObjectGroup' and g.Label.startswith('04')][0].addObject(xo)
doc.recompute(); doc.saveAs(ROOT+'/output/v3/CNC_v3_r3.FCStd')
