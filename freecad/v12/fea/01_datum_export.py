# -*- coding: utf-8 -*-
"""v12 Y-axis base (datum plate) FEA, step 1 (FreeCAD): export the datum plate, compute the loads it carries and mesh it.
  gantry   : every part of the machine that stands on the two feet (alignment kit removed), mass + CG
  table    : everything that rides on the Y blocks (table, Y rails, Y screw, Y motor ...) + a 3 kg work piece, mass + CG
  footprints of the feet, the 4 Y blocks, the Y nut bracket; the 4 base risers (supports)
Densities: steel 7.85, aluminium 2.70 g/cm3; motors, spindle, drives and panel from catalogue masses.
Run:  freecadcmd freecad/v12/fea/01_datum_export.py      Out: output/v12/fea/datum_plate.step, datum_loads.json, datum_mesh.inp"""
import os, json, subprocess
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v12', 'fea'); os.makedirs(OUT, exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v12', 'CNC_v12_base.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]
plate = O('Datum_base_plate').Shape.copy(); plate.exportStep(os.path.join(OUT, 'datum_plate.step'))

STEEL, AL = 7.85, 2.70
AL_PARTS = ('Work_table', 'Spindle_clamp', 'Gantry_column_', 'Y_coupling', 'X_coupling', 'Z_coupling')
CAT = {'X_motor': 1.3, 'Y_motor': 1.3, 'Z_motor': 1.8, 'Spindle_body': 2.2, 'Spindle_fan_cover': 0, 'Spindle_plug': 0,
       'Servo_amp_X': 0.8, 'Servo_amp_Y': 0.8, 'Servo_amp_Z': 0.8, 'Electrical_panel': 3.0}
ygrp = {o.Label for g in doc.Objects if g.TypeId == 'App::DocumentObjectGroup' and g.Label == '02 Y-axis' for o in g.Group}
def kind(o):
    n = o.Label
    if n == 'Datum_base_plate' or getattr(o, 'Adj', '') == 'base' or getattr(o, 'Kit', ''): return None
    if getattr(o, 'Motion', '') == 'y' or n in ygrp and not n.startswith(('Y_block', 'Y_ball_nut', 'Y_nut_bracket')): return 'table'
    if n.startswith(('Y_block', 'Y_ball_nut', 'Y_nut_bracket', 'Y_block_bolt', 'Y_block_ref_pin', 'Yaw_')): return None   # sit on the plate, small
    return 'gantry'
acc = {'gantry': [0, 0, 0, 0], 'table': [0, 0, 0, 0]}
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    k = kind(o)
    if not k: continue
    s = o.Shape
    m = CAT[o.Label] if o.Label in CAT else s.Volume * (AL if o.Label.startswith(AL_PARTS) else STEEL) * 1e-6
    if o.Label in CAT: c = s.BoundBox.Center
    elif hasattr(s, 'CenterOfMass'): c = s.CenterOfMass
    else:                                                    # compounds (vendor STEP): volume-weighted solids
        vs = [(so.Volume, so.CenterOfMass) for so in s.Solids]; tv = sum(v for v, _ in vs)
        c = App.Vector(sum(v * q.x for v, q in vs) / tv, sum(v * q.y for v, q in vs) / tv, sum(v * q.z for v, q in vs) / tv)
    a = acc[k]; a[0] += m; a[1] += m * c.x; a[2] += m * c.y; a[3] += m * c.z
wt = O('Work_table').Shape.BoundBox                         # 3 kg work piece at the table centre
a = acc['table']; a[0] += 3; a[1] += 0; a[2] += 3 * (wt.YMin + wt.YMax) / 2; a[3] += 3 * 125
res = {k: {'mass_kg': round(v[0], 2), 'cg_mm': [round(v[1] / v[0], 1), round(v[2] / v[0], 1), round(v[3] / v[0], 1)]} for k, v in acc.items()}
bb = lambda n: [round(x, 2) for x in (O(n).Shape.BoundBox.XMin, O(n).Shape.BoundBox.XMax, O(n).Shape.BoundBox.YMin, O(n).Shape.BoundBox.YMax)]
res.update({'plate_bbox': [plate.BoundBox.XMin, plate.BoundBox.XMax, plate.BoundBox.YMin, plate.BoundBox.YMax, plate.BoundBox.ZMin, plate.BoundBox.ZMax],
            'plate_mass_kg': round(plate.Volume * STEEL * 1e-6, 2),
            'feet': {'L': bb('Column_foot_L'), 'R': bb('Column_foot_R')},
            'blocks': {n: bb(n) for n in ('Y_block_L1', 'Y_block_R1', 'Y_block_L2', 'Y_block_R2')},
            'nut_bracket': bb('Y_nut_bracket'),
            'risers': [[(O(n).Shape.BoundBox.XMin + O(n).Shape.BoundBox.XMax) / 2, (O(n).Shape.BoundBox.YMin + O(n).Shape.BoundBox.YMax) / 2] for n in ('Base_riser_1', 'Base_riser_2', 'Base_riser_3', 'Base_riser_4')],
            'tool_tip': [0.0, round((O('Tool_D5').Shape.BoundBox.YMin + O('Tool_D5').Shape.BoundBox.YMax) / 2, 1), round(O('Tool_D5').Shape.BoundBox.ZMin, 1)]})
json.dump(res, open(os.path.join(OUT, 'datum_loads.json'), 'w', encoding='utf-8'), indent=1)
print(json.dumps({k: res[k] for k in ('gantry', 'table', 'plate_mass_kg')}))
GMSH = os.environ.get('GMSH', r'C:\Program Files\FreeCAD 1.1\bin\gmsh.exe')
r = subprocess.run([GMSH, os.path.join(OUT, 'datum_plate.step'), '-3', '-order', '2', '-setnumber', 'Mesh.SecondOrderLinear', '1', '-clmax', '8', '-clmin', '2', '-format', 'inp',
                    '-o', os.path.join(OUT, 'datum_mesh.inp')], capture_output=True, text=True)
print('gmsh rc', r.returncode, r.stdout[-300:].replace('\n', ' '))
