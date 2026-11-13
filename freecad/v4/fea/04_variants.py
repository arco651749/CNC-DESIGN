# -*- coding: utf-8 -*-
"""FEA step 4 (freecadcmd): design variants of the X base plate / X head, same loads model as 02_run_ccx.py.
Variants: plate t20 (baseline) / t30 / t40 (front rail face fixed, thicker towards the rear, slot through),
and t20 with an aluminium X carriage plate (lighter head).  Each at carriage x = 0 and x = +150.
Outputs per run: max von Mises, head tilt about X (= Z-axis squareness change in the YZ plane) and the tool-tip
Y offset estimate.
Run:  freecadcmd freecad/v4/fea/04_variants.py        Out: output/v4/fea/variants.json"""
import os, json, subprocess
import numpy as np
import FreeCAD as App
import Part
from FreeCAD import Vector as V

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
FEA = os.path.join(ROOT, 'output', 'v4', 'fea')
WORK = os.path.join(FEA, 'variants'); os.makedirs(WORK, exist_ok=True)
GMSH = r'C:\Program Files\FreeCAD 1.1\bin\gmsh.exe'
CCX = r'C:\Program Files\FreeCAD 1.1\bin\ccx.exe'
H = json.load(open(os.path.join(FEA, 'head_mass.json'), encoding='utf-8'))
doc = App.openDocument(os.path.join(ROOT, 'output', 'v4', 'CNC_v4.FCStd'))
plate20 = doc.getObjectsByLabel('X_base_plate')[0].Shape.copy()
X0, X1, Y0, Y1, Z0, Z1 = H['plate_bbox']           # Y0 = front face (rails, column contact)

# slot = through-thickness part of what was removed from the full t20 block
removed = Part.makeBox(X1 - X0, Y1 - Y0, Z1 - Z0, V(X0, Y0, Z0)).cut(plate20)
slots = [s for s in removed.Solids if s.BoundBox.YLength > (Y1 - Y0) - 0.5]
print('slot solids', len(slots), [tuple(round(v, 1) for v in (s.BoundBox.XMin, s.BoundBox.XMax, s.BoundBox.ZMin, s.BoundBox.ZMax)) for s in slots])


def make_plate(t):
    p = Part.makeBox(X1 - X0, t, Z1 - Z0, V(X0, Y0, Z0))
    for s in slots:
        b = s.BoundBox
        p = p.cut(Part.makeBox(b.XLength, t + 2, b.ZLength, V(b.XMin, Y0 - 1, b.ZMin)))
    return p


def head(al_carriage):
    m = mx = my = mz = 0.0
    for n, mass, x, y, z in H['parts']:
        if al_carriage and n == 'X_carriage_plate':
            mass = mass * 2.70 / 7.85
        m += mass; mx += mass * x; my += mass * y; mz += mass * z
    return m, (mx / m, my / m, mz / m)


def mesh(step, out):
    subprocess.run([GMSH, step, '-3', '-order', '2', '-clmax', '6', '-clmin', '2', '-format', 'inp', '-o', out],
                   capture_output=True, text=True, check=True)
    nodes, elems, mode = {}, [], None
    for ln in open(out, errors='ignore'):
        if ln.startswith('*'):
            u = ln.upper(); mode = 'N' if u.startswith('*NODE') else ('E' if (u.startswith('*ELEMENT') and 'C3D10' in u) else None); continue
        v = ln.replace(',', ' ').split()
        if not v: continue
        if mode == 'N': nodes[int(v[0])] = (float(v[1]), float(v[2]), float(v[3]))
        elif mode == 'E': elems.append([int(x) for x in v])
    ids = np.array(sorted(nodes)); return ids, np.array([nodes[i] for i in ids]), elems


def solve(tag, ids, XYZ, elems, mass, cg, xc):
    zr = H['x_rails_z']; hw = H['x_rail_width'] / 2; tol = 0.05
    front = np.abs(XYZ[:, 1] - Y0) < tol
    fix = front & (np.abs(XYZ[:, 0]) >= 280 - tol)
    top = front & (np.abs(XYZ[:, 0] - xc) <= 100) & (np.abs(XYZ[:, 2] - zr[1]) <= hw + tol)
    bot = front & (np.abs(XYZ[:, 0] - xc) <= 100) & (np.abs(XYZ[:, 2] - zr[0]) <= hw + tol)
    W = mass * 9.81; spacing = zr[1] - zr[0]; Fc = W * (Y0 - cg[1]) / spacing
    loads = {('top', 3): -W / 2, ('bot', 3): -W / 2, ('top', 2): -Fc, ('bot', 2): Fc}
    with open(os.path.join(WORK, tag + '.inp'), 'w') as f:
        f.write('*NODE\n'); [f.write('%d,%.6f,%.6f,%.6f\n' % (i, *p)) for i, p in zip(ids, XYZ)]
        f.write('*ELEMENT, TYPE=C3D10, ELSET=EALL\n'); [f.write(','.join(map(str, e)) + '\n') for e in elems]
        for nm, msk in (('NFIX', fix),):
            f.write('*NSET, NSET=%s\n' % nm); sel = ids[msk]
            for k in range(0, len(sel), 16): f.write(','.join(map(str, sel[k:k + 16])) + '\n')
        f.write('*MATERIAL, NAME=STEEL\n*ELASTIC\n210000.,0.3\n*DENSITY\n7.85e-9\n*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\n')
        f.write('*BOUNDARY\nNFIX,1,3\n*STEP\n*STATIC\n*DLOAD\nEALL,GRAV,9810.,0.,0.,-1.\n*CLOAD\n')
        for (s, dof), F in loads.items():
            sel = ids[top if s == 'top' else bot]
            for n in sel: f.write('%d,%d,%.6e\n' % (n, dof, F / len(sel)))
        f.write('*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n')
    subprocess.run([CCX, '-i', tag], cwd=WORK, capture_output=True, text=True)
    disp, stress, cur = {}, {}, None
    for ln in open(os.path.join(WORK, tag + '.frd'), errors='ignore'):
        if ln.startswith(' -4'):
            k = ln.split()[1]; cur = disp if k.startswith('DISP') else (stress if k.startswith('STRESS') else None)
        elif ln.startswith(' -1') and cur is not None:
            cur[int(ln[3:13])] = [float(ln[13 + 12 * j:25 + 12 * j]) for j in range((len(ln.rstrip()) - 13) // 12)]
        elif ln.startswith(' -3'):
            cur = None
    U = np.array([disp[i][:3] for i in ids]); S = np.array([stress[i][:6] for i in ids])
    a, b, c, d, e, g = S.T
    vm = np.sqrt(0.5 * ((a - b) ** 2 + (b - c) ** 2 + (c - a) ** 2) + 3 * (d ** 2 + e ** 2 + g ** 2))
    ut, ub = U[top].mean(axis=0), U[bot].mean(axis=0)
    th = (ut[1] - ub[1]) / spacing; zmid = sum(zr) / 2
    tool_dy = (ut[1] + ub[1]) / 2 + th * (180.0 - zmid)
    for ext in ('.inp', '.frd', '.dat', '.sta', '.cvg', '.12d'):
        p = os.path.join(WORK, tag + ext)
        if os.path.exists(p): os.remove(p)
    return {'max_vm_MPa': round(float(vm.max()), 2), 'tilt_urad': round(abs(th) * 1e6, 1),
            'squareness_um_per_100mm': round(abs(th) * 1e5, 1), 'tool_dy_um': round(abs(tool_dy) * 1000, 1)}


VARIANTS = [('t20', 20, False), ('t30', 30, False), ('t40', 40, False), ('t20_Al_carriage', 20, True)]
out = {}
for name, t, al in VARIANTS:
    p = make_plate(t); step = os.path.join(WORK, name + '.step'); p.exportStep(step)
    ids, XYZ, elems = mesh(step, os.path.join(WORK, name + '_mesh.inp'))
    m, cg = head(al)
    r = {'plate_t_mm': t, 'plate_mass_kg': round(p.Volume * 7.85e-6, 2), 'al_carriage': al,
         'head_mass_kg': round(m, 2), 'head_cg_y': round(cg[1], 1), 'nodes': int(len(ids))}
    for xc in (0.0, 150.0):
        r['x%+d' % xc] = solve('%s_x%d' % (name, xc), ids, XYZ, elems, m, cg, xc)
    r['squareness_change_um_per_100mm'] = round(r['x+0']['squareness_um_per_100mm'] - r['x+150']['squareness_um_per_100mm'], 1)
    out[name] = r
    print(name, json.dumps(r, ensure_ascii=False))
json.dump(out, open(os.path.join(FEA, 'variants.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
