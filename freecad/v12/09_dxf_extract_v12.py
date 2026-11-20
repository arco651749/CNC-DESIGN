# -*- coding: utf-8 -*-
"""v12 CNC parts -> 2D drawing data (step 1 of 2, FreeCAD). For every machined part: a main view along its thinnest axis
plus a view along any other axis that has holes; outline from a section at mid depth, pockets/steps from sections near
both faces; every round hole with its use, found from the part that goes into it:
  pin / dowel / pivot / bearing outer ring  -> H7 (match-reamed at assembly for the lock dowels)
  screw thread in the hole                   -> tap M.. (fine pitch from the screw spec)
  otherwise                                  -> clearance / counterbore
Run:  freecadcmd freecad/v12/09_dxf_extract_v12.py      Out: output/v12/dxf/parts.json  (then python freecad/v12/10_dxf_write_v12.py)"""
import os, re, json, math
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v12', 'dxf'); os.makedirs(OUT, exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v12', 'CNC_v12_base.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
PARTS = [('Datum_base_plate', 1), ('Work_table', 1), ('Column_foot_L', 1), ('Column_foot_R', 1), ('Gantry_column_L', 1), ('Gantry_column_R', 1),
         ('X_base_plate', 1), ('X_saddle_plate', 1), ('X_carriage_plate', 1), ('Z_slide_plate', 1), ('Z_spacer_L', 1), ('Z_spacer_R', 1),
         ('Z_motor_plate', 1), ('Z_nut_housing', 1), ('X_nut_bracket', 1), ('Y_nut_bracket', 1), ('X_motor_block', 1), ('Y_motor_block', 1),
         ('Spindle_clamp', 1), ('Spindle_mount_plate', 1), ('Base_riser_1', 4),
         ('Yaw_push_block', 1), ('X_roll_bracket', 1), ('Z_roll_block_L', 1), ('Z_roll_block_R', 1), ('Spindle_roll_block_L', 1), ('Spindle_roll_block_R', 1)]
AX = {'x': App.Vector(1, 0, 0), 'y': App.Vector(0, 1, 0), 'z': App.Vector(0, 0, 1)}
UV = {'z': ('x', 'y'), 'y': ('x', 'z'), 'x': ('y', 'z')}
comp = lambda v, a: getattr(v, a)

def cylinders(shape):
    out = []
    for f in shape.Faces:
        if f.Surface.__class__.__name__ != 'Cylinder': continue
        a = f.Surface.Axis; k = max('xyz', key=lambda q: abs(comp(a, q)))
        if abs(comp(a, k)) < 0.999: continue
        u0, u1, v0, v1 = f.ParameterRange
        p = f.valueAt((u0 + u1) / 2, (v0 + v1) / 2); n = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        c = f.Surface.Center; rv = p - c; rv = rv - AX[k] * rv.dot(AX[k])
        b = f.BoundBox; rng = {'x': (b.XMin, b.XMax), 'y': (b.YMin, b.YMax), 'z': (b.ZMin, b.ZMax)}[k]
        out.append({'k': k, 'c': c, 'r': f.Surface.Radius, 'rng': rng, 'span': abs(u1 - u0), 'hole': n.dot(rv) < 0})
    return out
# what goes into holes: pins (H7) and screws (taps), as world axis lines
PINS, SCREWS = [], []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull(): continue
    n = o.Label
    if re.search(r'(pivot_pin|lock_dowel|roll_pin|ref_pin_\d|ecc_pin_\d|pivot_bearing)', n):   # 'Spindle' contains 'pin': match whole names
        for c in cylinders(o.Shape):
            if not c['hole']: PINS.append((n, c))
    if re.search(r'(bolt|screw|jack|_stud)', n):
        spec = getattr(o, 'Spec', '') if 'Spec' in o.PropertiesList else ''
        for c in cylinders(o.Shape):
            if not c['hole']: SCREWS.append((n, spec, c))
def coaxial(h, c, tol_r=0.06):
    if h['k'] != c['k'] or abs(h['r'] - c['r']) > tol_r: return False
    d = h['c'] - c['c']; d = d - AX[h['k']] * d.dot(AX[h['k']])
    return d.Length < 0.2 and min(h['rng'][1], c['rng'][1]) - max(h['rng'][0], c['rng'][0]) > 0.3
H7 = [(0, 3, 0.010), (3, 6, 0.012), (6, 10, 0.015), (10, 18, 0.018), (18, 30, 0.021), (30, 50, 0.025), (50, 80, 0.030)]
def h7lim(d): return next(t for a, b, t in H7 if a < d <= b)

def edges2d(wire, k, off):
    u, v = UV[k]; P = lambda p: (round(comp(p, u) - off[0], 3), round(comp(p, v) - off[1], 3)); ents = []
    for e in wire.Edges:
        cn = e.Curve.__class__.__name__
        if cn in ('Line', 'LineSegment'): ents.append(['L', P(e.Vertexes[0].Point), P(e.Vertexes[-1].Point)])
        elif cn == 'Circle':
            if e.isClosed(): ents.append(['C', P(e.Curve.Center), round(e.Curve.Radius, 3)])
            else:
                a, b = e.ParameterRange; ents.append(['A', P(e.valueAt(a)), P(e.valueAt((a + b) / 2)), P(e.valueAt(b))])
        else: ents.append(['P', [P(p) for p in e.discretize(Deflection=0.02)]])
    return ents
def is_circle(w): return len(w.Edges) == 1 and w.Edges[0].Curve.__class__.__name__ == 'Circle'

data = []
for name, qty in PARTS:
    o = O(name); S = o.Shape; b = S.BoundBox
    size = {'x': b.XLength, 'y': b.YLength, 'z': b.ZLength}; lo = {'x': b.XMin, 'y': b.YMin, 'z': b.ZMin}; hi = {'x': b.XMax, 'y': b.YMax, 'z': b.ZMax}
    main = min('xyz', key=lambda q: size[q])
    cyl = [c for c in cylinders(S) if c['hole'] and c['r'] < 60]
    axes = [main] + [k for k in 'xyz' if k != main and any(c['k'] == k for c in cyl)]
    views = []
    for k in axes:
        u, v = UV[k]; off = (lo[u], lo[v])
        ents, seen = [], set()
        for tag, d in (('outline', (lo[k] + hi[k]) / 2), ('pocket', hi[k] - 0.3), ('pocket', lo[k] + 0.3)):
            for w in S.slice(AX[k], d):
                if is_circle(w): continue
                key = tuple(round(x, 1) for x in (w.BoundBox.XMin, w.BoundBox.XMax, w.BoundBox.YMin, w.BoundBox.YMax, w.BoundBox.ZMin, w.BoundBox.ZMax))
                if key in seen: continue
                seen.add(key); ents.append([tag, edges2d(w, k, off)])
        groups = {}                                           # holes along this axis, grouped by centre
        for c in cyl:
            if c['k'] != k: continue
            key = (round(comp(c['c'], u), 2), round(comp(c['c'], v), 2))
            groups.setdefault(key, []).append(c)
        holes = []
        for (cu, cv), cs in groups.items():
            rs = {}
            for c in cs:
                q = round(c['r'], 3); e = rs.setdefault(q, {'r': c['r'], 'span': 0, 'rng': [1e9, -1e9], 'c': c['c'], 'k': k})
                e['span'] += c['span']; e['rng'] = [min(e['rng'][0], c['rng'][0]), max(e['rng'][1], c['rng'][1])]
            full = sorted([e for e in rs.values() if e['span'] > 2 * math.pi - 0.15], key=lambda e: e['r'])
            if not full: continue
            m = full[0]; d = 2 * m['r']; through = m['rng'][0] <= lo[k] + 0.1 and m['rng'][1] >= hi[k] - 0.1
            depth = m['rng'][1] - m['rng'][0]
            side = 'top' if m['rng'][1] >= hi[k] - 0.1 else 'bottom'
            pin = next((pn for pn, pc in PINS if coaxial(m, pc)), None)
            scr = next(((sn, sp) for sn, sp, sc in SCREWS if coaxial(m, sc)), None)
            if pin:
                t = h7lim(d); txt = 'Ø%g H7 (+%.3f/0)%s' % (round(d, 2), t, ' thru' if through else ' depth %g' % round(depth, 1))
                if 'lock_dowel' in pin: txt += ', ream at assembly (pre-drill Ø%g)' % (round(d, 1) - 0.5)
                cls = 'H7'
            elif scr and not through or scr and scr[0].startswith(('Foot_col', 'X_plate_bolt', 'Base_mount', 'Spindle_clamp_bolt')) and False:
                mm = re.search(r'M(\d+)x([\d.]+)', scr[1]); pitch = ''
                if mm and float(mm.group(2)) < {4: .7, 5: .8, 6: 1, 8: 1.25, 10: 1.5, 12: 1.75}.get(int(mm.group(1)), 9): pitch = 'x%s' % mm.group(2)
                txt = 'M%d%s tap depth %g' % (round(d), pitch, round(depth, 1)); cls = 'TAP'
            elif scr:
                mm = re.search(r'M(\d+)x([\d.]+)', scr[1]); pitch = ''
                if mm and float(mm.group(2)) < {4: .7, 5: .8, 6: 1, 8: 1.25, 10: 1.5, 12: 1.75}.get(int(mm.group(1)), 9): pitch = 'x%s' % mm.group(2)
                txt = 'M%d%s tap thru' % (round(d), pitch); cls = 'TAP'
            else:
                txt = 'Ø%g%s' % (round(d, 2), ' thru' if through else ' depth %g' % round(depth, 1)); cls = 'HOLE'
            for e in full[1:]:                                # coaxial larger = counterbore
                txt += ', c-bore Ø%g depth %g' % (round(2 * e['r'], 2), round(e['rng'][1] - e['rng'][0], 1))
            if not through and cls != 'H7': txt += ' (from %s)' % side
            holes.append({'u': round(cu - off[0], 3), 'v': round(cv - off[1], 3), 'r': round(m['r'], 3), 'big': round(full[-1]['r'], 3), 'cls': cls, 'txt': txt})
        views.append({'axis': k, 'w': round(size[u], 2), 'h': round(size[v], 2), 'ents': ents, 'holes': holes})
    spec = getattr(o, 'Spec', '') if 'Spec' in o.PropertiesList else ''
    data.append({'name': name, 'qty': qty, 'size': [round(size[q], 2) for q in 'xyz'], 'spec': spec, 'views': views})
    print(name, 'views', [v['axis'] for v in views], 'holes', [len(v['holes']) for v in views], 'H7', sum(h['cls'] == 'H7' for v in views for h in v['holes']))
json.dump(data, open(os.path.join(OUT, 'parts.json'), 'w', encoding='utf-8'), ensure_ascii=False)
