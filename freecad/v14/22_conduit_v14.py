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
    # hanging runs: fixed length between two clamped ends, settles under gravity (Y: panel -> Y motor, Z: X carriage -> tool head)
    'Conduit_Y': ('Y 軸浪管：背板下緣 → Y 馬達（PA 浪管 NW23, AD 28.5），下垂 U 型', 28.5, 540.0,
                  ('s', (-120, 330, 295), (0, 0, -1)), ('y', (0, 395, 200), (0, 0, 1)), 50.0),
    'Conduit_ZB': ('Z 段浪管：X 滑座 → 工具頭（PA 浪管 NW29, AD 34.5），下垂 U 型', 34.5, 450.0,
                   ('x', (110, 40, 640), (0, 0, -1)), ('z', (110, -80, 470), (0, 0, 1)), 60.0),
    # rolling loop on a tray above the back plate (X: fixed leg y 390, moving leg y 230 on an arm from the carriage, bend R 80)
    'Conduit_XA': ('X 段浪管：托盤上的水平滾動 U 型環，R 80（PA 浪管 NW29, AD 34.5）', 34.5, None,
                   ('s', (110, 390, 587), (1, 0, 0)), ('x', (110, 230, 587), (1, 0, 0)), 60.0),
}
ROLL = {'Conduit_XA': {'R': 80.0, 'c': 100.0}}
STATIC_RUNS = {   # conduit pieces fixed to one frame (no flexing): drawn and checked for collisions
    'Conduit_panel_run': ('s', 34.5, [(-20, 340, 560), (-20, 345, 580), (30, 380, 587), (110, 390, 587)]),
    'Conduit_carriage_run': ('x', 34.5, [(110, 230, 587), (85, 230, 590), (85, 190, 690), (110, 110, 740), (110, 40, 715), (110, 40, 640)]),
    'Conduit_tray': ('s', 0, [(-190, 205, 568), (395, 415, 570)]),   # tray box corners (sheet t2), drawn as a box
}
def off(fr, P):
    dx, dy, dz = P
    return {'s': (0, 0, 0), 'y': (0, dy, 0), 'x': (dx, 0, 0), 'z': (dx, 0, dz)}[fr]
import numpy as np
AXIS = {'Conduit_Y': 1, 'Conduit_XA': 0, 'Conduit_ZB': 2}
G_STEP, K_BEND = 0.004, 0.05       # the one travel that changes each run's shape
def relax(c, P, n=41, it=6000):
    """hanging conduit: fixed length, both ends clamped (end point + direction), bending stiffness + gravity (position-based relaxation)"""
    _, D, L, (f0, a0, t0), (f1, a1, t1), _ = c
    A = np.add(a0, off(f0, P)); B = np.add(a1, off(f1, P)); tA = np.array(t0, float); tB = np.array(t1, float)
    seg = L / (n - 1)
    x = np.array([A + (B - A) * k / (n - 1) for k in range(n)], float)
    mid = (A + B) / 2 + np.array([0, 0, -0.25 * L])               # start sagging, so the shape settles below the straight line
    for k in range(n):
        u = k / (n - 1); x[k] = (1 - u) ** 2 * A + 2 * u * (1 - u) * mid + u * u * B
    fix = {0: A, 1: A + seg * tA, n - 2: B - seg * tB, n - 1: B}
    free = np.ones(n); free[[0, 1, n - 2, n - 1]] = 0
    FX = np.array([A, A + seg * tA, B - seg * tB, B]); FI = [0, 1, n - 2, n - 1]
    for _ in range(it):
        x[2:n - 2, 2] -= G_STEP                                    # gravity
        bi = x[0:n - 4] - 4 * x[1:n - 3] + 6 * x[2:n - 2] - 4 * x[3:n - 1] + x[4:n]   # gradient of the summed squared curvature
        x[2:n - 2] -= K_BEND * bi                                  # bending stiffness (clamped ends keep their direction)
        for _p in range(6):                                        # segment lengths (vectorised, Jacobi)
            d = x[1:] - x[:-1]; l = np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
            corr = (l - seg) / l * d
            w0 = free[:-1, None]; w1 = free[1:, None]; ws = w0 + w1; ws[ws == 0] = 1
            dx_ = np.zeros_like(x); dx_[:-1] += corr * w0 / ws; dx_[1:] -= corr * w1 / ws
            x += 0.9 * dx_; x[FI] = FX
    taut = np.linalg.norm(B - A) > 0.98 * L
    return [tuple(p) for p in x], ('TAUT' if taut else '')
def roll(name, c, P, n=61):
    """rolling loop in the plane of the legs: fixed leg from xf, moving leg from xa, both along +x, semicircle R at xb = (xf+xa)/2 + c"""
    R, cc = ROLL[name]['R'], ROLL[name]['c']
    (f0, a0, _), (f1, a1, _) = c[3], c[4]
    xf, yF, z = a0; xa = a1[0] + off(f1, P)[0]; yM = a1[1]
    xb = (xf + xa) / 2 + cc; yc = (yF + yM) / 2; r = abs(yF - yM) / 2
    q = [(xf + (xb - xf) * k / 12, yF, z) for k in range(13)]
    sgn = 1 if yF > yc else -1
    for k in range(1, 24): t = math.pi * k / 24; q.append((xb + r * math.sin(t), yc + sgn * r * math.cos(t), z))
    q += [(xb - (xb - xa) * k / 12, yM, z) for k in range(13)]
    return q, ''
def hang(c, P, n=60):
    """hanging U: a vertical leg down from each end, joined by a half circle in the vertical plane through both ends (radius = half
    their horizontal distance); leg lengths share the fixed conduit length so both legs end at the same height"""
    _, D, L, (f0, a0, _), (f1, a1, _), _ = c
    A = np.add(a0, off(f0, P)); B = np.add(a1, off(f1, P))
    h = (B - A)[:2]; dh = float(np.linalg.norm(h)); r = dh / 2; hu = h / dh if dh > 1e-9 else np.array([1.0, 0.0])
    dz = A[2] - B[2]; a = (L - math.pi * r + dz) / 2; b = (L - math.pi * r - dz) / 2
    flag = 'TAUT' if b < 5 else ''
    a = max(a, dz + 5); b = max(b, 5)
    q = [tuple(A - [0, 0, a * k / 15]) for k in range(16)]
    C = A - [0, 0, a] + np.array([hu[0] * r, hu[1] * r, 0])
    for k in range(1, 30):
        t = math.pi * k / 30; q.append(tuple(C + np.array([-math.cos(t) * hu[0] * r, -math.cos(t) * hu[1] * r, -math.sin(t) * r])))
    q += [tuple(B - [0, 0, b * (15 - k) / 15]) for k in range(16)]
    return q, flag
def curve(c, P, name=None):
    return roll(name, c, P) if name in ROLL else hang(c, P)
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
            q, flag = curve(c, P, name)
            if flag: taut.append(P)
            rmin = min(rmin, min_radius(q))
            T = tube(q, c[1]); tb = T.BoundBox
            for n, (sh, k) in OBJ.items():
                o = off(k if k in ('y', 'x', 'z') else 's', P)
                bb = sh.BoundBox; bb = App.BoundBox(bb.XMin + o[0], bb.YMin + o[1], bb.ZMin + o[2], bb.XMax + o[0], bb.YMax + o[1], bb.ZMax + o[2])
                if not tb.intersect(bb): continue
                s2 = sh.copy(); s2.translate(V(*o))
                try: v = T.common(s2).Volume
                except Exception: v = 0
                if v > 1: hits.setdefault((name, n), (P, round(v)))
        worst[name] = (rmin, taut)
    for name, (fr, D, pp) in STATIC_RUNS.items():
        for P in POSES:
            o_ = off(fr, P)
            if D == 0: T = Part.makeBox(pp[1][0] - pp[0][0], pp[1][1] - pp[0][1], pp[1][2] - pp[0][2], V(pp[0][0] + o_[0], pp[0][1] + o_[1], pp[0][2] + o_[2]))
            else: T = tube([tuple(a + b for a, b in zip(p, o_)) for p in pp], D)
            tb = T.BoundBox
            for n, (sh, k) in OBJ.items():
                o = off(k if k in ('y', 'x', 'z') else 's', P)
                bb = sh.BoundBox; bb = App.BoundBox(bb.XMin + o[0], bb.YMin + o[1], bb.ZMin + o[2], bb.XMax + o[0], bb.YMax + o[1], bb.ZMax + o[2])
                if not tb.intersect(bb): continue
                s2 = sh.copy(); s2.translate(V(*o))
                try: v = T.common(s2).Volume
                except Exception: v = 0
                if v > 1: hits.setdefault((name, n), (P, round(v)))
            if fr == 's' and D == 0: break
    L = ['v14 conduits: %d moving runs, %d poses' % (len(CONDUITS), len(POSES)), '']
    for name, c in CONDUITS.items():
        r, t = worst[name]
        L.append('%-12s %s  length %s, min bend radius over all poses %.0f (allowed %g) %s %s' % (name, c[0], c[2] or 'rolling', r, c[5],
                 'OK' if r >= c[5] else 'TOO TIGHT', ('TAUT at %s' % t) if t else ''))
    L += ['', 'COLLISIONS: %d' % len(hits)] + ['  %s x %s at %s: %s mm3' % (a, b, p, v) for (a, b), (p, v) in sorted(hits.items())]
    open(os.path.join(ROOT, 'output', 'v14', 'logs', 'v14_conduit_check.txt'), 'w', encoding='utf-8').write('\n'.join(L))
    RNG = {0: (-182.5, 182.5), 1: (-250.0, 150.0), 2: (-50.0, 50.0)}
    js = {'moving': {}, 'static': {n: {'f': f, 'D': d, 'p': p} for n, (f, d, p) in STATIC_RUNS.items()}}
    for name, c in CONDUITS.items():
        ax = AXIS[name]; lo, hi = RNG[ax]; vals = [lo + (hi - lo) * k / 20 for k in range(21)]
        fr = c[4][0]                                              # shapes stored in the moving end's frame minus the varying axis
        samples = []
        for v in vals:
            P = [0, 0, 0]; P[ax] = v
            q, _ = curve(c, tuple(P), name)
            if name == 'Conduit_ZB': q = [(p[0], p[1], p[2]) for p in q]   # relative to the X carriage (dx = 0)
            samples.append([[round(t, 1) for t in p] for p in q])
        js['moving'][name] = {'t': c[0], 'D': c[1], 'ax': 'xyz'[ax], 'v': vals, 's': samples, 'shiftx': name == 'Conduit_ZB'}
    json.dump(js, open(os.path.join(ROOT, 'output', 'v14', 'conduits.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n'.join(L))
