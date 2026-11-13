# -*- coding: utf-8 -*-
"""v4 collision sweep (Y -250/-50/+150, X -150/0/+150, Z -50/+50) and key clearances.
Run from the repository root:  freecadcmd freecad/v4/02_motion_check_v4.py"""
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v4', 'logs'); os.makedirs(LOG, exist_ok=True)
doc = App.openDocument(ROOT + '/output/v4/CNC_v4.FCStd')
P = {o.Label: o.Shape for o in doc.Objects if o.TypeId == 'Part::Feature'}
Y_MOV = {n for n in P if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_journal', 'Y_coupling', 'Y_motor'))}
Z_MOV = {n for n in P if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Spindle', 'ER11', 'Tool'))}
X_MOV = {n for n in P if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'Z_'))} | Z_MOV
SAME = [Y_MOV, X_MOV, Z_MOV]
EXPECT = {frozenset(p) for p in [('Y_ballscrew','Y_ball_nut'),('X_ballscrew','X_ball_nut'),('Z_ballscrew','Z_ball_nut'),
  ('X_rail_1','X_block_11'),('X_rail_1','X_block_12'),('X_rail_2','X_block_21'),('X_rail_2','X_block_22'),
  ('Z_rail_L','Z_block_L1'),('Z_rail_L','Z_block_L2'),('Z_rail_R','Z_block_R1'),('Z_rail_R','Z_block_R2'),
  ('Y_rail_L','Y_block_L1'),('Y_rail_L','Y_block_L2'),('Y_rail_R','Y_block_R1'),('Y_rail_R','Y_block_R2'),
  ('X_ballscrew','X_nut_bracket'),('X_journal','X_support_fixed'),('Y_journal','Y_support_fixed'),('Z_journal','Z_support_fixed'),
  ('X_motor','X_motor_block'),('X_coupling','X_journal'),('X_coupling','X_motor')]}
def pose(dy, dx, dz):
    out = {}
    for n, s in P.items():
        t = V(0, dy if n in Y_MOV else 0, 0) + V(dx if n in X_MOV else 0, 0, dz if n in Z_MOV else 0)
        s2 = s.copy(); s2.translate(t); out[n] = s2
    return out
hits = {}
names = sorted(P)
for dy, dx, dz in itertools.product((-250, -50, 150), (-150, 0, 150), (-50, 50)):
    S = pose(dy, dx, dz)
    for a, b in itertools.combinations(names, 2):
        if frozenset((a, b)) in EXPECT or any(a in g and b in g for g in SAME): continue
        if not S[a].BoundBox.intersect(S[b].BoundBox): continue
        v = S[a].common(S[b]).Volume
        if v > 1: hits.setdefault((a, b), []).append((dy, dx, dz, round(v)))
open(LOG + '/v4_motion.txt', 'w').write('\n'.join('%s x %s : %s' % (k[0], k[1], v) for k, v in sorted(hits.items())) or 'none')
d = lambda a, b, S=P: S[a].distToShape(S[b])[0]
rep = []
for dx in (-150, 150):
    S = pose(0, dx, 0); side = 'R' if dx > 0 else 'L'
    rep.append('dx=%+d: carriage-column %.1f, Z_motor_plate-column %.1f, X_block-column %.1f' % (dx, d('X_carriage_plate','Gantry_column_'+side,S), d('Z_motor_plate','Gantry_column_'+side,S), d('X_block_%s2' % ('2' if dx>0 else '1'),'Gantry_column_'+side,S) if False else min(d('X_block_12','Gantry_column_'+side,S), d('X_block_11','Gantry_column_'+side,S))))
    rep.append('dx=%+d: nut_bracket-plate(slot) %.1f, nut-plate %.1f, nut-support %.1f, nut-panel %.1f' % (dx, d('X_nut_bracket','X_base_plate',S), d('X_ball_nut','X_base_plate',S), d('X_ball_nut','X_support_fixed',S), d('X_ball_nut','Electrical_panel',S)))
rep.append('motor-plate %.1f, coupling-plate %.1f, motor-column_R %.1f, motor_block-support %.1f' % (d('X_motor','X_base_plate'), d('X_coupling','X_base_plate'), d('X_motor','Gantry_column_R'), d('X_motor_block','X_support_fixed')))
for dy in (-250, 150):
    S = pose(dy, 0, 0); rep.append('dy=%+d: table-column %.1f, Y_motor-plate %.1f, Y_motor-datum %.1f, Y_motor_block-panel %.1f' % (dy, min(d('Work_table','Gantry_column_L',S), d('Work_table','Gantry_column_R',S)), d('Y_motor','X_base_plate',S), d('Y_motor','Datum_base_plate',S), d('Y_motor','Electrical_panel',S)))
S = pose(0, 0, -50); rep.append('dz=-50: carriage bottom z %.0f, tool tip z %.0f' % (S['X_carriage_plate'].BoundBox.ZMin, S['Tool_D5'].BoundBox.ZMin))
open(LOG + '/v4_clear.txt', 'w').write('\n'.join(rep))
