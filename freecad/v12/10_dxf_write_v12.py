# -*- coding: utf-8 -*-
"""v12 CNC parts -> DXF (step 2 of 2, plain Python + ezdxf). One DXF per part, mm, origin at the lower-left corner of each view.
Layers: OUTLINE (section at mid depth), POCKET (sections near the faces, dashed), HOLE, H7 (red), CENTER, TEXT, TABLE.
Each hole carries a letter; the hole table lists size, type, depth and count. H7 holes show their limits.
Run:  python freecad/v12/10_dxf_write_v12.py      Out: output/v12/dxf/<part>.dxf, output/v12/dxf/README.md, preview PNGs"""
import os, json, string, datetime
import ezdxf
from ezdxf.math import ConstructionArc

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'output', 'v12', 'dxf')
D = json.load(open(os.path.join(OUT, 'parts.json'), encoding='utf-8'))
AXN = {'x': 'X', 'y': 'Y', 'z': 'Z'}
rows = []
NUT = 'nut-flange bolt holes and the mounting bolt holes are not modelled yet'
MOT = 'motor flange screw holes (4x on the motor PCD) are not modelled yet'
INCOMPLETE = {'Z_nut_housing': NUT, 'X_nut_bracket': NUT, 'Y_nut_bracket': NUT, 'Z_motor_plate': MOT, 'X_motor_block': MOT, 'Y_motor_block': MOT}
for p in D:
    doc = ezdxf.new('R2010', setup=True); doc.units = ezdxf.units.MM; msp = doc.modelspace()
    for n, c, lt in (('OUTLINE', 7, 'CONTINUOUS'), ('POCKET', 8, 'DASHED'), ('HOLE', 5, 'CONTINUOUS'), ('H7', 1, 'CONTINUOUS'),
                     ('CENTER', 3, 'CENTER'), ('TEXT', 7, 'CONTINUOUS'), ('TABLE', 7, 'CONTINUOUS')):
        doc.layers.add(n, color=c, linetype=lt)
    codes, x0 = {}, 0.0
    for v in p['views']:
        lay = lambda tag: 'OUTLINE' if tag == 'outline' else 'POCKET'
        for tag, ents in v['ents']:
            for e in ents:
                a = {'layer': lay(tag)}; o = (x0, 0)
                P = lambda q: (q[0] + o[0], q[1] + o[1])
                if e[0] == 'L': msp.add_line(P(e[1]), P(e[2]), dxfattribs=a)
                elif e[0] == 'C': msp.add_circle(P(e[1]), e[2], dxfattribs=a)
                elif e[0] == 'A':
                    try: ConstructionArc.from_3p(P(e[1]), P(e[3]), P(e[2])).add_to_layout(msp, dxfattribs=a)
                    except Exception: msp.add_lwpolyline([P(e[1]), P(e[2]), P(e[3])], dxfattribs=a)
                else: msp.add_lwpolyline([P(q) for q in e[1]], dxfattribs=a)
        for h in v['holes']:
            if h['txt'] not in codes: codes[h['txt']] = [string.ascii_uppercase[len(codes) % 26] + ('' if len(codes) < 26 else str(len(codes) // 26)), 0, h['cls']]
            codes[h['txt']][1] += 1
            c = (h['u'] + x0, h['v']); L = 'H7' if h['cls'] == 'H7' else 'HOLE'
            msp.add_circle(c, h['r'], dxfattribs={'layer': L})
            if h['big'] > h['r'] + 0.01: msp.add_circle(c, h['big'], dxfattribs={'layer': L, 'linetype': 'DASHED'})
            k = h['big'] + 2
            msp.add_line((c[0] - k, c[1]), (c[0] + k, c[1]), dxfattribs={'layer': 'CENTER'}); msp.add_line((c[0], c[1] - k), (c[0], c[1] + k), dxfattribs={'layer': 'CENTER'})
            msp.add_text(codes[h['txt']][0], height=3.5, dxfattribs={'layer': 'H7' if h['cls'] == 'H7' else 'TEXT'}).set_placement((c[0] + h['big'] + 1, c[1] + h['big'] + 1))
        msp.add_text('VIEW %s  %g x %g' % (AXN[v['axis']], v['w'], v['h']), height=4, dxfattribs={'layer': 'TEXT'}).set_placement((x0, -10))
        msp.add_text('looking along %s, section at mid depth' % AXN[v['axis']], height=2.5, dxfattribs={'layer': 'TEXT'}).set_placement((x0, -16))
        x0 += max(v['w'], 62) + 40
    # hole table + title block to the right
    tx, ty = x0, max(max(v['h'] for v in p['views']), 7 * (len(codes) + 7))
    lines = ['PART  %s   QTY %d   v12   %s' % (p['name'], p['qty'], datetime.date.today().isoformat()),
             'SIZE  %g x %g x %g mm (x y z)' % tuple(p['size']), 'SPEC  ' + p['spec'][:110], 'Units mm. General tolerance ISO 2768-m. H7 holes: see limits.', '',
             'HOLE TABLE']
    if p['name'] in INCOMPLETE: lines[4:4] = ['NOT FINAL: ' + INCOMPLETE[p['name']]]
    for txt, (code, n, cls) in codes.items(): lines.append('%-3s x%-3d %s' % (code, n, txt))
    for i, t in enumerate(lines):
        msp.add_text(t.replace('Ø', '%%c'), height=4 if i < 5 else 3.5, dxfattribs={'layer': 'H7' if (' H7 (' in t or t.startswith('NOT FINAL')) else 'TABLE'}).set_placement((tx, ty - 7 * i))
    f = os.path.join(OUT, p['name'] + '.dxf'); doc.saveas(f)
    rows.append((p['name'] + (' **(未完成)**' if p['name'] in INCOMPLETE else ''), p['qty'], 'x'.join('%g' % s for s in p['size']), sum(n for c, n, k in codes.values()), sum(n for c, n, k in codes.values() if k == 'H7'), p['spec'][:70]))
    print(p['name'], 'holes', rows[-1][3], 'H7', rows[-1][4])
md = ['# v12 CNC 加工件 DXF', '', '由 `freecad/v12/09_dxf_extract_v12.py`（抽取）與 `10_dxf_write_v12.py`（輸出）產生。單位 mm，每個視圖原點在左下角。',
      '定位銷、樞軸銷、靠銷、偏心銷與球面軸承的孔標 H7（紅色圖層），並寫公差上下限；標「ream at assembly」的孔在組裝調整後現場配鉸。', '',
      '**未完成**：3 個螺帽座缺螺帽法蘭孔與安裝孔，3 個馬達座缺馬達法蘭螺絲孔（模型還沒畫），DXF 標題欄有紅字 NOT FINAL，這 6 件先不要發包。', '',
      '| 零件 | 數量 | 外形 (x×y×z) | 孔數 | H7 孔 | 規格 |', '|---|---|---|---|---|---|']
md += ['| %s | %d | %s | %d | %d | %s |' % r for r in rows]
open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
# previews for a quick look
try:
    import matplotlib; matplotlib.use('Agg')
    from ezdxf.addons.drawing import matplotlib as mdraw
    PV = os.environ.get('DXF_PREVIEW_DIR')                    # optional: a PNG of every DXF for checking
    if PV:
        os.makedirs(PV, exist_ok=True)
        for p in D: mdraw.qsave(ezdxf.readfile(os.path.join(OUT, p['name'] + '.dxf')).modelspace(), os.path.join(PV, p['name'] + '.png'), bg='#FFFFFF', dpi=110)
except Exception as e:
    print('preview skipped', e)
