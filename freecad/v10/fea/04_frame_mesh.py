# -*- coding: utf-8 -*-
"""v10 frame FEA, step 4 (freecadcmd): X base plate t20 (steel) + both HFS8-80160-472 columns (MISUMI profile,
6063-T5 aluminium) + column foot plates t18 (steel), bonded at their contact faces (conformal mesh via gmsh
BooleanFragments).  The foot undersides sit on the datum plate (fixed).
Out: output/v10/fea/frame/frame_mesh.inp (C3D10, ELSETs PLATE / COLUMN / FOOT), frame_bodies.json
Run:  freecadcmd freecad/v10/fea/04_frame_mesh.py      (GMSH = path to gmsh, default the FreeCAD 1.1 bundle)"""
import os, json, subprocess
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
WORK = os.path.join(ROOT, 'output', 'v10', 'fea', os.environ.get('FRAME_DIR', 'frame')); os.makedirs(WORK, exist_ok=True)
GMSH = os.environ.get('GMSH', r'C:\Program Files\FreeCAD 1.1\bin\gmsh.exe')
CLMAX, CLMIN = float(os.environ.get('CLMAX', 6)), float(os.environ.get('CLMIN', 2))
doc = App.openDocument(os.path.join(ROOT, 'output', 'v10', 'CNC_v10.FCStd'))
BODIES = [('PLATE', 'X_base_plate'), ('COLUMN', 'Gantry_column_L'), ('COLUMN', 'Gantry_column_R'),
          ('FOOT', 'Column_foot_L'), ('FOOT', 'Column_foot_R')]
info, files = [], []
DEFEAT_R = float(os.environ.get('DEFEAT_R', 0))   # remove cylindrical fillet faces with radius <= DEFEAT_R on the columns
for grp, lab in BODIES:
    s = doc.getObjectsByLabel(lab)[0].Shape
    if grp == 'COLUMN' and os.environ.get('COLUMN_MODE') == 'box':
        # equivalent rectangular tube, same outline 80x160, wall thicknesses fitted so Ixx and Iyy equal the MISUMI
        # HFS8-80160 section (Ixx 1.005e7, Iyy 2.965e6 mm4; measured from the vendor STEP at z=300)
        import Part
        from FreeCAD import Vector as V
        bb = s.BoundBox; TX, TY = 5.787, 7.677
        s = Part.makeBox(bb.XLength, bb.YLength, bb.ZLength, V(bb.XMin, bb.YMin, bb.ZMin)).cut(
            Part.makeBox(bb.XLength - 2 * TX, bb.YLength - 2 * TY, bb.ZLength + 2, V(bb.XMin + TX, bb.YMin + TY, bb.ZMin - 1)))
    if grp == 'COLUMN' and DEFEAT_R > 0:
        small = [f for f in s.Faces if 'Cylinder' in f.Surface.TypeId and f.Surface.Radius <= DEFEAT_R + 0.01]
        s = s.defeaturing(small)          # r <= 2: section area -0.08 %, Ixx -0.21 %, Iyy -0.13 %
    f = os.path.join(WORK, lab + '.step'); s.exportStep(f); files.append(f)
    b = s.BoundBox
    info.append({'group': grp, 'label': lab, 'bbox': [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax], 'volume': s.Volume})
geo = ['SetFactory("OpenCASCADE");', 'Geometry.Tolerance = 1e-4;', 'Geometry.OCCFixSmallEdges = 1;']
for f in files:
    geo.append('ShapeFromFile("%s");' % f.replace('\\', '/'))
geo.append('BooleanFragments{ Volume{:}; Delete; }{}')
e = 0.2
for g in ('PLATE', 'COLUMN', 'FOOT'):
    parts = []
    for k, it in enumerate(i for i in info if i['group'] == g):
        b = it['bbox']
        geo.append('v_%s_%d() = Volume In BoundingBox{%g,%g,%g,%g,%g,%g};' % (g, k, b[0]-e, b[1]-e, b[2]-e, b[3]+e, b[4]+e, b[5]+e))
        parts.append('v_%s_%d()' % (g, k))
    geo.append('Physical Volume("%s") = {%s};' % (g, ', '.join(parts)))
geo += ['Mesh.CharacteristicLengthMax = %g;' % CLMAX, 'Mesh.CharacteristicLengthMin = %g;' % CLMIN,
        'Mesh.ElementOrder = 2;', 'Mesh.SecondOrderLinear = 1;', 'Mesh.Algorithm3D = %s;' % os.environ.get('ALGO3D', '10'), 'Mesh.SaveAll = 0;', 'Mesh 3;',
        'Save "%s";' % os.path.join(WORK, 'frame_mesh.inp').replace('\\', '/')]
gp = os.path.join(WORK, 'frame.geo'); open(gp, 'w').write('\n'.join(geo) + '\n')
r = subprocess.run([GMSH, gp, '-0', '-nt', '4'], capture_output=True, text=True)
open(os.path.join(WORK, 'gmsh.log'), 'w').write(r.stdout[-20000:] + r.stderr[-5000:])
json.dump({'bodies': info, 'clmax': CLMAX, 'clmin': CLMIN, 'defeature_r': DEFEAT_R, 'column_mode': os.environ.get('COLUMN_MODE', 'profile'), 'column_area_scale': (3902.1 / 2903.0) if os.environ.get('COLUMN_MODE') == 'box' else 1.0}, open(os.path.join(WORK, 'frame_bodies.json'), 'w'), indent=1)
