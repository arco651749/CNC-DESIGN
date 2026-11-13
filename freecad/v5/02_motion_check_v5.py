# -*- coding: utf-8 -*-
"""v5 collision sweep: all part pairs at home + the 8 travel-end poses (Y -250/+150, X +-150, Z +-50).
Pairs that already touch/overlap at home are listed separately (design contacts: rail/block, screw/nut, bores...),
everything else that overlaps at any pose is a collision.  Electrics are excluded (to be relocated).
Run:  freecadcmd freecad/v5/02_motion_check_v5.py     Out: output/v5/logs/v5_motion.txt"""
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
doc = App.openDocument(os.path.join(ROOT, 'output', 'v5', 'CNC_v5.FCStd'))
SKIP = ('Servo_amp', 'Electrical_panel')
P = {o.Label: o.Shape for o in doc.Objects if o.TypeId == 'Part::Feature' and not o.Label.startswith(SKIP)}

Y_MOV = {n for n in P if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor'))}
Z_MOV = {n for n in P if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool'))}
X_MOV = {n for n in P if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_'))} | Z_MOV


def pose(dy, dx, dz):
    S = {}
    for n, s in P.items():
        t = V(0, dy if n in Y_MOV else 0, 0) + V(dx if n in X_MOV else 0, 0, 0) + V(0, 0, dz if n in Z_MOV else 0)
        s2 = s.copy(); s2.translate(t); S[n] = s2
    return S


def overlaps(S):
    hit = {}
    for a, b in itertools.combinations(sorted(S), 2):
        if not S[a].BoundBox.intersect(S[b].BoundBox):
            continue
        v = S[a].common(S[b]).Volume
        if v > 1.0:
            hit[(a, b)] = round(v)
    return hit


home = overlaps(pose(0, 0, 0))
coll = {}
for dy, dx, dz in itertools.product((-250, 150), (-150, 150), (-50, 50)):
    for k, v in overlaps(pose(dy, dx, dz)).items():
        if k not in home:
            coll.setdefault(k, []).append((dy, dx, dz, v))


def d(a, b, S):
    return S[a].distToShape(S[b])[0]


H = pose(0, 0, 0)
clear = []
for a, b in (('X_saddle_bridge', 'Box_top_plate'), ('X_saddle_bridge', 'X_block_21'), ('X_saddle_bridge', 'X_block_R1'),
             ('X_saddle_bridge', 'X_base_plate'), ('X_saddle_rear', 'X_rail_rear'), ('X_saddle_rear', 'Box_rear_plate'),
             ('X_block_R1', 'Box_rear_plate'), ('X_saddle_bridge', 'X_carriage_plate'), ('X_saddle_rear', 'X_block_R1')):
    clear.append('home  %-16s - %-16s %6.1f mm' % (a, b, d(a, b, H)))
for dx in (-150, 150):
    S = pose(0, dx, 0)
    for a, b in (('X_saddle_bridge', 'Gantry_column_L'), ('X_saddle_bridge', 'Gantry_column_R'), ('X_saddle_rear', 'X_motor'),
                 ('X_saddle_rear', 'X_coupling'), ('X_carriage_plate', 'Gantry_column_R'), ('X_carriage_plate', 'Gantry_column_L')):
        clear.append('dx%+d %-16s - %-16s %6.1f mm' % (dx, a, b, d(a, b, S)))
rail = P['X_rail_rear'].BoundBox
for dx in (-150, 150):
    S = pose(0, dx, 0)
    b1, b2 = S['X_block_R1'].BoundBox, S['X_block_R2'].BoundBox
    clear.append('dx%+d rear blocks x[%.0f,%.0f] on rear rail x[%.0f,%.0f]' % (dx, min(b1.XMin, b2.XMin), max(b1.XMax, b2.XMax), rail.XMin, rail.XMax))

out = ['DESIGN CONTACTS AT HOME (overlap > 1 mm3, review):'] + ['  %s x %s : %d mm3' % (a, b, v) for (a, b), v in sorted(home.items())]
out += ['', 'COLLISIONS AT TRAVEL ENDS (new vs home): %d' % len(coll)] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(coll.items())]
out += ['', 'CLEARANCES:'] + ['  ' + c for c in clear]
open(os.path.join(ROOT, 'output', 'v5', 'logs', 'v5_motion.txt'), 'w', encoding='utf-8').write('\n'.join(out))
