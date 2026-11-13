# -*- coding: utf-8 -*-
"""r4 -> r5: Z assembly +100, spindle mounted lower (tool tip unchanged)
Run from the repository root:  freecadcmd freecad/revisions/05_r5_raise_z_assembly.py
(steps 01..07 in order; each opens the previous output in output/v3/)"""
import os
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v3', 'logs'); os.makedirs(LOG, exist_ok=True)
import FreeCAD as App
from FreeCAD import Vector as V
doc = App.openDocument(ROOT+'/output/v3/CNC_v3_r4.FCStd')
DZ=100.0
out=[]
def bbz(l):
    b=doc.getObjectsByLabel(l)[0].Shape.BoundBox; return '%s z[%.0f,%.0f]'%(l,b.ZMin,b.ZMax)
out.append('before: '+', '.join(bbz(l) for l in ('X_carriage_plate','Z_slide_plate','Spindle_clamp','Spindle_body','Tool_D5')))
for o in doc.Objects:
    if o.TypeId.startswith('Part::') and (o.Label.startswith('Z_') or o.Label=='X_carriage_plate'):
        s=o.Shape.copy(); s.translate(V(0,0,DZ)); o.Shape=s
cp=doc.getObjectsByLabel('X_carriage_plate')[0]
if 'Spec' in cp.PropertiesList: cp.Spec=str(cp.Spec)+'; Z assembly raised 100 (spindle mounted 100 lower in the slide, tool tip unchanged)'
out.append('after:  '+', '.join(bbz(l) for l in ('X_carriage_plate','Z_slide_plate','Spindle_clamp','Spindle_body','Tool_D5','Z_motor')))
doc.recompute(); doc.saveAs(ROOT+'/output/v3/CNC_v3_r5.FCStd')
open(LOG+'/r5.txt','w').write('\n'.join(out))
