# -*- coding: utf-8 -*-
"""v3 -> r2: flat motor plates, Y guide H=70, gantry +12
Run from the repository root:  freecadcmd freecad/revisions/01_r2_flat_plates_h70_guide.py
(steps 01..07 in order; each opens the previous output in output/v3/)"""
import os
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v3', 'logs'); os.makedirs(LOG, exist_ok=True)
import FreeCAD as App, Part
from FreeCAD import Vector as V
doc = App.openDocument(ROOT+'/output/v3/CNC_v3.FCStd')
def box(x0,x1,y0,y1,z0,z1): return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cylx(x0,x1,y,z,r): return Part.makeCylinder(r,x1-x0,V(x0,y,z),V(1,0,0))
def cyly(y0,y1,x,z,r): return Part.makeCylinder(r,y1-y0,V(x,y0,z),V(0,1,0))
def cylz(z0,z1,x,y,r): return Part.makeCylinder(r,z1-z0,V(x,y,z0),V(0,0,1))
O = lambda l: doc.getObjectsByLabel(l)[0]
def setspec(o,txt):
    if 'Spec' in o.PropertiesList: o.Spec=txt
def setsrc(o,txt):
    if 'Source' in o.PropertiesList: o.Source=txt
def move(o,d):
    s=o.Shape.copy(); s.translate(V(*d)); o.Shape=s
log=[]
BIG=2000
# ===================== Y: taller guide H=70 (no carrier bars), end plate on table rear face
DH = 12.0                        # table underside 58 -> 70
for side,xr in (('L',-160),('R',160)):
    r=O('Y_rail_'+side); r.Shape=box(xr-22.5,xr+22.5,-290,390,32,70)
    setsrc(r,'linear guide size 45, H=70 (modelled from HIWIN HGH45CA dims; MISUMI equivalent TBD)')
    setspec(r,'rail 45x38, L680, inverted: bolted straight to table underside (no carrier bar)')
    for k,yc in ((1,-72),(2,72)):
        b=O('Y_block_%s%d'%(side,k))
        b.Shape=box(xr-43,xr+43,yc-69.7,yc+69.7,0,60.5).cut(box(xr-23.5,xr+23.5,yc-71,yc+71,31,61))
        setsrc(b,'linear guide size 45 block (HGH45CA dims, MISUMI equivalent TBD)'); setspec(b,'block 86x139.4, fixed on datum plate')
    doc.removeObject(O('Y_carrier_bar_'+side).Name)
move(O('Work_table'),(0,0,DH))
DY = -57.5                       # screw assembly forward so the motor flange sits on the end plate
for n in ('Y_ballscrew','Y_ball_nut','Y_support_fixed','Y_journal','Y_coupling','Y_motor'):
    move(O(n),(0,DY,DH))
YSZ = 33+DH                      # screw axis z = 45
nb=O('Y_nut_bracket'); nb.Shape=box(-60,60,-129+DY,-114+DY,0,54+DH).cut(cyly(-130+DY,-113+DY,0,YSZ,18))
setspec(nb,'steel t15, nut flange seat on datum plate (single face)')
yp=O('Y_motor_bracket'); yp.Label='Y_motor_plate'
yp.Shape=box(-70,70,210,222,12,98+DH).cut(cyly(209,223,0,YSZ,22)).cut(cyly(219,223,0,YSZ,25.05))
setspec(yp,'flat plate t12 140x98: bolted to table rear end face (y), motor bolted from outside (y); bore D44 for coupling, pilot recess D50x3')
# ===================== X: motor flange on the (extended) right joint plate, screw assembly 22.5 inboard
DX=-22.5
xs=O('X_ballscrew'); s=xs.Shape
A=s.common(box(-BIG,77.5,-BIG,BIG,-BIG,BIG)); B=s.common(box(100,BIG,-BIG,BIG,-BIG,BIG)); B.translate(V(DX,0,0))
xs.Shape=A.fuse(B).removeSplitter(); setspec(xs,'C-KBS1505-517.5 (shortened 22.5 for the joint-plate motor mount)')
for n in ('X_support_fixed','X_journal','X_coupling','X_motor'): move(O(n),(DX,0,0))
doc.removeObject(O('X_motor_bracket').Name)
jp=O('Gantry_joint_plate_R')
jp.Shape=box(320,332,122,367,218,478).cut(cylx(319,333,167,398,22)).cut(cylx(329,333,167,398,25.05))
setspec(jp,'Al plate t12, column + beam + rail-plate ends; extended forward = X motor plate (bore D44, pilot recess D50x3, motor bolted from outside)')
# ===================== Z: flat top plate on the carriage top edge, carriage 62 taller
cp=O('X_carriage_plate'); cp.Shape=box(-120,120,104,134,160,602); setspec(cp,'steel t30, 240x442 (top edge carries the Z motor plate)')
zp=O('Z_motor_bracket'); zp.Label='Z_motor_plate'
zp.Shape=box(-60,60,40,134,602,614).cut(cylz(601,615,0,79,22)).cut(cylz(611,615,0,79,25.05))
setspec(zp,'flat plate t12 120x94 on carriage top edge (bolts z), motor bolted from top; bore D44, pilot recess D50x3')
# ===================== gantry +12 so table-top -> beam clearance and tool reach stay the same
for side in ('L','R'):
    c=O('Gantry_column_'+side); s=c.Shape; cut=168
    lo=s.common(box(-BIG,BIG,-BIG,BIG,-BIG,cut)); hi=s.common(box(-BIG,BIG,-BIG,BIG,cut,BIG)); sl=s.common(box(-BIG,BIG,-BIG,BIG,cut-DH,cut))
    hi.translate(V(0,0,DH)); sl.translate(V(0,0,DH))
    c.Shape=lo.fuse([sl,hi]).removeSplitter(); setspec(c,'HFS8-80160-312')
shift=[]
for g in doc.Objects:
    if g.TypeId=='App::DocumentObjectGroup' and g.Label[:2] in ('03','04','05','06','07'):
        for o in g.Group:
            if o.Label.startswith(('Column_foot','Gantry_column')): continue
            shift.append(o)
for o in shift: move(o,(0,0,DH))
doc.recompute()
doc.saveAs(ROOT+'/output/v3/CNC_v3_r2.FCStd')
out=[]
for o in doc.Objects:
    if o.TypeId.startswith('Part::') and o.Label.startswith(('Y_','X_motor','X_coupl','X_support','X_journal','X_ballscrew','Z_motor','Z_coupl','Z_support','X_carriage','Gantry','Work','Datum')):
        b=o.Shape.BoundBox; out.append('%-22s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f]'%(o.Label,b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))
out.append('objects %d'%len(doc.Objects))
open(LOG+'/r2.txt','w').write('\n'.join(out))
