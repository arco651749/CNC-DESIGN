# -*- coding: utf-8 -*-
"""v10 frame FEA, step 5 (python + numpy): CalculiX linear static of plate + columns + feet (mesh from step 4).
Same loads as 02_run_ccx.py (head weight + CG couple on the two X-rail strips of the plate front face, optional
100 N tool force), gravity on every body, foot undersides (z = 0, on the datum plate) fixed in x/y/z.
Materials: steel E 210000 MPa (plate, feet), aluminium 6063-T5 E 69000 MPa nu 0.33 rho 2.7e-9 (columns).
Solver: ccx iterative Cholesky (the direct solver needs more memory than 16 GB at ~2.3 M dof).
Run:  python freecad/v10/fea/05_frame_solve.py      Out: output/v10/fea/frame/results_frame.json (+ .npy for the page)"""
import os, re, json, subprocess
import numpy as np

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
FEA = os.path.join(ROOT, 'output', 'v10', 'fea'); WORK = os.path.join(FEA, os.environ.get('FRAME_DIR', 'frame'))
SOLVER = os.environ.get('SOLVER', 'ITERATIVE CHOLESKY')   # or SPOOLES (direct, multithreaded, more memory)
CCX = os.environ.get('CCX', r'C:\Program Files\FreeCAD 1.1\bin\ccx.exe')
H = json.load(open(os.path.join(FEA, 'head_mass.json'), encoding='utf-8'))
BODIES = json.load(open(os.path.join(WORK, 'frame_bodies.json')))
RHO_AL = 2.70e-9 * BODIES.get('column_area_scale', 1.0)   # equivalent-box columns keep the real profile mass
PLATE_ONLY = json.load(open(os.path.join(FEA, 'results.json'), encoding='utf-8'))

# ---------------- mesh
nodes, elems, sets, mode, cur = {}, {}, {}, None, None
for ln in open(os.path.join(WORK, 'frame_mesh.inp'), errors='ignore'):
    if ln.startswith('*'):
        u = ln.upper()
        if u.startswith('*NODE'): mode = 'N'
        elif u.startswith('*ELEMENT') and 'C3D10' in u: mode = 'E'
        elif u.startswith('*ELSET'): mode = 'S'; cur = re.search(r'ELSET=(\w+)', ln, re.I).group(1).upper(); sets[cur] = []
        else: mode = None
        continue
    v = ln.replace(',', ' ').split()
    if not v: continue
    if mode == 'N': nodes[int(v[0])] = (float(v[1]), float(v[2]), float(v[3]))
    elif mode == 'E': elems[int(v[0])] = [int(x) for x in v[1:]]
    elif mode == 'S': sets[cur] += [int(x) for x in v]
ids = np.array(sorted(nodes)); XYZ = np.array([nodes[i] for i in ids])
print('nodes', len(ids), 'C3D10', len(elems), {k: len(v) for k, v in sets.items()})

with open(os.path.join(WORK, 'mesh_include.inp'), 'w') as f:
    f.write('*NODE, NSET=NALL\n'); [f.write('%d,%.6f,%.6f,%.6f\n' % (i, *nodes[i])) for i in ids]
    for g in ('PLATE', 'COLUMN', 'FOOT'):
        f.write('*ELEMENT, TYPE=C3D10, ELSET=%s\n' % g)
        for e in sets[g]: f.write('%d,%s\n' % (e, ','.join(map(str, elems[e]))))

xmin, xmax, ymin, ymax, zmin, zmax = H['plate_bbox']; YF = ymin; tol = 0.05
plate_nodes = np.isin(ids, np.unique([n for e in sets['PLATE'] for n in elems[e]]))
front = plate_nodes & (np.abs(XYZ[:, 1] - YF) < tol)
fix = np.abs(XYZ[:, 2]) < tol
zr = H['x_rails_z']; hw = H['x_rail_width'] / 2
def rail_sets(xc):
    t = front & (np.abs(XYZ[:, 0] - xc) <= 100 + tol) & (np.abs(XYZ[:, 2] - zr[1]) <= hw + tol)
    b = front & (np.abs(XYZ[:, 0] - xc) <= 100 + tol) & (np.abs(XYZ[:, 2] - zr[0]) <= hw + tol)
    return t, b
W = H['head_mass_kg'] * 9.81; cg = H['head_cg_mm']; spacing = zr[1] - zr[0]; zmid = sum(zr) / 2
Fc = W * (YF - cg[1]) / spacing; TOOL_Z = 180.0
def rail_loads(tool_fy):
    f = {('top', 3): -W / 2, ('bot', 3): -W / 2, ('top', 2): -Fc, ('bot', 2): Fc}
    if tool_fy:
        c = tool_fy * (zmid - TOOL_Z) / spacing
        f[('top', 2)] += tool_fy / 2 - c; f[('bot', 2)] += tool_fy / 2 + c
    return f

def read_frd(path):
    disp, stress, cur = {}, {}, None
    for ln in open(path, errors='ignore'):
        if ln.startswith(' -4'):
            k = ln.split()[1]; cur = disp if k.startswith('DISP') else (stress if k.startswith('STRESS') else None)
        elif ln.startswith(' -1') and cur is not None:
            cur[int(ln[3:13])] = [float(ln[13 + 12 * j:25 + 12 * j]) for j in range((len(ln.rstrip()) - 13) // 12)]
        elif ln.startswith(' -3'): cur = None
    return disp, stress

CASES = {'A_weight': (0.0, 0.0), 'B_weight_plus_100N': (100.0, 0.0), 'C_weight_x+150': (0.0, 150.0)}
col_nodes = np.isin(ids, np.unique([n for e in sets['COLUMN'] for n in elems[e]]))
res = {'model': 'plate t20 steel + 2x HFS8-80160-472 (6063-T5; %s) + feet t18 steel, bonded; feet fixed' % ('equivalent tube 80x160, Ixx/Iyy = MISUMI profile' if BODIES.get('column_mode') == 'box' else 'MISUMI profile'), 'solver': SOLVER,
       'nodes': int(len(ids)), 'elements': len(elems), 'head_mass_kg': H['head_mass_kg'], 'cases': {}}
for name, (tfy, xc) in CASES.items():
    top, bot = rail_sets(xc)
    with open(os.path.join(WORK, name + '.inp'), 'w') as f:
        f.write('*INCLUDE, INPUT=mesh_include.inp\n')
        f.write('*NSET, NSET=NFIX\n'); sel = ids[fix]; [f.write(','.join(map(str, sel[k:k + 16])) + '\n') for k in range(0, len(sel), 16)]
        f.write('*MATERIAL, NAME=STEEL\n*ELASTIC\n210000.,0.3\n*DENSITY\n7.85e-9\n')
        f.write('*MATERIAL, NAME=AL6063\n*ELASTIC\n69000.,0.33\n*DENSITY\n%.4e\n' % RHO_AL)
        f.write('*SOLID SECTION, ELSET=PLATE, MATERIAL=STEEL\n*SOLID SECTION, ELSET=FOOT, MATERIAL=STEEL\n*SOLID SECTION, ELSET=COLUMN, MATERIAL=AL6063\n')
        f.write('*BOUNDARY\nNFIX,1,3\n*STEP\n*STATIC, SOLVER=%s\n' % SOLVER + '*DLOAD\nPLATE,GRAV,9810.,0.,0.,-1.\nFOOT,GRAV,9810.,0.,0.,-1.\nCOLUMN,GRAV,9810.,0.,0.,-1.\n*CLOAD\n')
        for (s, dof), F in rail_loads(tfy).items():
            sel = ids[top if s == 'top' else bot]
            for n in sel: f.write('%d,%d,%.6e\n' % (n, dof, F / len(sel)))
        f.write('*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n')
    r = subprocess.run([CCX, '-i', name], cwd=WORK, capture_output=True, text=True)
    open(os.path.join(WORK, name + '.ccxlog'), 'w').write(r.stdout[-6000:] + r.stderr[-3000:])
    disp, stress = read_frd(os.path.join(WORK, name + '.frd'))
    U = np.array([disp[i][:3] for i in ids]); S = np.array([stress[i][:6] for i in ids])
    a, b, c, d, e, g = S.T
    vm = np.sqrt(0.5 * ((a - b) ** 2 + (b - c) ** 2 + (c - a) ** 2) + 3 * (d ** 2 + e ** 2 + g ** 2))
    ut, ub = U[top].mean(axis=0), U[bot].mean(axis=0)
    th = (ut[1] - ub[1]) / spacing
    tool_dy = (ut[1] + ub[1]) / 2 + th * (TOOL_Z - zmid); tool_dz = (ut[2] + ub[2]) / 2
    im = int(np.argmax(vm)); ctop = col_nodes & (XYZ[:, 2] > zmax - 1)
    po = PLATE_ONLY['cases'].get(name, {})
    res['cases'][name] = {
        'carriage_x_mm': xc, 'tool_force_y_N': tfy, 'max_disp_mm': round(float(np.linalg.norm(U, axis=1).max()), 5),
        'max_vm_MPa': round(float(vm.max()), 2), 'max_vm_at_mm': [round(float(v), 1) for v in XYZ[im]],
        'max_vm_column_MPa': round(float(vm[col_nodes].max()), 2), 'safety_factor_column_yield_175': round(175.0 / float(vm[col_nodes].max()), 1),
        'column_top_mean_disp_mm': [round(float(v), 5) for v in U[ctop].mean(axis=0)],
        'head_rotation_urad': round(th * 1e6, 1), 'tool_tip_dy_mm_est': round(float(tool_dy), 5), 'tool_tip_dz_mm_est': round(float(tool_dz), 5),
        'plate_only_tool_tip_dy_mm': po.get('tool_tip_dy_mm_est'), 'plate_only_head_rotation_urad': po.get('head_rotation_urad')}
    np.save(os.path.join(WORK, name + '_U.npy'), U.astype(np.float32)); np.save(os.path.join(WORK, name + '_VM.npy'), vm.astype(np.float32))
    print(name, json.dumps(res['cases'][name], ensure_ascii=False), flush=True)
    for ext in ('.frd', '.dat', '.sta', '.cvg', '.12d'):
        p = os.path.join(WORK, name + ext)
        if os.path.exists(p) and ext != '.frd': os.remove(p)
np.save(os.path.join(WORK, 'node_ids.npy'), ids); np.save(os.path.join(WORK, 'node_xyz.npy'), XYZ.astype(np.float32))
np.save(os.path.join(WORK, 'tets.npy'), np.array([elems[e] for e in sorted(elems)])[:, :4])
json.dump(res, open(os.path.join(WORK, 'results_frame.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
