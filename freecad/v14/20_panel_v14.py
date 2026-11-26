# -*- coding: utf-8 -*-
"""v14 electrical back plate as its own assembly (owner: lay it out separately from the machine). The plate behind the X base plate
(v10..v14: 220 x 220 steel t5 on standoffs, 3 x MR-J4-40A) with the RP23CNC controller added.
Local frame = the plate seen from its component side (from behind the machine): X to the right, Y up, Z out of the plate (components
on +Z, plate z -5..0, standoffs behind). Machine position: x = X0_M - X, z = Z0_M + Y, plate front face at y = Y0_M.
Everything that sets the layout is in LAYOUT below; keep-out boxes (servo airflow / wiring space) are checked against the parts.
Run:  freecadcmd freecad/v14/20_panel_v14.py      Out: output/v14/panel/CNC_v14_panel.FCStd, .step, logs/panel_check.txt"""
import os, itertools
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v14', 'panel'); os.makedirs(os.path.join(OUT, 'logs'), exist_ok=True)
X0_M, Y0_M, Z0_M = 50.0, 262.0, 300.0           # machine position of the plate's lower-left corner (right edge kept at machine x 50)

LAYOUT = {
    'plate': (290.0, 260.0, 5.0),                # W, H, t (was 220 x 220: no room for the controller, servo top / bottom gap only 26)
    'servo': [(40.0, 130.0), (90.0, 130.0), (140.0, 130.0)],   # MR-J4-40A centres (40 wide, 168 high): 10 apart, 46 free above / below
    'servo_keep': (10.0, 40.0),                  # MR-J4-A manual installation clearance: sides 10, top / bottom 40 (electrician to confirm)
    'board': (175.0, 82.0, 10.0),                # RP23CNC lower-left corner on the plate, standoff height (M3 hex)
    'board_keep': 15.0,                          # wiring room around the board edges (terminals on 3 sides)
    'standoffs': [(10.0, 150.0), (167.5, 150.0), (280.5, 150.0)],  # plate -> X base plate rear face, D20 x 75, M8 from the front
}
W, H, T = LAYOUT['plate']
doc = App.newDocument('CNC_v14_panel')
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cyl(r, z0, z1, x, y): return Part.makeCylinder(r, z1 - z0, V(x, y, z0))
G = {}
def grp(n):
    if n not in G: G[n] = doc.addObject('App::DocumentObjectGroup', n)
    return G[n]
def add(label, shape, group, spec):
    o = doc.addObject('Part::Feature', label); o.Label = label; o.Shape = shape
    o.addProperty('App::PropertyString', 'Spec', 'CNC'); o.Spec = spec; grp(group).addObject(o); return o

plate = box(0, W, 0, H, -T, 0)
sv_step = Part.read(os.path.join(ROOT, 'vendor', 'mitsubishi', 'MR-J4-40A', 'step', 'mr-j4-40ab.stp'))   # 40 x 168 x 175.9, back face z 0
rp_step = Part.read(os.path.join(ROOT, 'vendor', 'brookwood', 'RP23CNC-V2.02', 'RP23CNC-V2.02.step'))   # PCB x 81..177, y -144..-48, z 0..1.6
SK, SV = LAYOUT['servo_keep']
ring = cyl(4.25, 0, 30, -14, -78).cut(cyl(3.0, 0, 30, -14, -78))       # drive flange thickness at its mounting hole (vendor STEP)
FL = max(v.Point.z for v in sv_step.common(ring).Vertexes if v.Point.z < 30)
for i, (cx, cy) in enumerate(LAYOUT['servo'], 1):
    s = sv_step.copy(); s.translate(V(cx, cy, 0))
    add('Servo_amp_%s' % 'XYZ'[i - 1], s, 'Drives', 'Mitsubishi MR-J4-40A (vendor STEP), 2 x M5 into the plate (holes 156 apart, 6 from its left side)')
    for dy in (-78, 78):
        plate = plate.cut(cyl(2.5, -T, 0, cx - 14, cy + dy))
        add('Servo_bolt_%s_%d' % ('XYZ'[i - 1], 1 if dy < 0 else 2), cyl(2.5, -T, FL, cx - 14, cy + dy).fuse(cyl(4.0, FL, FL + 4, cx - 14, cy + dy)), 'Fasteners',
            'M5x10 pan head (head D8, fits the lower U-slot of the drive flange), drive flange into the plate (M5 tapped through t5)')
    add('Keepout_servo_%s' % 'XYZ'[i - 1], box(cx - 20 - SK, cx + 20 + SK, cy - 84 - SV, cy + 84 + SV, 0, 176).cut(box(cx - 20, cx + 20, cy - 84, cy + 84, 0, 176)),
        'Keep-out', 'servo clearance: sides %g, top / bottom %g (airflow, manual)' % (SK, SV))
bx, by, bh = LAYOUT['board']
r = rp_step.copy(); r.translate(V(bx - 81, by + 144, bh))
add('Controller_RP23CNC', r, 'Controller', 'Brookwood Design RP23CNC V2.02 (vendor STEP), on 4 x M3 hex standoffs %g' % bh)
for k, (hx, hy) in enumerate(((4, 4), (92, 4), (4, 92), (92, 92)), 1):
    plate = plate.cut(cyl(1.5, -T, 0, bx + hx, by + hy))
    add('Board_standoff_%d' % k, cyl(2.75, 0, bh, bx + hx, by + hy), 'Controller', 'M3 hex standoff F-F %g (SW5.5), M3 tapped through the plate' % bh)
bk = LAYOUT['board_keep']
add('Keepout_board', box(bx - bk, bx + 96 + bk, by - bk, by + 96 + bk, 0, 40).cut(box(bx, bx + 96, by, by + 96, 0, 40)), 'Keep-out',
    'wiring room %g around the controller (terminal blocks on the top, bottom and right edges)' % bk)
for k, (sx, sy) in enumerate(LAYOUT['standoffs'], 1):
    plate = plate.cut(cyl(4.5, -T, 0, sx, sy))
    add('Panel_standoff_%d' % k, cyl(10, -T - 75, -T, sx, sy).cut(cyl(4, -T - 18, -T, sx, sy)).cut(cyl(4, -T - 75, -T - 57, sx, sy)), 'Plate',
        'steel standoff D20 x 75, M8 tapped 18 both ends: plate -> X base plate rear face')
    add('Panel_standoff_bolt_%d' % k, cyl(4, -T - 16, 0, sx, sy).fuse(cyl(6.5, 0, 8, sx, sy)), 'Fasteners', 'M8x20 SHCS from the component side into the standoff')
add('Electrical_panel', plate, 'Plate', 'steel plate t%g, %g x %g (back plate, behind the X base plate), holes for drives, controller standoffs, 3 plate standoffs' % (T, W, H))

# checks: parts vs parts, parts vs other parts' keep-outs, everything on the plate
P = {o.Label: o for o in doc.Objects if o.TypeId == 'Part::Feature'}
real = [n for n in P if not n.startswith('Keepout')]
keep = [n for n in P if n.startswith('Keepout')]
own = lambda k, n: k.split('_')[-1] == n.split('_')[-1] or (k == 'Keepout_board' and n.startswith(('Controller', 'Board')))
L = ['v14 back plate: %g x %g x %g, machine lower-left corner x %g (plate right edge), z %g, front face y %g' % (W, H, T, X0_M, Z0_M, Y0_M), '']
for n in real:
    b = P[n].Shape.BoundBox; L.append('%-22s X[%6.1f,%6.1f] Y[%6.1f,%6.1f] Z[%6.1f,%6.1f]' % (n, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
L.append('')
hit = []
for a, b in itertools.combinations(real, 2):
    if P[a].Shape.BoundBox.intersect(P[b].Shape.BoundBox):
        v = P[a].Shape.common(P[b].Shape).Volume
        if v > 0.5: hit.append('%s x %s %.1f mm3' % (a, b, v))
for k in keep:
    for n in real:
        if own(k, n) or 'bolt' in n.lower() or n == 'Electrical_panel' or n.startswith('Panel_standoff'): continue
        if P[k].Shape.BoundBox.intersect(P[n].Shape.BoundBox) and P[k].Shape.common(P[n].Shape).Volume > 0.5: hit.append('%s inside %s' % (n, k))
off = [n for n in real if not n.startswith('Panel_standoff') and (P[n].Shape.BoundBox.XMin < -0.01 or P[n].Shape.BoundBox.XMax > W + 0.01 or
       P[n].Shape.BoundBox.YMin < -0.01 or P[n].Shape.BoundBox.YMax > H + 0.01)]
L.append('OVERLAPS / KEEP-OUT VIOLATIONS: %d' % len(hit)); L += ['  ' + h for h in hit]
L.append('PARTS OFF THE PLATE: %s' % (off or 'none'))
doc.recompute(); doc.saveAs(os.path.join(OUT, 'CNC_v14_panel.FCStd'))
Part.makeCompound([P[n].Shape for n in real]).exportStep(os.path.join(OUT, 'CNC_v14_panel.step'))
open(os.path.join(OUT, 'logs', 'panel_check.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(L[-4:]))
