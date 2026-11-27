# -*- coding: utf-8 -*-
"""Front view of the base cabinet plate (SVG).  python3 base_cabinet/build.py"""
import os
import layout as L
HERE = os.path.dirname(os.path.abspath(__file__))
COL = {'RCD': '#e3b341', 'QF2': '#e3b341', 'QF3': '#e3b341', 'QF4': '#e3b341', 'KM1': '#58a6ff', 'X0': '#ffa657', 'FL2': '#cccccc'}
NM = {'RCD': 'RCD 漏電斷路器', 'QF2': 'QF2 伺服(共用)', 'QF3': 'QF3 變頻器', 'QF4': 'QF4 電源', 'KM1': 'KM1 接觸器(共用)', 'X0': 'X0 進線 / PE / 出線端子', 'FL2': 'FL2 濾波器(預留)'}
parts, h = L.place(); S = 2.0; M = 60
W, H = L.PLATE_W * S + 2 * M, L.PLATE_H * S + 2 * M + 70
o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="Noto Sans CJK TC, sans-serif"><rect width="100%%" height="100%%" fill="#fff"/>' % (W, H),
     '<text x="20" y="26" font-size="18" font-weight="bold">底座電箱（保護類）安裝板佈置：%d×%d 板，箱體 %d×%d×%d</text>' % (L.PLATE_W, L.PLATE_H, L.CAB_W, L.CAB_H, L.CAB_D),
     '<text x="20" y="46" font-size="12" fill="#555">從前面看（開門）。灰條 = 35 mm DIN 軌，綠條 = 配線槽。急停與啟動在另一個操作盒。尺寸為估算</text>',
     '<rect x="%d" y="%d" width="%d" height="%d" fill="#f2f2f2" stroke="#222" stroke-width="2"/>' % (M, M, L.PLATE_W * S, L.PLATE_H * S)]
y = L.MARGIN
for title, keys in L.ROWS:
    hm = max(L.PARTS[k][3] for k in keys)
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#cfe8cf" stroke="#6a6"/>' % (M + 10, M + (y + 2) * S, (L.PLATE_W - 20) * S, 12))
    y += L.DUCT
    o.append('<rect x="%d" y="%d" width="%d" height="14" fill="#999"/>' % (M + 10, M + (y + hm / 2 - 7) * S, (L.PLATE_W - 20) * S))
    y += hm
o.append('<rect x="%d" y="%d" width="%d" height="12" fill="#cfe8cf" stroke="#6a6"/>' % (M + 10, M + (y + 4) * S, (L.PLATE_W - 20) * S))
for p in parts:
    X, Y = M + p['x'] * S, M + p['y'] * S
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="%s" stroke="#222"/>' % (X, Y, p['w'] * S, p['h'] * S, COL[p['key']], '0.4' if p['key'] == 'FL2' else '0.85'))
    o.append('<text x="%.1f" y="%.1f" font-size="12" text-anchor="middle" font-weight="bold">%s</text><text x="%.1f" y="%.1f" font-size="10" text-anchor="middle">%dx%d</text>' % (X + p['w'] * S / 2, Y + p['h'] * S / 2 - 2, NM[p['key']].split(' ')[0], X + p['w'] * S / 2, Y + p['h'] * S / 2 + 12, p['w'], p['h']))
    o.append('<text x="%.1f" y="%.1f" font-size="10" text-anchor="middle" fill="#333">%s</text>' % (X + p['w'] * S / 2, Y + p['h'] * S + 12, NM[p['key']].split(' ', 1)[1] if ' ' in NM[p['key']] else ''))
o.append('<text x="%d" y="%d" font-size="11" fill="#333">板高用 %d / %d mm</text></svg>' % (M, H - 14, h, L.PLATE_H))
open(os.path.join(HERE, 'panel_layout.svg'), 'w', encoding='utf-8').write('\n'.join(o))
