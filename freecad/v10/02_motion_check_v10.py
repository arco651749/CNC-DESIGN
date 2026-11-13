# -*- coding: utf-8 -*-
"""v10 collision sweep: all part pairs at home + the 8 travel-end poses (Y -250/+150, X +-150, Z +-50).
Pairs that already touch/overlap at home are listed separately (design contacts: rail/block, screw/nut, bores...),
everything else that overlaps at any pose is a collision.  Electrics are excluded (to be relocated).
Run:  freecadcmd freecad/v10/02_motion_check_v10.py     Out: output/v10/logs/v10_motion.txt"""
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
doc = App.openDocument(os.path.join(ROOT, 'output', 'v10', 'CNC_v10.FCStd'))
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
for a, b in (('X_nut_bracket', 'X_block_11'), ('X_nut_bracket', 'X_block_12'), ('X_ball_nut', 'X_base_plate'),
             ('X_nut_bracket', 'X_base_plate'), ('X_motor', 'X_base_plate'), ('X_block_11', 'X_carriage_plate'),
             ('X_rail_1', 'Work_table'), ('X_base_plate', 'Work_table'), ('X_carriage_plate', 'Work_table'), ('X_block_11', 'Work_table')):
    clear.append('home  %-16s - %-16s %6.1f mm' % (a, b, d(a, b, H)))
for dx in (-150, 150):
    S = pose(0, dx, 0)
    for a, b in (('X_nut_bracket', 'X_base_plate'), ('X_ball_nut', 'X_support_fixed'), ('X_carriage_plate', 'Gantry_column_R'),
                 ('X_carriage_plate', 'Gantry_column_L'), ('X_nut_bracket', 'X_block_11'), ('X_nut_bracket', 'X_block_12')):
        clear.append('dx%+d %-16s - %-16s %6.1f mm' % (dx, a, b, d(a, b, S)))
for dy in (-250, 150):
    S = pose(dy, 0, -50)
    for a, b in (('Work_table', 'X_base_plate'), ('Y_motor', 'X_base_plate'), ('Y_motor_block', 'X_base_plate'), ('Work_table', 'X_rail_1')):
        clear.append('dy%+d dz-50 %-14s - %-14s %6.1f mm' % (dy, a, b, d(a, b, S)))
out = ['DESIGN CONTACTS AT HOME (overlap > 1 mm3, review):'] + ['  %s x %s : %d mm3' % (a, b, v) for (a, b), v in sorted(home.items())]
out += ['', 'COLLISIONS AT TRAVEL ENDS (new vs home): %d' % len(coll)] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(coll.items())]
out += ['', 'CLEARANCES:'] + ['  ' + c for c in clear]
open(os.path.join(ROOT, 'output', 'v10', 'logs', 'v10_motion.txt'), 'w', encoding='utf-8').write('\n'.join(out))
