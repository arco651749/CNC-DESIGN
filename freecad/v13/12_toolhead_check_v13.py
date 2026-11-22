# -*- coding: utf-8 -*-
"""v13 tool-head checks on the base model: (1) tool-head parts vs everything over 64 poses incl. the tool-measuring pose,
(2) camera light path (down to the prism, across to the tool) at the measuring pose, (3) probe retracted / extended contacts,
(4) contacts between module parts at home.
Run:  freecadcmd freecad/v13/12_toolhead_check_v13.py     Out: output/v13/logs/v13_toolhead_check.txt"""
import os, itertools
import FreeCAD as App, Part
from FreeCAD import Vector as V
ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
doc = App.openDocument(os.path.join(ROOT, 'output', 'v13', 'CNC_v13_base.FCStd'))
OBJ = {o.Label: o for o in doc.Objects if o.TypeId == 'Part::Feature' and not o.Shape.isNull()}
def cls(o):
    n = o.Label
    if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''
C = {n: cls(o) for n, o in OBJ.items()}
def moved(n, dx, dy, dz, S=None):
    s = (S or {}).get(n, OBJ[n].Shape).copy(); c = C[n]
    s.translate(V(dx if c in ('x', 'z') else 0, dy if c == 'y' else 0, dz if c == 'z' else 0)); return s
def vol(a, b):
    try: return a.common(b).Volume
    except Exception: return 0.0
out = []
HEAD = [n for n in OBJ if n.startswith(('Camera', 'Tool_mirror', 'Mirror', 'Probe', 'Coolant_nozzle'))]
for n in ('Spindle_body', 'Spindle_clamp', 'Spindle_nose'):
    if n not in HEAD: HEAD.append(n)
SX0, SY, PX = -7.5, -20.0, 77.5
ab_ = OBJ['Camera_CS_C_adapter'].Shape.BoundBox; CX = (ab_.XMin + ab_.XMax) / 2   # camera axis from the model
pb_ = OBJ['Tool_mirror'].Shape.BoundBox                         # fold point from the model: prism centre, 10 above its bottom
MX, MY, MZ = (pb_.XMin + pb_.XMax) / 2, (pb_.YMin + pb_.YMax) / 2, pb_.ZMin + 10.0
MEAS = (MX - CX, SY - MY, MZ - OBJ['Tool_D5'].Shape.BoundBox.ZMin)   # (-117.5, -220, Z)
# (1) tool-head parts vs all others (same-class pairs only checked once, at home)
home = {}
for n in HEAD:
    for m in OBJ:
        if m == n or (m in HEAD and m < n): continue
        if not OBJ[n].Shape.BoundBox.intersect(OBJ[m].Shape.BoundBox): continue
        v = vol(OBJ[n].Shape, OBJ[m].Shape)
        if v > 0.5: home[(n, m)] = round(v, 1)
out.append('CONTACTS AT HOME (tool-head parts): %d' % len(home)); out += ['  %s x %s : %s mm3' % (a, b, v) for (a, b), v in sorted(home.items())]
TOOLSIDE = ('Tool_D5', 'ER11_nut', 'Coolant_nozzle_1', 'Coolant_nozzle_2')
FIXT = ('Work_table', 'Tool_mirror', 'Mirror_bracket', 'Mirror_bracket_bolt_1', 'Mirror_bracket_bolt_2', 'Mirror_cover', 'Mirror_cover_actuator',
        'Mirror_cover_fitting_1', 'Mirror_cover_fitting_2', 'Mirror_cover_tube_1', 'Mirror_cover_tube_2')
bad, fixt = {}, {}
for dx, dz, dy in itertools.product((-227.5, MEAS[0], 0, 227.5), (-50, MEAS[2], 0, 50), (-250, MEAS[1], 0, 150)):
    for n in HEAD:
        a = moved(n, dx, dy, dz)
        for m in OBJ:
            if m == n or C[m] == C[n]: continue
            if (n, m) in home or (m, n) in home: continue
            b = moved(m, dx, dy, dz)
            if not a.BoundBox.intersect(b.BoundBox): continue
            v = vol(a, b)
            if v > 1: (fixt if (n in TOOLSIDE and m in FIXT) or (m in TOOLSIDE and n in FIXT) else bad).setdefault(tuple(sorted((n, m))), (dx, dy, dz, round(v, 1)))
out += ['', 'CLASHES OVER 64 POSES: %d' % len(bad)] + ['  %s x %s at %s' % (a, b, p) for (a, b), p in sorted(bad.items())]
out += ['TOOL / NOZZLE TIPS INTO THE TABLE OR THE PRISM STATION (allowed, like any fixture): %d' % len(fixt)] + ['  %s x %s at %s' % (a, b, p) for (a, b), p in sorted(fixt.items())]
# (2) light path at the measuring pose: FOV 13.4 (along X / along the tool) x 11.2
dx, dy, dz = MEAS
OPEN = OBJ['Mirror_cover'].Shape.copy(); OPEN.translate(V(0, 30, 0))   # cover slid open
S_OPEN = {'Mirror_cover': OPEN}
lf = OBJ['Camera_lens'].Shape.BoundBox.ZMin + dz
FW, FH = 16.8, 14.0                                              # FOV of MML04-HR120D (0.4x) on the daA2448, long side along X / the tool
paths = {'down': Part.makeBox(FW, FH, lf - (MZ + FW / 2), V(MX - FW / 2, SY - FH / 2, MZ + FW / 2)),
         'across': Part.makeBox((SX0 + dx - 2.5) - (MX + FW / 2), FH, FW, V(MX + FW / 2, SY - FH / 2, MZ - FW / 2))}
for k, p in paths.items():
    hits = [(m, round(vol(p, moved(m, dx, dy, dz, S_OPEN)), 1)) for m in OBJ if p.BoundBox.intersect(moved(m, dx, dy, dz, S_OPEN).BoundBox)]
    out.append('PATH %-6s %s' % (k, [h for h in hits if h[1] > 0.01] or 'clear'))
tip = moved('Tool_D5', dx, dy, dz).BoundBox
out.append('measuring pose X %+.1f table %+.0f Z %+.0f: tool tip z %.1f at x %.1f, prism fold (%.0f, %.0f) -> table at y %.0f; air path %.1f'
           % (dx, dy, dz, tip.ZMin, (tip.XMin + tip.XMax) / 2, MX, MZ, MY + dy, (lf - MZ) + ((tip.XMin + tip.XMax) / 2 - MX)))
for a in ('Camera_lens', 'Camera_air_ring', 'Camera_bracket', 'Spindle_body', 'ER11_nut', 'Probe_body', 'Coolant_nozzle_1'):
    out.append('  min gap %-18s - prism parts (cover open) %.1f mm' % (a, min(moved(a, dx, dy, dz).distToShape(moved(b, dx, dy, dz, S_OPEN))[0] for b in ('Tool_mirror', 'Mirror_bracket', 'Mirror_bracket_bolt_1', 'Mirror_cover', 'Mirror_cover_actuator'))))
# (3) probe retracted / extended
MOVE = ('Probe_body', 'Probe_holder', 'Probe_slide_table', 'Probe_pinch_bolt') + tuple('Probe_holder_bolt_%d' % k for k in range(1, 5))
OK = {('Probe_slide_body', 'Probe_slide_table'), ('Probe_block', 'Probe_rail'), ('Probe_holder', 'Probe_solenoid'), ('Probe_bracket', 'Probe_stop_screw'), ('Probe_body', 'Probe_holder'),
      ('Probe_holder', 'Probe_pinch_bolt'), ('Probe_bracket', 'Probe_rail'), ('Probe_block', 'Probe_holder'), ('Probe_bracket', 'Probe_bracket_bolt_1'),
      ('Probe_bracket', 'Probe_bracket_bolt_2'), ('Probe_bracket', 'Probe_bracket_bolt_3'), ('Probe_bracket', 'Probe_bracket_bolt_4')}
for state, d in (('retracted', 0), ('extended', -60)):
    S = {n: OBJ[n].Shape.copy() for n in MOVE}
    for s in S.values(): s.translate(V(0, 0, d))
    un = []
    for a in MOVE:
        for b in OBJ:
            if b == a or b in MOVE: continue
            if not S[a].BoundBox.intersect(OBJ[b].Shape.BoundBox): continue
            v = vol(S[a], OBJ[b].Shape)
            if v > 0.5 and tuple(sorted((a, b))) not in OK: un.append((a, b, round(v, 1)))
    out.append('PROBE %-9s ball z %.1f, slide table z %.1f..%.1f (body %.1f..%.1f), unexpected contacts: %s' % (state, S['Probe_body'].BoundBox.ZMin,
               S['Probe_slide_table'].BoundBox.ZMin, S['Probe_slide_table'].BoundBox.ZMax, OBJ['Probe_slide_body'].Shape.BoundBox.ZMin, OBJ['Probe_slide_body'].Shape.BoundBox.ZMax, un or 'none'))
open(os.path.join(ROOT, 'output', 'v13', 'logs', 'v13_toolhead_check.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
