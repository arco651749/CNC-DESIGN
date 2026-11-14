# -*- coding: utf-8 -*-
"""v11 motion-simulation page: same viewer as v10 (template = the v10 motion page), DATA rebuilt from CNC_v11.FCStd, in production state (removable alignment kit taken off).
Translation group (g), spin axis (r) and colour of v10 parts come from the v10 page by label; new v11 parts take their
group from the Motion property and their colour from the adjuster colour scheme. The work piece sits on the fixture plate.
Run:  freecadcmd freecad/v11/04_export_motion_html_v11.py      Out: output/v11/CNC_motion_v11.html"""
import os, re, json, base64, struct, importlib.util
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
TEMPLATE = os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html')
FCSTD = os.path.join(ROOT, 'output', 'v11', 'CNC_v11.FCStd')
OUT = os.path.join(ROOT, 'output', 'v11', 'CNC_motion_v11.html')
LOG = os.path.join(ROOT, 'output', 'v11', 'logs', 'export_motion_html_v11.txt')


def colour(n):   # same scheme as the adjuster tour page
    if re.search(r'(dowel|ref_pin|pivot_pin|roll_pin)', n): return [0.16, 0.5, 0.78]
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
    pts, tris = o.Shape.tessellate(0.15)
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
html2 = re.sub(r'<title>[^<]*</title>', '<title>CNC v11 動作模擬</title>', html2, count=1)
html2 = re.sub(r'<div class="sub">.*?</div>',
               '<div class="sub">v11 生產狀態（校正工具組已拆下；腳座墊片、主軸三點支撐留在機上；主軸前移 13 mm，工件在治具板上）· 拖曳旋轉、滾輪縮放</div>', html2, count=1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(html2)
log.insert(0, 'parts=%d size=%d' % (len(out), len(html2)))
open(LOG, 'w', encoding='utf-8').write('\n'.join(log))
print(log[0]); print(log[-2]); print(log[-1])
