# -*- coding: utf-8 -*-
"""v13 motion-simulation page: same viewer as v10 (template = the v10 motion page), DATA rebuilt from CNC_v13.FCStd, in production state (removable alignment kit taken off).
Translation group (g), spin axis (r) and colour of v10 parts come from the v10 page by label; new v11 parts take their
group from the Motion property and their colour from the adjuster colour scheme. The work piece sits on the fixture plate.
Run:  freecadcmd freecad/v13/04_export_motion_html_v13.py      Out: output/v13/CNC_motion_v13.html"""
import os, re, json, base64, struct, importlib.util
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
TEMPLATE = os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html')
FCSTD = os.path.join(ROOT, 'output', 'v13', 'CNC_v13.FCStd')
OUT = os.path.join(ROOT, 'output', 'v13', 'CNC_motion_v13.html')
LOG = os.path.join(ROOT, 'output', 'v13', 'logs', 'export_motion_html_v13.txt')


def colour(n):   # same scheme as the adjuster tour page
    if re.search(r'(air_fitting|cover_fitting)', n): return [0.12, 0.12, 0.13]      # push-in fittings: black resin
    if re.search(r'(air_tube|cover_tube)', n): return [0.15, 0.42, 0.85]            # D4 air tube: blue
    if n.startswith('Camera_lens'): return [0.1, 0.1, 0.11]
    if n.startswith(('Camera_body', 'Camera_CS_C')): return [0.15, 0.3, 0.55]
    if n == 'Camera_light_guide': return [0.85, 0.85, 0.2]
    if n == 'Tool_mirror': return [0.75, 0.9, 1.0]
    if n == 'Probe_body': return [0.12, 0.12, 0.13]
    if n in ('Probe_slide_body', 'Mirror_cover_actuator'): return [0.8, 0.82, 0.85]
    if n == 'Probe_slide_table': return [0.55, 0.58, 0.62]
    if n.startswith('Probe_reed'): return [0.85, 0.2, 0.2]
    if n == 'Mirror_cover': return [0.62, 0.66, 0.7]
    if n == 'Camera_air_ring': return [0.35, 0.38, 0.42]
    if 'epoxy' in n: return [0.13, 0.62, 0.56]
    if re.search(r'(bolt|pinch)', n): return [0.96, 0.78, 0.12]
    if re.search(r'(dowel|ref_pin|pivot_pin|roll_pin|Z_pivot_|pivot_bearing|pivot_stud)', n): return [0.16, 0.5, 0.78]
    if re.search(r'(bolt|springs|pinch|bar_screw)', n): return [0.45, 0.48, 0.5]
    if re.search(r'(_block|_bracket|_bar$|wedge_base)', n): return [0.2, 0.23, 0.26]
    if re.search(r'(jack|screw|ecc_pin|wedge|shim)', n): return [0.88, 0.36, 0.12]
    if n == 'Fixture_plate': return [0.78, 0.8, 0.82]
    if n == 'X_saddle_plate': return [0.52, 0.56, 0.6]
    return [0.7, 0.72, 0.75]


html = open(TEMPLATE, encoding='utf-8').read()
m = re.search(r'^const DATA=(\[.*\]);', html, re.M)
old = {d['n']: d for d in json.loads(m.group(1))}
doc = App.openDocument(FCSTD)
out, log = [], []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids:
        continue
    name = o.Label
    if 'Kit' in o.PropertiesList and o.Kit:      # production state: the alignment kit is off the machine
        log.append('KIT (not shown) ' + name); continue
    if name in old:
        g, r, c = old[name]['g'], old[name]['r'], old[name]['c']
        if name == 'Spindle_clamp': c = [0.62, 0.66, 0.7]
    else:
        g = o.Motion if 'Motion' in o.PropertiesList else ''
        r, c = '', colour(name)
        if name == 'X_support_float': c = old['X_support_fixed']['c']
    pts, tris = o.Shape.tessellate(1.0 if o.Label == 'Camera_lens' else (0.8 if re.search(r'(Camera_body|pivot_bearing|^[XYZ]_block_|ball_nut)', o.Label) else 0.2))
    if not tris:
        continue
    coords = [int(round(v * 10)) for p in pts for v in (p.x, p.y, p.z)]
    w = 1 if len(pts) < 65536 else 0
    idx = [k for t in tris for k in t]
    out.append({'n': name, 'c': c, 'g': g, 'r': r,
                'p': base64.b64encode(struct.pack('<%dh' % len(coords), *coords)).decode('ascii'),
                'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode('ascii'),
                'w': w, 'nt': len(tris)})
    log.append('%s g=%r r=%r tris=%d' % (name, g, r, len(tris)))
html2 = html[:m.start()] + 'const DATA=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';' + html[m.end():]
def axis(l):
    b = doc.getObjectsByLabel(l)[0].Shape.BoundBox
    return (b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2, (b.ZMin + b.ZMax) / 2
xa, ya, za = axis('X_ballscrew'), axis('Y_ballscrew'), axis('Z_ballscrew')
piv = ('piv.y.position.set(%.1f,0,%.1f);gY.add(piv.y);piv.x.position.set(0,%.1f,%.1f);gS.add(piv.x);'
       'piv.z.position.set(%.1f,%.1f,0);gX.add(piv.z);' % (ya[0], ya[2], xa[1], xa[2], za[0], za[1]))
html2, npiv = re.subn(r'piv\.y\.position\.set\([^;]*\);gY\.add\(piv\.y\);piv\.x\.position\.set\([^;]*\);gS\.add\(piv\.x\);'
                      r'piv\.z\.position\.set\([^;]*\);gX\.add\(piv\.z\);', piv, html2, count=1)
log.append('pivots replaced=%d: %s' % (npiv, piv))
html2, nwp = re.subn(r"const tt=bb\['Work_table'\]\.max\.z", "const tt=bb['Fixture_plate']?bb['Fixture_plate'].max.z:bb['Work_table'].max.z", html2, count=1)
log.append('work piece on fixture plate replaced=%d' % nwp)
html2 = re.sub(r'<title>[^<]*</title>', '<title>CNC v13 動作模擬</title>', html2, count=1)
html2 = re.sub(r'<div class="sub">.*?</div>',
               '<div class="sub">v13 生產狀態：工具頭模組（相機、主軸、探頭排成 X 向一條線，相機在主軸左 70、探頭在右 85），X 行程加長到 ±227.5；稜鏡在工作台左後角 · 拖曳旋轉、滾輪縮放</div>', html2, count=1)
# probe extend / retract control: the slide parts go into their own group under the Z group, animated by a button
PROBE_JS_GROUP = ("const gP=new THREE.Group();gZ.add(gP);const PM=['Probe_body','Probe_holder','Probe_slide_table','Probe_pinch_bolt','Probe_holder_bolt_1','Probe_holder_bolt_2','Probe_holder_bolt_3','Probe_holder_bolt_4'];"
                  "for(const m of [...gZ.children])if(PM.includes(m.userData.n))gP.add(m);let probeT=0,probeZ=0;\n")
html2, p1 = re.subn(r" if\(p\.r\)\{const pv=piv\[p\.r\];", " m.userData.n=p.n;\n if(p.r){const pv=piv[p.r];", html2, count=1)
html2, p2 = re.subn(r"(// tool tip and a work piece on the table)", lambda m_: PROBE_JS_GROUP + m_.group(1), html2, count=1)
html2, p3 = re.subn(r'(<button id="trail")', '<button id="probe">探頭 伸出</button>\\1', html2, count=1)
html2, p4 = re.subn(r"( ctl\.update\(\);R\.render\(scene,cam\);requestAnimationFrame\(step\)\})",
                    lambda m_: " {const d=probeT-probeZ;if(Math.abs(d)>0.01){probeZ+=Math.sign(d)*Math.min(Math.abs(d),dt/speed*240);gP.position.z=probeZ}}\n" + m_.group(1), html2, count=1)
html2 = html2.replace("bg();setPose();", "btn('probe').onclick=()=>{probeT=probeT<0?0:-60;btn('probe').textContent=probeT<0?'探頭 縮回':'探頭 伸出';"
                      "btn('probe').classList.toggle('on',probeT<0);st.textContent=probeT<0?'探頭伸出（氣壓滑台伸到行程調整擋）：球頭低於刀尖 19 mm'"
                      ":'探頭縮回（閥斷電、彈簧復歸，滑台收回；收回開關＝主軸允許運轉）：球頭高於刀尖 41 mm，與主軸本體底面同高'};bg();setPose();", 1)
log.append('probe control injected: %d %d %d %d' % (p1, p2, p3, p4))
_ns = {}; exec(open(os.path.join(ROOT, 'freecad', 'v13', 'toolset_inject.py'), encoding='utf-8').read(), _ns)
html2, _n = _ns['inject'](html2); log.append('tool-setting / FOV injected: %s' % _n)
html2 = html2.replace('<i>±150</i>', '<i>±227.5</i>', 1).replace('id="sx" type="range" min="-150" max="150" step="1"', 'id="sx" type="range" min="-227.5" max="227.5" step="0.5"', 1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(html2)
log.insert(0, 'parts=%d size=%d' % (len(out), len(html2)))
open(LOG, 'w', encoding='utf-8').write('\n'.join(log))
print(log[0]); print(log[-2]); print(log[-1])
