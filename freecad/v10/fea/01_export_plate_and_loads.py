# -*- coding: utf-8 -*-
"""v10 X base plate FEA, step 1 (FreeCAD; same model as freecad/v4/fea, v10 geometry): export the X base plate solid to STEP and compute the moving X head
(everything that rides on the X rails) mass and centre of gravity from part volumes x density.
Run:  freecadcmd freecad/v10/fea/01_export_plate_and_loads.py
Out:  output/v10/fea/x_base_plate.step, head_mass.json, mesh.inp (gmsh C3D10, -clmax 6 -clmin 2 as freecad/v4/fea/04_variants.py)"""
import os, json
import FreeCAD as App
import Part

ROOT = os.environ.get('CNC_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, 'output', 'v10', 'fea')
os.makedirs(OUT, exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, 'output', 'v10', 'CNC_v10.FCStd'))
O = lambda l: doc.getObjectsByLabel(l)[0]

plate = O('X_base_plate').Shape.copy()
plate.exportStep(os.path.join(OUT, 'x_base_plate.step'))

# parts carried by the X carriage (move with X): density g/cm3 or catalogue mass kg
STEEL, AL = 7.85, 2.70
HEAD = {
    'X_carriage_plate': STEEL, 'X_block_11': STEEL, 'X_block_12': STEEL, 'X_block_21': STEEL, 'X_block_22': STEEL,
    'X_ball_nut': STEEL, 'X_nut_bracket': STEEL,
    'Z_rail_L': STEEL, 'Z_rail_R': STEEL, 'Z_block_L1': STEEL, 'Z_block_L2': STEEL, 'Z_block_R1': STEEL,
    'Z_block_R2': STEEL, 'Z_spacer_L': STEEL, 'Z_spacer_R': STEEL, 'Z_slide_plate': STEEL, 'Z_ballscrew': STEEL,
    'Z_ball_nut': STEEL, 'Z_nut_housing': STEEL, 'Z_support_fixed': STEEL, 'Z_coupling': AL, 'Z_motor_plate': STEEL,
    'Spindle_clamp': AL, 'Spindle_nose': STEEL, 'ER11_nut': STEEL, 'Tool_D5': 14.5,
}
CATALOGUE_KG = {'Z_motor': 1.8,          # HG-KR43B with brake (Mitsubishi catalogue ~1.8 kg)
                'Spindle_body': 2.2,     # 0.8 kW air-cooled D65 spindle incl. fan cover (typ. 2.0-2.5 kg)
                'Spindle_fan_cover': 0.0, 'Spindle_plug': 0.0}
rows, m_tot, mx, my, mz = [], 0.0, 0.0, 0.0, 0.0
for n, rho in HEAD.items():
    s = O(n).Shape
    m = s.Volume * rho * 1e-6               # mm3 * g/cm3 -> kg
    c = s.CenterOfMass if hasattr(s, 'CenterOfMass') else s.BoundBox.Center
    rows.append((n, round(m, 3), round(c.x, 1), round(c.y, 1), round(c.z, 1)))
    m_tot += m; mx += m * c.x; my += m * c.y; mz += m * c.z
for n, m in CATALOGUE_KG.items():
    if m <= 0:
        continue
    c = O(n).Shape.BoundBox.Center
    rows.append((n, m, round(c.x, 1), round(c.y, 1), round(c.z, 1)))
    m_tot += m; mx += m * c.x; my += m * c.y; mz += m * c.z
cg = (mx / m_tot, my / m_tot, mz / m_tot)
pb = plate.BoundBox
res = {'head_mass_kg': round(m_tot, 2), 'head_cg_mm': [round(v, 1) for v in cg], 'parts': rows,
       'plate_bbox': [pb.XMin, pb.XMax, pb.YMin, pb.YMax, pb.ZMin, pb.ZMax], 'plate_volume_mm3': plate.Volume,
       'plate_mass_kg': round(plate.Volume * STEEL * 1e-6, 2),
       'x_rails_z': [round((O('X_rail_1').Shape.BoundBox.ZMin + O('X_rail_1').Shape.BoundBox.ZMax) / 2, 1),
                     round((O('X_rail_2').Shape.BoundBox.ZMin + O('X_rail_2').Shape.BoundBox.ZMax) / 2, 1)],
       'x_rail_width': O('X_rail_1').Shape.BoundBox.ZLength,
       'x_blocks_x': [round(O(n).Shape.BoundBox.XMin, 1) for n in ('X_block_11', 'X_block_12')] +
                     [round(O(n).Shape.BoundBox.XMax, 1) for n in ('X_block_11', 'X_block_12')],
       'columns': [[O(n).Shape.BoundBox.XMin, O(n).Shape.BoundBox.XMax, O(n).Shape.BoundBox.YMin,
                    O(n).Shape.BoundBox.YMax, O(n).Shape.BoundBox.ZMin, O(n).Shape.BoundBox.ZMax]
                   for n in ('Gantry_column_L', 'Gantry_column_R')]}
json.dump(res, open(os.path.join(OUT, 'head_mass.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# mesh (same gmsh settings as freecad/v4/fea/04_variants.py)
import subprocess
GMSH = os.environ.get('GMSH', r'C:\Program Files\FreeCAD 1.1\bin\gmsh.exe')
subprocess.run([GMSH, os.path.join(OUT, 'x_base_plate.step'), '-3', '-order', '2', '-clmax', '6', '-clmin', '2',
                '-format', 'inp', '-o', os.path.join(OUT, 'mesh.inp')], capture_output=True, text=True, check=True)
