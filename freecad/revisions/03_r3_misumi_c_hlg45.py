# -*- coding: utf-8 -*-
"""r3: Y guide = MISUMI C-HLG45-700 vendor STEP (L700)
Run from the repository root:  freecadcmd freecad/revisions/03_r3_misumi_c_hlg45.py
(steps 01..07 in order; each opens the previous output in output/v3/)"""
import os
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v3', 'logs'); os.makedirs(LOG, exist_ok=True)
import FreeCAD as App, Part
from FreeCAD import Vector as V
doc = App.openDocument(ROOT+'/output/v3/CNC_v3_r3.FCStd')
def box(x0,x1,y0,y1,z0,z1): return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cylz(z0,z1,x,y,r): return Part.makeCylinder(r,z1-z0,V(x,y,z0),V(0,0,1))
O=lambda l: doc.getObjectsByLabel(l)[0]
def meta(o,src,spec):
    if 'Source' in o.PropertiesList: o.Source=src
    if 'Spec' in o.PropertiesList: o.Spec=spec
# MISUMI C-HLG45-700 vendor STEP: rail along +Zv (-665..35), height +Yv (rail base 0, block top 70), block hole centre Zv=7.19
vs = Part.Shape(); vs.read(ROOT+'/vendor/misumi/C-HLG45-700/C-HLG45-700.stp')
VR, VB = vs.Solids[0], Part.Compound([vs.Solids[1], vs.Solids[2]])
def place(sh, flip, t):
    s=sh.copy(); s.rotate(V(0,0,0),V(1,0,0),-90)          # Yv up -> -z (inverted), Zv -> +y
    if flip: s.rotate(V(0,0,0),V(0,0,1),180)               # rear block: grease nipple to the outside
    s.translate(V(*t)); return s
for side,xr in (('L',-160),('R',160)):
    r=O('Y_rail_'+side); r.Shape=place(VR,False,(xr,365,70))
    meta(r,'MISUMI (vendor STEP)','C-HLG45 rail L700 (inverted: base bolted to table underside, M12x35 from rail top, P105 E35)')
    for k,yc,flip in ((1,-72,False),(2,72,True)):
        b=O('Y_block_%s%d'%(side,k)); b.Shape=place(VB,flip,(xr,(yc+7.19) if flip else (yc-7.19),70))
        meta(b,'MISUMI (vendor STEP)','C-HLG45 standard block (fixed on datum plate, 4-M10x17 face down)')
doc.recompute(); doc.save()
out=[]
for o in doc.Objects:
    if o.Label.startswith(('Y_rail','Y_block')):
        b=o.Shape.BoundBox; out.append('%-12s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%5.1f,%5.1f]'%(o.Label,b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))
# quick interference of the guide parts against everything at the Y travel ends
P={o.Name:o for o in doc.Objects if o.TypeId=='Part::Feature'}
mov=lambda n: n.startswith(('Y_rail','Y_carrier','Work_table','Y_ballscrew','Y_support','Y_journal','Y_coupling','Y_motor'))
for dy in (-250,-50,150):
    for a in [n for n in P if n.startswith(('Y_rail','Y_block'))]:
        sa=P[a].Shape.copy()
        if mov(a): sa.translate(V(0,dy,0))
        for bn,bo in P.items():
            if bn==a or (a.startswith('Y_rail') and bn.startswith('Y_block')) or (a.startswith('Y_block') and bn.startswith('Y_rail')): continue
            if mov(a)==mov(bn) and mov(a): continue
            sb=bo.Shape.copy()
            if mov(bn): sb.translate(V(0,dy,0))
            if sa.BoundBox.intersect(sb.BoundBox):
                v=sa.common(sb).Volume
                if v>1: out.append('HIT dy=%d %s x %s %.0f'%(dy,a,bn,v))
    # rail must still cover both blocks
    out.append('dy=%d rail y[%.1f,%.1f] vs blocks y[%.1f,%.1f]'%(dy,-300+dy,400+dy,-72-67.5,72+67.5))
open(LOG+'/hlg.txt','w').write('\n'.join(out))
