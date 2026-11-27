# -*- coding: utf-8 -*-
"""Interactive 3D page from mesh.json (three.js inlined from the mechanical session's v10 motion page).  python3 column_box/build_viewer.py"""
import base64, json, os, re, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
src = subprocess.check_output(['git', '-C', ROOT, 'show', 'origin/claude/exciting-fermat-76sspv:output/v10/CNC_motion_v10.html']).decode('utf-8')
m = re.search(r'^const DATA=\[.*\];', src, re.M); three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]
M = json.load(open(os.path.join(HERE, 'mesh.json')))
def share(n):
    if n == 'L_plate_vertical': return 'wall'
    if n.startswith('L_plate'): return 'roof'
    if n.startswith('Rail_'): return 'rails'
    if n.startswith('PullNut'): return 'nuts'
    return 'part'
NAMECOL = {'PSU': (0.25, 0.7, 0.3), 'VFD': (1, 0.5, 0.45), 'PC': (0.6, 0.4, 0.95), 'IOTA': (0.1, 0.45, 0.25), 'KM1': (0.35, 0.6, 1), 'RCD': (0.9, 0.7, 0.2), 'QF': (0.9, 0.7, 0.2), 'Fan': (0.4, 0.4, 0.45),
           'BD': (0.1, 0.5, 0.3), 'SV': (0.2, 0.22, 0.25), 'AIRV': (0.1, 0.75, 0.75), 'KA': (0.8, 0.6, 0.95), 'X1': (1, 0.65, 0.35), 'XT': (1, 0.65, 0.35), 'DC1': (0.55, 0.58, 0.62), 'FL2': (0.8, 0.8, 0.8), 'Intake': (0.5, 0.5, 0.55), 'Louvre': (0.5, 0.5, 0.55)}
def colour(n):
    if n.startswith('L_plate'): return [0.72, 0.76, 0.8]
    if n.startswith('Rail_'): return [0.5, 0.52, 0.56]
    if n.startswith('PullNut'): return [0.95, 0.8, 0.1]
    for k, c in NAMECOL.items():
        if n.startswith(k): return list(c)
    return [0.75, 0.55, 0.3]
LABELS = {'RCD': 'RCD 漏電斷路器', 'QF2': 'QF2 伺服斷路器(共用)', 'QF3': 'QF3 變頻器斷路器', 'QF4': 'QF4 電源斷路器', 'KM1': 'KM1 接觸器(共用)', 'DC1': 'DC1 24→5V', 'KA2': 'KA2 泵繼電器',
          'KA3': 'KA3 Z煞車繼電器', 'XT': 'XT 端子排', 'BD': 'BD 控制板 RP23CNC', 'IOTA_pcb': 'PC LattePanda IOTA', 'FL2': 'FL2 濾波器(預留)', 'PSU1': 'PSU1 24V 5A', 'PSU2': 'PSU2 12V 6.3A',
          'SVX': 'SVX 伺服 X', 'SVY': 'SVY 伺服 Y', 'SVZ': 'SVZ 伺服 Z', 'VFD': 'VFD 主軸變頻器', 'AIRV': 'SVL 吹氣閥', 'X1': 'X1 電源端子排', 'Fan_120': '進風扇 120mm', 'Louvre_filter': '出風濾網', 'Intake_filter': '進風濾網', 'IOTA_cooler': 'FIT1027 散熱器'}
out = []
for o in M:
    pts, tris = o['p'], o['t']
    if not tris: continue
    c = [int(round(v * 10)) for p in pts for v in p]; idx = [i for t in tris for i in t]; w = 1 if len(pts) < 65536 else 0
    s = share(o['n']); resv = o['g'].startswith('reserved')
    out.append({'n': o['n'], 's': s, 'l': LABELS.get(o['n'], ''), 'c': colour(o['n']), 't': 1 if (resv or s in ('roof',)) else 0,
                'p': base64.b64encode(struct.pack('<%dh' % len(c), *c)).decode(), 'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode(), 'w': w})
info = '立柱電控板（控制類）：一片折成 L 型的板（SPHC t4，沒有蓋子）。所有電料都鎖在垂直板的後面往後伸，接頭朝後方（+y），從機台後面就能維修；水平板上只有吊鎖孔與 X 浪管孔，沒有電料。垂直板上由左到右：左欄 BD 控制板（上）與 IOTA 電腦（下）；中間一排 X1 端子、SVL 吹氣閥、PSU1 24V、PSU2 12V；上方一排 DC1、KA2、KA3、XT；右邊 VFD 變頻器與三台伺服 SVX/SVY/SVZ。保護類（斷路器、接觸器）在底座電箱。"標示"可關閉名稱，勾選方塊可隱藏零件。'
page = open(os.path.join(HERE, 'viewer_page.html'), encoding='utf-8').read().replace('<!--THREE-->', three, 1).replace('/*DATA*/', 'const DATA=' + json.dumps(out, separators=(',', ':')) + ';', 1).replace('/*INFO*/', info, 1)
open(os.path.join(HERE, 'column_box_3d.html'), 'w', encoding='utf-8').write(page)
print('parts', len(out), 'size MB %.1f' % (len(page) / 1e6))
