# -*- coding: utf-8 -*-
"""FEA check: the X head as a load at its centre of gravity (reference node) tied to the X rail strips with a
CalculiX DISTRIBUTING COUPLING (spreads force + moment, adds no stiffness).  Compared with case A of 02_run_ccx.py,
where the weight and couple were converted to rail forces by hand.
Run:  python freecad/v4/fea/05_refnode_cg.py      Out: output/v4/fea/refnode_cg.json"""
import os, json, subprocess
import numpy as np

ROOT = os.environ.get('CNC_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FEA = os.path.join(ROOT, 'output', 'v4', 'fea')
CCX = os.environ.get('CCX', r'C:\Program Files\FreeCAD 1.1\bin\ccx.exe')
H = json.load(open(os.path.join(FEA, 'head_mass.json'), encoding='utf-8'))
ids = np.load(os.path.join(FEA, 'node_ids.npy')); XYZ = np.load(os.path.join(FEA, 'node_xyz.npy'))
tets = np.load(os.path.join(FEA, 'tets.npy'))

Y0 = H['plate_bbox'][2]; zr = H['x_rails_z']; hw = H['x_rail_width'] / 2; tol = 0.05
front = np.abs(XYZ[:, 1] - Y0) < tol
fix = front & (np.abs(XYZ[:, 0]) >= 280 - tol)
W = H['head_mass_kg'] * 9.81
CG = H['head_cg_mm']
REF = int(ids.max()) + 1


def run(tag, xc, tool_fy=0.0):
    strip = front & (np.abs(XYZ[:, 0] - xc) <= 100) & ((np.abs(XYZ[:, 2] - zr[0]) <= hw + tol) | (np.abs(XYZ[:, 2] - zr[1]) <= hw + tol))
    sel = ids[strip]
    cg = (CG[0] + xc, CG[1], CG[2])                      # head moves with the carriage in X
    with open(os.path.join(FEA, tag + '.inp'), 'w') as f:
        f.write('*NODE\n')
        for i, p in zip(ids, XYZ):
            f.write('%d,%.6f,%.6f,%.6f\n' % (i, *p))
        f.write('%d,%.6f,%.6f,%.6f\n' % (REF, *cg))
        f.write('*ELEMENT, TYPE=C3D10, ELSET=EALL\n')
        for k, e in enumerate(tets):
            f.write('%d,' % (k + 1) + ','.join(map(str, e)) + '\n')
        # element faces on the rail strips (C3D10 face numbering on corner nodes) -> coupling surface
        inset = set(int(n) for n in sel)
        FACES = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}
        f.write('*SURFACE, NAME=SCOUP, TYPE=ELEMENT\n')
        nf = 0
        for k, e in enumerate(tets):
            for sid, (a, b, c) in FACES.items():
                if e[a] in inset and e[b] in inset and e[c] in inset:
                    f.write('%d,S%d\n' % (k + 1, sid)); nf += 1
        print(tag, 'coupling faces', nf)
        f.write('*COUPLING, REF NODE=%d, SURFACE=SCOUP, CONSTRAINT NAME=CHEAD\n*DISTRIBUTING\n1,3\n' % REF)
        f.write('*NSET, NSET=NFIX\n')
        sf = ids[fix]
        for k in range(0, len(sf), 16):
            f.write(','.join(map(str, sf[k:k + 16])) + '\n')
        f.write('*MATERIAL, NAME=STEEL\n*ELASTIC\n210000.,0.3\n*DENSITY\n7.85e-9\n*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\n')
        f.write('*BOUNDARY\nNFIX,1,3\n*STEP\n*STATIC\n*DLOAD\nEALL,GRAV,9810.,0.,0.,-1.\n')
        f.write('*CLOAD\n%d,3,%.6f\n' % (REF, -W))
        if tool_fy:                                      # tool force: equivalent force + moment at the CG
            f.write('%d,2,%.6f\n' % (REF, tool_fy))
        f.write('*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n')
    r = subprocess.run([CCX, '-i', tag], cwd=FEA, capture_output=True, text=True)
    disp, stress, cur = {}, {}, None
    frd = os.path.join(FEA, tag + '.frd')
    if not os.path.exists(frd):
        raise SystemExit(r.stdout[-3000:])
    for ln in open(frd, errors='ignore'):
        if ln.startswith(' -4'):
            k = ln.split()[1]; cur = disp if k.startswith('DISP') else (stress if k.startswith('STRESS') else None)
        elif ln.startswith(' -1') and cur is not None:
            cur[int(ln[3:13])] = [float(ln[13 + 12 * j:25 + 12 * j]) for j in range((len(ln.rstrip()) - 13) // 12)]
        elif ln.startswith(' -3'):
            cur = None
    U = np.array([disp[i][:3] for i in ids]); S = np.array([stress[i][:6] for i in ids])
    a, b, c, d, e, g = S.T
    vm = np.sqrt(0.5 * ((a - b) ** 2 + (b - c) ** 2 + (c - a) ** 2) + 3 * (d ** 2 + e ** 2 + g ** 2))
    top = front & (np.abs(XYZ[:, 0] - xc) <= 100) & (np.abs(XYZ[:, 2] - zr[1]) <= hw + tol)
    bot = front & (np.abs(XYZ[:, 0] - xc) <= 100) & (np.abs(XYZ[:, 2] - zr[0]) <= hw + tol)
    ut, ub = U[top].mean(axis=0), U[bot].mean(axis=0)
    th = (ut[1] - ub[1]) / (zr[1] - zr[0]); zmid = sum(zr) / 2
    tool_dy = (ut[1] + ub[1]) / 2 + th * (180.0 - zmid)
    return {'carriage_x_mm': xc, 'max_disp_um': round(float(np.linalg.norm(U, axis=1).max()) * 1000, 1),
            'max_vm_MPa': round(float(vm.max()), 2), 'tilt_urad': round(abs(th) * 1e6, 1),
            'squareness_um_per_100mm': round(abs(th) * 1e5, 1), 'tool_dy_um': round(abs(tool_dy) * 1000, 1)}


ref = json.load(open(os.path.join(FEA, 'results.json'), encoding='utf-8'))['cases']
out = {'method': 'reference node at the head CG + *COUPLING/*DISTRIBUTING (surface) to the rail strips',
       'head_mass_kg': H['head_mass_kg'], 'cg_mm': CG,
       'E_cg_x0': run('E_cg_x0', 0.0), 'E_cg_x150': run('E_cg_x150', 150.0)}
for k, rk in (('E_cg_x0', 'A_weight'), ('E_cg_x150', 'C_weight_x+150')):
    a = ref[rk]
    out[k]['hand_method'] = {'max_disp_um': round(a['max_disp_mm'] * 1000, 1), 'max_vm_MPa': a['max_vm_MPa'],
                             'tilt_urad': round(abs(a['head_rotation_urad']), 1),
                             'tool_dy_um': round(abs(a['tool_tip_dy_mm_est']) * 1000, 1)}
json.dump(out, open(os.path.join(FEA, 'refnode_cg.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False, indent=1))
