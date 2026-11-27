# -*- coding: utf-8 -*-
"""Demo: a block on the table, an AI-style measuring plan (camera shots at two corners, probe the -X face, the -Y face and the top),
then a second plan with a deliberate mistake (moving down onto the block with the probe out) to show crash reporting.
Run:  MUJOCO_GL=egl python3 sandbox/demo_plan.py      Out: output/v14/mujoco/runs/demo_ok/, demo_crash/ (report.json + images)"""
import os, json, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cnc_sandbox import CNCSandbox, ROOT

L, W, H, YAW, C = 120.0, 80.0, 25.0, 5.0, (20.0, 10.0)        # block size, rotation and centre on the table
TOP = 110.0 + H
def corner(sx, sy):                                            # block corner in table coordinates
    a = math.radians(YAW); x, y = sx * L / 2, sy * W / 2
    return C[0] + x * math.cos(a) - y * math.sin(a), C[1] + x * math.sin(a) + y * math.cos(a)

sb = CNCSandbox()
sb.add_box('block', (L, W, H), C, YAW)
safe = {'Z': 45.0}
cx, cy = corner(-1, -1); ex, ey = corner(1, 1)
cam1, cam2 = sb.camera_over(cx, cy, TOP), sb.camera_over(ex, ey, TOP)
# probe the -X face at the block's y centre line, 10 below the top; start 10 outside the face (face nominal x from the corner geometry)
a_ = math.radians(YAW)
fx = C[0] - L / 2 * math.cos(a_) - (L / 2 * math.sin(a_)) * math.tan(a_)   # -X face at the probing line y = C[1] (exact, block turned YAW)
fx0 = fx; p_x0 = sb.probe_at(fx - 10, C[1], TOP - 10); p_x1 = sb.probe_at(fx + 5, C[1], TOP - 10)
fy = C[1] - W / 2 * math.cos(a_) - (W / 2 * math.sin(a_)) * math.tan(a_)   # -Y face at the probing line x = C[0]
fy0 = fy; p_y0 = sb.probe_at(C[0], fy - 10, TOP - 10); p_y1 = sb.probe_at(C[0], fy + 5, TOP - 10)
p_t0 = sb.probe_at(C[0], C[1], TOP + 10); p_t1 = sb.probe_at(C[0], C[1], TOP - 5)
plan = [
    {'op': 'move', **safe},
    {'op': 'move', 'X': cam1['X'], 'Y': cam1['Y']}, {'op': 'move', 'Z': cam1['Z']}, {'op': 'capture', 'name': 'corner_minus'},
    {'op': 'move', **safe}, {'op': 'move', 'X': cam2['X'], 'Y': cam2['Y']}, {'op': 'move', 'Z': cam2['Z']}, {'op': 'capture', 'name': 'corner_plus'},
    {'op': 'move', **safe}, {'op': 'probe', 'state': 'down'},
    {'op': 'move', 'X': p_x0['X'], 'Y': p_x0['Y']}, {'op': 'move', 'Z': p_x0['Z']}, {'op': 'probe_move', 'X': p_x1['X'], 'feed': 200},
    {'op': 'move', 'X': p_x0['X']}, {'op': 'move', **safe},
    {'op': 'move', 'X': p_y0['X'], 'Y': p_y0['Y']}, {'op': 'move', 'Z': p_y0['Z']}, {'op': 'probe_move', 'Y': p_y1['Y'], 'feed': 200},
    {'op': 'move', 'Y': p_y0['Y']}, {'op': 'move', **safe},
    {'op': 'move', 'X': p_t0['X'], 'Y': p_t0['Y']}, {'op': 'move', 'Z': p_t0['Z']}, {'op': 'probe_move', 'Z': p_t1['Z'], 'feed': 200},
    {'op': 'move', **safe}, {'op': 'probe', 'state': 'up'},
]
out = os.path.join(ROOT, 'output', 'v14', 'mujoco', 'runs', 'demo_ok')
rep = sb.run(plan, out); os.makedirs(out, exist_ok=True); json.dump({'plan': plan, 'report': rep}, open(os.path.join(out, 'report.json'), 'w'), indent=1)
print('plan ok:', rep['ok'], ' time %.1f s' % rep['estimated_time_s'])
for r in rep['steps']:
    extra = r.get('ball_centre') or r.get('surfaces') or r.get('warning') or r.get('parts') or ''
    print('  %2d %-10s %-10s %s' % (r['step'], r['op'], r['status'], extra))
# nominal vs measured
trig = [r for r in rep['steps'] if r['status'] == 'triggered']
if len(trig) == 3:
    print('  -X face: ball centre x %.3f -> face x %.3f (nominal %.3f)' % (trig[0]['ball_centre'][0], trig[0]['ball_centre'][0] + 1.0, fx))
    print('  -Y face: ball centre y %.3f -> face y %.3f (nominal %.3f)' % (trig[1]['ball_centre'][1], trig[1]['ball_centre'][1] + 1.0, fy))
    print('  top:     ball centre z %.3f -> top z %.3f (nominal %.1f)' % (trig[2]['ball_centre'][2], trig[2]['ball_centre'][2] - 1.0, TOP))

sb2 = CNCSandbox(); sb2.add_box('block', (L, W, H), C, YAW)
bad = [{'op': 'move', **safe}, {'op': 'probe', 'state': 'down'}, {'op': 'move', 'X': p_t0['X'], 'Y': p_t0['Y']}, {'op': 'move', 'Z': -40.0}]
out2 = os.path.join(ROOT, 'output', 'v14', 'mujoco', 'runs', 'demo_crash')
rep2 = sb2.run(bad, out2); os.makedirs(out2, exist_ok=True); json.dump({'plan': bad, 'report': rep2}, open(os.path.join(out2, 'report.json'), 'w'), indent=1)
print('crash plan ok:', rep2['ok'], '->', rep2['steps'][-1])

# overview pictures for people: the probing pose on the -X face and a close look at the tool head
import mujoco
from PIL import Image
sb3 = CNCSandbox(); sb3.add_box('block', (L, W, H), C, YAW)
sb3._set({'Z': p_x0['Z'], 'X': p_x0['X'], 'Y': p_x0['Y'], 'P': 60.0}); mujoco.mj_forward(sb3.m, sb3.d)
r = mujoco.Renderer(sb3.m, 720, 1100); cam = mujoco.MjvCamera()
for name, (look, dist_, az, el) in {'overview_probe': ((0.0, -0.05, 0.15), 1.1, 225, -25), 'closeup_probe': ((-0.03, -0.06, 0.13), 0.35, 215, -18)}.items():
    cam.lookat[:] = look; cam.distance = dist_; cam.azimuth = az; cam.elevation = el
    r.update_scene(sb3.d, cam); Image.fromarray(r.render()).save(os.path.join(out, name + '.png'))
