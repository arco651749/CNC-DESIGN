# -*- coding: utf-8 -*-
"""v11 collision sweep: all part pairs at home + the 8 travel-end poses (Y -250/+150, X +-150, Z +-50).
Pairs that overlap at home are listed separately (design contacts); anything else that overlaps at a pose is a collision.
New v11 parts carry their motion class in the Motion property; v10 parts use the v10 name rules.
Allowed: Tool_D5 x Fixture_plate at Z -50 (the tool must reach below the plate top to skim it).
Run:  freecadcmd freecad/v11/02_motion_check_v11.py     Out: output/v11/logs/v11_motion.txt"""
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
doc = App.openDocument(os.path.join(ROOT, 'output', 'v11', 'CNC_v11.FCStd'))
SKIP = ('Servo_amp', 'Electrical_panel')
OBJ = {o.Label: o for o in doc.Objects if o.TypeId == 'Part::Feature' and not o.Label.startswith(SKIP)}
P = {n: o.Shape for n, o in OBJ.items()}
ALLOWED = {('Fixture_plate', 'Tool_D5')}

def cls(n):
    o = OBJ[n]
    if 'Motion' in o.PropertiesList: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''
C = {n: cls(n) for n in P}

def pose(dy, dx, dz):
    S = {}
    for n, s in P.items():
        c = C[n]
        t = V(dx if c in ('x', 'z') else 0, dy if c == 'y' else 0, dz if c == 'z' else 0)
        s2 = s.copy(); s2.translate(t); S[n] = s2
    return S

def overlaps(S):
    hit = {}
    for a, b in itertools.combinations(sorted(S), 2):
        if not S[a].BoundBox.intersect(S[b].BoundBox): continue
        v = S[a].common(S[b]).Volume
        if v > 1.0: hit[(a, b)] = round(v)
    return hit

home = overlaps(pose(0, 0, 0))
coll, allowed = {}, {}
for dy, dx, dz in itertools.product((-250, 150), (-150, 150), (-50, 50)):
    for k, v in overlaps(pose(dy, dx, dz)).items():
        if k in home: continue
        (allowed if k in ALLOWED else coll).setdefault(k, []).append((dy, dx, dz, v))

d = lambda a, b, S: S[a].distToShape(S[b])[0]
clear = []
H = pose(0, 0, 0)
for a, b in (('X_saddle_plate', 'X_base_plate'), ('X_saddle_plate', 'Z_motor_plate'), ('X_block_21', 'X_ecc_pin_2'), ('X_block_11', 'X_ref_pin_2'),
             ('X_block_11', 'X_side_screw_Mb'), ('Z_block_L1', 'Z_ref_pin_1'), ('Z_block_R1', 'Z_ecc_pin_1'), ('Y_block_L1', 'Y_ref_pin_1'),
             ('Y_block_R1', 'Y_ecc_pin_1'), ('Foot_bolt_rear_R1', 'X_base_plate'), ('Yaw_push_block_L', 'Work_table'), ('Column_foot_L', 'Work_table'),
             ('Spindle_clamp', 'Spindle_plug'), ('Indicator_holder', 'Spindle_clamp'), ('Fixture_plate', 'Tool_D5'), ('Fixture_plate', 'ER11_nut')):
    clear.append('home  %-18s - %-18s %6.1f mm' % (a, b, d(a, b, H)))
for dx in (-150, 150):
    S = pose(0, dx, 0)
    for a, b in (('X_saddle_plate', 'Gantry_column_L'), ('X_saddle_plate', 'Gantry_column_R'), ('Z_tram_screw_L', 'Gantry_column_L'),
                 ('Z_tram_screw_R', 'Gantry_column_R'), ('X_carriage_plate', 'Gantry_column_L'), ('X_carriage_plate', 'Gantry_column_R')):
        clear.append('dx%+d %-18s - %-18s %6.1f mm' % (dx, a, b, d(a, b, S)))
S = pose(0, 0, -50)
for a, b in (('Fixture_plate', 'ER11_nut'), ('Fixture_plate', 'Indicator_holder'), ('Fixture_plate', 'Spindle_clamp')):
    clear.append('dz-50 %-18s - %-18s %6.1f mm' % (a, b, d(a, b, S)))
S = pose(0, 0, 50)
for a, b in (('Spindle_clamp', 'Z_motor_plate'), ('Spindle_roll_block_R', 'Z_support_fixed')):
    clear.append('dz+50 %-18s - %-18s %6.1f mm' % (a, b, d(a, b, S)))
out = ['parts: %d   motion classes: static %d / y %d / x %d / z %d' % (len(P), *[sum(1 for v in C.values() if v == k) for k in ('', 'y', 'x', 'z')]), '',
       'DESIGN CONTACTS AT HOME (overlap > 1 mm3, review): %d' % len(home)] + ['  %s x %s : %d mm3' % (a, b, v) for (a, b), v in sorted(home.items())]
out += ['', 'COLLISIONS AT TRAVEL ENDS (new vs home): %d' % len(coll)] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(coll.items())]
out += ['', 'ALLOWED:'] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(allowed.items())]
out += ['', 'CLEARANCES:'] + ['  ' + c for c in clear]
open(os.path.join(ROOT, 'output', 'v11', 'logs', 'v11_motion.txt'), 'w', encoding='utf-8').write('\n'.join(out))
