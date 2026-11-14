# -*- coding: utf-8 -*-
"""v11 adjuster tour page: the v11 model with one station per adjustment (what it sets, how to measure, how to adjust).
Each part is exported with its kinematic group (k) and adjuster tag (a); colours of v10 parts come from the v10 motion page.
Run:  freecadcmd freecad/v11/03_export_adjust_html_v11.py      Out: output/v11/CNC_adjusters_v11.html"""
import os, re, json, base64, struct
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
V10 = os.path.join(ROOT, 'output', 'v10', 'CNC_motion_v10.html')
TPL = os.path.join(ROOT, 'freecad', 'v11', 'adjusters_page.html')
OUT = os.path.join(ROOT, 'output', 'v11', 'CNC_adjusters_v11.html')

src = open(V10, encoding='utf-8').read()
m = re.search(r'^const DATA=(\[.*\]);', src, re.M)
old = {d['n']: d['c'] for d in json.loads(m.group(1))}
three = src[src.find('<script'):src.rfind('<script>', 0, m.start())]

RULES = [   # first match wins
    ('sp', r'^(Spindle_body|Spindle_fan_cover|Spindle_plug|Spindle_nose|ER11_nut|Tool_D5|Spindle_clamp|Spindle_pinch_screw_|Spindle_bolt_|Spindle_disc_springs_)'),
    ('z', r'^(Z_block|Z_spacer|Z_slide|Z_ball_nut|Z_nut_housing|Spindle_)'),
    ('zp', r'^(X_carriage_plate|Z_rail_|Z_ballscrew|Z_support_fixed|Z_coupling|Z_motor|Z_ref_pin_|Z_ecc_pin_|Z_side_screw_|Z_tram_bolt_|Z_tram_pivot_pin|Z_tram_lock_dowel)'),
    ('x', r'^(X_saddle_plate|X_block_|X_ball_nut|X_nut_bracket|Z_tram_block|Z_tram_screw)'),
    ('y', r'^(Y_rail|Work_table|Y_ballscrew|Y_support|Y_coupling|Y_motor|Y_ref_pin_|Y_ecc_pin_|Y_side_screw_|Fixture_plate)'),
    ('gan', r'^(Column_foot_|Gantry_column_|Foot_)'),
    ('xp', r'^(X_base_plate|X_rail_|X_ballscrew|X_support_fixed|X_coupling|X_motor|X_ref_pin_|X_ecc_pin_|X_side_screw_|X_plate_bolt_|Servo_amp|Electrical_panel)'),
]
def group(n):
    for k, rx in RULES:
        if re.match(rx, n): return k
    return 'base'
def colour(n, adj):
    if n in old and n != 'Spindle_clamp': return old[n]
    if re.search(r'(dowel|ref_pin|pivot_pin|roll_pin)', n): return [0.16, 0.5, 0.78]             # pins: blue
    if re.search(r'(bolt|springs|pinch|bar_screw)', n): return [0.45, 0.48, 0.5]               # fasteners: grey
    if re.search(r'(_block|_bracket|_bar$|wedge_base)', n): return [0.2, 0.23, 0.26]           # fixed blocks: dark
    if re.search(r'(jack|screw|ecc_pin|wedge)', n): return [0.88, 0.36, 0.12]                  # what you turn or what moves: orange
    if n == 'Spindle_clamp': return [0.62, 0.66, 0.7]
    if n == 'Fixture_plate': return [0.78, 0.8, 0.82]
    if n == 'X_saddle_plate': return [0.52, 0.56, 0.6]
    return [0.7, 0.72, 0.75]

doc = App.openDocument(os.path.join(ROOT, 'output', 'v11', 'CNC_v11.FCStd'))
out = []
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    pts, tris = o.Shape.tessellate(0.15)
    if not tris: continue
    coords = [int(round(v * 10)) for p in pts for v in (p.x, p.y, p.z)]
    w = 1 if len(pts) < 65536 else 0
    idx = [k for t in tris for k in t]
    adj = o.Adj if 'Adj' in o.PropertiesList else ''
    out.append({'n': o.Label, 'c': colour(o.Label, adj), 'k': group(o.Label), 'a': adj,
                'p': base64.b64encode(struct.pack('<%dh' % len(coords), *coords)).decode('ascii'),
                'i': base64.b64encode(struct.pack(('<%dH' if w else '<%dI') % len(idx), *idx)).decode('ascii'), 'w': w, 'nt': len(tris)})
page = open(TPL, encoding='utf-8').read()
assert '<!--THREE-->' in page and '/*DATA*/' in page
page = page.replace('<!--THREE-->', three, 1).replace('/*DATA*/', 'const DATA=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';', 1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(page)
print('parts=%d size=%d' % (len(out), len(page)))
