# -*- coding: utf-8 -*-
"""v14 electrical boxes review page (light, a few MB): machine on its base, the column-top box on its top plate and the base cabinet
(both drawn by the electrical session: column_box/column_box.step, base_cabinet/base_cabinet.step, local copies), the conduits.
Box shells can be switched between solid and see-through. Same page frame as the conduit page (conduit_page.html).
Run:  freecadcmd freecad/v14/25_export_elec_html_v14.py      Out: output/v14/CNC_v14_electrics.html"""
import os, re, json, base64, struct
import FreeCAD as App, Part, Import
ROOT = os.environ.get('CNC_ROOT') or r'D:\\Claude\\CNC DESIGN'
src = open(os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html'), encoding='utf-8').read()
m = re.search(r'^const DATA=\[.*\];', src, re.M); three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]
doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))
def cls(o):
    n = o.Label
    if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''
SHELL = ('Cabinet_box', 'Cabinet_door', 'OpBox')                 # column box is one open L plate (no shell); base cabinet body / door and the operator box
def colour(n, k, src_):
    if src_ == 'm' and n.startswith(('Conduit_', 'X_branch_box', 'Table_cable', 'Feeder_entry')):   # cable system = one dark layer (design review)
        return [0.07, 0.07, 0.08] if re.search(r'(fitting|connector|gland)', n) else [0.22, 0.24, 0.27]
    if src_ != 'm':                                            # electrical boxes
        if n in SHELL: return [0.83, 0.85, 0.80]
        if n.startswith(('SV', 'VFD', 'PSU', 'PC')): return [0.22, 0.24, 0.27]
        if n.startswith(('BD', 'RP23')): return [0.1, 0.45, 0.25]
        if n.startswith(('S1', 'S2')): return [0.85, 0.15, 0.1]
        return [0.62, 0.66, 0.72]
    if n.startswith('Box_top'): return [0.80, 0.82, 0.78]
    if n.startswith('Feeder_') and 'clamp' not in n and 'gland' not in n: return [0.16, 0.17, 0.19]
    if n.startswith(('X_motor', 'Y_motor', 'Z_motor')) and 'plate' not in n and 'block' not in n: return [0.2, 0.22, 0.25]
    if n.startswith(('Guard_window',)): return [0.75, 0.85, 0.92]
    return {'y': [0.78, 0.62, 0.42], 'x': [0.5, 0.64, 0.8], 'z': [0.62, 0.72, 0.84]}.get(k, [0.68, 0.71, 0.75])
OBJS = [(o, 'm') for o in doc.Objects]
for d in ('column_box', 'base_cabinet'):
    f = os.path.join(ROOT, d, d + '.step')
    if os.path.exists(f):
        bd = App.newDocument(d); Import.insert(f, bd.Name); OBJS += [(o, d) for o in bd.Objects]
out = []
for o, s_ in OBJS:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    sh = o.Shape; b = sh.BoundBox
    own = s_ == 'm' and o.Label.startswith(('Conduit_', 'Feeder_entry', 'Feeder_cabinet', 'X_branch_box', 'Table_cable')) and not re.search(r'(bolt|screw)', o.Label)
    if sh.Volume < 300 or (re.search(r'(bolt|screw|_pin|dowel|epoxy|shim|fitting|tube|reed|nut$|PullNut|standoff)', o.Label, re.I) and not own): continue
    if s_ == 'm' and re.search(r'^(Guard_(rear|side|front)|Coolant_(tank|pan|baffle|filter|drain|pump|silicone|castor|hose))', o.Label): continue
    if len(sh.Faces) > 60 and not o.Label.startswith(('Box_top', 'Conduit_', 'Feeder_', 'X_branch_box', 'Table_')):   # vendor-detailed parts as boxes; own sheet parts keep their real outline
        sh = Part.makeBox(b.XLength, b.YLength, b.ZLength, App.Vector(b.XMin, b.YMin, b.ZMin))
    pts, tris = sh.tessellate(max(1.5, 0.012 * max(b.XLength, b.YLength, b.ZLength)))
    c = [int(round(v * 4)) for p in pts for v in (p.x, p.y, p.z)]; idx = [i for t in tris for i in t]; w = 1 if len(pts) < 65536 else 0
    k = cls(o) if s_ == 'm' else ''
    out.append({'n': o.Label, 'k': k, 'c': colour(o.Label, k, s_), 't': 1 if o.Label in SHELL else 0,
                'p': base64.b64encode(struct.pack('<%dh' % len(c), *c)).decode(),
                'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode(), 'w': w})
page = open(os.path.join(ROOT, 'freecad', 'v14', 'conduit_page.html'), encoding='utf-8').read()
page = page.replace('<title>v14 浪管檢視</title>', '<title>v14 電控箱</title>').replace('<b>v14 浪管檢視（從機台後方）</b>', '<b>v14 電控箱（立柱電箱 + 底座電箱）</b>')
page = page.replace('<button data-v="front">前方</button></div>', '<button data-v="front">前方</button><button id="shell">底座箱透明</button></div>')
page = page.replace('黑色＝浪管（Y 段、X 段頂板滾動環、Z 段）；機台已簡化', '灰白＝立柱 L 板、底座箱、操作盒；深灰＝伺服 / 變頻器 / 電源；黑＝浪管；護罩、水箱未顯示')
page = page.replace("const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:new THREE.Color(...p.c),metalness:0.1,roughness:0.65}));",
                    "const mt=new THREE.MeshStandardMaterial({color:new THREE.Color(...p.c),metalness:0.1,roughness:0.65});if(p.t)SH.push(mt);const m=new THREE.Mesh(g,mt);")
page = page.replace('for(const p of DATA){', 'const SH=[];for(const p of DATA){', 1)
page = page.replace("const T=new THREE.Vector3(0,120,330);const VIEWS={back:[1500,2300,1400],side:[2600,150,700],front:[-1300,-2300,1300]};",
                    "const T=new THREE.Vector3(0,0,0);const VIEWS={back:[1700,2700,1300],side:[3000,0,500],front:[-1500,-2700,900]};")
page = page.replace("window.renderOnce=", "let see=false;document.getElementById('shell').onclick=e=>{see=!see;e.target.classList.toggle('on',see);"
                    "for(const mt of SH){mt.transparent=see;mt.opacity=see?0.25:1;mt.depthWrite=!see;mt.needsUpdate=true}};window.renderOnce=")
page = page.replace('<!--THREE-->', three, 1).replace('/*DATA*/', 'const DATA=' + json.dumps(out, separators=(',', ':')) + ';', 1)
_nc = {}; exec(open(os.path.join(ROOT, 'freecad', 'v14', 'conduit_inject.py'), encoding='utf-8').read(), _nc)
page, _ = _nc['inject'](page, ROOT)
page = page.replace(' if(CD.box){', ' if(false&&CD.box){', 1)            # the real box shells are drawn: no envelope
open(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_electrics.html'), 'w', encoding='utf-8').write(page)
print('parts', len(out), 'size', len(page))
