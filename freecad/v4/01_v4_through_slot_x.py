# -*- coding: utf-8 -*-
"""v4 from v3 r7: X drive behind the X base plate (through-slot), X base plate t20 = gantry beam,
columns forward to the Y blocks, datum plate t20.  Y and Z as r7.
Run from the repository root:  freecadcmd freecad/v4/01_v4_through_slot_x.py"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v4', 'logs'); os.makedirs(LOG, exist_ok=True)
doc = App.openDocument(ROOT + '/output/v3/CNC_v3_r7.FCStd')
BIG = 3000
R7_COUPLING = doc.getObjectsByLabel('X_coupling')[0].Shape.copy()
R7_MOTOR = doc.getObjectsByLabel('X_motor')[0].Shape.copy()
def box(x0,x1,y0,y1,z0,z1): return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cylx(x0,x1,y,z,r): return Part.makeCylinder(r,x1-x0,V(x0,y,z),V(1,0,0))
def cyly(y0,y1,x,z,r): return Part.makeCylinder(r,y1-y0,V(x,y0,z),V(0,1,0))
O = lambda l: doc.getObjectsByLabel(l)[0]
def grp(p): return [g for g in doc.Objects if g.TypeId=='App::DocumentObjectGroup' and g.Label.startswith(p)][0]
def meta(o, src=None, spec=None):
    for pn,val in (('Source',src),('Spec',spec)):
        if val is None: continue
        if pn not in o.PropertiesList: o.addProperty('App::PropertyString',pn,'CNC')
        setattr(o,pn,val)
def new(name, shape, g, src, spec):
    o = doc.addObject('Part::Feature', name); o.Shape = shape; meta(o, src, spec); grp(g).addObject(o); return o
def rm(*labels):
    for l in labels: doc.removeObject(O(l).Name)
def moved(sh, d): s = sh.copy(); s.translate(V(*d)); return s

# ---------------- key planes
YPF, T = 162.0, 20.0              # X base plate front face (30 closer: spacer bars gone), thickness
YPR = YPF + T                     # 182 rear face
XS_Y, XS_Z = YPR + 25, 410.0      # X screw axis behind the plate (C-TEK12 centre height 25)
CX0, CX1 = 280.0, 360.0           # columns |x|
CY0, CY1 = YPF - 160, YPF         # columns y 2..162 (front at the rear Y blocks)
DZ0 = -20.0                       # datum plate t20

# ---------------- base: datum plate t20, trimmed to what it carries
dp = O('Datum_base_plate'); dp.Shape = box(-CX1, CX1, -145, YPR, DZ0, 0)
meta(dp, spec='Q235 t20 720x327 milled datum plate (single face): Y block seats, Y nut seat, column feet')

# ---------------- gantry: no beams / joint plates; columns forward; X base plate t20 bolted to the column rear faces
rm('Gantry_beam_1', 'Gantry_beam_2', 'Gantry_joint_plate_L', 'Gantry_joint_plate_R', 'X_rail_plate')
for side, sx in (('L', -1), ('R', 1)):
    c = O('Gantry_column_' + side); s = c.Shape; b = s.BoundBox
    s = moved(s, ((CX0 - b.XMin) if sx > 0 else (-CX0 - b.XMax), CY0 - b.YMin, 0))   # inner face at |x|=280, y 2..162
    cut = 174.0
    lo = s.common(box(-BIG,BIG,-BIG,BIG,-BIG,cut)); hi = moved(s.common(box(-BIG,BIG,-BIG,BIG,cut,BIG)), (0,0,160))
    sl = moved(s.common(box(-BIG,BIG,-BIG,BIG,18,178)), (0,0,cut-18))
    c.Shape = lo.fuse([sl, hi]).removeSplitter(); meta(c, spec='HFS8-80160-472 (z18..490)')
    f = O('Column_foot_' + side); f.Shape = box(min(sx*CX0, sx*CX1), max(sx*CX0, sx*CX1), CY0, YPR, 0, 18)
SLOT = (-181.0, 166.0, 380.0, 440.0)
xp = box(-CX1, CX1, YPF, YPR, 330, 490).cut(box(SLOT[0], SLOT[1], YPF-1, YPR+1, SLOT[2], SLOT[3]))
new('X_base_plate', xp, '03', 'custom (machined)',
    'steel t20 720x160 = gantry beam; front: X rails, rear: C-TEK12 + X motor block; slot 347x60 for the nut housing; bolted to the column rear faces')

# ---------------- X axis: rails L540 on the plate front, carriage straight on the blocks
DYF = YPF - 192.0                 # -30
for k in (1, 2):
    r = O('X_rail_%d' % k); r.Shape = moved(r.Shape, (0, DYF, 0)).common(box(-270, 270, -BIG, BIG, -BIG, BIG))
    meta(r, spec='SX2RNL28-540 rail (between the columns)')
    for j in (1, 2):
        b = O('X_block_%d%d' % (k, j)); b.Shape = moved(b.Shape, (0, DYF, 0))
rm('X_spacer_1', 'X_spacer_2', 'X_coupling', 'X_motor_block')
# screw: r7 screw (x -295..222.5 at y167) -> right 395 mm, fixed end at x=200, axis behind the plate
xs = O('X_ballscrew'); s = xs.Shape.common(box(222.5-395, BIG, -BIG, BIG, -BIG, BIG))
xs.Shape = moved(s, (-22.5, XS_Y-167, 0)); meta(xs, spec='C-KBS1505-395, fixed-free, behind the X base plate')
n = O('X_ball_nut'); n.Shape = moved(n.Shape, (0, XS_Y-167, 0))
tek = O('X_support_fixed'); s = tek.Shape.copy(); s.rotate(V(0,167,XS_Z), V(1,0,0), 180)   # base now faces -y (plate rear face)
tek.Shape = moved(s, (-22.5, XS_Y-167, 0)); meta(tek, spec='C-TEK12 fixed support on the X base plate REAR face')
# nut housing: one CNC block wrapping the ball nut body (D28), flange (52x45, +x end) bolted to its +x face,
# the block passes through the plate slot and bolts to the carriage rear face
nb = O('X_nut_bracket')
nb.Shape = box(-26, 11, 134, XS_Y + 22.6, XS_Z - 26, XS_Z + 26).cut(cylx(-27, 12, XS_Y, XS_Z, 14.1))   # same size as the flange (52 high, rear edge = flange)
meta(nb, spec='nut housing (CNC): wraps the C-KBS1505 nut body, flange bolted to the +x face; passes through the slot, 4 bolts into the carriage rear face')
# X motor direct (CPJC40 coupling), in line behind the plate; motor half-width 30 > axis offset 25,
# so the plate rear gets a 7 mm locating pocket where the motor block and motor sit
jr = O('X_journal'); jr.Shape = cylx(200, 263.5, XS_Y, XS_Z, 6); meta(jr, spec='screw end journal D12')
cp = doc.addObject('Part::Feature', 'X_coupling'); grp('04').addObject(cp)
cp.Shape = moved(R7_COUPLING, (-22.5, XS_Y - 167, 0)); meta(cp, 'MISUMI', 'CPJC40-RD-12-14')
m = O('X_motor'); m.Shape = moved(R7_MOTOR, (-22.5, XS_Y - 167, 0))
meta(m, spec='HG-KR43 400 W, direct (CPJC40), behind the X base plate')
xb = O('X_base_plate'); xb.Shape = xb.Shape.cut(box(266, CX1 + 1, YPR - 7, YPR + 1, 368, 452)).removeSplitter()
meta(xb, spec='steel t20 720x160 = gantry beam; front: X rails; rear: C-TEK12 + 7 mm pocket for the X motor block; slot 347x60 for the nut housing; bolted to the column rear faces')
MF = 309.5                                                     # motor flange face
mb = box(MF - 38, MF, YPR - 7, XS_Y + 35, 372, 448)            # Z-style block, front part sits in the pocket
mb = mb.cut(cylx(MF - 39, MF + 1, XS_Y, XS_Z, 22)).cut(cylx(MF - 3, MF + 1, XS_Y, XS_Z, 25.05))
for xx in (MF - 30, MF - 8):
    for zz in (380, 440): mb = mb.cut(cyly(YPR - 8, XS_Y + 36, xx, zz, 3.3))
new('X_motor_block', mb.removeSplitter(), '04', 'custom (machined)',
    'Z-style block in the 7 mm pocket of the X base plate REAR face, 4xM6 (same face as C-TEK12); bore D44, pilot D50x3')
# ---------------- Y and Z nut housings (same idea as X): one CNC block wrapping the nut body, flange bolted to its end face
# Y: nut 26 back so the housing sits fully on the datum plate (front edge y=-145); housing bolted DOWN into the datum plate
yn = O('Y_ball_nut'); yn.Shape = moved(yn.Shape, (0, 26, 0)); b = yn.Shape.BoundBox      # body y -145..-113, flange -113..-103
yh = O('Y_nut_bracket')
yh.Shape = box(-26, 26, b.YMin, b.YMin + 32, 0, b.ZMax).cut(cyly(b.YMin - 1, b.YMin + 33, 0, (b.ZMin + b.ZMax) / 2, 14.1))
meta(yh, spec='Y nut housing (CNC): wraps the C-KBS1505 nut body, flange on its +y face, bolted down into the datum plate (same face as the Y blocks)')
# Z: housing bolted to the slide REAR face, flange (top) bolted onto it
zn = O('Z_ball_nut'); b = zn.Shape.BoundBox                                               # body z 411..443, flange 443..453
zc = ((b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2)
zh = box(-26, 26, 62, b.YMax, b.ZMin, b.ZMax - 10).cut(Part.makeCylinder(14.1, 34, V(zc[0], zc[1], b.ZMin - 1), V(0, 0, 1)))
new('Z_nut_housing', zh, '05', 'custom (machined)', 'Z nut housing (CNC): wraps the nut body, flange on its top face, bolted to the slide rear face')
# ---------------- motor seats: one straight D50 H7 through bore = HG-KR43(B) spigot D50 x 3 (measured from the
# Mitsubishi STEP); the D40 coupling passes through the same bore
SPIG = 25.05   # D50 H7 (modelled 50.1 so it merges with the old pilot recess)
zp = O('Z_motor_plate'); b = zp.Shape.BoundBox
zp.Shape = zp.Shape.cut(Part.makeCylinder(SPIG, b.ZLength + 2, V(0, 79, b.ZMin - 1), V(0, 0, 1))).removeSplitter()
meta(zp, spec=str(zp.Spec).replace('bore D44, pilot D50x3', 'D50 H7 through bore (motor spigot)'))
yb = O('Y_motor_block'); b = yb.Shape.BoundBox
yb.Shape = yb.Shape.cut(cyly(b.YMin - 1, b.YMax + 1, 0, 45, SPIG)).removeSplitter()
meta(yb, spec=str(yb.Spec).replace('bore D44, pilot D50x3', 'D50 H7 through bore (motor spigot)'))
xm = O('X_motor_block'); b = xm.Shape.BoundBox
xm.Shape = xm.Shape.cut(cylx(b.XMin - 1, b.XMax + 1, XS_Y, XS_Z, SPIG)).removeSplitter()
meta(xm, spec=str(xm.Spec).replace('bore D44, pilot D50x3', 'D50 H7 through bore (motor spigot)'))
# ---------------- electrics: drives on a panel behind the X plate
for k, n in enumerate(('Servo_amp_X', 'Servo_amp_Y', 'Servo_amp_Z')):
    a = O(n); b = a.Shape.BoundBox; a.Shape = moved(a.Shape, (0, 262 - b.YMin, 0))
pan = box(-170, 50, 257, 262, 300, 520)
for x in (-160, 30): pan = pan.fuse(box(x, x+20, YPR, 257, 460, 480))
new('Electrical_panel', pan, '07', 'custom', 'steel sheet t5 + 2 standoffs from the X base plate rear face (above the screw)')
doc.recompute(); doc.saveAs(ROOT + '/output/v4/CNC_v4.FCStd')
out = []
for o in doc.Objects:
    if o.TypeId.startswith('Part::') and o.Label.startswith(('X_','Gantry','Column','Datum','Electrical','Servo')):
        b = o.Shape.BoundBox; out.append('%-18s x[%6.1f,%6.1f] y[%6.1f,%6.1f] z[%6.1f,%6.1f]' % (o.Label,b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))
open(LOG + '/v4_parts.txt', 'w').write('\n'.join(out))
