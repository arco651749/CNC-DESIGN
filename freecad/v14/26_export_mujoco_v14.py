# -*- coding: utf-8 -*-
"""v14 -> MuJoCo sandbox, step 1 (FreeCAD): meshes and a manifest for sandbox/build_mjcf.py.
The sandbox is for an AI to plan measuring moves (camera shots, probe touches) on a workpiece and have them checked before the real
machine runs them; it is not the design interference check (02 / 07 / 12 stay the reference for clearances).
Bodies: base (static), table (Y), carriage (X), head (Z, on the carriage), probe (MXH slide, on the head), cover (prism cover, on the table).
Visual meshes are merged per body and colour; colliders are the parts the AI can run into (tool-head front, probe, prism station, table),
one mesh each (MuJoCo uses their convex hulls), plus exact primitives for the table top and the probe ball.
Run:  freecadcmd freecad/v14/26_export_mujoco_v14.py      Out: output/v14/mujoco/meshes/*.stl, output/v14/mujoco/manifest.json"""
import os, re, json, struct
import FreeCAD as App, Part, Import, MeshPart
ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v14', 'mujoco'); MESH = os.path.join(OUT, 'meshes'); os.makedirs(MESH, exist_ok=True)
for f in os.listdir(MESH): os.remove(os.path.join(MESH, f))
doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))

PROBE_MOVE = ('Probe_body', 'Probe_holder', 'Probe_stem', 'Probe_slide_table', 'Probe_pinch_bolt', 'Probe_holder_bolt', 'Probe_stem_bolt')
def body_of(o):
    n = o.Label
    if n.startswith(PROBE_MOVE): return 'probe'
    if n == 'Mirror_cover': return 'cover'
    m = o.Motion if 'Motion' in o.PropertiesList and o.Motion else ''
    if not m:
        if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): m = 'y'
        elif n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): m = 'z'
        elif n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): m = 'x'
    return {'y': 'table', 'x': 'carriage', 'z': 'head'}.get(m, 'base')
# parts the AI's moves can hit (head side) and the things on the table they can hit (obstacles; the workpiece is added at run time)
HEAD_COLL = r'^(Spindle_(body|fan_cover|clamp|nose|plug)|ER11_nut|Tool_D5|Camera_(lens|air_ring|body|bracket|bracket_cap|light_guide)|Coolant_nozzle(_block)?_\d|' \
            r'Conduit_head_(bracket|end_fitting)|Probe_(body|holder|stem|slide_table|slide_body))$'
OBST_COLL = r'^(Tool_mirror|Mirror_(bracket|cover|cover_actuator|cover_fitting_\d|cover_tube_\d))$'
def colour(n, b):
    if n.startswith(('X_motor', 'Y_motor', 'Z_motor', 'Spindle_body', 'Camera_body', 'Probe_slide_body')): return [0.22, 0.24, 0.27, 1]
    if n.startswith('Tool'): return [0.85, 0.85, 0.88, 1]
    if n.startswith(('Conduit_', 'Feeder_')) and 'bracket' not in n and 'tab' not in n and 'plate' not in n: return [0.15, 0.16, 0.18, 1]
    if n.startswith('Guard_window'): return [0.75, 0.85, 0.92, 0.35]
    return {'table': [0.78, 0.62, 0.42, 1], 'carriage': [0.5, 0.64, 0.8, 1], 'head': [0.62, 0.72, 0.84, 1], 'probe': [0.9, 0.55, 0.2, 1],
            'cover': [0.7, 0.7, 0.72, 1]}.get(b, [0.68, 0.71, 0.75, 1])
def tess(sh, fine):
    if not fine and len(sh.Solids) > 1:                           # detailed vendor parts: drop their small solids (screws, pins, labels)
        big = [x for x in sh.Solids if x.Volume > 150]
        if big: sh = Part.makeCompound(big)
    b = sh.BoundBox; L = max(b.XLength, b.YLength, b.ZLength)
    m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.3 if fine else max(1.0, 0.008 * L), AngularDeflection=0.35 if fine else 0.7, Relative=False)
    return [(p.x, p.y, p.z) for p in m.Points], [tuple(f.PointIndices) for f in m.Facets]
def write_stl(path, groups):                                   # binary STL, mm (scaled to m in the MJCF)
    tri = []
    for pts, tris in groups:
        for a, b_, c in tris: tri.append((pts[a], pts[b_], pts[c]))
    with open(path, 'wb') as f:
        f.write(b'v14 cnc sandbox'.ljust(80, b' ')); f.write(struct.pack('<I', len(tri)))
        for a, b_, c in tri: f.write(struct.pack('<12fH', 0, 0, 0, *a, *b_, *c, 0))
    return len(tri)

vis, coll, ntri = {}, [], 0
SRC = [(o, 'm') for o in doc.Objects]
for d in ('column_box', 'base_cabinet'):                       # electrical boxes (electrical session), visual only
    f = os.path.join(ROOT, d, d + '.step')
    if os.path.exists(f):
        bd = App.newDocument(d); Import.insert(f, bd.Name); SRC += [(o, d) for o in bd.Objects]
for o, s_ in SRC:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    n = o.Label; sh = o.Shape
    if s_ == 'm' and n.startswith('Keepout'): continue
    b = body_of(o) if s_ == 'm' else 'base'
    if s_ == 'm' and re.search(HEAD_COLL + '|' + OBST_COLL, n):
        csh = sh
        if n == 'Probe_body':                                     # body + shank only: the stylus and ball are trigger geoms (build_mjcf)
            bb = sh.BoundBox; csh = sh.common(Part.makeBox(200, 200, 200, App.Vector(bb.XMin - 50, bb.YMin - 50, bb.ZMin + 24)))
        fn = 'c_%s.stl' % n; ntri += write_stl(os.path.join(MESH, fn), [tess(csh, True)])
        coll.append({'name': n, 'body': b, 'mesh': fn, 'side': 'head' if re.search(HEAD_COLL, n) else 'obstacle'})
    if sh.Volume < (40 if s_ == 'm' else 400) or re.search(r'(bolt|screw|_pin$|_pin_|washer|PullNut|standoff)', n, re.I): continue   # small hardware: not drawn
    rgba = colour(n, b) if s_ == 'm' else ([0.83, 0.85, 0.80, 1] if n.startswith(('L_plate', 'Cabinet', 'Box_')) else [0.25, 0.27, 0.3, 1])
    vis.setdefault((b, tuple(rgba)), []).append(tess(sh, False))
visuals = []
for k, ((b, rgba), groups) in enumerate(sorted(vis.items(), key=lambda kv: kv[0][0])):
    fn = 'v_%s_%02d.stl' % (b, k); ntri += write_stl(os.path.join(MESH, fn), groups)
    visuals.append({'body': b, 'mesh': fn, 'rgba': list(rgba)})
O = lambda l: doc.getObjectsByLabel(l)[0].Shape.BoundBox
wt, pb, tl, cl = O('Work_table'), O('Probe_body'), O('Tool_D5'), O('Camera_lens')
man = {
    'units': 'mm in this file and the meshes; the MJCF is in metres',
    'joints': {'Y': {'body': 'table', 'axis': [0, 1, 0], 'range': [-250.0, 150.0]}, 'X': {'body': 'carriage', 'axis': [1, 0, 0], 'range': [-182.5, 182.5]},
               'Z': {'body': 'head', 'axis': [0, 0, 1], 'range': [-50.0, 50.0]}, 'P': {'body': 'probe', 'axis': [0, 0, -1], 'range': [0.0, 60.0]},
               'C': {'body': 'cover', 'axis': [0, 1, 0], 'range': [0.0, 30.0]}},
    'parents': {'table': 'world', 'carriage': 'world', 'head': 'carriage', 'probe': 'head', 'cover': 'table'},
    'table_top': {'x': [wt.XMin, wt.XMax], 'y': [wt.YMin, wt.YMax], 'z': [wt.ZMin, wt.ZMax], 'work_area': [300, 300]},
    'probe_ball': {'centre': [-11.0, -73.0, pb.ZMin + 1.0], 'radius': 1.0, 'stylus_top_z': pb.ZMin + 26.0, 'stylus_radius': 1.0,
                   'note': 'ball D2 on a 26 stylus (probe catalog); home = probe retracted. Ball or stylus contact triggers the probe'},
    'tool_tip': [(tl.XMin + tl.XMax) / 2, (tl.YMin + tl.YMax) / 2, tl.ZMin],
    'camera': {'axis_xy': [-32.5, -20.0], 'lens_front_z': cl.ZMin, 'wd': 120.0, 'dof': 5.3, 'fov': [16.8, 14.0], 'pixels': [2448, 2048],
               'note': 'Moritex MML04-HR120D 0.4x telecentric + Basler daA2448-70uc: orthographic, image x = machine +X, image up = machine +Y'},
    'visuals': visuals, 'colliders': coll, 'triangles': ntri,
}
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
open(os.path.join(ROOT, 'output', 'v14', 'logs', 'v14_mujoco_export.txt'), 'w', encoding='utf-8').write(
    'mujoco export: %d visual meshes, %d colliders, %d triangles\n' % (len(visuals), len(coll), ntri) + '\n'.join('  %-28s %-8s %s' % (c['name'], c['body'], c['side']) for c in coll))
