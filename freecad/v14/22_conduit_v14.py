# -*- coding: utf-8 -*-
"""v14 cable conduits (owner: corrugated PA conduit, no drag chains): each moving run is a conduit of fixed length between two
anchors (point + direction the conduit runs through it); at every pose its centre line is the cubic Bezier through the anchors whose
handles are set so its length equals the conduit length (slack bulges out, a stretched run goes straight). The same rule drives the
motion pages (CONDUITS json). Checked at all 27 travel-end poses: collisions with the machine, minimum bend radius, taut runs.
Fixed ends sit on the electrical box on the gantry columns (Y: bottom cover gland, X: roof gland + rolling loop on the roof).
Frames: 's' static, 'y' table, 'x' X carriage, 'z' Z slide (moves with X and Z). Machine coordinates at home.
Run:  freecadcmd freecad/v14/22_conduit_v14.py      Out: output/v14/conduits.json, output/v14/logs/v14_conduit_check.txt"""
import os, json, math, itertools
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
# electrical box on the gantry columns (docs/handoff_electrical_box_v14.md): outer envelope, sheet metal not modelled yet. Conduits enter it
# only through the bottom cover (Y) and the roof gland (X); everything else of every conduit must stay outside it.
BOX = ((-392.5, 252.0, 241.0), (392.5, 450.0, 494.0))   # box (electrical session, column_box/) hung under the box top plate (01: z 491..494)
ZT = BOX[1][2] + 34.5 / 2 + 10.75       # X loop centre height: as the roof adaptor on its tab and the carriage-arm clamp (01)
XFF = -50.0 - 1.2 * 37.0  # fixed leg start: end of the roof PAQ-2929 body (adaptor on the tab at x -50 pointing -x, 01; loop folded LEFT, 2026-11-28)
XF = 34.0      # X loop moving leg end (clamp on the carriage conduit carrier, 01); the conduit leaves it heading +x (fixed leg on the roof, moving leg on the carriage arm): loop spans x -120..368 incl. its radius, roof edge 392.5
GLANDS = [(-50, 390, BOX[1][2], 34.5)]   # (x, y, z, conduit OD): X roof (the Y run no longer enters the box)
ATTACH = {   # conduit -> its own end fittings / clamps (01): the conduit ends inside them, reported apart as expected
    'Conduit_Y': ('Conduit_Y_top_fitting', 'Conduit_Y_end_fitting'), 'Conduit_ZB': ('Conduit_head_end_fitting', 'Conduit_ZB_top_fitting'),
    'Conduit_XA': ('Conduit_X_roof_connector', 'Conduit_X_moving_clamp'),
    'Conduit_carriage_run': ('Conduit_X_moving_clamp', 'Conduit_X_riser_clamp', 'Conduit_X_box_fitting'),
    'Conduit_Ymotor_run': ('Conduit_Ymotor_box_fitting', 'Conduit_Ymotor_end_fitting'),
    'Conduit_mirror_run': ('Conduit_mirror_box_fitting', 'Conduit_mirror_end_fitting', 'Conduit_Y_yoke_L', 'Conduit_Y_yoke_R')}
OLD_PANEL = ('Electrical_panel', 'Servo_amp', 'Servo_bolt', 'Controller', 'Board_standoff', 'Panel_standoff')   # replaced by the box
# name: (label, outer D, length, (frame, point, direction) start, (frame, point, direction) end, min bend radius allowed)
CONDUITS = {
    # hanging runs: fixed length between two clamped ends, settles under gravity (Y: panel -> Y motor, Z: X carriage -> tool head)
    # rolling loop in the vertical plane x 280 (table right side): fixed drop from the L-plate bracket, lower leg in the base tray, bend R 55,
    # upper leg in the table tray to the end adaptor (01); the shape is computed by roll_y
    'Conduit_Y': ('Y 軸浪管：立柱電箱 L 板支架直下 → 底座托盤 → R55 滾動彎 → 工作台右後集線盒（KSS PA-23，模型外徑 28.5），x 280 平面', 28.5, None,
                  ('s', (280, 446, 233.0 - 1.2 * 28.3), (0, 0, -1)), ('y', (280, 225.0 - 1.2 * 28.3, 127.25), (0, 1, 0)), 50.0),
    'Conduit_ZB': ('Z 段浪管：X 滑座集線盒 → 工具頭（KSS PA-29，模型外徑 34.5），下垂 U 型', 34.5, 560.0,
                   ('x', (114, 40, 712.0 - 1.2 * 37.0), (0, 0, -1)), ('z', (114, -80, 470.0 - 2 * 1.2 * 37.0 - 3.0), (0, 0, 1)), 60.0),   # end under the head bracket arm
    # rolling loop on the box top plate (X: fixed leg y 390, moving leg y 230 on an arm from the carriage, bend R 80)
    'Conduit_XA': ('X 段浪管：電箱頂板上的水平滾動 U 型環，R 80（KSS PA-29，模型外徑 34.5）', 34.5, None,
                   ('s', (XFF, 390, ZT), (-1, 0, 0)), ('x', (XF, 230, ZT), (-1, 0, 0)), 60.0),
}
ROLL = {'Conduit_XA': {'R': 80.0, 'c': 164.0, 'm': -1}}   # m -1: legs run -x from their ends, bend on the left; c 164: reach x -382.5 at X -182.5, bend left of the fixed leg start at X +182.5
def _arc(c, r, a0, a1, plane, n=8):    # points on an arc in the 'xz' or 'yz' plane through centre c, angles in degrees
    out = []
    for k in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * k / n); u, w = r * math.cos(t), r * math.sin(t)
        out.append((c[0] + u, c[1], c[2] + w) if plane == 'xz' else (c[0], c[1] + u, c[2] + w))
    return out
# carriage run (x frame, the same PA-29 as the roof loop; owner 2026-11-28, design review): moving-end clamp at x 34 -> straight to x 54 ->
# bend A up R 60 (plane y 230) -> riser in the plane x 114 -> bend B forward R 60 over the saddle -> PAQ-2929 in the branch box rear wall (01)
CARRIAGE_RUN = ([(XF, 230, ZT)] + _arc((54, 230, ZT + 60), 60, -90, 0, 'xz') + _arc((114, 170, 683.5), 60, 0, 90, 'yz')
                + [(114, 100.0 + 1.2 * 37.0, 743.5)])
TZ, TY1, TY2 = 99.0, 292.0, 326.0                              # table rear PA-17 lanes: one plane z 99, y 292 (Y motor) / 326 (mirror cover), pitch 34
MIRROR_RUN = ([(180 - 1.2 * 22.5, TY2, TZ), (-200, TY2, TZ)] + [(-200 + 50 * math.cos(math.radians(t)), 276 + 50 * math.sin(math.radians(t)), TZ)
              for t in range(90, 181, 10)] + [(-250, 203 + 1.2 * 22.5, TZ)])
STATIC_RUNS = {   # conduit pieces fixed to one frame (no flexing): drawn and checked for collisions
    'Conduit_carriage_run': ('x', 34.5, CARRIAGE_RUN),
    'Conduit_Ymotor_run': ('y', 21.2, [(180 - 1.2 * 22.5, TY1, TZ), (73 + 1.2 * 22.5, TY1, TZ)]),   # table end box -> Y motor bracket (PA-17)
    'Conduit_mirror_run': ('y', 21.2, MIRROR_RUN),                                                  # table end box -> mirror-cover bracket (PA-17)
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
    """rolling loop in the plane of the legs: fixed leg from xf, moving leg from xa, both along m*x, semicircle R at xb = (xf+xa)/2 + c
    (computed in u = m*x)"""
    R, cc, m = ROLL[name]['R'], ROLL[name]['c'], ROLL[name].get('m', 1)
    (f0, a0, _), (f1, a1, _) = c[3], c[4]
    xf, yF, z = a0; xa = a1[0] + off(f1, P)[0]; yM = a1[1]
    xf, xa = m * xf, m * xa
    xb = (xf + xa) / 2 + cc; yc = (yF + yM) / 2; r = abs(yF - yM) / 2
    q = [(xf + (xb - xf) * k / 12, yF, z) for k in range(13)]
    sgn = 1 if yF > yc else -1
    for k in range(1, 24): t = math.pi * k / 24; q.append((xb + r * math.sin(t), yc + sgn * r * math.cos(t), z))
    q += [(xb - (xb - xa) * k / 12, yM, z) for k in range(13)]
    return [(m * u, y, z_) for u, y, z_ in q], ('INVERTED' if xb < max(xf, xa) - 0.5 else '')
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
YROLL = {'x': 280.0, 'zl': 17.25, 'zu': 127.25, 'R': 55.0, 'yl': 391.0, 'K': 258.5}   # lower leg starts at yl (after the drop bend); K sets the loop
def roll_y(c, P):
    """Y rolling loop: drop from the fixed adaptor, quarter bend into the lower leg (heading -y), half-circle bend, upper leg back (+y) to the
    moving end; the bend sits at yb = (yl + ym) / 2 - K, i.e. it moves half the table travel"""
    g = YROLL; x, R = g['x'], g['R']; A = c[3][1]; ym = c[4][1][1] + P[1]
    yb = (g['yl'] + ym) / 2 - g['K']; zc = g['zl'] + R
    q = [(x, A[1], A[2] - (A[2] - zc) * k / 8) for k in range(9)]
    q += [(x, g['yl'] + R * math.cos(t), zc - R * math.sin(t)) for t in [math.pi / 2 * k / 10 for k in range(1, 11)]]
    q += [(x, g['yl'] - (g['yl'] - yb) * k / 12, g['zl']) for k in range(1, 13)]
    q += [(x, yb - R * math.sin(t), zc - R * math.cos(t)) for t in [math.pi * k / 20 for k in range(1, 21)]]
    q += [(x, yb + (ym - yb) * k / 10, g['zu']) for k in range(1, 11)]
    return q, ('TOO SHORT' if ym - yb < 10 else '')
def curve(c, P, name=None):
    if name == 'Conduit_Y': return roll_y(c, P)
    return roll(name, c, P) if name in ROLL else hang(c, P)
def min_radius(q):
    r = 1e9
    for i in range(1, len(q) - 1):
        a, b, c = V(*q[i - 1]), V(*q[i]), V(*q[i + 1])
        ab, bc, ca = (b - a).Length, (c - b).Length, (a - c).Length
        cr = (b - a).cross(c - b).Length
        if cr > 1e-9: r = min(r, ab * bc * ca / (2 * cr))
    return r
def tube(q, D, poly=False):
    # Fused cylinders + spheres along the centre line (one valid solid). A swept pipe shell was used before, but its booleans with the machine
    # parts silently returned 0 volume, so 22 reported 0 collisions while the Y conduit ran through the work table (found by the owner).
    parts = []
    for a_, b_ in zip(q[:-1], q[1:]):
        d = V(*b_) - V(*a_)
        if d.Length > 1e-6: parts.append(Part.makeCylinder(D / 2, d.Length, V(*a_), d))
    parts += [Part.makeSphere(D / 2, V(*p)) for p in q[1:-1]]
    sh = parts[0].multiFuse(parts[1:]) if len(parts) > 1 else parts[0]
    return sh.removeSplitter() if sh.isValid() else sh

if True:                                                        # freecadcmd does not set __main__
    doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))
    def cls(o):
        n = o.Label
        if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
        if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
        if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
        if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
        return ''
    OBJ = {o.Label: (o.Shape, cls(o)) for o in doc.Objects if o.TypeId == 'Part::Feature' and not o.Shape.isNull() and not o.Label.startswith(('Keepout',) + OLD_PANEL)}
    (bx0, by0, bz0), (bx1, by1, bz1) = BOX
    CB = os.path.join(ROOT, 'column_box', 'column_box.step')   # the real box (electrical session) when present, else its envelope
    if os.path.exists(CB):
        import Import
        cbd = App.newDocument('column_box'); Import.insert(CB, cbd.Name)
        for o in cbd.Objects:
            if o.TypeId == 'Part::Feature' and not o.Shape.isNull() and o.Shape.Solids: OBJ['Box:' + o.Label] = (o.Shape, '')
    else:
        EB = Part.makeBox(bx1 - bx0, by1 - by0, bz1 - bz0, V(bx0, by0, bz0))
        for gx, gy, gz, gd in GLANDS: EB = EB.cut(Part.makeCylinder(gd / 2 + 2, 80, V(gx, gy, gz - 40)))   # gland holes: the only way in
        OBJ['Electrical_box (envelope)'] = (EB, '')
    POSES = list(itertools.product((-182.5, 0, 182.5), (-250, 0, 150), (-50, 0, 50)))
    out, hits, worst, seat = [], {}, {}, {}
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
                if v > 1 and n in ATTACH.get(name, ()): seat.setdefault((name, n), round(v))
                elif v > 1: hits.setdefault((name, n), (P, round(v)))
        worst[name] = (rmin, taut)
    for name, (fr, D, pp) in STATIC_RUNS.items():
        for P in POSES:
            o_ = off(fr, P)
            if D == 0: T = Part.makeBox(pp[1][0] - pp[0][0], pp[1][1] - pp[0][1], pp[1][2] - pp[0][2], V(pp[0][0] + o_[0], pp[0][1] + o_[1], pp[0][2] + o_[2]))
            else: T = tube([tuple(a + b for a, b in zip(p, o_)) for p in pp], D, poly=name.endswith('_entry'))
            tb = T.BoundBox
            for n, (sh, k) in OBJ.items():
                o = off(k if k in ('y', 'x', 'z') else 's', P)
                bb = sh.BoundBox; bb = App.BoundBox(bb.XMin + o[0], bb.YMin + o[1], bb.ZMin + o[2], bb.XMax + o[0], bb.YMax + o[1], bb.ZMax + o[2])
                if not tb.intersect(bb): continue
                s2 = sh.copy(); s2.translate(V(*o))
                try: v = T.common(s2).Volume
                except Exception: v = 0
                if v > 1 and n in ATTACH.get(name, ()): seat.setdefault((name, n), round(v))
                elif v > 1: hits.setdefault((name, n), (P, round(v)))
            if fr == 's': break                                   # fixed pieces do not move
    L = ['v14 conduits: %d moving runs, %d poses' % (len(CONDUITS), len(POSES)), '']
    for name, c in CONDUITS.items():
        r, t = worst[name]
        L.append('%-12s %s  length %s, min bend radius over all poses %.0f (allowed %g) %s %s' % (name, c[0], c[2] or 'rolling', r, c[5],
                 'OK' if r >= c[5] - 0.5 else 'TOO TIGHT', ('TAUT at %s' % t) if t else ''))
    L += ['', 'CONDUIT ENDS IN THEIR OWN FITTINGS / CLAMPS (expected): %d' % len(seat)] + ['  %s in %s: %s mm3' % (a, b, v) for (a, b), v in sorted(seat.items())]
    L += ['', 'COLLISIONS: %d' % len(hits)] + ['  %s x %s at %s: %s mm3' % (a, b, p, v) for (a, b), (p, v) in sorted(hits.items())]
    open(os.path.join(ROOT, 'output', 'v14', 'logs', 'v14_conduit_check.txt'), 'w', encoding='utf-8').write('\n'.join(L))
    RNG = {0: (-182.5, 182.5), 1: (-250.0, 150.0), 2: (-50.0, 50.0)}
    js = {'moving': {}, 'static': {n: {'f': f, 'D': d, 'p': p} for n, (f, d, p) in STATIC_RUNS.items()}, 'box': BOX, 'glands': GLANDS}
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
    print('conduit check written: %d collisions' % len(hits))
