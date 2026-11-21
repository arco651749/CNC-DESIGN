"""v13 tool-head module concept sketch (spindle + camera + probe in one line along X).
Writes output/v13/toolhead/concept.html; render to PNG with Playwright."""
import os
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'v13', 'toolhead')

# ---- concept numbers (mm, machine frame of v12: spindle axis x0 y-20, tool tip z180 at home)
SY = -20.0; TIP = 180.0
CX = -70.0                      # camera axis (left)
PX = 85.0                       # probe axis (right)  -- decided: option C 70/85
WD = 110.0
H = WD - abs(CX)                # lens front above tool tip -> path = H + D = 110
LF = TIP + H                    # lens front z
LENS_L, LENS_R = 139.1, 17.5
PL = (-100, 108, 300, 520)      # module plate x0,x1,z0,z1 (y 20..32)
SOL = (PX - 20, PX + 20, 335, 445)  # solenoid body
BALL_R, BALL_E = TIP + 50, TIP - 10

C = dict(plate='#cfd8e3', plates='#5b6b7d', sp='#b9bec4', sps='#4a4f55', cam='#2b2b2b', lens='#3a3f44',
         probe='#e0a020', sol='#5a3e2b', clamp='#9aa7b4', zs='#888', red='#d62728', blue='#1f77b4', grn='#2ca02c')

class View:
    def __init__(s, x0, x1, v0, v1, k, ox, oy):
        s.x0, s.x1, s.v0, s.v1, s.k, s.ox, s.oy = x0, x1, v0, v1, k, ox, oy
        s.w, s.h = (x1 - x0) * k, (v1 - v0) * k
        s.e = []
    def P(s, x, v): return s.ox + (x - s.x0) * s.k, s.oy + (s.v1 - v) * s.k
    def rect(s, x0, x1, v0, v1, fill, stroke='#333', sw=1, extra=''):
        a, b = s.P(min(x0, x1), max(v0, v1))
        s.e.append(f'<rect x="{a:.1f}" y="{b:.1f}" width="{abs(x1-x0)*s.k:.1f}" height="{abs(v1-v0)*s.k:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def circ(s, x, v, r, fill, stroke='#333', sw=1, extra=''):
        a, b = s.P(x, v)
        s.e.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{r*s.k:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def line(s, x0, v0, x1, v1, col='#333', sw=1, dash=''):
        a, b = s.P(x0, v0); c, d = s.P(x1, v1)
        da = f' stroke-dasharray="{dash}"' if dash else ''
        s.e.append(f'<line x1="{a:.1f}" y1="{b:.1f}" x2="{c:.1f}" y2="{d:.1f}" stroke="{col}" stroke-width="{sw}"{da}/>')
    def poly(s, pts, fill, stroke='#333', sw=1):
        p = ' '.join('%.1f,%.1f' % s.P(x, v) for x, v in pts)
        s.e.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def text(s, x, v, t, size=12, col='#222', anchor='start', bold=False, dy=0):
        a, b = s.P(x, v)
        s.e.append(f'<text x="{a:.1f}" y="{b+dy:.1f}" font-size="{size}" fill="{col}" text-anchor="{anchor}"{" font-weight=\"700\"" if bold else ""}>{t}</text>')
    def dim(s, x0, v0, x1, v1, t, off=0, col=C['blue'], horiz=True):
        # simple dimension line with arrows-ish ticks
        s.line(x0, v0, x1, v1, col, 1)
        for x, v in ((x0, v0), (x1, v1)):
            if horiz: s.line(x, v - 4, x, v + 4, col, 1)
            else: s.line(x - 4, v, x + 4, v, col, 1)
        mx, mv = (x0 + x1) / 2, (v0 + v1) / 2
        if horiz: s.text(mx, mv, t, 12, col, 'middle', dy=-4)
        else: s.text(mx + 5, mv, t, 12, col, 'start', dy=4)

def front():
    v = View(-200, 175, 145, 560, 1.0, 20, 60)
    # Z slide plate behind (dashed)
    v.rect(-110, 110, 317, 547, 'none', C['zs'], 1, 'stroke-dasharray="6 4"')
    v.text(-108, 545, 'Z 滑台（後方）', 11, C['zs'], dy=14)
    v.rect(*PL, C['plate'], C['plates'], 1.5)
    v.text(PL[0] + 3, PL[3] - 3, '模組底板', 12, C['plates'], 'start', True, dy=14)
    # spindle
    v.rect(-32.5, 32.5, 221, 409, C['sp'], C['sps']); v.rect(-32.5, 32.5, 409, 435, '#9da3a9', C['sps'])
    v.rect(-11, 11, 216, 221, '#777'); v.rect(-2.5, 2.5, TIP, 202, '#c9a227', '#7a6010')
    v.rect(-48, 48, 331, 405, C['clamp'], C['plates'], 1, 'fill-opacity=".85"')
    v.text(0, 368, '主軸夾座 Ø65 H7', 11, '#123', 'middle')
    v.text(0, 300, '主軸', 13, '#222', 'middle', True)
    # camera
    v.rect(CX - LENS_R, CX + LENS_R, LF, LF + LENS_L, C['lens'], '#111')
    v.rect(CX - 15, CX + 15, LF + LENS_L, LF + LENS_L + 5, '#555')
    v.rect(CX - 14.5, CX + 14.5, LF + LENS_L + 5, LF + LENS_L + 24.4, '#2c64b0', '#123')
    pz = LF + 91.47 - 6.55
    v.rect(CX - 86, CX - LENS_R, pz - 5.5, pz + 5.5, '#ffd84a', '#8a6d00')
    v.text(CX - 88, pz + 8, '同軸照明光導管', 10, '#6a5300', 'start', dy=-6)
    v.rect(CX - 26, PL[0] - 0, LF + 106, LF + 126, '#7d8a97', C['plates'])
    v.text(CX, LF + LENS_L + 40, '相機', 13, '#222', 'middle', True)
    v.text(CX, LF + LENS_L + 54, 'daA2448 + MML05', 10, '#555', 'middle')
    # probe
    v.rect(PX - 6, PX + 6, 228, 327, '#999', '#555')            # rail
    v.rect(PX - 17, PX + 17, 281, 335, '#7d8a97', C['plates'])   # holder/block
    v.rect(PX - 16.5, PX + 16.5, 255, 297, C['probe'], '#7a5200')
    v.rect(PX - 2, PX + 2, BALL_R + 3, 255, '#aaa'); v.circ(PX, BALL_R + 3, 3, C['red'], '#600')
    v.rect(*SOL, C['sol'], '#2a1a10'); v.rect(PX - 4, PX + 4, SOL[3], SOL[3] + 40, '#888')
    v.text(SOL[1] + 4, 420, '推拉', 11, C['sol'], 'start', True)
    v.text(SOL[1] + 4, 405, '電磁鐵', 11, C['sol'], 'start', True)
    v.text(SOL[1] + 4, 390, '行程 60', 10, C['sol'], 'start')
    v.text(PX + 22, 270, '探棒', 13, '#222', 'start', True)
    # probe extended ghost
    v.rect(PX - 16.5, PX + 16.5, 195, 237, 'none', C['probe'], 1.2, 'stroke-dasharray="4 3"')
    v.line(PX, 195, PX, BALL_E + 3, C['probe'], 1.2, '4 3'); v.circ(PX, BALL_E + 3, 3, 'none', C['red'], 1.2)
    # reference lines
    v.line(-195, TIP, 170, TIP, C['grn'], 1, '5 4'); v.text(-195, TIP, '刀尖 z180', 10, C['grn'], 'start', dy=-4)
    v.line(CX - 25, LF, CX + 25, LF, C['red'], 1, '3 3')
    v.dim(CX, 166, 0, 166, '70', horiz=True)
    v.dim(0, 154, PX, 154, '%d' % PX, horiz=True)
    v.dim(CX - 30, TIP, CX - 30, LF, 'h=%d' % H, horiz=False)
    v.text(PX + 22, BALL_R, '球 +50（收）', 10, C['red'], 'start', dy=4)
    v.text(PX + 22, BALL_E, '球 −10（伸）', 10, C['red'], 'start', dy=4)
    return v, '正視圖（從前面看）'

def top():
    v = View(-200, 165, -95, 140, 1.0, 20, 60)
    v.rect(-110, 110, 34, 62, 'none', C['zs'], 1, 'stroke-dasharray="6 4"')
    for x in (-80, 80): v.rect(x - 10, x + 10, 88.5, 104, 'none', C['zs'], 1, 'stroke-dasharray="6 4"')
    v.text(0, 120, 'Z 滑台／滑軌（龍門側）', 11, C['zs'], 'middle')
    v.rect(PL[0], PL[1], 20, 32, C['plate'], C['plates'], 1.5)
    v.text(PL[1], 26, '底板', 11, C['plates'], 'start', dy=4)
    v.rect(-48, 48, -63, 20, C['clamp'], C['plates'])
    v.circ(0, SY, 32.5, C['sp'], C['sps'], 1.5); v.circ(0, SY, 2.5, '#c9a227')
    v.rect(CX - 26, CX + 0, -2.5, 20, '#7d8a97', C['plates'])   # cam bracket arm
    v.circ(CX, SY, LENS_R, C['lens'], '#111'); v.rect(CX - 14.5, CX + 14.5, SY - 14.5, SY + 14.5, '#2c64b0', '#123', 1, 'fill-opacity=".6"')
    v.rect(CX - 86, CX - LENS_R, SY - 5.5, SY + 5.5, '#ffd84a', '#8a6d00')
    v.rect(PX - 6, PX + 6, -3, 20, '#999', '#555')
    v.rect(*SOL[:2], SY - 22.5 + 0, SY + 22.5, C['sol'], '#2a1a10', 1, 'fill-opacity=".35"')
    v.circ(PX, SY, 16.5, C['probe'], '#7a5200')
    v.line(-195, SY, 135, SY, C['red'], 1.5, '8 4')
    v.text(-195, -42, '三個中心', 12, C['red'], 'start', True)
    v.text(-195, -56, '同一條線 y −20', 12, C['red'], 'start', True)
    v.dim(120, -63, 120, 32, '深 95', horiz=False)
    v.text(CX, -55, '相機', 12, '#222', 'middle', True); v.text(0, -78, '主軸', 12, '#222', 'middle', True)
    v.text(PX, -55, '探棒', 12, '#222', 'middle', True)
    v.text(-20, -92, '最前端 y −63（v12 是 −126）', 11, C['blue'], 'start')
    return v, '俯視圖（排成 X 方向一條線）'

def measure():
    v = View(-245, -95, 95, 420, 1.0, 20, 60)
    cx = -135.0  # carriage x at measuring pose
    tip = 140.0; lf = tip + H
    v.rect(-245, -95, 70, 110, '#d9dde1', '#555'); v.text(-170, 86, '工作台左緣', 10, '#444')
    v.line(-220, 70, -220, 110, '#555', 1)
    v.rect(-213, -197, 110, 130, '#333')                         # holder
    v.poly([(-215, 130), (-195, 130), (-215, 150)], '#9fd3ff', '#1d5e8c', 1.2)
    v.line(-215, 150, -195, 130, '#1d5e8c', 2.5)
    cam = cx + CX
    v.rect(cam - LENS_R, cam + LENS_R, lf, lf + LENS_L, C['lens'], '#111')
    v.rect(cam - 14.5, cam + 14.5, lf + LENS_L + 5, lf + LENS_L + 24.4, '#2c64b0', '#123')
    v.rect(cx - 32.5, cx + 32.5, tip + 41, tip + 41 + 190, C['sp'], C['sps'], 1, 'fill-opacity=".8"')
    v.rect(cx - 11, cx + 11, tip + 36, tip + 41, '#777'); v.rect(cx - 2.5, cx + 2.5, tip, tip + 22, '#c9a227', '#7a6010')
    v.line(cam, lf, cam, 140, C['red'], 2, '5 3'); v.line(cam, 140, cx - 2.5, 140, C['red'], 2, '5 3')
    v.circ(cx, tip, 3, C['red'], '#600')
    v.dim(cam, 122, cx, 122, 'D=70', col=C['red'])
    v.dim(cam + 22, 140, cam + 22, lf, '%d' % H, col=C['red'], horiz=False)
    v.text(-240, 410, '稜鏡在台面左緣，不佔工作區', 11, '#1d5e8c', 'start', True)
    v.text(-240, 395, '光路 %d + 70 = 110（=WD）' % H, 11, C['red'], 'start')
    v.text(-240, 380, 'X 到 −135、Z 下 40', 11, '#333', 'start')
    return v, '量刀時（正視）'

def compareB():
    v = View(-110, 170, -205, 120, 0.8, 20, 60)
    v.rect(-110, 110, 34, 62, 'none', C['zs'], 1, 'stroke-dasharray="6 4"')
    v.rect(-78, 78, 20, 32, C['plate'], C['plates'])
    v.circ(0, SY, 32.5, C['sp'], C['sps']); v.circ(0, -100, LENS_R, C['lens'], '#111'); v.circ(0, -175, 16.5, C['probe'], '#7a5200')
    v.line(0, 30, 0, -195, C['red'], 1.2, '6 4')
    v.dim(70, -192, 70, 32, '深 224', horiz=False)
    v.text(-75, -200, '前後一條線：懸臂多一倍以上，', 11, '#a00', 'start', dy=16)
    v.text(-75, -200, 'Z 底板扭矩、振動都變大', 11, '#a00', 'start', dy=30)
    return v, '對照：排 Y 方向（不建議）'

def svg(view_t):
    v, title = view_t
    W, Hh = v.w + 40, v.h + 90
    return (f'<svg width="{W:.0f}" height="{Hh:.0f}" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">'
            f'<rect x="1" y="1" width="{W-2:.0f}" height="{Hh-2:.0f}" fill="#fff" stroke="#ccc"/>'
            f'<text x="{W/2:.0f}" y="30" font-size="17" font-weight="700" text-anchor="middle">{title}</text>' + ''.join(v.e) + '</svg>')

def main():
    os.makedirs(OUT, exist_ok=True)
    notes = ('<ul style="font:13px/1.6 sans-serif;margin:6px 24px 14px;color:#222">'
             f'<li>模組 = 一塊底板（取代 Spindle_mount_plate，保留樞軸＋滾轉微調，只為主軸調垂直度）＋主軸夾座＋相機座＋探棒滑台＋電磁鐵，桌上先組好、整組裝上 Z 滑台；調完主軸垂直度後，再校正相機、探棒對主軸的偏移量。</li>'
             f'<li>相機在左 {abs(CX):.0f}、探棒在右 {PX:.0f}，三個中心都在 y −20。相機距離 D={abs(CX):.0f} → 鏡頭前緣高刀尖 {H:.0f}（光路 {H:.0f}+{abs(CX):.0f}=110），鏡頭不會低於主軸鼻端。</li>'
             '<li>稜鏡改成往 +X 反射，固定在台面左緣：量刀時 X 到 −135，稜鏡完全在工作區外。</li>'
             '<li>代價：每個工具都有 X 偏移 → 已決定 X 行程加長 155（70+85），三樣都能走遍工作區。</li>'
             '<li>外罩：相機、電磁鐵用鈑金罩包住，鏡頭前加保護玻璃＋吹氣；線材集中到模組頂部一個接頭板。</li></ul>')
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>v13 工具頭模組</title></head>'
            '<body style="margin:0;background:#fff">'
            '<div style="font:700 21px sans-serif;margin:14px 22px 2px">v13 工具頭模組（主軸＋相機＋探棒 一條線）簡圖</div>'
            + notes +
            '<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 12px 12px">'
            + svg(front()) + svg(top()) + svg(measure()) + svg(compareB()) + '</div></body></html>')
    p = os.path.join(OUT, 'concept.html')
    open(p, 'w').write(html); print('wrote', p, 'H=%.0f LF=%.0f' % (H, LF))

main()
