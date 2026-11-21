"""v13 tool-head spacing options: camera distance D / probe distance P, front views.
Writes output/v13/toolhead/spacing_options.html"""
import os, importlib.util
here = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location('c', os.path.join(here, '00_toolhead_concept_sketch.py'))
src = open(os.path.join(here, '00_toolhead_concept_sketch.py')).read().replace('\nmain()\n', '\n')
ns = {'__file__': os.path.join(here, '00_toolhead_concept_sketch.py')}; exec(src, ns)
View, C, OUT = ns['View'], ns['C'], ns['OUT']
TIP, NOSE, LR, CW = 180.0, 216.0, 17.5, 48.0

def panel(tag, D, P, note):
    h = 110 - D; lf = TIP + h
    v = View(-125, 135, 120, 470, 1.0, 20, 70)
    # spindle + clamp
    v.rect(-32.5, 32.5, 221, 435, C['sp'], C['sps']); v.rect(-11, 11, 216, 221, '#777')
    v.rect(-2.5, 2.5, TIP, 202, '#c9a227', '#7a6010')
    v.rect(-CW, CW, 331, 405, C['clamp'], C['plates'], 1, 'fill-opacity=".9"')
    v.text(0, 372, '夾座寬 96', 11, '#123', 'middle')
    # camera lens + shroud
    cx = -D
    v.rect(cx - LR, cx + LR, lf, lf + 139, C['lens'], '#111')
    v.rect(cx - LR - 4, cx + LR + 4, lf - 2, 460, 'none', '#7a3db8', 1.3, 'stroke-dasharray="5 3"')
    v.text(cx - LR - 6, 452, '外罩', 10, '#7a3db8', 'end')
    # probe + solenoid
    v.rect(P - 20, P + 20, 335, 445, C['sol'], '#2a1a10')
    v.rect(P - 17, P + 17, 281, 335, '#7d8a97', C['plates'])
    v.rect(P - 16.5, P + 16.5, 255, 297, C['probe'], '#7a5200')
    v.rect(P - 2, P + 2, 233, 255, '#aaa'); v.circ(P, 233, 3, C['red'], '#600')
    v.rect(P - 20 - 4, P + 20 + 4, 230, 460, 'none', '#7a3db8', 1.3, 'stroke-dasharray="5 3"')
    # gaps between clamp and lens / solenoid (at clamp height)
    g1 = (cx + LR) ; g2 = P - 20
    v.rect(g1, -CW, 340, 396, '#ff4d4d', 'none', 0, 'fill-opacity=".35"')
    v.rect(CW, g2, 340, 396, '#ff4d4d', 'none', 0, 'fill-opacity=".35"')
    v.text((g1 - CW) / 2, 412, '%.1f' % (-CW - g1), 12, '#c00', 'middle', True)
    v.text(g2 - 2, 412, '%.0f' % (g2 - CW), 12, '#c00', 'end', True)
    # lines: tip, nose, lens front
    v.line(-120, TIP, 130, TIP, C['grn'], 1, '5 4'); v.text(130, TIP, '刀尖', 10, C['grn'], 'end', dy=13)
    v.line(-40, NOSE, 40, NOSE, '#555', 1, '3 3'); v.text(40, NOSE, '主軸鼻端', 10, '#555', 'start', dy=4)
    v.line(cx - 30, lf, cx + 30, lf, C['red'], 1.2, '3 3')
    v.dim(cx - 28, TIP, cx - 28, lf, '%d' % h, col=C['red'], horiz=False)
    v.dim(cx, 160, 0, 160, 'D=%d' % D, horiz=True)
    v.dim(0, 140, P, 140, 'P=%d' % P, horiz=True)
    rel = '比鼻端高 %d' % (lf - NOSE) if lf >= NOSE else '比鼻端低 %d' % (NOSE - lf)
    W = v.w + 40
    head = (f'<text x="{W/2:.0f}" y="28" font-size="18" font-weight="700" text-anchor="middle">{tag}</text>'
            f'<text x="{W/2:.0f}" y="50" font-size="13" text-anchor="middle" fill="#333">鏡頭前緣高刀尖 {h}（{rel}）</text>')
    foot_y = v.h + 95
    foot = ''.join(f'<text x="20" y="{foot_y + 18*i:.0f}" font-size="13" fill="{c}">{t}</text>' for i, (t, c) in enumerate([
        ('相機和夾座間隙 %.1f mm，探棒和夾座 %d mm' % (-CW - g1, g2 - CW), '#c00'),
        ('X 行程要加 %d + %d = %d mm' % (D, P, D + P), C['blue']),
        (note, '#333')]))
    Hh = foot_y + 18 * 3 + 6
    return (f'<svg width="{W:.0f}" height="{Hh:.0f}" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">'
            f'<rect x="1" y="1" width="{W-2:.0f}" height="{Hh-2:.0f}" fill="#fff" stroke="#ccc"/>' + head + ''.join(v.e) + foot + '</svg>')

def why():
    v = View(-120, 95, 100, 330, 1.0, 20, 60)
    D = 70; h = 40; tip = 150
    v.rect(-120, 95, 100, 110, '#d9dde1', '#555')
    v.poly([(-80, 130), (-60, 130), (-80, 150)], '#9fd3ff', '#1d5e8c')
    v.line(-80, 150, -60, 130, '#1d5e8c', 2.5)
    v.rect(-70 - LR, -70 + LR, 140 + h, 320, C['lens'], '#111')
    v.rect(-2.5, 2.5, 140, 165, '#c9a227', '#7a6010')
    v.line(-70, 140 + h, -70, 140, C['red'], 2, '5 3'); v.line(-70, 140, -2.5, 140, C['red'], 2, '5 3')
    v.dim(-100, 140, -100, 140 + h, '110−D', col=C['red'], horiz=False)
    v.dim(-70, 120, 0, 120, 'D', col=C['red'])
    v.text(-35, 300, '鏡頭焦距固定 110：', 12, '#222', bold=True)
    v.text(-35, 282, '往下 + 橫向 = 110', 12, C['red'])
    v.text(-35, 264, 'D 越大 → 鏡頭越低', 12, '#222')
    W, Hh = v.w + 40, v.h + 90
    return (f'<svg width="{W:.0f}" height="{Hh:.0f}" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">'
            f'<rect x="1" y="1" width="{W-2:.0f}" height="{Hh-2:.0f}" fill="#fff" stroke="#ccc"/>'
            f'<text x="{W/2:.0f}" y="30" font-size="17" font-weight="700" text-anchor="middle">D 和鏡頭高度的關係</text>' + ''.join(v.e) + '</svg>')

html = ('<!doctype html><html><head><meta charset="utf-8"><title>v13 間距選項</title></head><body style="margin:0;background:#fff">'
        '<div style="font:700 21px sans-serif;margin:14px 22px 2px">第 2 題：相機距離 D、探棒距離 P 要設多少？（正視圖，從前面看）</div>'
        '<div style="font:13px/1.6 sans-serif;margin:4px 22px 8px;color:#333">紅色區塊＝零件和主軸夾座之間的間隙（外罩、螺絲、線材都要塞在這裡）；紫色虛線＝外罩。'
        '間距加大 → 好做外罩和拆裝，但鏡頭變低、X 行程要加更多。</div>'
        '<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 12px 12px">'
        + why()
        + panel('A. 70 / 75（最緊湊）', 70, 75, '外罩只能用 1 mm 鈑金貼著鏡頭')
        + panel('B. 80 / 85（各放寬 10）', 80, 85, '外罩、螺絲好做；鏡頭和 v12 一樣低')
        + panel('C. 70 / 85（相機近、探棒寬）', 70, 85, '鏡頭維持高；電磁鐵、滑台有空間')
        + '</div></body></html>')
p = os.path.join(OUT, 'spacing_options.html'); open(p, 'w').write(html); print('wrote', p)
