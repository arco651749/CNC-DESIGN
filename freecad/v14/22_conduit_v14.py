# -*- coding: utf-8 -*-
"""v14 cable conduits (owner: corrugated PA conduit, no drag chains): each moving run is a conduit of fixed length between two
anchors (point + direction the conduit runs through it); at every pose its centre line is the cubic Bezier through the anchors whose
handles are set so its length equals the conduit length (slack bulges out, a stretched run goes straight). The same rule drives the
motion pages (CONDUITS json). Checked at all 27 travel-end poses: collisions with the machine, minimum bend radius, taut runs.
Frames: 's' static, 'y' table, 'x' X carriage, 'z' Z slide (moves with X and Z). Machine coordinates at home.
Run:  freecadcmd freecad/v14/22_conduit_v14.py      Out: output/v14/conduits.json, output/v14/logs/v14_conduit_check.txt"""
import os, json, math, itertools
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
# name: (label, outer D, length, (frame, point, direction) start, (frame, point, direction) end, min bend radius allowed)
CONDUITS = {
    'Conduit_Y': ('Y 軸浪管：背板下緣 → Y 馬達（PA 浪管 NW23, AD 28.5）', 28.5, 380.0,
                  ('s', (-80, 330, 295), (0, 0, -1)), ('y', (0, 395, 140), (0, 0, -1)), 60.0),
    'Conduit_XA': ('X 段浪管：背板上緣 → X 滑座（PA 浪管 NW29, AD 34.5）', 34.5, 560.0,
                   ('s', (-120, 340, 565), (0, 0, 1)), ('x', (0, 160, 730), (0, -1, 0)), 70.0),
    'Conduit_ZB': ('Z 段浪管：X 滑座 → 工具頭（PA 浪管 NW29, AD 34.5）', 34.5, 300.0,
                   ('x', (110, 40, 640), (0, 0, -1)), ('z', (75, -30, 470), (0, 0, -1)), 70.0),
}
STATIC_RUNS = {   # conduit pieces that do not flex (fixed to one frame): drawn, not checked for bending
    'Conduit_X_carriage_run': ('x', 34.5, [(0, 160, 730), (0, 60, 730), (110, 40, 720), (110, 40, 640)]),
}
def off(fr, P):
    dx, dy, dz = P
    return {'s': (0, 0, 0), 'y': (0, dy, 0), 'x': (dx, 0, 0), 'z': (dx, 0, dz)}[fr]
def bez(p0, p1, p2, p3, t):
    u = 1 - t; return tuple(u**3*a + 3*u*u*t*b + 3*u*t*t*c + t**3*d for a, b, c, d in zip(p0, p1, p2, p3))
def curve(c, P, n=48):
    _, D, L, (f0, a0, t0), (f1, a1, t1), _ = c
    A = tuple(a + o for a, o in zip(a0, off(f0, P))); B = tuple(a + o for a, o in zip(a1, off(f1, P)))
    def pts(h):
        p1 = tuple(a + h * t for a, t in zip(A, t0)); p2 = tuple(b - h * t for b, t in zip(B, t1))
        return [bez(A, p1, p2, B, i / n) for i in range(n + 1)]
    length = lambda q: sum(math.dist(q[i], q[i + 1]) for i in range(len(q) - 1))
    lo, hi = 0.0, L
    if length(pts(lo)) > L: return pts(lo), 'TAUT'
    while length(pts(hi)) < L and hi < 10 * L: hi *= 1.5
    for _ in range(40):
        m = (lo + hi) / 2
        if length(pts(m)) < L: lo = m
        else: hi = m
    return pts((lo + hi) / 2), ''
def min_radius(q):
    r = 1e9
    for i in range(1, len(q) - 1):
        a, b, c = V(*q[i - 1]), V(*q[i]), V(*q[i + 1])
        ab, bc, ca = (b - a).Length, (c - b).Length, (a - c).Length
        cr = (b - a).cross(c - b).Length
        if cr > 1e-9: r = min(r, ab * bc * ca / (2 * cr))
    return r
def tube(q, D):
    e = Part.BSplineCurve(); e.interpolate([V(*p) for p in q]); w = Part.Wire(e.toShape())
    t = e.tangent(e.FirstParameter)[0]; circ = Part.Wire(Part.makeCircle(D / 2, V(*q[0]), t))
    return w.makePipeShell([circ], True, True)

if True:                                                        # freecadcmd does not set __main__
    doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))
    def cls(o):
        n = o.Label
        if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
        if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
        if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
        if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
        return ''
    OBJ = {o.Label: (o.Shape, cls(o)) for o in doc.Objects if o.TypeId == 'Part::Feature' and not o.Shape.isNull() and not o.Label.startswith('Keepout')}
    POSES = list(itertools.product((-182.5, 0, 182.5), (-250, 0, 150), (-50, 0, 50)))
    out, hits, worst = [], {}, {}
    for name, c in CONDUITS.items():
        rmin, taut = 1e9, []
        for P in POSES:
            q, flag = curve(c, P)
            if flag: taut.append(P)
            rmin = min(rmin, min_radius(q))
            T = tube(q, c[1]); tb = T.BoundBox
            for n, (sh, k) in OBJ.items():
                o = off({'': 's'}.get(k, k) if k in ('y', 'x', 'z') else 's', P)
                bb = sh.BoundBox; bb = App.BoundBox(bb.XMin + o[0], bb.YMin + o[1], bb.ZMin + o[2], bb.XMax + o[0], bb.YMax + o[1], bb.ZMax + o[2])
                if not tb.intersect(bb): continue
                s2 = sh.copy(); s2.translate(V(*o))
                try: v = T.common(s2).Volume
                except Exception: v = 0
                if v > 1: hits.setdefault((name, n), (P, round(v)))
        worst[name] = (rmin, taut)
    L = ['v14 conduits: %d moving runs, %d poses' % (len(CONDUITS), len(POSES)), '']
    for name, c in CONDUITS.items():
        r, t = worst[name]
        L.append('%-12s %s  length %g, min bend radius over all poses %.0f (allowed %g) %s %s' % (name, c[0], c[2], r, c[5],
                 'OK' if r >= c[5] else 'TOO TIGHT', ('TAUT at %s' % t) if t else ''))
    L += ['', 'COLLISIONS: %d' % len(hits)] + ['  %s x %s at %s: %s mm3' % (a, b, p, v) for (a, b), (p, v) in sorted(hits.items())]
    open(os.path.join(ROOT, 'output', 'v14', 'logs', 'v14_conduit_check.txt'), 'w', encoding='utf-8').write('\n'.join(L))
    js = {'moving': {n: {'t': c[0], 'D': c[1], 'L': c[2], 'a': [c[3][0], c[3][1], c[3][2]], 'b': [c[4][0], c[4][1], c[4][2]]} for n, c in CONDUITS.items()},
          'static': {n: {'f': f, 'D': d, 'p': p} for n, (f, d, p) in STATIC_RUNS.items()}}
    json.dump(js, open(os.path.join(ROOT, 'output', 'v14', 'conduits.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n'.join(L))
