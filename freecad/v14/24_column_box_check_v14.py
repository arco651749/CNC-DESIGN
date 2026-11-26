# -*- coding: utf-8 -*-
"""v14 column-top electrical box (drawn by the electrical session, column_box/column_box.step, machine coordinates) checked against
the machine: every leaf solid of the box against every machine part at the 27 travel-end poses (the old back plate and its drives,
which the box replaces, are left out). Also lists what holds the box up (parts touching it from outside).
Run:  freecadcmd freecad/v14/24_column_box_check_v14.py      Out: output/v14/logs/v14_column_box_check.txt"""
import os, itertools
import FreeCAD as App, Part, Import
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
STEP = os.path.join(ROOT, 'column_box', 'column_box.step')
OLD_PANEL = ('Electrical_panel', 'Servo_amp', 'Servo_bolt', 'Controller', 'Board_standoff', 'Panel_standoff', 'Keepout')
if True:
    cb = App.newDocument('column_box'); Import.insert(STEP, cb.Name)
    BOX = [(o.Label, o.Shape) for o in cb.Objects if o.TypeId == 'Part::Feature' and not o.Shape.isNull() and o.Shape.Solids]
    BB = App.BoundBox()
    for _, s in BOX: BB.add(s.BoundBox)
    doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))
    def cls(o):
        n = o.Label
        if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
        if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
        if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
        if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
        return ''
    def off(k, P):
        dx, dy, dz = P
        return {'y': (0, dy, 0), 'x': (dx, 0, 0), 'z': (dx, 0, dz)}.get(k, (0, 0, 0))
    M = [(o.Label, o.Shape, cls(o)) for o in doc.Objects if o.TypeId == 'Part::Feature' and not o.Shape.isNull() and o.Shape.Solids
         and not o.Label.startswith(OLD_PANEL)]
    POSES = list(itertools.product((-182.5, 0, 182.5), (-250, 0, 150), (-50, 0, 50)))
    hits, near = {}, {}
    for n, sh, k in M:
        for P in (POSES if k else [(0, 0, 0)]):
            o = off(k, P); b = sh.BoundBox
            mb = App.BoundBox(b.XMin + o[0], b.YMin + o[1], b.ZMin + o[2], b.XMax + o[0], b.YMax + o[1], b.ZMax + o[2])
            g = App.BoundBox(mb); g.enlarge(3)
            if not g.intersect(BB): continue
            s2 = None
            for bn, bs in BOX:
                if not g.intersect(bs.BoundBox): continue
                if s2 is None: s2 = sh.copy(); s2.translate(V(*o))
                try: v = bs.common(s2).Volume
                except Exception: v = -1
                if v > 0.5: hits.setdefault((bn, n), (P, round(v)))
                elif not k:
                    d = bs.distToShape(s2)[0]
                    if d < 0.05: near[(bn, n)] = d
    L = ['v14 column box (%s): %d box solids, envelope x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (os.path.relpath(STEP, ROOT), len(BOX),
         BB.XMin, BB.XMax, BB.YMin, BB.YMax, BB.ZMin, BB.ZMax), '%d machine parts, %d poses' % (len(M), len(POSES)), '',
         'COLLISIONS (box x machine): %d' % len(hits)] + ['  %s x %s at %s: %s mm3' % (a, b, p, v) for (a, b), (p, v) in sorted(hits.items())]
    L += ['', 'SUPPORT (fixed machine parts touching the box): %d' % len(near)] + ['  %s - %s' % ab for ab in sorted(near)]
    if not near: L.append('  none: the box is not attached to the machine yet (mounting to be designed by the mechanical side)')
    os.makedirs(os.path.join(ROOT, 'output', 'v14', 'logs'), exist_ok=True)
    open(os.path.join(ROOT, 'output', 'v14', 'logs', 'v14_column_box_check.txt'), 'w', encoding='utf-8').write('\n'.join(L))
