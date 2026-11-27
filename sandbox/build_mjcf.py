# -*- coding: utf-8 -*-
"""Build the MuJoCo model of the v14 machine from output/v14/mujoco/manifest.json (written by freecad/v14/26_export_mujoco_v14.py).
Kinematic sandbox for planning measuring moves: slide joints X / Y / Z, probe slide P (60 down), prism cover C (30 toward +Y).
Collision classes: tool-head side (contype 1) only meets obstacles (conaffinity 1): table top, prism station, workpieces.
Run:  python3 sandbox/build_mjcf.py      Out: output/v14/mujoco/cnc_v14.xml"""
import os, json
ROOT = os.environ.get('CNC_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'output', 'v14', 'mujoco')
M = json.load(open(os.path.join(OUT, 'manifest.json'), encoding='utf-8'))
mm = lambda v: ' '.join('%.6g' % (x / 1000.0) for x in v)
HEAD_MARGIN = 0.5                                              # mm: head-side contacts are reported from this distance on (clearance warnings)

asset, bodies = [], {b: [] for b in ('world', 'table', 'carriage', 'head', 'probe', 'cover')}
for i, v in enumerate(M['visuals']):
    asset.append('<mesh name="%s" file="%s" scale=".001 .001 .001"/>' % (v['mesh'][:-4], v['mesh']))
    asset.append('<material name="m%d" rgba="%s"/>' % (i, ' '.join('%.3g' % c for c in v['rgba'])))
    bodies['world' if v['body'] == 'base' else v['body']].append(
        '<geom name="vis_%s" type="mesh" mesh="%s" material="m%d" contype="0" conaffinity="0" group="1"/>' % (v['mesh'][2:-4], v['mesh'][:-4], i))
for c in M['colliders']:
    asset.append('<mesh name="%s" file="%s" scale=".001 .001 .001"/>' % (c['mesh'][:-4], c['mesh']))
    ct, ca = (1, 0) if c['side'] == 'head' else (0, 1)
    bodies['world' if c['body'] == 'base' else c['body']].append(
        '<geom name="%s" type="mesh" mesh="%s" contype="%d" conaffinity="%d" group="3" rgba="1 0 0 .3" margin="%g"/>'
        % (c['name'], c['mesh'][:-4], ct, ca, HEAD_MARGIN / 1000.0 if ct else 0))
t = M['table_top']                                             # table top: exact box (T-slots ignored)
bodies['table'].append('<geom name="Work_table_top" type="box" pos="%s" size="%s" contype="0" conaffinity="1" group="3" rgba="1 0 0 .3"/>'
                       % (mm([(t['x'][0] + t['x'][1]) / 2, (t['y'][0] + t['y'][1]) / 2, (t['z'][0] + t['z'][1]) / 2]),
                          mm([(t['x'][1] - t['x'][0]) / 2, (t['y'][1] - t['y'][0]) / 2, (t['z'][1] - t['z'][0]) / 2])))
pb = M['probe_ball']
bodies['probe'].append('<geom name="Probe_ball" type="sphere" pos="%s" size="%g" contype="1" conaffinity="0" group="0" rgba="0.9 0.1 0.1 1" margin="%g"/>'
                       % (mm(pb['centre']), pb['radius'] / 1000.0, HEAD_MARGIN / 1000.0))
bodies['probe'].append('<geom name="Probe_stylus" type="capsule" fromto="%s %s" size="%g" contype="1" conaffinity="0" group="0" rgba=".85 .85 .85 1" margin="%g"/>'
                       % (mm([pb['centre'][0], pb['centre'][1], pb['centre'][2] + 1.5]), mm([pb['centre'][0], pb['centre'][1], pb['stylus_top_z']]),
                          pb['stylus_radius'] / 1000.0, HEAD_MARGIN / 1000.0))
bodies['probe'].append('<site name="probe_ball" pos="%s" size=".001" rgba="0 0 0 0" group="5"/>' % mm(pb['centre']))
bodies['head'].append('<site name="tool_tip" pos="%s" size=".001" rgba="0 0 0 0" group="5"/>' % mm(M['tool_tip']))
cam = M['camera']; cz = cam['lens_front_z'] - 3.0                # camera point 3 below the lens front (clear of the air ring)
bodies['head'].append('<camera name="cam" pos="%s" xyaxes="1 0 0 0 1 0" projection="orthographic" fovy="%g"/>'
                      % (mm([cam['axis_xy'][0], cam['axis_xy'][1], cz]), cam['fov'][1] / 1000.0))
bodies['head'].append('<light name="cam_light" pos="%s" dir="0 0 -1" diffuse=".45 .45 .45" specular="0 0 0" cutoff="25" castshadow="false"/>'
                      % mm([cam['axis_xy'][0], cam['axis_xy'][1], cz]))
bodies['head'].append('<site name="cam_focus" pos="%s" size=".001" rgba="0 0 0 0" group="5"/>' % mm([cam['axis_xy'][0], cam['axis_xy'][1], cam['lens_front_z'] - cam['wd']]))
J = M['joints']
def joint(name):
    j = J[name]; return '<joint name="%s" type="slide" axis="%s" range="%s" limited="true" damping="50"/>' % (
        name, ' '.join(str(a) for a in j['axis']), mm(j['range']))
INERT = '<inertial pos="0 0 0" mass="5" diaginertia=".05 .05 .05"/>'
def body(name, inner):
    return '<body name="%s">%s%s\n%s\n%s</body>' % (name, INERT, joint({'table': 'Y', 'carriage': 'X', 'head': 'Z', 'probe': 'P', 'cover': 'C'}[name]),
                                                   '\n'.join(bodies[name]), inner)
world = '\n'.join(bodies['world'])
tree = body('table', body('cover', '')) + '\n' + body('carriage', body('head', body('probe', '')))
act = '\n'.join('<position name="a%s" joint="%s" kp="20000" ctrlrange="%s" ctrllimited="true"/>' % (n, n, mm(J[n]['range'])) for n in ('X', 'Y', 'Z', 'P', 'C'))
sens = '\n'.join('<jointpos name="pos_%s" joint="%s"/>' % (n, n) for n in ('X', 'Y', 'Z', 'P', 'C'))
xml = '''<mujoco model="cnc_v14_sandbox">
<!-- generated by sandbox/build_mjcf.py from output/v14/mujoco/manifest.json; machine coordinates in metres, home = all joints 0 -->
<compiler meshdir="meshes" angle="degree" boundmass=".01" boundinertia=".0001"/>
<option timestep="0.002" gravity="0 0 -9.81"/>
<visual><global offwidth="2448" offheight="2048"/><quality shadowsize="2048"/><headlight ambient=".3 .3 .3" diffuse=".35 .35 .35"/></visual>
<asset>
%s
</asset>
<worldbody>
<light pos="0.8 -1.5 2.0" dir="-0.3 0.6 -1" diffuse=".6 .6 .6"/>
<camera name="overview" pos="1.9 -2.2 1.4" xyaxes="0.76 0.65 0 -0.3 0.35 0.89"/>
%s
%s
</worldbody>
<actuator>
%s
</actuator>
<sensor>
%s
</sensor>
</mujoco>
''' % ('\n'.join(asset), world, tree, act, sens)
open(os.path.join(OUT, 'cnc_v14.xml'), 'w', encoding='utf-8').write(xml)
print('written', os.path.join(OUT, 'cnc_v14.xml'))
