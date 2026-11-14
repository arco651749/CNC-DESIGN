# -*- coding: utf-8 -*-
"""v12 collision sweep: all part pairs at home + the 8 travel-end poses (Y -250/+150, X +-150, Z +-50).
Pairs that overlap at home are listed separately (design contacts); anything else that overlaps at a pose is a collision.
New v12 parts carry their motion class in the Motion property; v10 parts use the v10 name rules.
Allowed: none (the tool must reach below the plate top to skim it).
Run:  freecadcmd freecad/v12/02_motion_check_v12.py     Out: output/v12/logs/v12_motion.txt"""
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
doc = App.openDocument(os.path.join(ROOT, 'output', 'v12', 'CNC_v12.FCStd'))
SKIP = ('Servo_amp', 'Electrical_panel')
OBJ = {o.Label: o for o in doc.Objects if o.TypeId == 'Part::Feature' and not o.Label.startswith(SKIP)}
P = {n: o.Shape for n, o in OBJ.items()}
ALLOWED = set()

def cls(n):
    o = OBJ[n]
    if 'Motion' in o.PropertiesList: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''
C = {n: cls(n) for n in P}

def vol(a, b):
    try:
        return a.common(b).Volume
    except Exception:          # touching faces can give a null common
        return 0.0

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
        v = vol(S[a], S[b])
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
for a, b in (('X_saddle_plate', 'X_base_plate'), ('X_saddle_plate', 'Z_motor_plate'), ('X_saddle_plate', 'X_carriage_plate'),
             ('X_block_11', 'X_side_screw_M2'), ('Y_block_L1', 'Y_ref_pin_1'), ('Y_block_R1', 'Y_ecc_pin_1'),
             ('Yaw_push_block', 'Work_table'), ('X_roll_bracket', 'X_motor_block'), ('X_base_plate', 'Gantry_column_R'),
             ('Spindle_clamp', 'Z_slide_plate'), ('Spindle_clamp', 'Spindle_plug'), ('Spindle_roll_block_R', 'Spindle_clamp'),
             ('Z_face_screw_R', 'Z_motor_plate'), ('Tool_D5', 'Work_table'), ('ER11_nut', 'Work_table')):
    clear.append('home  %-22s - %-22s %6.1f mm' % (a, b, d(a, b, H)))
for dx in (-150, 150):
    S = pose(0, dx, 0)
    for a, b in (('X_saddle_plate', 'Gantry_column_L'), ('X_saddle_plate', 'Gantry_column_R'), ('Z_roll_screw_L', 'Gantry_column_L'),
                 ('Z_roll_screw_R', 'Gantry_column_R'), ('Spindle_roll_screw_R', 'Gantry_column_R'), ('Spindle_roll_screw_L', 'Gantry_column_L')):
        clear.append('dx%+d %-22s - %-22s %6.1f mm' % (dx, a, b, d(a, b, S)))
for dz in (-50, 50):
    S = pose(0, 0, dz)
    for a, b in (('Tool_D5', 'Work_table'), ('Spindle_clamp', 'Work_table'), ('Spindle_roll_screw_R', 'Z_support_fixed'), ('Z_face_screw_R', 'Z_slide_plate')):
        clear.append('dz%+d %-22s - %-22s %6.1f mm' % (dz, a, b, d(a, b, S)))
tb = P['Tool_D5'].BoundBox; ty = (tb.YMin + tb.YMax) / 2
clear.append('tool y %.1f covers table y %.1f .. %.1f' % (ty, ty - 150, ty + 250))
out = ['parts: %d   motion classes: static %d / y %d / x %d / z %d' % (len(P), *[sum(1 for v in C.values() if v == k) for k in ('', 'y', 'x', 'z')]), '',
       'DESIGN CONTACTS AT HOME (overlap > 1 mm3, review): %d' % len(home)] + ['  %s x %s : %d mm3' % (a, b, v) for (a, b), v in sorted(home.items())]
out += ['', 'COLLISIONS AT TRAVEL ENDS (new vs home): %d' % len(coll)] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(coll.items())]
out += ['', 'ALLOWED:'] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(allowed.items())]
out += ['', 'CLEARANCES:'] + ['  ' + c for c in clear]
open(os.path.join(ROOT, 'output', 'v12', 'logs', 'v12_motion.txt'), 'w', encoding='utf-8').write('\n'.join(out))
