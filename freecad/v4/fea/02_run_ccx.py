# -*- coding: utf-8 -*-
"""FEA step 2 (plain Python + numpy): build CalculiX jobs for the X base plate, run them, read results.
Mesh: output/v4/fea/mesh.inp (gmsh, C3D10).  Units: mm, N, MPa, t/mm3.
Model:
  - steel plate t20 (E 210 GPa, nu 0.3, rho 7.85e-9 t/mm3), gravity on the plate
  - FIXED: plate front face where it bolts to the two column rear faces (|x| >= 280) - columns taken as rigid
  - the X head (mass from head_mass.json) hangs on the two X rails -> per rail: half the weight (-Z) plus the
    couple W*(lever to CG)/rail spacing (top rail pulled forward -Y, bottom rail pushed back +Y), applied on the
    plate front-face strip under the rail over the block span (x -100..100, carriage at centre)
  - case B adds a 100 N tool force (+Y, the direction that adds to the weight couple) at the tool tip
Run:  python freecad/v4/fea/02_run_ccx.py      Out: output/v4/fea/results.json, *.frd"""
import os, json, re, subprocess, math
import numpy as np

ROOT = os.environ.get('CNC_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FEA = os.path.join(ROOT, 'output', 'v4', 'fea')
CCX = os.environ.get('CCX', r'C:\Program Files\FreeCAD 1.1\bin\ccx.exe')
H = json.load(open(os.path.join(FEA, 'head_mass.json'), encoding='utf-8'))

# ---------------- mesh
txt = open(os.path.join(FEA, 'mesh.inp'), encoding='utf-8', errors='ignore').read().splitlines()
nodes, elems, mode = {}, [], None
for ln in txt:
    if ln.startswith('*'):
        u = ln.upper()
        mode = 'N' if u.startswith('*NODE') else ('E' if (u.startswith('*ELEMENT') and 'C3D10' in u) else None)
        continue
    if not ln.strip():
        continue
    v = [p for p in ln.replace(',', ' ').split()]
    if mode == 'N':
        nodes[int(v[0])] = (float(v[1]), float(v[2]), float(v[3]))
    elif mode == 'E':
        elems.append([int(x) for x in v])
ids = np.array(sorted(nodes))
XYZ = np.array([nodes[i] for i in ids])
print('nodes', len(ids), 'C3D10', len(elems))

xmin, xmax, ymin, ymax, zmin, zmax = H['plate_bbox']
YF = ymin                          # plate front face (rails + column contact)
tol = 0.05
front = np.abs(XYZ[:, 1] - YF) < tol
fix = front & (np.abs(XYZ[:, 0]) >= 280 - tol)
zr = H['x_rails_z']; hw = H['x_rail_width'] / 2
def rail_sets(xc):
    """Front-face strips under the two rails over the block span (blocks at xc +-100)."""
    xb0, xb1 = xc - 100.0, xc + 100.0
    t = front & (XYZ[:, 0] >= xb0) & (XYZ[:, 0] <= xb1) & (np.abs(XYZ[:, 2] - zr[1]) <= hw + tol)
    b = front & (XYZ[:, 0] >= xb0) & (XYZ[:, 0] <= xb1) & (np.abs(XYZ[:, 2] - zr[0]) <= hw + tol)
    return t, b


top, bot = rail_sets(0.0)
print('fix', fix.sum(), 'top', top.sum(), 'bot', bot.sum())

# ---------------- loads
g = 9810.0
W = H['head_mass_kg'] * 9.81                     # N
cg = H['head_cg_mm']
spacing = zr[1] - zr[0]
zmid = (zr[0] + zr[1]) / 2
M_w = W * (YF - cg[1])                           # N.mm, head hangs in front of the plate face
F_couple_w = M_w / spacing
TOOL = (0.0, 0.0, 180.0)                         # tool tip (Tool_D5 lower end)


def rail_loads(tool_fy, head=1.0):
    """Return {(set, dof): total force} for weight + optional tool force in Y at the tool tip."""
    f = {('top', 3): -W / 2 * head, ('bot', 3): -W / 2 * head, ('top', 2): -F_couple_w * head, ('bot', 2): +F_couple_w * head}
    if tool_fy:
        arm = zmid - TOOL[2]                     # tool below the rail centre line
        c = tool_fy * arm / spacing
        f[('top', 2)] += tool_fy / 2 - c
        f[('bot', 2)] += tool_fy / 2 + c
    return f


CASES = {'A_weight': (0.0, 0.0), 'B_weight_plus_100N': (100.0, 0.0), 'C_weight_x+150': (0.0, 150.0),
         'D_plate_self_weight_only': (0.0, 0.0)}
HEAD_ON = {'D_plate_self_weight_only': 0.0}


def write_job(name, tool_fy, head=1.0):
    p = os.path.join(FEA, name + '.inp')
    with open(p, 'w') as f:
        f.write('*NODE\n')
        for i, (x, y, z) in zip(ids, XYZ):
            f.write('%d,%.6f,%.6f,%.6f\n' % (i, x, y, z))
        f.write('*ELEMENT, TYPE=C3D10, ELSET=EALL\n')
        for e in elems:
            f.write(','.join(str(v) for v in e) + '\n')
        for nm, msk in (('NFIX', fix), ('NTOP', top), ('NBOT', bot)):
            f.write('*NSET, NSET=%s\n' % nm)
            sel = ids[msk]
            for k in range(0, len(sel), 16):
                f.write(','.join(str(v) for v in sel[k:k + 16]) + '\n')
        f.write('*MATERIAL, NAME=STEEL\n*ELASTIC\n210000.,0.3\n*DENSITY\n7.85e-9\n')
        f.write('*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\n')
        f.write('*BOUNDARY\nNFIX,1,3\n')
        f.write('*STEP\n*STATIC\n*DLOAD\nEALL,GRAV,%.1f,0.,0.,-1.\n' % g)
        f.write('*CLOAD\n')
        for (sname, dof), F in rail_loads(tool_fy, head).items():
            sel = ids[top if sname == 'top' else bot]
            per = F / len(sel)
            for n in sel:
                f.write('%d,%d,%.6e\n' % (n, dof, per))
        f.write('*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n')
    return p


def read_frd(path):
    """Return dict: disp[nid]=(ux,uy,uz), stress[nid]=(sxx,syy,szz,sxy,syz,szx) (nodal, averaged)."""
    disp, stress, cur = {}, {}, None
    with open(path, errors='ignore') as f:
        for ln in f:
            if ln.startswith(' -4'):
                key = ln.split()[1]
                cur = disp if key.startswith('DISP') else (stress if key.startswith('STRESS') else None)
            elif ln.startswith(' -1') and cur is not None:
                nid = int(ln[3:13])
                vals = [float(ln[13 + 12 * k:25 + 12 * k]) for k in range((len(ln.rstrip()) - 13) // 12)]
                cur[nid] = vals
            elif ln.startswith(' -3'):
                cur = None
    return disp, stress


res = {'head_mass_kg': H['head_mass_kg'], 'head_weight_N': round(W, 1), 'cg': cg, 'lever_mm': round(YF - cg[1], 1),
       'couple_per_rail_N': round(F_couple_w, 1), 'cases': {}}
for name, (tfy, xc) in CASES.items():
    top, bot = rail_sets(xc)
    hd = HEAD_ON.get(name, 1.0)
    job = write_job(name, tfy, hd)
    r = subprocess.run([CCX, '-i', name], cwd=FEA, capture_output=True, text=True)
    frd = os.path.join(FEA, name + '.frd')
    if not os.path.exists(frd):
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('ccx failed for ' + name)
    disp, stress = read_frd(frd)
    U = np.array([disp[i][:3] for i in ids])
    S = np.array([stress[i][:6] for i in ids])
    sxx, syy, szz, sxy, syz, szx = S.T
    vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + szx ** 2))
    umag = np.linalg.norm(U, axis=1)
    # rail-strip motion -> head (taken rigid) -> tool tip estimate
    ut, ub = U[top].mean(axis=0), U[bot].mean(axis=0)
    theta = (ut[1] - ub[1]) / spacing            # rotation about X (rad), +: top moves +Y more
    tool_dy = (ut[1] + ub[1]) / 2 + theta * (TOOL[2] - zmid)
    tool_dz = (ut[2] + ub[2]) / 2
    imax = int(np.argmax(vm))
    res['cases'][name] = {
        'carriage_x_mm': xc, 'tool_force_y_N': tfy, 'loads_N': {'%s_%s' % (k[0], 'XYZ'[k[1] - 1]): round(v, 1) for k, v in rail_loads(tfy, hd).items()},
        'max_disp_mm': round(float(umag.max()), 5), 'max_vm_MPa': round(float(vm.max()), 2),
        'max_vm_at_mm': [round(float(c), 1) for c in XYZ[imax]],
        'safety_factor_yield_235': round(235.0 / float(vm.max()), 1),
        'rail_top_mean_disp_mm': [round(float(c), 5) for c in ut], 'rail_bot_mean_disp_mm': [round(float(c), 5) for c in ub],
        'head_rotation_urad': round(theta * 1e6, 2), 'tool_tip_dy_mm_est': round(float(tool_dy), 5),
        'tool_tip_dz_mm_est': round(float(tool_dz), 5)}
    np.save(os.path.join(FEA, name + '_U.npy'), U)
    np.save(os.path.join(FEA, name + '_VM.npy'), vm)
    print(name, json.dumps(res['cases'][name], ensure_ascii=False))
np.save(os.path.join(FEA, 'node_ids.npy'), ids)
np.save(os.path.join(FEA, 'node_xyz.npy'), XYZ)
np.save(os.path.join(FEA, 'tets.npy'), np.array(elems)[:, 1:])
json.dump(res, open(os.path.join(FEA, 'results.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
