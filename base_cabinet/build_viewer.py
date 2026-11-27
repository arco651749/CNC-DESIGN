# -*- coding: utf-8 -*-
"""Interactive 3D page of the base cabinet + operator box (same template as column_box).  python3 base_cabinet/build_viewer.py"""
import base64, json, os, re, struct, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
src = subprocess.check_output(['git', '-C', ROOT, 'show', 'origin/claude/exciting-fermat-76sspv:output/v10/CNC_motion_v10.html']).decode('utf-8')
m = re.search(r'^const DATA=\[.*\];', src, re.M); three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]
M = json.load(open(os.path.join(HERE, 'mesh.json')))
def share(n):
    if n.startswith('ref_'): return 'frame'
    if n == 'Cabinet_door': return 'door'
    if n.startswith(('Cabinet_box', 'Cabinet_plate')): return 'box'
    if n.startswith(('Upright', 'Rail_', 'Bracket')): return 'newframe'
    if n.startswith('DIN_'): return 'din'
    return 'part'
COL = {'RCD': (0.9, 0.7, 0.2), 'QF': (0.9, 0.7, 0.2), 'KM1': (0.35, 0.6, 1), 'X0': (1, 0.65, 0.35), 'S1': (0.9, 0.15, 0.15), 'S2': (0.2, 0.7, 0.3), 'OpBox': (0.55, 0.6, 0.65), 'FL2': (0.8, 0.8, 0.8), 'DIN': (0.5, 0.52, 0.56),
       'Upright': (0.25, 0.6, 0.85), 'Rail': (0.25, 0.6, 0.85), 'Bracket': (0.95, 0.8, 0.1), 'Cabinet_box': (0.8, 0.84, 0.88), 'Cabinet_plate': (0.65, 0.7, 0.75), 'Cabinet_door': (0.8, 0.84, 0.88)}
def colour(n):
    if n.startswith('ref_'): return [0.55, 0.57, 0.6]
    for k, c in COL.items():
        if n.startswith(k): return list(c)
    return [0.75, 0.55, 0.3]
LAB = {'RCD': 'RCD 漏電斷路器', 'QF2': 'QF2 伺服(共用)', 'QF3': 'QF3 變頻器', 'QF4': 'QF4 電源', 'KM1': 'KM1 接觸器(共用)', 'X0': 'X0 進線 / PE / 出線端子', 'FL2': 'FL2 濾波器(預留)', 'S1_estop': 'S1 急停', 'S2_start': 'S2 啟動', 'OpBox': '操作盒'}
out = []
for o in M:
    pts, tris = o['p'], o['t']
    if not tris: continue
    c = [int(round(v * 10)) for p in pts for v in p]; idx = [i for t in tris for i in t]; w = 1 if len(pts) < 65536 else 0
    s = share(o['n'])
    out.append({'n': o['n'], 's': s, 'l': LAB.get(o['n'], ''), 'c': colour(o['n']), 't': 1 if (s in ('door', 'box') or o['g'].startswith('reserved')) else 0,
                'p': base64.b64encode(struct.pack('<%dh' % len(c), *c)).decode(), 'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode(), 'w': w})
cfg = {'target': [60, -620, -370], 'views': {'front': [60, -1700, -330], 'iso': [900, -1500, 150], 'side': [1500, -620, -330], 'under': [700, -1300, -900]},
       'names': {'front': '從前面看', 'iso': '等角', 'side': '從右側看', 'under': '從下方看'},
       'toggles': [['door', '門'], ['box', '箱體與安裝板'], ['frame', '現有框架（參考）'], ['newframe', '新立柱 / 橫樑 / 角鐵'], ['din', 'DIN 軌']], 'hidden': ['door']}
info = '底座電控設備（單位 mm，機台座標）：左邊是底座電箱（保護類：RCD、QF2、QF3、QF4、KM1、進線端子 X0、濾波器預留位），固定在兩支新立柱與兩條橫樑上；右邊小盒是操作盒（急停 S1 與啟動 S2），掛在右立柱側面。門預設隱藏，方便看箱內。灰色是現有框架（參考，v14），藍色是新增的立柱與橫樑，黃色是角鐵。「標示」可關閉名稱。'
page = open(os.path.join(ROOT, 'column_box', 'viewer_page.html'), encoding='utf-8').read().replace('<!--THREE-->', three, 1).replace('/*DATA*/', 'const DATA=' + json.dumps(out, separators=(',', ':')) + ';', 1).replace('/*INFO*/', info, 1).replace('/*LINES*/', 'const LINES=[];', 1).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False), 1).replace('立柱電箱 3D', '底座電箱與操作盒 3D')
open(os.path.join(HERE, 'base_cabinet_3d.html'), 'w', encoding='utf-8').write(page)
# artifact version
style = re.search(r'<style>(.*?)</style>', page, re.S).group(1); body = page[page.index('<body>') + 6:page.rindex('</body>')]
style = (style.replace('background:#eef1f4', 'background:var(--bg)').replace('color:#1d2630', 'color:var(--fg)').replace('#ffffffe6', 'var(--panel)').replace('#c9d1da', 'var(--line)')
         .replace('background:#fff;cursor', 'background:var(--panel);color:var(--fg);cursor').replace('border:1px solid #9aa6b3', 'border:1px solid var(--line)').replace('left:12px', 'left:max(16px,env(safe-area-inset-left,0px))').replace('#1d2630', 'var(--fg)'))
tokens = ':root{--bg:#eef1f4;--fg:#1d2630;--panel:#ffffffe6;--line:#c3ccd6}\n@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#171c22;--fg:#e6ebf0;--panel:#222a33e6;--line:#3a4552;color-scheme:dark}}\n:root[data-theme="dark"]{--bg:#171c22;--fg:#e6ebf0;--panel:#222a33e6;--line:#3a4552;color-scheme:dark}\nhtml,body{height:100%}body{background:var(--bg);color:var(--fg)}\n'
body = body.replace('scene.background=new THREE.Color(0xeef1f4)', "scene.background=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()||'#eef1f4')")
open(os.path.join(HERE, 'base_cabinet_3d_artifact.html'), 'w', encoding='utf-8').write('<title>底座電箱 3D</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n<style>' + tokens + style + '</style>\n' + body)
print('parts', len(out))
