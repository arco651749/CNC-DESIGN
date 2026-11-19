# -*- coding: utf-8 -*-
"""v12 datum plate FEA, step 2 (plain Python + numpy + CalculiX).
Model: Q235 plate t20 (E 210 GPa, nu 0.3), C3D10 from gmsh; bottom face fixed on the 4 base risers (60x60, bolted);
gravity on the plate; gantry weight on the two foot footprints (shared by the CG in X, linear in Y for the CG offset);
table weight on the 4 Y blocks (front/rear pair shared by the table CG at its position); case D adds a 100 N cutting force
(+Y on the tool -> shear and a rear-heavy couple at the feet, -Y on the Y nut bracket).
Run:  python freecad/v12/fea/02_datum_solve.py      Out: output/v12/fea/datum_results.json (+ .npy for the page)"""
import os, json, subprocess
import numpy as np

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
FEA = os.path.join(ROOT, 'output', 'v12', 'fea')
CCX = os.environ.get('CCX', r'C:\Program Files\FreeCAD 1.1\bin\ccx.exe')
L = json.load(open(os.path.join(FEA, 'datum_loads.json'), encoding='utf-8'))
nodes, elems, mode = {}, [], None
for ln in open(os.path.join(FEA, 'datum_mesh.inp'), errors='ignore'):
    if ln.startswith('*'):
        u = ln.upper(); mode = 'N' if u.startswith('*NODE') else ('E' if (u.startswith('*ELEMENT') and 'C3D10' in u) else None); continue
    v = ln.replace(',', ' ').split()
    if not v: continue
    if mode == 'N': nodes[int(v[0])] = tuple(map(float, v[1:4]))
    elif mode == 'E': elems.append([int(x) for x in v])
ids = np.array(sorted(nodes)); XYZ = np.array([nodes[i] for i in ids]); X, Y, Z = XYZ.T
print('nodes', len(ids), 'C3D10', len(elems))
ZT, ZB = L['plate_bbox'][5], L['plate_bbox'][4]
top, bot = np.abs(Z - ZT) < 0.05, np.abs(Z - ZB) < 0.05
inside = lambda r, m: m & (X >= r[0] - 0.05) & (X <= r[1] + 0.05) & (Y >= r[2] - 0.05) & (Y <= r[3] + 0.05)
fix = np.zeros(len(ids), bool)
for x, y in L['risers']: fix |= inside((x - 30, x + 30, y - 30, y + 30), bot)
feet = {k: inside(v, top) for k, v in L['feet'].items()}
blocks = {k: inside(v, top) for k, v in L['blocks'].items()}
nut = inside(L['nut_bracket'], top)
print('fix', fix.sum(), {k: int(v.sum()) for k, v in feet.items()}, {k: int(v.sum()) for k, v in blocks.items()}, 'nut', nut.sum())

g = 9810.0
Wg = L['gantry']['mass_kg'] * 9.81; xg, yg, _ = L['gantry']['cg_mm']
Wt = L['table']['mass_kg'] * 9.81; yt0 = L['table']['cg_mm'][1]
FX = {'L': -320.0, 'R': 320.0}
def foot_forces(fy_tool):
    """per node force arrays (dof2, dof3) on the feet: weight shared by CG, linear in y for the CG offset and the tool couple"""
    f2, f3 = np.zeros(len(ids)), np.zeros(len(ids))
    zt = L['tool_tip'][2] - ZT
    for k, m in feet.items():
        F = Wg * (xg - FX['L' if k == 'R' else 'R']) / (FX['R'] - FX['L']) * (1 if k == 'R' else -1) if False else None
        share = (xg - FX['L']) / (FX['R'] - FX['L']); F = Wg * (share if k == 'R' else 1 - share)
        yy = Y[m]; yc = yy.mean(); d = yy - yc
        M = F * (yg - yc) + fy_tool * zt / 2              # rear-heavy for +Y tool force on the gantry
        down = F / m.sum() + M * d / (d @ d)
        f3[np.where(m)[0]] -= down
        f2[np.where(m)[0]] += fy_tool / 2 / m.sum()
    return f2, f3
def block_forces(dy):
    f3 = np.zeros(len(ids)); yc = yt0 + dy
    yf = np.mean([np.mean(L['blocks'][n][2:]) for n in ('Y_block_L1', 'Y_block_R1')]); yr = np.mean([np.mean(L['blocks'][n][2:]) for n in ('Y_block_L2', 'Y_block_R2')])
    Fr = Wt * (yc - yf) / (yr - yf); Ff = Wt - Fr
    for n, m in blocks.items():
        f3[np.where(m)[0]] -= (Fr if n.endswith('2') else Ff) / 2 / m.sum()
    return f3, round(Ff, 1), round(Fr, 1)
CASES = {'A_table_centre': (0, 0), 'B_table_load_pos_y-250': (-250, 0), 'C_table_rear_y+150': (150, 0), 'D_centre_plus_100N_cut': (0, 100)}

def read_frd(path):
    disp, stress, cur = {}, {}, None
    for ln in open(path, errors='ignore'):
        if ln.startswith(' -4'):
            k = ln.split()[1]; cur = disp if k.startswith('DISP') else (stress if k.startswith('STRESS') else None)
        elif ln.startswith(' -1') and cur is not None:
            cur[int(ln[3:13])] = [float(ln[13 + 12 * j:25 + 12 * j]) for j in range((len(ln.rstrip()) - 13) // 12)]
        elif ln.startswith(' -3'): cur = None
    return disp, stress
mesh_inc = os.path.join(FEA, 'datum_mesh_include.inp')
with open(mesh_inc, 'w') as f:
    f.write('*NODE\n'); [f.write('%d,%.6f,%.6f,%.6f\n' % (i, *p)) for i, p in zip(ids, XYZ)]
    f.write('*ELEMENT, TYPE=C3D10, ELSET=EALL\n'); [f.write(','.join(map(str, e)) + '\n') for e in elems]
    f.write('*NSET, NSET=NFIX\n'); sel = ids[fix]; [f.write(','.join(map(str, sel[k:k + 16])) + '\n') for k in range(0, len(sel), 16)]
res = {'gantry': L['gantry'], 'table': L['table'], 'plate_mass_kg': L['plate_mass_kg'], 'cases': {}}
for name, (dy, fy) in CASES.items():
    f2, f3 = foot_forces(fy); b3, Ff, Fr = block_forces(dy); f3 = f3 + b3
    if fy: f2[np.where(nut)[0]] -= fy / nut.sum()
    with open(os.path.join(FEA, name + '.inp'), 'w') as f:
        f.write('*INCLUDE, INPUT=datum_mesh_include.inp\n*MATERIAL, NAME=Q235\n*ELASTIC\n210000.,0.3\n*DENSITY\n7.85e-9\n')
        f.write('*SOLID SECTION, ELSET=EALL, MATERIAL=Q235\n*BOUNDARY\nNFIX,1,3\n*STEP\n*STATIC, SOLVER=SPOOLES\n*DLOAD\nEALL,GRAV,%.1f,0.,0.,-1.\n*CLOAD\n' % g)
        for dof, arr in ((2, f2), (3, f3)):
            for k in np.nonzero(arr)[0]: f.write('%d,%d,%.6e\n' % (ids[k], dof, arr[k]))
        f.write('*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n')
    r = subprocess.run([CCX, '-i', name], cwd=FEA, capture_output=True, text=True, env=dict(os.environ, OMP_NUM_THREADS='4'))
    frd = os.path.join(FEA, name + '.frd')
    if not os.path.exists(frd): print(r.stdout[-1500:]); raise SystemExit('ccx failed ' + name)
    disp, stress = read_frd(frd)
    U = np.array([disp[i][:3] for i in ids]); S = np.array([stress[i][:6] for i in ids])
    sxx, syy, szz, sxy, syz, szx = S.T
    vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + szx ** 2))
    uz = {n: float(U[m, 2].mean()) for n, m in blocks.items()}
    ft = {}
    for k, m in feet.items():
        yy = Y[m]; fr, rr = m.copy(), m.copy(); fr[m] = yy < yy.min() + 40; rr[m] = yy > yy.max() - 40
        ft[k] = (float(U[rr, 2].mean()) - float(U[fr, 2].mean())) / (float(Y[rr].mean()) - float(Y[fr].mean()))   # rad, + = rear rises
    pitch = ((uz['Y_block_L2'] + uz['Y_block_R2']) - (uz['Y_block_L1'] + uz['Y_block_R1'])) / 2 / 159.0
    roll_f = (uz['Y_block_R1'] - uz['Y_block_L1']) / 320.0; roll_r = (uz['Y_block_R2'] - uz['Y_block_L2']) / 320.0
    imax = int(np.argmax(vm))
    res['cases'][name] = {'table_y_mm': dy, 'cut_force_N': fy, 'block_pair_N': [Ff, Fr],
        'max_disp_mm': round(float(np.linalg.norm(U, axis=1).max()), 5), 'max_vm_MPa': round(float(vm.max()), 2),
        'max_vm_at_mm': [round(float(c), 1) for c in XYZ[imax]], 'safety_factor_yield_235': round(235 / float(vm.max()), 1),
        'block_uz_um': {n: round(v * 1000, 2) for n, v in uz.items()},
        'table_pitch_urad': round(pitch * 1e6, 2), 'table_roll_front_urad': round(roll_f * 1e6, 2), 'table_roll_rear_urad': round(roll_r * 1e6, 2),
        'rail_twist_urad': round((roll_r - roll_f) * 1e6, 2),
        'foot_tilt_urad': {k: round(v * 1e6, 2) for k, v in ft.items()}}
    np.save(os.path.join(FEA, name + '_U.npy'), U); np.save(os.path.join(FEA, name + '_VM.npy'), vm)
    print(name, json.dumps(res['cases'][name]))
A = res['cases']['A_table_centre']
def delta(a, b, key):
    return round(res['cases'][a][key] - res['cases'][b][key], 2)
res['travel_change'] = {
    'table_pitch_urad_B_minus_C': delta('B_table_load_pos_y-250', 'C_table_rear_y+150', 'table_pitch_urad'),
    'rail_twist_urad_B_minus_C': delta('B_table_load_pos_y-250', 'C_table_rear_y+150', 'rail_twist_urad'),
    'foot_tilt_urad_B_minus_C': {k: round(res['cases']['B_table_load_pos_y-250']['foot_tilt_urad'][k] - res['cases']['C_table_rear_y+150']['foot_tilt_urad'][k], 2) for k in ('L', 'R')},
    'foot_tilt_urad_D_minus_A': {k: round(res['cases']['D_centre_plus_100N_cut']['foot_tilt_urad'][k] - A['foot_tilt_urad'][k], 2) for k in ('L', 'R')}}
np.save(os.path.join(FEA, 'datum_node_xyz.npy'), XYZ); np.save(os.path.join(FEA, 'datum_tets.npy'), np.array(elems)[:, 1:])
np.save(os.path.join(FEA, 'datum_node_ids.npy'), ids)
json.dump(res, open(os.path.join(FEA, 'datum_results.json'), 'w', encoding='utf-8'), indent=1)
print('TRAVEL', json.dumps(res['travel_change']))
