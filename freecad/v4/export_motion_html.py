# -*- coding: utf-8 -*-
"""Rebuild the v4 motion-simulation HTML from output/v4/CNC_v4.FCStd.
Keeps the page template (three.js viewer, controls) and replaces only the embedded DATA array.
Per part: n name, c colour, g translation axis ('x'|'y'|'z'|''), r spin axis, p int16 positions (mm*10, base64),
i indices (uint16 if w=1 else uint32, base64), nt triangle count.  g/r/c are taken from the previous page when the
part name existed there; new parts get g='' and r=''.
Run:  freecadcmd freecad/v4/export_motion_html.py      (from any directory; uses CNC_ROOT or the repo path)"""
import os, re, json, base64, struct
import FreeCAD as App
import Part

ROOT = os.environ.get('CNC_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FCSTD = os.path.join(ROOT, 'output', 'v4', 'CNC_v4.FCStd')
HTML = os.path.join(ROOT, 'output', 'v4', 'CNC_motion_v4_screws.html')
LOG = os.path.join(ROOT, 'output', 'v4', 'logs', 'export_motion_html.txt')
os.makedirs(os.path.dirname(LOG), exist_ok=True)

html = open(HTML, encoding='utf-8').read()
m = re.search(r'^const DATA=(\[.*\]);', html, re.M)
if not m:
    raise SystemExit('DATA line not found')
old = {d['n']: d for d in json.loads(m.group(1))}

doc = App.openDocument(FCSTD)
out, log = [], []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids:
        continue
    name = o.Label                                  # page uses labels (internal Name can differ, e.g. Z_motor_bracket)
    old_d = old.get(name) or old.get(o.Name, {})
    if not old_d:
        log.append('NEW (no g/r from previous page) ' + name)
    pts, tris = o.Shape.tessellate(0.15)
    if not tris:
        continue
    coords = []
    for v in pts:
        coords += [int(round(v.x * 10)), int(round(v.y * 10)), int(round(v.z * 10))]
    if max(abs(c) for c in coords) > 32767:
        log.append('OVERFLOW ' + name)
        continue
    w = 1 if len(pts) < 65536 else 0
    idx = []
    for t in tris:
        idx += [t[0], t[1], t[2]]
    p_b64 = base64.b64encode(struct.pack('<%dh' % len(coords), *coords)).decode('ascii')
    fmt = '<%dH' % len(idx) if w else '<%dI' % len(idx)
    i_b64 = base64.b64encode(struct.pack(fmt, *idx)).decode('ascii')
    out.append({'n': name, 'c': old_d.get('c', [0.7, 0.72, 0.75]), 'g': old_d.get('g', ''), 'r': old_d.get('r', ''),
                'p': p_b64, 'i': i_b64, 'w': w, 'nt': len(tris)})
    log.append('%s pts=%d tris=%d g=%r r=%r' % (name, len(pts), len(tris), out[-1]['g'], out[-1]['r']))

new_line = 'const DATA=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
html2 = html[:m.start()] + new_line + html[m.end():]
open(HTML, 'w', encoding='utf-8', newline='\n').write(html2)
log.insert(0, 'parts=%d (old=%d) size=%d' % (len(out), len(old), len(html2)))
open(LOG, 'w', encoding='utf-8').write('\n'.join(log))
print('HTML', HTML, len(out), 'parts')
