# -*- coding: utf-8 -*-
"""v14 CNC parts -> DXF (step 2 of 2, plain Python + ezdxf). One DXF per part, mm, origin at the lower-left corner of each view.
Every drawing carries:
  - overall size: real DIMENSION entities for the largest length / width / height (an edge view is added for the thickness)
  - H7 holes: size + limits in the callout, position dimensioned from the lower-left edges with a position tolerance
  - every hole group: a leader callout with its spec (tap size and pitch, clearance for which screw, counterbore, depth, face)
  - ground faces: marked on the edge view (heavy magenta line, GROUND) and listed in the notes
  - v14: every hole numbered (A1, A2 ...) with its X / Y position from the lower-left corner of its view in a position table;
    arcs, bores and half seats called out (R / diameter + centre), pockets with their size and corner; material, finish,
    datums and part-specific machining notes in the title block
Layers: OUTLINE, POCKET (dashed), HOLE, H7 (red), CENTER, DIM, GRIND (magenta), TEXT, TABLE.
Run:  python freecad/v14/10_dxf_write_v14.py      Out: output/v14/dxf/<part>.dxf, README.md (DXF_PREVIEW_DIR=... also writes PNGs)"""
import os, json, string, datetime
import ezdxf
from ezdxf.math import ConstructionArc

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v14', 'dxf')
D = json.load(open(os.path.join(OUT, 'parts.json'), encoding='utf-8'))
AXN = {'x': 'X', 'y': 'Y', 'z': 'Z'}
UV = {'z': ('x', 'y'), 'y': ('x', 'z'), 'x': ('y', 'z')}
POS_TOL = 0.02                                             # position tolerance of H7 holes from the datum edges
FLAT = 'flatness 0.01'
GRIND = {   # part: (faces, note)   faces as +/- axis, -Y = operator side
    'Datum_base_plate': (['+z'], 'top face ground (Y block seats), ' + FLAT),
    'Work_table': (['-z', '+z'], 'Y slide table: BOTH faces ground - underside = Y rail face, top = work face; %s, parallelism 0.01' % FLAT),
    'X_base_plate': (['-y'], 'front face ground (X rail face), %s; grind first, then mill the 1 mm steps at the column ends' % FLAT),
    'X_carriage_plate': (['-y'], 'front face ground (Z rail face), ' + FLAT),
    'X_saddle_plate': (['+y'], 'rear face ground (X block face), ' + FLAT),
    'Z_slide_plate': (['+y'], 'rear face ground (spacer / Z block face), ' + FLAT),
    'Z_spacer_L': (['-y', '+y'], 'both faces ground, t14 -0/+0.005, grind L and R together (same thickness)'),
    'Z_spacer_R': (['-y', '+y'], 'both faces ground, t14 -0/+0.005, grind L and R together (same thickness)'),
    'Spindle_mount_plate': (['-y', '+y'], 'both faces ground, %s, parallelism 0.01' % FLAT),
}
NUT = 'nut-flange bolt holes and the mounting bolt holes are not modelled yet'
MOT = 'motor flange screw holes (4x on the motor PCD) are not modelled yet'
INCOMPLETE = {}
SPECIAL = {   # part-specific machining notes
    'Camera_bracket': 'machine as one block with Camera_bracket_cap: drill / tap, saw apart (split gap 0.5), then bore D45 H7 with both halves bolted together',
    'Camera_bracket_cap': 'machine as one block with Camera_bracket: see there (bore D45 H7 together, split gap 0.5)',
    'Probe_stem': 'shank bore D6 H7 and slit 1 wide x 20 deep from the bore to the front face; M4 pinch across the slit',
    'Probe_holder': '4 x M4 c-bores on the underside (rod-end plate bolts), 2 x M4 c-bores on the top (stem bolts): mind the faces',
    'Spindle_clamp': 'bore D65 H7, front split 2 wide from the bore to the front face; 4 x M6 taps in the REAR face (bolts from the module plate)',
    'Z_nut_housing': 'bore D28.2 for the nut body; flange taps on the top face, M6 taps in the front face',
    'Mirror_bracket': 'window through the base for the prism and slot 18 wide through the base under the light path; tenon key 14 h7',
}
def material(spec, name):
    s_ = spec.lower()
    if 'hfs8' in s_: return 'MATERIAL  MISUMI HFS8 extrusion (6063-T5), cut to length + additional machining; FINISH  as supplied (clear anodized)'
    if '6061' in s_: return 'MATERIAL  6061-T6 aluminium; FINISH  clear anodize (after machining, threads masked or re-tapped)'
    if 'sus' in s_: return 'MATERIAL  SUS304; FINISH  as machined'
    if 'q235' in s_ or 'steel' in s_: return 'MATERIAL  steel (Q235 / S45C as in the spec); FINISH  black oxide, ground faces bare + rust oil'
    return 'MATERIAL  see SPEC; FINISH  see SPEC'
T = lambda s: s.replace('Ø', '%%c')

rows = []
for p in D:
    doc = ezdxf.new('R2010', setup=True); doc.units = ezdxf.units.MM; msp = doc.modelspace()
    for n, c, lt in (('OUTLINE', 7, 'CONTINUOUS'), ('POCKET', 8, 'DASHED'), ('HOLE', 5, 'CONTINUOUS'), ('H7', 1, 'CONTINUOUS'), ('CENTER', 3, 'CENTER'),
                     ('DIM', 4, 'CONTINUOUS'), ('GRIND', 6, 'CONTINUOUS'), ('TEXT', 7, 'CONTINUOUS'), ('TABLE', 7, 'CONTINUOUS')):
        doc.layers.add(n, color=c, linetype=lt)
    big = max(p['size']); th = 2.5 if big < 150 else (3.5 if big < 400 else 5)    # text height scales with the part
    ds = doc.dimstyles.new('CNC'); ds.dxf.dimtxt = th; ds.dxf.dimasz = th * 0.8; ds.dxf.dimexe = th * 0.5; ds.dxf.dimexo = 1
    ds.dxf.dimgap = th * 0.3; ds.dxf.dimdec = 2; ds.dxf.dimzin = 8; ds.dxf.dimtad = 1; ds.dxf.dimtih = 0; ds.dxf.dimtoh = 0; ds.dxf.dimclrd = 4; ds.dxf.dimclre = 4
    def dim(base, p1, p2, ang, tol=None):
        ov = {'dimtol': 1, 'dimtp': tol, 'dimtm': tol, 'dimtdec': 2, 'dimtfac': 0.8} if tol else {}
        msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle='CNC', override=ov, dxfattribs={'layer': 'DIM'}).render()
    def text(s, at, h=None, layer='TEXT'):
        msp.add_text(T(s), height=h or th, dxfattribs={'layer': layer}).set_placement(at)

    # ---- views: the extracted ones, plus an edge view if an axis is not shown or a ground face needs to be seen
    views = list(p['views']); shown = {a for v in views for a in UV[v['axis']]}
    gfaces, gnote = GRIND.get(p['name'], ([], ''))
    need = (set('xyz') - shown) | {f[1] for f in gfaces if not any(f[1] in UV[v['axis']] for v in views)}
    edge = None
    if need:
        m = sorted(need)[0]; a = next(k for k in ('y', 'z', 'x') if m in UV[k] and k != views[0]['axis'])
        u, v = UV[a]; sz = dict(zip('xyz', p['size']))
        edge = {'axis': a, 'w': sz[u], 'h': sz[v], 'ents': [['outline', []]], 'holes': [], 'edge': True}
    codes = {}
    for v in views:
        for h in v['holes']:
            if h['txt'] not in codes: codes[h['txt']] = [string.ascii_uppercase[len(codes) % 26] + ('' if len(codes) < 26 else str(len(codes) // 26)), 0, h['cls'], False]
            codes[h['txt']][1] += 1

    x0, dimmed = 0.0, set()
    POS, FEAT, cnt = [], [], {}
    def place(v, ox, oy):
        u_ax, v_ax = UV[v['axis']]; W, H = v['w'], v['h']
        P = lambda q: (q[0] + ox, q[1] + oy)
        if v.get('edge'):
            msp.add_lwpolyline([P((0, 0)), P((W, 0)), P((W, H)), P((0, H))], close=True, dxfattribs={'layer': 'OUTLINE'})
        for tag, ents in v['ents']:
            for e in ents:
                at = {'layer': 'OUTLINE' if tag == 'outline' else 'POCKET'}
                if e[0] == 'L': msp.add_line(P(e[1]), P(e[2]), dxfattribs=at)
                elif e[0] == 'C': msp.add_circle(P(e[1]), e[2], dxfattribs=at)
                elif e[0] == 'A':
                    try: ConstructionArc.from_3p(P(e[1]), P(e[3]), P(e[2])).add_to_layout(msp, dxfattribs=at)
                    except Exception: msp.add_lwpolyline([P(e[1]), P(e[2]), P(e[3])], dxfattribs=at)
                else: msp.add_lwpolyline([P(q) for q in e[1]], dxfattribs=at)
        # features: bores / arcs / half seats that are not holes, pockets (size + lower-left corner)
        hc = [(h['u'], h['v'], h['r'], h['big']) for h in v['holes']]
        isho = lambda cx, cy, r: any(abs(cx - a) < 0.1 and abs(cy - b) < 0.1 and (abs(r - r1) < 0.1 or abs(r - r2) < 0.1) for a, b, r1, r2 in hc)
        for tag, ents in v['ents']:
            for e in ents:
                try:
                    if e[0] == 'C': cx, cy, r, lp, full = e[1][0], e[1][1], e[2], (e[1][0] + e[2] * 0.7, e[1][1] + e[2] * 0.7), True
                    elif e[0] == 'A':
                        ca = ConstructionArc.from_3p(e[1], e[3], e[2]); cx, cy, r, lp, full = ca.center.x, ca.center.y, ca.radius, tuple(e[2]), False
                    elif e[0] == 'P' and tag != 'outline':
                        us_ = [q[0] for q in e[1]]; vs_ = [q[1] for q in e[1]]
                        pw, ph = max(us_) - min(us_), max(vs_) - min(vs_)
                        if pw > 1 and ph > 1:
                            FEAT.append((AXN[v['axis']], 'pocket %.1f x %.1f' % (pw, ph), min(us_), min(vs_)))
                            text('pocket %.1f x %.1f' % (pw, ph), P(((min(us_) + max(us_)) / 2 - 4 * th, (min(vs_) + max(vs_)) / 2)), th * 0.7, 'DIM')
                        continue
                    else: continue
                except Exception: continue
                if r < 0.6 or isho(cx, cy, r): continue
                lab = ('Ø%.2f' % (2 * r)) if full else ('R%.2f' % r)
                if any(f[1] == lab and abs(f[2] - cx) < 0.1 and abs(f[3] - cy) < 0.1 for f in FEAT): continue
                FEAT.append((AXN[v['axis']], lab, cx, cy))
                q = P(lp); msp.add_line(q, (q[0] + 2 * th, q[1] + 2 * th), dxfattribs={'layer': 'DIM'})
                text(lab + ('' if full else ' (Ø%.2f)' % (2 * r)), (q[0] + 2.3 * th, q[1] + 2 * th), th * 0.8, 'DIM')
        # overall size: width above, height on the left (once per axis)
        if u_ax not in dimmed: dim((ox, oy + H + 3 * th), P((0, H)), P((W, H)), 0); dimmed.add(u_ax)
        if v_ax not in dimmed: dim((ox - 3 * th, oy), P((0, 0)), P((0, H)), 90); dimmed.add(v_ax)
        # holes
        h7 = [h for h in v['holes'] if h['cls'] == 'H7' and 'ream at assembly' not in h['txt']]
        rep, anchors = {}, []                                   # one callout per group, on the hole farthest from the other callouts
        for txt in codes:
            cand = [h for h in v['holes'] if h['txt'] == txt]
            if not cand: continue
            best = max(cand, key=lambda h: min([((h['u'] - a[0]) ** 2 + (h['v'] - a[1]) ** 2) for a in anchors] or [0]) - 1e-3 * h['u'])
            rep[txt] = id(best); anchors.append((best['u'], best['v']))
        for h in v['holes']:
            c = P((h['u'], h['v'])); L = 'H7' if h['cls'] == 'H7' else 'HOLE'; code = codes[h['txt']]
            msp.add_circle(c, h['r'], dxfattribs={'layer': L})
            if h['big'] > h['r'] + 0.01: msp.add_circle(c, h['big'], dxfattribs={'layer': L, 'linetype': 'DASHED'})
            k = h['big'] + 1.5
            msp.add_line((c[0] - k, c[1]), (c[0] + k, c[1]), dxfattribs={'layer': 'CENTER'}); msp.add_line((c[0], c[1] - k), (c[0], c[1] + k), dxfattribs={'layer': 'CENTER'})
            cnt[code[0]] = cnt.get(code[0], 0) + 1; lab = '%s%d' % (code[0], cnt[code[0]])
            POS.append((AXN[v['axis']], lab, h['u'], h['v']))
            text(lab, (c[0] + h['big'] * 0.75 + 0.5, c[1] + h['big'] * 0.75 + 0.5), th * 0.7, L)
            if rep.get(h['txt']) == id(h):                     # one leader callout per hole group
                r0 = h['big'] * 0.707; q = (c[0] + r0, c[1] - r0); gi = list(codes).index(h['txt']) % 4; e1 = (q[0] + (2.5 + 1.5 * gi) * th, q[1] - (2.5 + 1.5 * gi) * th)
                msp.add_line(q, e1, dxfattribs={'layer': L}); msp.add_line(e1, (e1[0] + th, e1[1]), dxfattribs={'layer': L})
                s = '%s  %dx %s' % (code[0], code[1], h['txt']) if code[1] > 1 else '%s  %s' % (code[0], h['txt'])
                text(s, (e1[0] + th * 1.3, e1[1] - th * 0.4), th * 0.8, L)
        us = sorted({round(h['u'], 2): h for h in h7}.items()); vs = sorted({round(h['v'], 2): h for h in h7}.items())
        for i, (uu, h) in enumerate(us):                       # H7 positions from the lower-left edges, one dim per distinct coordinate
            dim((ox, oy + H + (6 + 3 * i) * th), P((0, H)), P((h['u'], h['v'])), 0, POS_TOL)
        for i, (vv, h) in enumerate(vs):
            dim((ox + W + (3 + 3 * i) * th, oy), P((W, 0)), P((h['u'], h['v'])), 90, POS_TOL)
        # ground faces seen in this view
        for f in gfaces:
            if f[1] not in (u_ax, v_ax): continue
            g = 1.2; wd = 0.25 * th
            if f[1] == v_ax: seg = [P((0, H + g)), P((W, H + g))] if f[0] == '+' else [P((0, -g)), P((W, -g))]
            else: seg = [P((W + g, 0)), P((W + g, H))] if f[0] == '+' else [P((-g, 0)), P((-g, H))]
            msp.add_lwpolyline(seg, dxfattribs={'layer': 'GRIND', 'const_width': wd})
            mid = ((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2)
            off = (0, th * 0.6) if (f[1] == v_ax and f[0] == '+') else ((0, -th * 1.8) if f[1] == v_ax else (th, 0))
            text('GROUND ' + FLAT, (mid[0] + off[0] - 8 * th, mid[1] + off[1]), th * 0.8, 'GRIND')
        nH = max(len(us), len(vs))
        text('VIEW %s  %g x %g' % (AXN[v['axis']], W, H), (ox, oy - 2.2 * th - (th * 2 if any(f[1] == v_ax and f[0] == '-' for f in gfaces) else 0)), th)
        text('looking along %s%s' % (AXN[v['axis']], '' if v.get('edge') else ', section at mid depth'),
             (ox, oy - 3.6 * th - (th * 2 if any(f[1] == v_ax and f[0] == '-' for f in gfaces) else 0)), th * 0.7)
        return W + (3 + 3 * nH) * th
    for v in views:
        x0 += 4 * th
        x0 += place(v, x0, 0) + 14 * th
    if edge:                                                   # edge view under the first view
        place(edge, 4 * th, -edge['h'] - 12 * th)
    # ---- notes and hole table
    H0 = max(v['h'] for v in views) + (6 + 3 * max(len({round(h['u'], 2) for h in v['holes'] if h['cls'] == 'H7'}) for v in views)) * th
    tx, ty = x0, max(H0, 1.6 * th * (len(codes) + 12))
    lines = ['PART  %s   QTY %d   v14   %s' % (p['name'], p['qty'], datetime.date.today().isoformat()),
             'OVERALL  %g x %g x %g mm (X x Y x Z)' % tuple(p['size']), 'SPEC  ' + p['spec'][:110],
             'Units mm. General tolerance ISO 2768-m. Break sharp edges 0.3.',
             'H7 holes: limits in the callout; position +-%.2f from the lower-left edges (datum edges machined square).' % POS_TOL,
             material(p['spec'], p['name']),
             'DATUMS  A = largest face; B / C = lower / left edge of each view (machined square to A). Positions below are from B / C.']
    if p['name'] in SPECIAL: lines.append('NOTE  ' + SPECIAL[p['name']])
    if gnote: lines.append('GRIND: ' + gnote)
    if p['name'] in INCOMPLETE: lines.append('NOT FINAL: ' + INCOMPLETE[p['name']])
    lines += ['', 'HOLE TABLE']
    for txt, (code, n, cls, _) in codes.items(): lines.append('%-3s x%-3d %s' % (code, n, txt))
    if POS:
        lines += ['', 'HOLE POSITIONS  (view: hole = X, Y from the lower-left corner of that view)']
        for va in sorted({q[0] for q in POS}):
            it = ['%s=(%.2f, %.2f)' % (q[1], q[2], q[3]) for q in POS if q[0] == va]
            for i in range(0, len(it), 4): lines.append(('VIEW %s  ' % va if i == 0 else '         ') + '   '.join(it[i:i + 4]))
    if FEAT:
        lines += ['', 'FEATURES  (bores, arcs, pockets: size, centre or lower-left corner)']
        for q in FEAT: lines.append('VIEW %s  %s at (%.2f, %.2f)' % (q[0], q[1], q[2], q[3]))
    for i, t in enumerate(lines):
        lay = 'H7' if (' H7 (' in t or t.startswith('NOT FINAL')) else ('GRIND' if t.startswith('GRIND') else 'TABLE')
        text(t, (tx, ty - 1.6 * th * i), th, lay)
    doc.saveas(os.path.join(OUT, p['name'] + '.dxf'))
    nh = sum(c[1] for c in codes.values()); n7 = sum(c[1] for c in codes.values() if c[2] == 'H7')
    rows.append((p['name'] + (' **(未完成)**' if p['name'] in INCOMPLETE else ''), p['qty'], ' × '.join('%g' % s for s in p['size']), nh, n7,
                 gnote.split(',')[0] if gnote else '—', p['spec'][:60]))
    print(p['name'], 'holes', nh, 'H7', n7, 'edge' if edge else '')
md = ['# v14 CNC 加工件 DXF', '', '由 `freecad/v14/09_dxf_extract_v14.py`（抽取）與 `10_dxf_write_v14.py`（輸出）產生。單位 mm，每個視圖原點在左下角。', '',
      '每張圖都有：', '',
      '- 最大長寬高的尺寸標註（板件另加側視圖標厚度）；',
      '- H7 孔：孔徑與公差上下限，孔位從左下兩邊標尺寸，位置公差 ±%.2f（基準邊要加工成直角）；' % POS_TOL,
      '- 每組孔一條引線，寫規格（攻牙尺寸與牙距、給幾號螺絲的過孔、沉頭、深度、從哪一面）；',
      '- 研磨面在側視圖用紫色粗線加 GROUND 標出，並寫在註記欄；',
      '- 每個孔都有編號（A1、A2…），孔位表列出每個孔在該視圖的 X、Y（從左下角量）；',
      '- 圓弧、搪孔、半圓座標 R／直徑與圓心，口袋標大小與左下角位置；',
      '- 標題欄寫材質、表面處理、基準（A＝最大面，B／C＝各視圖下緣／左緣）與該零件的加工註記（例如成對加工）。', '',
      '標「ream at assembly」的孔在組裝調整後現場配鉸，不標孔位。', '',
      'RBPB8 座孔 Ø22 H7：外環 h6，用固持膠（Loctite 641）黏固，不壓入。', '',
      '| 零件 | 數量 | 外形 X × Y × Z | 孔數 | H7 孔 | 研磨 | 規格 |', '|---|---|---|---|---|---|---|']
md += ['| %s | %d | %s | %d | %d | %s | %s |' % r for r in rows]
open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
PV = os.environ.get('DXF_PREVIEW_DIR')                        # optional: a PNG of every DXF for checking
if PV:
    import matplotlib; matplotlib.use('Agg')
    from ezdxf.addons.drawing import matplotlib as mdraw
    os.makedirs(PV, exist_ok=True)
    for p in D: mdraw.qsave(ezdxf.readfile(os.path.join(OUT, p['name'] + '.dxf')).modelspace(), os.path.join(PV, p['name'] + '.png'), bg='#FFFFFF', dpi=130)
