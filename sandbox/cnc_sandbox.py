# -*- coding: utf-8 -*-
"""v14 CNC sandbox for an AI to plan and check measuring moves before the real machine runs them (MuJoCo, kinematic).

The AI places workpieces on the table, then hands over a plan (a list of steps). The sandbox runs it step by step and reports, for each
step: reached / crashed (which parts, where) / out of travel, probe trigger positions, camera images and focus. It does not cut.

Coordinates (mm):
  axes   X, Y, Z = machine axis positions (home 0; X -182.5..182.5, Y -250..150, Z -50..50). Y moves the table, X / Z the tool head.
  table  points on the table in the table frame = machine coordinates at Y = 0 (table top z 110, T-slots at x 0 / +-65 / +-130).
Plan steps (dicts):
  {"op": "move", "X": .., "Y": .., "Z": .., "feed": mm/min}     straight move in axis space (any subset of X/Y/Z), checked all the way
  {"op": "probe", "state": "down" | "up"}                       MXH slide: probe extended (60 down, ball 25 below the tool tip) / retracted
  {"op": "probe_move", "X": .., "Y": .., "Z": .., "feed": ..}   G38.2-like: move until the probe ball touches; error if it never does
  {"op": "capture", "name": ".."}                               camera image (orthographic, 16.8 x 14.0 mm field) + focus check
  {"op": "cover", "state": "open" | "closed"}                   prism cover
Helpers convert table points to axis targets: camera_over(), probe_at(), tool_at(), and back: where().
"""
import os, json, math
import numpy as np
import mujoco

ROOT = os.environ.get('CNC_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(ROOT, 'output', 'v14', 'mujoco', 'cnc_v14.xml')
MAN = json.load(open(os.path.join(ROOT, 'output', 'v14', 'mujoco', 'manifest.json'), encoding='utf-8'))
RANGE = {k: tuple(v['range']) for k, v in MAN['joints'].items()}
RAPID = 5000.0                     # mm/min, assumed rapid feed for the time estimate
STEP = 0.5                         # mm, collision check spacing along a move
PROBE_STROKE = 60.0


class CNCSandbox:
    def __init__(self, image_size=(1024, 1224)):
        self.spec = mujoco.MjSpec.from_file(XML)
        self.workpieces = []
        self.image_size = image_size
        self._compile()

    # ---------------------------------------------------------------- model
    def _compile(self):
        self.m = self.spec.compile()
        self.d = mujoco.MjData(self.m)
        self.adr = {n: self.m.joint(n).qposadr[0] for n in ('X', 'Y', 'Z', 'P', 'C')}
        self.axes = {n: 0.0 for n in self.adr}
        self.head_side = {i for i in range(self.m.ngeom) if self.m.geom_contype[i] & 1}
        self.ball = self.m.geom('Probe_ball').id
        self.trig = {self.ball, self.m.geom('Probe_stylus').id}   # ball or stylus contact triggers the probe
        self.wp_geoms = {self.m.geom(w['name']).id for w in self.workpieces}
        self._renderer = None
        self._set({})

    def add_box(self, name, size, centre, yaw=0.0, base_z=None, rgba=(0.42, 0.45, 0.5, 1)):
        """Box workpiece (size lx, ly, lz mm), centred at table point centre (x, y), standing on the table top (or base_z), turned yaw deg."""
        base_z = MAN['table_top']['z'][1] if base_z is None else base_z
        g = self.spec.body('table').add_geom()
        g.name = name; g.type = mujoco.mjtGeom.mjGEOM_BOX
        g.size = [size[0] / 2000.0, size[1] / 2000.0, size[2] / 2000.0]
        g.pos = [centre[0] / 1000.0, centre[1] / 1000.0, (base_z + size[2] / 2) / 1000.0]
        q = np.zeros(4); mujoco.mju_axisAngle2Quat(q, np.array([0, 0, 1.0]), math.radians(yaw)); g.quat = q
        g.contype = 0; g.conaffinity = 1; g.rgba = list(rgba); g.group = 0
        self.workpieces.append({'name': name, 'type': 'box', 'size': list(size), 'centre': list(centre), 'yaw': yaw, 'base_z': base_z})
        self._compile()

    def add_mesh(self, name, stl_path, pos=(0, 0, 0), yaw=0.0, rgba=(0.55, 0.6, 0.65, 1)):
        """Workpiece from an STL in mm (its own origin placed at table point pos, turned yaw deg). Collision uses its convex hull."""
        self.spec.add_mesh(name='mesh_' + name, file=os.path.abspath(stl_path), scale=[0.001] * 3)
        g = self.spec.body('table').add_geom()
        g.name = name; g.type = mujoco.mjtGeom.mjGEOM_MESH; g.meshname = 'mesh_' + name
        g.pos = [p / 1000.0 for p in pos]
        q = np.zeros(4); mujoco.mju_axisAngle2Quat(q, np.array([0, 0, 1.0]), math.radians(yaw)); g.quat = q
        g.contype = 0; g.conaffinity = 1; g.rgba = list(rgba)
        self.workpieces.append({'name': name, 'type': 'mesh', 'file': stl_path, 'pos': list(pos), 'yaw': yaw})
        self._compile()

    # ---------------------------------------------------------------- state
    def _set(self, ax):
        self.axes.update(ax)
        for n, v in self.axes.items():                           # P: probe extension downward (its joint axis already points -Z)
            self.d.qpos[self.adr[n]] = v / 1000.0
        mujoco.mj_kinematics(self.m, self.d)
        mujoco.mj_collision(self.m, self.d)

    def _site(self, name):
        return self.d.site(name).xpos * 1000.0

    def _table(self, world):
        return [float(world[0]), float(world[1] - self.axes['Y']), float(world[2])]

    def where(self):
        """current axes and the table points of the tool tip, probe ball centre and camera focus point"""
        return {'axes': {k: round(v, 3) for k, v in self.axes.items()},
                'tool_tip': [round(v, 3) for v in self._table(self._site('tool_tip'))],
                'probe_ball': [round(v, 3) for v in self._table(self._site('probe_ball'))],
                'camera_focus': [round(v, 3) for v in self._table(self._site('cam_focus'))]}

    # inverse helpers: axis targets that put a head point onto a table point (the point's home world position minus the target)
    def _to(self, site_home, p):
        return {'X': p[0] - site_home[0], 'Y': site_home[1] - p[1], 'Z': p[2] - site_home[2]}
    def camera_over(self, x, y, z_surface):
        """axes that put the camera focus plane on the table point (x, y, z_surface)"""
        c = MAN['camera']; return self._to([c['axis_xy'][0], c['axis_xy'][1], c['lens_front_z'] - c['wd']], (x, y, z_surface))
    def probe_at(self, x, y, z):
        """axes that put the probe ball centre (probe extended) on the table point (x, y, z)"""
        b = MAN['probe_ball']['centre']; return self._to([b[0], b[1], b[2] - PROBE_STROKE], (x, y, z))
    def tool_at(self, x, y, z):
        return self._to(MAN['tool_tip'], (x, y, z))

    def _contacts(self):
        out = []
        for i in range(self.d.ncon):
            c = self.d.contact[i]
            a, b = (c.geom1, c.geom2) if c.geom1 in self.head_side else (c.geom2, c.geom1)
            out.append((a, b, c.dist * 1000.0, c.pos * 1000.0))
        return out
    def _name(self, g):
        return mujoco.mj_id2name(self.m, mujoco.mjtObj.mjOBJ_GEOM, g)

    # ---------------------------------------------------------------- steps
    def _check_limits(self, tgt):
        bad = {k: v for k, v in tgt.items() if not (RANGE[k][0] - 1e-6 <= v <= RANGE[k][1] + 1e-6)}
        return bad

    def _sweep(self, tgt, stop_on_ball=False):
        """move in axis space to tgt in STEP increments; returns (status, info)"""
        start = dict(self.axes); n = max(1, int(math.ceil(max(abs(tgt.get(k, start[k]) - start[k]) for k in tgt) / STEP)))
        last, near = dict(start), None
        for i in range(1, n + 1):
            f = i / n; pose = {k: start[k] + (tgt[k] - start[k]) * f for k in tgt}
            self._set(pose)
            hit = [(a, b, dist, pos) for a, b, dist, pos in self._contacts() if dist < 0]
            for a, b, dist, pos in self._contacts():                # clearance warnings: not for the probe tip (it works close to the part)
                if dist >= 0 and a not in self.trig and (near is None or dist < near[2]): near = (a, b, dist, pos)
            if not hit: last = dict(self.axes); continue
            ball = [h for h in hit if h[0] in self.trig]
            crash = [h for h in hit if h[0] not in self.trig]
            if crash or not stop_on_ball:
                self._set(last)
                h = (crash or ball)[0]
                return 'crash', {'parts': [self._name(h[0]), self._name(h[1])], 'at_table': [round(v, 2) for v in self._table(h[3])],
                                 'stopped_at': {k: round(v, 3) for k, v in last.items()}}
            lo, hi = dict(last), dict(self.axes)                   # probe touch: bisect to 1 um
            for _ in range(40):
                mid = {k: (lo[k] + hi[k]) / 2 for k in tgt}; self._set(mid)
                if any(a in self.trig and dist < 0 for a, b, dist, pos in self._contacts()): hi = mid
                else: lo = mid
                if max(abs(hi[k] - lo[k]) for k in tgt) < 0.001: break
            self._set(hi)
            b = ball[0]
            return 'triggered', {'touched': self._name(b[1]), 'axes': {k: round(v, 3) for k, v in self.axes.items()},
                                 'ball_centre': [round(v, 3) for v in self._table(self._site('probe_ball'))],
                                 'contact': [round(v, 3) for v in self._table(b[3])]}
        res = {'reached': {k: round(v, 3) for k, v in self.axes.items()}}
        if near is not None and near[2] < 0.5:
            res['warning'] = 'clearance %.2f mm between %s and %s' % (near[2], self._name(near[0]), self._name(near[1]))
        return 'ok', res

    def capture(self, name, out_dir):
        h, w = self.image_size
        if self._renderer is None: self._renderer = mujoco.Renderer(self.m, h, w)
        mujoco.mj_forward(self.m, self.d)
        opt = mujoco.MjvOption(); opt.sitegroup[:] = 0                # no sites in the camera image
        self._renderer.update_scene(self.d, 'cam', scene_option=opt)
        self._renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False   # coaxial light: no cast shadows in the camera image
        img = self._renderer.render()
        os.makedirs(out_dir, exist_ok=True); path = os.path.join(out_dir, name + '.png')
        from PIL import Image; Image.fromarray(img).save(path)
        c = MAN['camera']; cam = self.d.cam('cam')                 # focus over a 7 x 7 grid of the field: first surface below each point
        grp = np.array([1, 0, 0, 1, 0, 0], dtype=np.uint8); focus = c['wd'] - 3.0; fw, fh = c['fov'][1] * w / h, c['fov'][1]
        hits = []
        for u in np.linspace(-0.45, 0.45, 7):
            for v in np.linspace(-0.45, 0.45, 7):
                gid = np.array([-1], dtype=np.int32); p0 = cam.xpos + np.array([u * fw, v * fh, 0]) / 1000.0
                dist = mujoco.mj_ray(self.m, self.d, p0, np.array([0, 0, -1.0]), grp, 1, self.m.body('head').id, gid)
                if gid[0] >= 0: hits.append((self._name(gid[0]), dist * 1000.0 - focus))
        surf = {}
        for nme, err in hits: surf.setdefault(nme, []).append(err)
        info = {'image': os.path.relpath(path, ROOT), 'mm_per_px': round(fh / h, 5), 'field_mm': [round(fw, 2), fh],
                'centre_table': [round(v, 3) for v in self._table(self._site('cam_focus'))[:2]],
                'surfaces': {k: {'share': round(len(v) / 49, 2), 'focus_error_mm': round(float(np.median(v)), 2),
                                 'in_focus': bool(abs(np.median(v)) <= c['dof'] / 2)} for k, v in surf.items()}}
        return info

    def run(self, plan, out_dir=None, stop_on_error=True):
        out_dir = out_dir or os.path.join(ROOT, 'output', 'v14', 'mujoco', 'runs', 'latest')
        rep, t = [], 0.0
        for k, s in enumerate(plan, 1):
            op = s['op']; r = {'step': k, 'op': op}
            if op in ('move', 'probe_move'):
                tgt = {a: float(s[a]) for a in ('X', 'Y', 'Z') if a in s}
                bad = self._check_limits(tgt)
                if bad: r.update(status='out_of_travel', limits=bad)
                elif op == 'probe_move' and self.axes['P'] < PROBE_STROKE - 1e-6: r.update(status='error', reason='probe is not down')
                else:
                    L = math.sqrt(sum((tgt[a] - self.axes[a]) ** 2 for a in tgt))
                    st, info = self._sweep(tgt, stop_on_ball=(op == 'probe_move'))
                    if op == 'probe_move' and st == 'ok': st, info = 'no_trigger', {'reached': info['reached']}
                    t += L / s.get('feed', RAPID if op == 'move' else 300.0) * 60.0
                    r.update(status=st, **info)
            elif op == 'probe':
                st, info = self._sweep({'P': PROBE_STROKE if s['state'] == 'down' else 0.0}); t += 0.5
                r.update(status=st, **info)
            elif op == 'cover':
                st, info = self._sweep({'C': 30.0 if s['state'] == 'open' else 0.0}); t += 0.5
                r.update(status=st, **info)
            elif op == 'capture':
                r.update(status='ok', **self.capture(s.get('name', 'img%02d' % k), out_dir)); t += 0.2
            else:
                r.update(status='error', reason='unknown op')
            rep.append(r)
            if stop_on_error and r['status'] in ('crash', 'out_of_travel', 'error', 'no_trigger'): break
        ok = all(r['status'] in ('ok', 'triggered') for r in rep) and len(rep) == len(plan)
        return {'ok': ok, 'estimated_time_s': round(t, 1), 'workpieces': self.workpieces, 'steps': rep, 'final': self.where()}
