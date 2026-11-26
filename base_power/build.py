# -*- coding: utf-8 -*-
"""Panel layout (SVG), isometric view of base + cabinet (SVG) and cable list (CSV).  python3 base_power/build.py"""
import csv, math, os
import layout as L

HERE = os.path.dirname(os.path.abspath(__file__))
COL = {'QF': '#e3b341', 'KM': '#58a6ff', 'PSU1': '#3fb950', 'PSU2': '#3fb950', 'KA': '#d2a8ff', 'DC1': '#8b949e', 'SV': '#f85149',
       'VFD': '#ff7b72', 'FL': '#79c0ff', 'FLV': '#79c0ff', 'TB': '#ffa657', 'BD': '#56d364', 'TBP': '#ffa657', 'FLS': '#79c0ff', 'PC': '#a371f7', 'XT': '#ffa657', 'PSU': '#3fb950'}


# ------------------------------------------------------------------ 1. panel layout
def panel_svg():
    parts, rep, ok = L.place()
    S = 1.0; M = 70
    W, H = L.PLATE_W * S + 2 * M, L.PLATE_H * S + 2 * M + 150
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Noto Sans CJK TC, sans-serif">' % (W, H, W, H),
         '<rect width="100%" height="100%" fill="#fff"/>']
    o.append('<text x="%d" y="30" font-size="20" font-weight="bold">電控箱 = 背板（%d × %d mm 安裝板，箱體 %d × %d × %d）</text>' % (M, L.PLATE_W, L.PLATE_H, L.CAB_W, L.CAB_H, L.CAB_D))
    o.append('<text x="%d" y="50" font-size="12" fill="#555">視角：開門看箱內（箱體在底座右側，門朝 +x）。* 為估算尺寸，下單前以廠商圖面確認。灰條 = 35 mm DIN 軌，綠條 = 配線槽</text>' % M)
    ox, oy = M, M
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#f2f2f2" stroke="#222" stroke-width="2"/>' % (ox, oy, L.PLATE_W, L.PLATE_H))
    # rows: draw rails and ducts
    y = L.MARGIN
    for rid, title, items in L.rows():
        top = L.SERVO_TOP if rid == 'R3' else L.DUCT
        o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#cfe8cf" stroke="#6a6"/>' % (ox + 10, oy + y, L.PLATE_W - 20, 18))   # duct above (18 high slot)
        o.append('<text x="%d" y="%d" font-size="10" fill="#363">duct</text>' % (ox + 14, oy + y + 13))
        y += top
        h = max(L.P[k][3] for k, n in items)
        if rid in ('R1', 'R2'):
            o.append('<rect x="%d" y="%d" width="%d" height="9" fill="#999"/>' % (ox + 10, oy + y + h / 2 - 4, L.PLATE_W - 20))
        o.append('<text x="%d" y="%d" font-size="10" fill="#555" transform="rotate(-90 %d %d)">%s</text>' % (ox - 8, oy + y + h, ox - 8, oy + y + h, title))
        y += h
    o.append('<rect x="%d" y="%d" width="%d" height="18" fill="#cfe8cf" stroke="#6a6"/>' % (ox + 10, oy + y + 3, L.PLATE_W - 20))
    for p in parts:
        c = COL[p['key']]
        o.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" fill="%s" fill-opacity="0.85" stroke="#222"/>' % (ox + p['x'], oy + p['y'], p['w'], p['h'], c))
        lab = p['des'].split('/')[0] if p['key'] in ('QF', 'KM', 'KA', 'SV', 'FL', 'FLV', 'XT') else p['des']
        if p['key'] == 'QF': lab = ['QF1', 'QF2', 'QF3', 'QF4'][p['idx'] - 1]
        if p['key'] == 'KM': lab = 'KM1'
        if p['key'] == 'FLS': lab = 'FL2'
        if p['key'] == 'XT': lab = 'XT'
        if p['key'] == 'PC': lab = 'PC'
        if p['key'] == 'SV': lab = 'SV' + 'XYZ'[p['idx'] - 1]
        if p['key'] in ('FL', 'FLV'): lab = 'FL2' + 'XYZ'[p['idx'] - 1]
        if p['key'] == 'TB': lab = 'TB' + 'XYZ'[p['idx'] - 1]
        if p['key'] == 'KA': lab = ('KA3', 'KA4')[p['idx'] - 1]
        if p['key'] == 'PSU': lab = 'PSU1'
        star = '*' if p['src'] == 'A' else ''
        fs = 9 if p['w'] < 60 else 11
        o.append('<text x="%.1f" y="%.1f" font-size="%d" text-anchor="middle" font-weight="bold">%s%s</text>' % (ox + p['x'] + p['w'] / 2, oy + p['y'] + p['h'] / 2, fs, lab, star))
        o.append('<text x="%.1f" y="%.1f" font-size="8" text-anchor="middle" fill="#222">%dx%d</text>' % (ox + p['x'] + p['w'] / 2, oy + p['y'] + p['h'] / 2 + 11, p['w'], p['h']))
    # servo clearance check
    sv = [p for p in parts if p['key'] == 'SV']
    for p in sv:
        above = [q for q in parts if q['y'] + q['h'] <= p['y'] and q['x'] < p['x'] + p['w'] and q['x'] + q['w'] > p['x']]
        gap = p['y'] - max(q['y'] + q['h'] for q in above) if above else p['y']
        below = L.PLATE_H - (p['y'] + p['h'])
        rep.append('%s%s clearance above %d mm, below %d mm to plate edge (manual: 40 mm)' % (p['des'][:2], 'XYZ'[p['idx'] - 1], gap, below))
    # dims
    o.append('<text x="%d" y="%d" font-size="12" text-anchor="middle">%d</text><line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#222"/>' % (ox + L.PLATE_W / 2, oy + L.PLATE_H + 18, L.PLATE_W, ox, oy + L.PLATE_H + 8, ox + L.PLATE_W, oy + L.PLATE_H + 8))
    # legend / report
    ty = oy + L.PLATE_H + 40
    for i, line in enumerate(rep + ['', '* = 估算尺寸（approx）。M = 三菱手冊值（MR-J4-40A 50×168×135）']):
        o.append('<text x="%d" y="%d" font-size="11" fill="#333" font-family="monospace">%s</text>' % (ox, ty + 14 * i, line.replace('&', '&amp;').replace('<', '&lt;')))
    o.append('</svg>')
    open(os.path.join(HERE, 'panel_layout.svg'), 'w', encoding='utf-8').write('\n'.join(o))
    open(os.path.join(HERE, 'panel_check.txt'), 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
    return rep


# ------------------------------------------------------------------ 2. isometric view of the base
BX, FLOOR = 517.5, -790
BOXES = []   # (x0,x1,y0,y1,z0,z1,color,opacity,label)
def box(x0, x1, y0, y1, z0, z1, c, a=1.0, lab=''): BOXES.append((x0, x1, y0, y1, z0, z1, c, a, lab))

def base_boxes():
    LEG = '#b8bcc4'
    for x, y in [(-BX, -580), (BX, -580), (-BX, 40), (BX, 40), (-BX, 560), (BX, 560)]:
        box(x - 20, x + 20, y - 20, y + 20, FLOOR + 60, -130, LEG)
        box(x - 40, x + 40, y - 40, y + 40, FLOOR, FLOOR + 15, '#444444')
    for x0, x1, y0, y1 in [(-BX - 20, -BX + 20, -560, 540), (BX - 20, BX + 20, -560, 540), (-BX - 20, BX + 20, -600, -560), (-BX - 20, BX + 20, 540, 580)]:
        box(x0, x1, y0, y1, -130, -90, LEG)
    for y in (-120, 168): box(-BX + 20, BX - 20, y - 20, y + 20, -130, -90, LEG)
    LZ = FLOOR + 90                                        # low ring unchanged
    for x0, x1 in ((-BX - 20, -BX + 20), (BX - 20, BX + 20)):
        box(x0, x1, -560, 540, LZ, LZ + 40, LEG)
    box(-BX + 20, BX - 20, -600, -560, LZ, LZ + 40, LEG)       # low front beam kept (no cabinet in the front bay any more)
    # pan
    box(-532.5, 532.5, -595, 575, -90, -85, '#7d8590', 0.5)
    # tank (rear)
    box(-300, 300, 0, 520, FLOOR + 60, FLOOR + 360, '#6e7681', 0.55, 'coolant tank')
    # machine envelope
    box(-420, 420, -420, 330, -85, 40, '#58a6ff', 0.18, 'machine (mechanical session)')
    # electrical cabinet = back plate, floor standing on the right side of the base, door facing +x
    box(L.CAB_X0, L.CAB_X0 + L.CAB_D, L.CAB_Y0, L.CAB_Y0 + L.CAB_W, L.CAB_Z0, L.CAB_Z0 + L.CAB_H, '#cfd8dc', 1, 'electrical cabinet')
    for y in (L.CAB_Y0 + 40, L.CAB_Y0 + L.CAB_W - 40):
        for x in (L.CAB_X0 + 40, L.CAB_X0 + L.CAB_D - 40): box(x - 30, x + 30, y - 30, y + 30, FLOOR, FLOOR + 15, '#444444')
    for z in (-600, -250): box(BX + 20, L.CAB_X0, 0, 60, z - 30, z + 30, '#d29922', 1, 'bracket' if z == -250 else '')

def iso_svg():
    BOXES.clear(); base_boxes()
    e = math.radians(28); k = 0.62
    def pr(x, y, z):
        sx = (x + y) / math.sqrt(2); t = (x - y) / math.sqrt(2)
        return sx * k, -(z * math.cos(e) - t * math.sin(e)) * k
    polys = []
    for (x0, x1, y0, y1, z0, z1, c, a, lab) in BOXES:
        cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        key = (cx - cy) + (cz) * 0.01 + (x1 - x0) * 0
        faces = [([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], 1.0),   # top
                 ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], 0.80),  # front (-y)
                 ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], 0.62)]  # right (+x)
        polys.append((key, faces, c, a, lab, (cx, cy, z1)))
    polys.sort(key=lambda p: p[0])
    def shade(c, f):
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        return '#%02x%02x%02x' % (int(r * f), int(g * f), int(b * f))
    pts_all = [pr(x, y, z) for (x0, x1, y0, y1, z0, z1, *_r) in BOXES for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    mnx = min(p[0] for p in pts_all); mxx = max(p[0] for p in pts_all); mny = min(p[1] for p in pts_all); mxy = max(p[1] for p in pts_all)
    Wd, Ht = mxx - mnx + 120, mxy - mny + 160
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Noto Sans CJK TC, sans-serif"><rect width="100%%" height="100%%" fill="#fff"/>' % (Wd, Ht, Wd, Ht)]
    o.append('<text x="20" y="28" font-size="18" font-weight="bold">底座 + 電控箱（等角視圖，右前上方）</text>')
    for key, faces, c, a, lab, anchor in polys:
        for pts, f in faces:
            P = ' '.join('%.1f,%.1f' % ((pr(*p)[0] - mnx + 60), (pr(*p)[1] - mny + 70)) for p in pts)
            o.append('<polygon points="%s" fill="%s" fill-opacity="%.2f" stroke="#222" stroke-width="0.6"/>' % (P, shade(c, f), a))
        if lab:
            px, py = pr(*anchor)
            o.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="bold" fill="#000">%s</text>' % (px - mnx + 60, py - mny + 62, lab))
    o.append('</svg>')
    open(os.path.join(HERE, 'base_iso.svg'), 'w', encoding='utf-8').write('\n'.join(o))


# ------------------------------------------------------------------ 3. cable list
CABLES = [
 # id, from, to, cable, est length m, notes
 ('W01', '現場電源盤', 'QF1', '3C×5.5 mm² (L1,L2,PE) 起點值', '—', '電工依現場決定；進線從箱體頂部或右側壁 M32 護套'),
 ('W02', 'QF1', 'QF2（三軸共用）, QF3, QF4', '盤內，線徑依 QF2 額定', '盤內', '共用 QF2 的線徑與各台保險絲由電工決定（手冊要求每台各一，見檢查單）'),
 ('W03', 'QF2→KM1→FL2→SV(L1/L3)', 'SVX/Y/Z', '2 mm² (AWG14) 每台一路', '盤內', 'L1/L3，L2 空接；L11/L21 取自 KM1 之前；三路分支若細於 QF2 額定要加保險絲'),
 ('W04', 'QF3', 'VFD (R/S)', '3.5 mm²（起點值）', '盤內', 'MS300 輸入電流未查證'),
 ('M01', 'SVX U/V/W/PE', 'MX 馬達 HG-KR43', '三菱 MR-PWS1CBL□M-A1-L（可動型用 -H）', '5', '預製線，型號待型錄確認；經拖鏈'),
 ('M02', 'SVX CN2', 'MX 編碼器', '三菱 MR-J3ENCBL□M-A1-L/-H', '5', '預製編碼器線，經拖鏈'),
 ('M03', 'SVY U/V/W/PE', 'MY 馬達', '同 M01', '5', '經拖鏈'),
 ('M04', 'SVY CN2', 'MY 編碼器', '同 M02', '5', ''),
 ('M05', 'SVZ U/V/W/PE', 'MZ 馬達（附煞車）', '同 M01', '10', 'Z 軸在龍門柱上，路徑最長'),
 ('M06', 'SVZ CN2', 'MZ 編碼器', '同 M02', '10', ''),
 ('M07', 'KA3 / PSU', 'MZ 煞車', '三菱 MR-BKS1CBL□M-A1-L', '10', '煞車線與動力線分開'),
 ('S01', 'VFD U/V/W/PE', '主軸 SP（4 針航空插頭）', '4C 屏蔽 1.0 mm²（高柔性）', '6', '屏蔽層單端接 PE；經 Z 拖鏈'),
 ('C01', 'BD STEP/DIR', 'TBX/Y/Z → CN1', '自製：CN1 連接器組 MR-J3CN1（3M 10150-3000PE，焊接式）+ 屏蔽雙絞線', '0.5', '不用端子台，一條一條焊；控制板與驅動器同板，脈衝線短'),
 ('C03', 'BD', 'LAN 交換器', 'Cat5e', '2', '盤外 RJ45 穿牆接頭，IP54'),
 ('P01', 'BD HOME X/Y/Z', 'SENS 感測器 ×3', '3C 0.34 mm² 屏蔽，M12 插頭', '4~8', '經拖鏈；X/Y/Z 各一條'),
 ('P02', 'BD PROBE', '探頭 PRB', '3C 屏蔽 0.34 mm²', '6', '經 Z 拖鏈'),
 ('D01', 'PSU1 +24V / KA2', '冷卻泵 PUMP', '2C 1.0 mm²（約 2 A）', '3', '泵在水箱蓋上；有飛輪二極體 DP'),
 ('D02', 'KA5', '吹氣閥 SVL', '2C 0.5 mm²', '6', '經拖鏈'),
 ('E01', 'S1/S2', '操作盒按鈕', '多芯 0.75 mm²', '3', '操作盒裝在底座右前方（待定）'),
 ('G01', '盤內 PE 排', '底座框架、導軌座、盤門', '6~10 mm² 黃綠線 + 編織跳線', '—', '全部接同一個接地點；電工決定'),
]

def cable_csv():
    with open(os.path.join(HERE, 'CABLE_LIST.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['線號', '起點', '終點', '線種', '估算長度 m', '備註'])
        for r in CABLES: w.writerow(r)


if __name__ == '__main__':
    print('\n'.join(panel_svg())); iso_svg(); cable_csv(); print('ok')
