# -*- coding: utf-8 -*-
"""v13 on the coolant base, collision sweep: all part pairs at home + the 8 travel-end poses (Y -250/+150, X +-227.5, Z +-50).
Pairs that overlap at home are listed separately (design contacts); anything else that overlaps at a pose is a collision.
New v13 parts carry their motion class in the Motion property; v10 parts use the v10 name rules.
Allowed: none (the tool must reach below the plate top to skim it).
Run:  freecadcmd freecad/v13/02_motion_check_v13.py     Out: output/v13/logs/v13_motion.txt"""
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
doc = App.openDocument(os.path.join(ROOT, 'output', 'v13', 'CNC_v13_base.FCStd'))
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
for dy, dx, dz in itertools.product((-250, 150), (-227.5, 227.5), (-50, 50)):
    for k, v in overlaps(pose(dy, dx, dz)).items():
        if k in home: continue
        (allowed if k in ALLOWED else coll).setdefault(k, []).append((dy, dx, dz, v))

d = lambda a, b, S: S[a].distToShape(S[b])[0]
clear = []
H = pose(0, 0, 0)
clear = []
for dy in (-250, 150):
    S = pose(dy, 0, 0)
    for a, b in (('Work_table', 'Guard_front_lip'), ('Y_motor', 'Guard_rear'), ('Y_ballscrew', 'Guard_rear'), ('Y_ballscrew', 'Guard_front_lip'), ('Work_table', 'Coolant_pan')):
        clear.append('dy%+d %-18s - %-18s %6.1f mm' % (dy, a, b, d(a, b, S)))
for dx in (-227.5, 227.5):
    S = pose(0, dx, 0)
    for a, b in (('X_motor', 'Guard_side_R'), ('Coolant_nozzle_1', 'Gantry_column_L'), ('Coolant_nozzle_2', 'Gantry_column_R')):
        clear.append('dx%+d %-18s - %-18s %6.1f mm' % (dx, a, b, d(a, b, S)))
S = pose(0, 0, -50)
for a, b in (('Coolant_nozzle_1', 'Work_table'), ('Coolant_nozzle_2', 'Work_table'), ('Coolant_nozzle_1', 'Spindle_body'), ('Tool_D5', 'Work_table')):
    clear.append('dz-50 %-18s - %-18s %6.1f mm' % (a, b, d(a, b, S)))
tb = P['Tool_D5'].BoundBox
clear.append('nozzle tip to tool tip at home: %.1f mm' % P['Coolant_nozzle_1'].distToShape(P['Tool_D5'])[0])
out = ['parts: %d   motion classes: static %d / y %d / x %d / z %d' % (len(P), *[sum(1 for v in C.values() if v == k) for k in ('', 'y', 'x', 'z')]), '',
       'DESIGN CONTACTS AT HOME (overlap > 1 mm3, review): %d' % len(home)] + ['  %s x %s : %d mm3' % (a, b, v) for (a, b), v in sorted(home.items())]
out += ['', 'COLLISIONS AT TRAVEL ENDS (new vs home): %d' % len(coll)] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(coll.items())]
out += ['', 'ALLOWED:'] + ['  %s x %s : %s' % (a, b, p) for (a, b), p in sorted(allowed.items())]
out += ['', 'CLEARANCES:'] + ['  ' + c for c in clear]
open(os.path.join(ROOT, 'output', 'v13', 'logs', 'v13_base_motion.txt'), 'w', encoding='utf-8').write('\n'.join(out))
