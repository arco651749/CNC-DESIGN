# -*- coding: utf-8 -*-
"""Gantry-column box: placement table (CSV), checks, heat budget (HEAT.md), STEP.   python3 column_box/build.py"""
import csv, itertools, os
import layout as L
HERE = os.path.dirname(os.path.abspath(__file__))
x0e, x1e, y0e, y1e, z0e, z1e = L.ENV
def bb(p): return (p[3], p[3] + p[6], p[4], p[4] + p[7], p[5], p[5] + p[8])
rep = []
for p in L.PARTS:
    b = bb(p)
    if b[0] < x0e or b[1] > x1e or b[2] < y0e or b[3] > y1e or b[4] < z0e or b[5] > z1e: rep.append('OUTSIDE ENVELOPE: %s %s' % (p[1], b))
for a, b_ in itertools.combinations(L.PARTS, 2):
    A, B = bb(a), bb(b_)
    if all(min(A[2*i+1], B[2*i+1]) - max(A[2*i], B[2*i]) > 0.01 for i in range(3)): rep.append('OVERLAP: %s x %s' % (a[1], b_[1]))
sv = [p for p in L.PARTS if p[1].startswith('SV')]
for p in sv:
    b = bb(p); rep.append('%s: below %.0f mm, above %.0f mm to the box (manual 40; owner accepted 35 for the first build)' % (p[1], b[4] - z0e, z1e - b[5]))
for p, q in zip(sv, sv[1:]): rep.append('%s-%s side gap %.0f mm (manual 10)' % (p[1], q[1], bb(q)[0] - bb(p)[1]))
rep.append('servo front face y=%.0f; nearest obstacle y=242 -> wiring room %.0f mm (need >= 60)' % (min(bb(p)[2] for p in sv), min(bb(p)[2] for p in sv) - 242))
with open(os.path.join(HERE, 'placement.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['位號', '零件', 'x min', 'x max', 'y min', 'y max', 'z min', 'z max', '尺寸 dx×dy×dz', '安裝面', '方向', '尺寸來源'])
    for p in L.PARTS:
        b = bb(p); w.writerow([p[1], p[2]] + ['%.0f' % v for v in b] + ['%gx%gx%g' % (p[6], p[7], p[8]), p[9], p[10], p[11]])
with open(os.path.join(HERE, 'openings.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['面', 'x', 'y', 'z', '用途'])
    for o in L.OPENINGS: w.writerow(o)
open(os.path.join(HERE, 'placement_check.txt'), 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))

# ---------------- heat budget
LOSS = [  # (item, qty, W each, source)
    ('MR-J4-40A + HG-KR43 at rated output', 3, 35, '三菱 MR-J4-A 手冊表 10.1 (servo-off 15 W)'),
    ('Delta MS300 VFD (0.8 kW spindle)', 1, 40, '估算（約 5% 損失，手冊值待查）'),
    ('Mean Well SDR-120-24 (~79 W out, ~90%)', 1, 9, '估算（銘牌效率未查）'),
    ('Mean Well XDR-75E-12 (60 W out, 89%)', 1, 7, '規格書效率 89%（12V 型）'),
    ('LattePanda IOTA (owner: 12 V 60 W)', 1, 60, 'owner 提供，最壞值'),
    ('RP23CNC + DC-DC + KA3 + XT', 1, 4, '估算'),
    ('fan 120 mm 24 V', 1, 5, '估算'),
]
P = sum(q * w for _, q, w, _ in LOSS)
AIR = 0.335        # W per (m3/h K)
WALL = 4.4         # W/K, 0.8 m2 x 5.5 (mechanical session estimate)
rows = ['| 項目 | 數量 | 每個 W | 小計 W | 來源 |', '|---|---|---|---|---|'] + ['| %s | %d | %g | %g | %s |' % (a, q, w, q * w, s) for a, q, w, s in LOSS]
dt = lambda Pw, Q: Pw / (AIR * Q + WALL)
md = ['# 立柱電箱散熱計算', '', '座標與空間來源：機構 session `docs/handoff_electrical_box_v14.md`。', '',
      '## 發熱（最壞情況：三軸都在額定輸出、主軸有載）', ''] + rows + ['| **合計** | | | **%g** | |' % P, '',
      '三台伺服以手冊值計（35 W，不是機構文件估的 25 W）。PC IOTA 與 12 V 電源（owner 決定）**放在箱內**，佔 67 W；若 PC 改放箱外，總發熱降為 %g W。' % (P - 67), '',
      '## 風扇與溫升', '', '公式：ΔT = P ÷ (0.335 × 風量[m³/h] + 箱壁自然散熱 %.1f W/K)（箱壁 0.8 m² × 5.5 W/m²K，機構文件的估算）' % WALL, '',
      '| 風量 | 箱內溫升（%g W） | 環境 35 °C 時箱內 | 備註 |' % P, '|---|---|---|---|']
for Q, note in ((0, '不裝風扇'), (30, '機構文件的 80~92 mm 風扇'), (60, '92 mm 風扇'), (100, '建議：120 mm 24V 風扇 ≥ 100 m³/h')):
    d = dt(P, Q); md.append('| %d m³/h | %.1f K | %.0f °C | %s |' % (Q, d, 35 + d, note))
md += ['', '- 手冊：MR-J4 環境 0~55 °C；**緊貼安裝要 ≤ 45 °C 或 ≤ 75% 負載**（環境規格表備註 2）。我們左右留 10 mm，不算緊貼，但箱內 ≤ 45 °C 較保險 → 環境 35 °C 時要風量 ≥ 100 m³/h（濾網損失後）。',
       '- PC 在箱內：%g W 在 60 m³/h 下 ΔT = %.1f K（箱內約 %.0f °C，環境 35 °C）；在 100 m³/h 下 %.1f K。若 PC 發熱沒到 60 W（多數時間低很多），溫升會更低。' % (P, dt(P, 60), 35 + dt(P, 60), dt(P, 100)),
       '- 風扇 **型號採購時依規格書選**（120×120×25 mm、24 V、≥ 100 m³/h、含進出風濾網；濾網會降風量約 20~30%）。我沒查到可驗證的型號，不亂報。',
       '- 進風：後牆 x -280, z 400（120 mm 風扇 + 濾網，開孔 Ø110，風扇 x -340..-220、z 340..460；頂板後折邊蓋住 z 471..491，所以風扇在它下方）；出風：後牆 x 125..215, z 459..484，濾網 90×25（在變頻器上方）。進出風口相距 345 mm，空氣由左後吸入、橫過電料與伺服、由右後上方排出；底蓋不開進風口（朝加工區，油霧）。',
       '- 風扇故障沒有偵測：先不加（精簡）；建議之後在 PSU1 的 DC OK 繼電器接點旁加溫度開關。',
       '- 以上都是估算；實機要用溫度計量箱內最熱點（伺服上方）。']
open(os.path.join(HERE, 'HEAT.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print('total %g W' % P)

# ---------------- views (SVG): front view looking at the back wall (+y), plan view from above
COLS = {'SV': '#f85149', 'AIRV': '#00c0c0', 'VFD': '#ff7b72', 'PSU': '#3fb950', 'RCD': '#e3b341', 'QF': '#e3b341', 'KM': '#58a6ff', 'DC': '#8b949e', 'KA': '#d2a8ff', 'XT': '#ffa657', 'BD': '#56d364', 'X1': '#ffa657', 'FL': '#cccccc', 'PC': '#a371f7'}
def col(d): return next(c for k, c in COLS.items() if d.startswith(k))
def view(title, ax_h, ax_v, flip_v, ox, oy, sc, parts, out):
    # ax: 0=x,1=y,2=z ; horizontal axis x, vertical axis z (front) or y (plan)
    for p in parts:
        b = bb(p); h0, h1 = b[2*ax_h], b[2*ax_h+1]; v0, v1 = b[2*ax_v], b[2*ax_v+1]
        X = ox + (h0 - x0e) * sc; Wd = (h1 - h0) * sc
        Y = oy + ((v0 - (z0e if ax_v == 2 else y0e)) * sc if not flip_v else ((z1e if ax_v == 2 else y1e) - v1) * sc); Ht = (v1 - v0) * sc
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="%s" stroke="#222"/>' % (X, Y, Wd, Ht, col(p[1]), '0.25' if p[1] == 'FL2' else '0.8'))
        out.append('<text x="%.1f" y="%.1f" font-size="9" text-anchor="middle">%s</text>' % (X + Wd / 2, Y + Ht / 2 + 3, p[1]))
sc = 1.2; W = int(760 * sc) + 120; Hh = int(238 * sc + 240 * sc) + 240
o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="Noto Sans CJK TC, sans-serif"><rect width="100%%" height="100%%" fill="#fff"/>' % (W, Hh),
     '<text x="20" y="24" font-size="16" font-weight="bold">立柱電箱佈置（機台座標，x -380..380）</text>']
o.append('<text x="60" y="48" font-size="12">上：正視後牆（從前方 -y 看向 +y；x 向右，z 向上），後牆上的零件與屋頂零件（淡色為掛在屋頂的零件）</text>')
o.append('<rect x="60" y="60" width="%d" height="%d" fill="#f4f4f4" stroke="#000" stroke-width="2"/>' % (760 * sc, 238 * sc))
view('front', 0, 2, True, 60, 60, sc, [p for p in L.PARTS], o)
y2 = 60 + 238 * sc + 50
o.append('<text x="60" y="%d" font-size="12">下：俯視（x 向右，y 向上：後牆在最上方，前方 y 255 在最下方）</text>' % (y2 - 8))
o.append('<rect x="60" y="%d" width="%d" height="%d" fill="#f4f4f4" stroke="#000" stroke-width="2"/>' % (y2, 760 * sc, 240 * sc))
view('plan', 0, 1, True, 60, y2, sc, [p for p in L.PARTS], o)
for nm, x, y, z, why in L.OPENINGS:
    if nm == 'roof' or nm == 'bottom cover':
        X = 60 + (x - x0e) * sc; Y = y2 + (y1e - y) * sc
        o.append('<circle cx="%.1f" cy="%.1f" r="6" fill="none" stroke="#c00" stroke-width="2"/><text x="%.1f" y="%.1f" font-size="9" fill="#c00">%s</text>' % (X, Y, X + 8, Y + 3, ('屋頂' if nm == 'roof' else '底蓋') + ':' + why.split('(')[0].split(':')[0][:14]))
o.append('</svg>')
open(os.path.join(HERE, 'column_box_views.svg'), 'w', encoding='utf-8').write('\n'.join(o))
