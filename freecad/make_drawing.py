# -*- coding: utf-8 -*-
"""General-arrangement drawing (A1, 1:8, third-angle) from CNC_Gantry.FCStd.
Run: freecadcmd.exe make_drawing.py  -> ../output/CNC_Gantry_GA.svg
"""
import os, re, json, math
import FreeCAD as App, Part, TechDraw
from FreeCAD import Vector as V, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "output")
info = json.load(open(os.path.join(OUT, "cnc_info.json"), encoding="utf-8"))
doc = App.openDocument(os.path.join(OUT, "CNC_Gantry.FCStd"))
objs = [o for o in doc.Objects if o.TypeId == "Part::Feature" and o.Name != "Work_area_300x300"]
coolant = [o for o in objs if o.getParentGroup() and o.getParentGroup().Label.startswith("07")]
comp_all = Part.makeCompound([o.Shape for o in objs])
comp_cool = Part.makeCompound([o.Shape for o in coolant])

S = 1 / 8.0          # drawing scale
W, H = 841, 594      # A1 landscape


def mat(rows):
    m = Matrix()
    (m.A11, m.A12, m.A13), (m.A21, m.A22, m.A23), (m.A31, m.A32, m.A33) = rows
    return m


def nrm(v):
    l = math.sqrt(sum(c * c for c in v)); return [c / l for c in v]


VIEWS = {  # rows: screen-u, screen-v, depth(towards viewer)
    "front": mat([(1, 0, 0), (0, 0, 1), (0, -1, 0)]),
    "right": mat([(0, 1, 0), (0, 0, 1), (1, 0, 0)]),
    "top":   mat([(1, 0, 0), (0, 1, 0), (0, 0, 1)]),
    "iso":   mat([nrm((1, 1, 0)), nrm((-1, 1, 2)), nrm((1, -1, 1))]),
}


def project(shape, view, hidden=False):
    sh = shape.copy(); sh.transformShape(VIEWS[view])
    svg = TechDraw.projectToSVG(sh, V(0, 0, 1), "ShowHiddenLines" if hidden else "")
    paths = re.findall(r'd="([^"]*)"', svg)
    bb = sh.BoundBox
    return paths, (bb.XMin, bb.XMax, bb.YMin, bb.YMax), svg


def place(view, cx, cy, shape=comp_all, color="#000", sw=0.25, extra=""):
    """Put view so model bbox centre lands at sheet (cx,cy). Returns mapper model(u,v)->sheet."""
    paths, (u0, u1, v0, v1), svg = project(shape, view)
    uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
    tx, ty = cx - uc * S, cy + vc * S
    g = [f'<g transform="translate({tx:.2f},{ty:.2f}) scale({S},{-S})" fill="none" stroke="{color}" '
         f'stroke-width="{sw / S:.2f}" stroke-linejoin="round" {extra}>']
    # projectToSVG groups may hold hidden lines in a second <g>; keep only visible group(s)
    for grp in re.findall(r"<g(.*?)</g>", svg, re.S):
        dashed = "stroke-dasharray" in grp
        if dashed:
            continue
        for d in re.findall(r'd="([^"]*)"', grp):
            g.append(f'<path d="{d}"/>')
    g.append("</g>")
    m = lambda u, v: (tx + u * S, ty - v * S)
    return "\n".join(g), m, (u0, u1, v0, v1)


out = []
A = out.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" '
  f'font-family="Arial, Microsoft JhengHei, sans-serif">')
A('<defs><marker id="ar" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" '
  'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,2 L10,5 L0,8 z" fill="#000"/></marker>'
  '<marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="2.5" markerHeight="2.5" '
  'markerUnits="userSpaceOnUse"><circle cx="5" cy="5" r="5" fill="#c00"/></marker></defs>')
A(f'<rect width="{W}" height="{H}" fill="#fff"/>')
A(f'<rect x="20" y="10" width="{W-30}" height="{H-20}" fill="none" stroke="#000" stroke-width="0.7"/>')


def dim(p1, p2, off, txt, horiz=True, fs=3.5):
    """Linear dimension between sheet points p1,p2 offset 'off' (mm on sheet)."""
    (x1, y1), (x2, y2) = p1, p2
    if horiz:
        y = min(y1, y2) + off if off > 0 else min(y1, y2) + off
        y = (y1 if off < 0 else y1) + off
        A(f'<path d="M{x1},{y1} V{y} M{x2},{y2} V{y}" stroke="#000" stroke-width="0.18"/>')
        A(f'<path d="M{x1},{y} H{x2}" stroke="#000" stroke-width="0.25" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        A(f'<text x="{(x1+x2)/2}" y="{y-1.2}" font-size="{fs}" text-anchor="middle">{txt}</text>')
    else:
        x = x1 + off
        A(f'<path d="M{x1},{y1} H{x} M{x2},{y2} H{x}" stroke="#000" stroke-width="0.18"/>')
        A(f'<path d="M{x},{y1} V{y2}" stroke="#000" stroke-width="0.25" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        A(f'<text x="{x-1.2}" y="{(y1+y2)/2}" font-size="{fs}" text-anchor="middle" '
          f'transform="rotate(-90 {x-1.2} {(y1+y2)/2})">{txt}</text>')


def label(x, y, txt, fs=4, anchor="middle", bold=False):
    fw = ' font-weight="bold"' if bold else ""
    txt = str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    A(f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="{anchor}"{fw}>{txt}</text>')


def callout(px, py, tx, ty, n):
    A(f'<path d="M{px},{py} L{tx},{ty}" stroke="#c00" stroke-width="0.25" marker-start="url(#dot)"/>')
    A(f'<circle cx="{tx}" cy="{ty}" r="3.6" fill="#fff" stroke="#c00" stroke-width="0.35"/>')
    A(f'<text x="{tx}" y="{ty+1.4}" font-size="3.8" text-anchor="middle" fill="#c00" font-weight="bold">{n}</text>')


zl, ov, pr = info["z_levels"], info["overall"], info["params"]

# ---------- views (third angle: top above front, right to the right) ----------
FX, FY = 130, 400      # front view centre
RX = 345               # right view centre x
TY = 150               # top view centre y
g, mF, bbF = place("front", FX, FY); A(g)
g, mR, bbR = place("right", RX, FY); A(g)
g, mT, bbT = place("top", FX, TY); A(g)
# coolant/air system highlighted in blue on every view
for v, cx, cy in (("front", FX, FY), ("right", RX, FY), ("top", FX, TY)):
    g, _, _ = place(v, cx, cy, comp_all, "#000", 0.25)  # mapper reference
    _, (u0, u1, v0, v1), _ = project(comp_all, v)
    gc, _, _ = place(v, cx + ((project(comp_cool, v)[1][0] + project(comp_cool, v)[1][1]) / 2 - (u0 + u1) / 2) * S,
                     cy - ((project(comp_cool, v)[1][2] + project(comp_cool, v)[1][3]) / 2 - (v0 + v1) / 2) * S,
                     comp_cool, "#0a6cd6", 0.3)
    A(gc)
label(FX, 568, "前視圖 FRONT VIEW  1:8", 5, bold=True)
label(RX, 568, "右視圖 RIGHT VIEW  1:8  (左=前/換料側)", 5, bold=True)
label(FX, 40, "俯視圖 TOP VIEW  1:8", 5, bold=True)

# ---------- iso view ----------
IX, IY = 345, 150
g, mI, bbI = place("iso", IX, IY, comp_all, "#000", 0.18); A(g)
_, bi, _ = project(comp_all, "iso"); _, bc, _ = project(comp_cool, "iso")
gc, _, _ = place("iso", IX + ((bc[0] + bc[1]) / 2 - (bi[0] + bi[1]) / 2) * S,
                 IY - ((bc[2] + bc[3]) / 2 - (bi[2] + bi[3]) / 2) * S, comp_cool, "#0a6cd6", 0.25)
A(gc)
label(IX, 40, "立體圖 ISOMETRIC (參考)", 5, bold=True)

# ---------- dimensions ----------
xmin, xmax, ymin, ymax, zmin, zmax = ov["xmin"], ov["xmax"], ov["ymin"], ov["ymax"], ov["zmin"], ov["zmax"]
# front: overall width / height, levels
dim(mF(xmin, zmin), mF(xmax, zmin), 12, f"{ov['x']}")
dim(mF(xmin, zmin), mF(xmin, zmax), -14, f"{ov['z']}", horiz=False)
dim(mF(xmax, 0), mF(xmax, zl["table_top"]), 10, f"台面高 {zl['table_top']:.0f}", horiz=False)
dim(mF(xmax + 40, zl["table_top"]), mF(xmax + 40, zl["beam_bottom"]), 14, f"{pr['clear']}", horiz=False)
dim(mF(-pr["work"] / 2, zl["table_top"]), mF(pr["work"] / 2, zl["table_top"]), -62, "加工區 300 (X行程)")
# right: overall depth, Y travel
dim(mR(ymin, zmin), mR(ymax, zmin), 12, f"{ov['y']}")
ty0 = info["table_y"]["load"]; ty1 = info["table_y"]["work"]
dim(mR(ty0, zl["table_top"]), mR(ty1, zl["table_top"]), -75, "Y 行程 600 (換料 300 + 加工 300)")
dim(mR(ty1 - 150, zl["table_top"]), mR(ty1 + 150, zl["table_top"]), -60, "加工區 300")
# Z travel note
tipx, tipy = mF(0, zl["table_top"] + 120)
A(f'<path d="M{tipx+14},{tipy} V{mF(0, zl["table_top"]+20)[1]}" stroke="#000" stroke-width="0.25" '
  'marker-start="url(#ar)" marker-end="url(#ar)"/>')
label(tipx + 16, tipy + 8, "Z 100", 3.2, "start")
# top: overall
dim(mT(xmin, ymin), mT(xmax, ymin), 10, f"{ov['x']}")
dim(mT(xmin, ymin), mT(xmin, ymax), -12, f"{ov['y']}", horiz=False)
# loading / machining zones on top view
for (y0, y1, txt, col) in ((ty0 - 150, ty0 + 150, "換料區 LOADING ZONE", "#e08a00"),
                           (ty1 - 150, ty1 + 150, "加工區 MACHINING 300x300", "#2a9d3a")):
    (ax, ay), (bx, by) = mT(-150, y1), mT(150, y0)
    A(f'<rect x="{ax}" y="{ay}" width="{bx-ax}" height="{by-ay}" fill="{col}" fill-opacity="0.12" '
      f'stroke="{col}" stroke-width="0.35" stroke-dasharray="2,1"/>')
    label((ax + bx) / 2, (ay + by) / 2 + 1.2, txt, 3, bold=True)
fx, fy = mT(0, ymin)
label(fx, fy + 17, "▲ 操作者 / 前方 (開放裝卸側)", 3.6)

# ---------- coolant callouts on right view ----------
def ctr(name):
    o = doc.getObject(name); return o.Shape.BoundBox.Center
c = {n: ctr(n) for n in ("Coolant_tank", "Coolant_pump", "Chip_filter_basket", "Drain_pipe", "Coolant_trough_rear",
                        "Guard_side_R", "Coolant_nozzle_1", "Air_blow_nozzle", "Air_solenoid_FRL", "Coolant_hose",
                        "Y_bellows_front", "Filter_baffle")}
items = [("Coolant_nozzle_1", 1), ("Air_blow_nozzle", 2), ("Guard_side_R", 3), ("Coolant_trough_rear", 4),
         ("Drain_pipe", 5), ("Chip_filter_basket", 6), ("Filter_baffle", 7), ("Coolant_tank", 8),
         ("Coolant_pump", 9), ("Coolant_hose", 10), ("Air_solenoid_FRL", 11), ("Y_bellows_front", 12)]
rx_right = mR(ymax, 0)[0] + 20
for i, (n, k) in enumerate(items):
    px, py = mR(c[n].y, c[n].z)
    callout(px, py, rx_right, 300 + i * 20, k)

# ---------- coolant legend / flow ----------
LX, LY = 470, 300
A(f'<rect x="{LX}" y="{LY-10}" width="170" height="250" fill="none" stroke="#0a6cd6" stroke-width="0.4"/>')
label(LX + 4, LY - 3, "冷卻液 / 吹氣 / 排屑系統 (藍色)", 4.4, "start", True)
legend = [
    (1, "冷卻液噴嘴 x2 (Loc-Line 1/4\")，夾於主軸夾座"),
    (2, "吹氣噴嘴 0.5 MPa (吹屑/霧化，M7)"),
    (3, "防濺護罩 SUS304 t2，兩側+後方，前方低擋邊開放換料"),
    (4, "集液槽：兩側+後方，斜度 1:100 流向後方"),
    (5, "排液管 PVC Ø40 → 過濾籃"),
    (6, "排屑過濾籃 (沖孔板+60目濾袋)，可抽出清屑"),
    (7, "沉澱隔板：髒液側 | 清液側"),
    (8, "冷卻液箱 SUS304 ~100 L (裝 80 L)，附輪可由後方拉出"),
    (9, "浸入式幫浦 90 W，25 L/min，0.2 MPa (M8 控制)"),
    (10, "供液管 PU 12x8，走拖鏈至主軸"),
    (11, "三點組合 FRL + 24V 電磁閥 (氣/液)"),
    (12, "Y軸伸縮護罩 (防水防屑，保護滑軌/螺桿)"),
]
for i, (k, t) in enumerate(legend):
    yy = LY + 8 + i * 12
    A(f'<circle cx="{LX+8}" cy="{yy-1.3}" r="3.3" fill="#fff" stroke="#c00" stroke-width="0.3"/>')
    label(LX + 8, yy, str(k), 3.4, bold=True)
    label(LX + 15, yy, t, 3.3, "start")
yy = LY + 8 + 12 * 12 + 4
label(LX + 4, yy, "循環路徑：", 3.5, "start", True)
label(LX + 4, yy + 7, "液箱(清) → 幫浦 → 供液管/拖鏈 → 噴嘴 → 工件", 3.2, "start")
label(LX + 4, yy + 13, "→ 護罩/集液槽 → 排液管 → 過濾籃 → 沉澱 → 液箱(清)", 3.2, "start")

# ---------- spec block ----------
SX, SY = 470, 50
A(f'<rect x="{SX}" y="{SY-10}" width="170" height="225" fill="none" stroke="#000" stroke-width="0.4"/>')
label(SX + 4, SY - 3, "主要規格 SPECIFICATION", 4.4, "start", True)
spec = [
    "形式：龍門固定、工作台移動 (Y)",
    "加工材料：鋼材 (結構按鋼件切削剛性設計)",
    "行程 X / Y / Z：300 / 600 / 100 mm",
    "加工區：300 x 300 mm；換料區：前方 300 mm",
    "工作台：440 x 420 x 40，T 槽 14 x5",
    "台面高：%.0f mm，龍門淨空：%d mm" % (zl["table_top"], pr["clear"]),
    "床身：Q235 鋼板焊接 (t30 面板, t20 筋)，退火去應力",
    "龍門：焊接箱型 t12，可灌環氧花崗岩",
    "Y 導軌：HGR25 x2 (4 滑塊)；滾珠螺桿 SFU2010",
    "X 導軌：HGR20 x2；滾珠螺桿 SFU1605",
    "Z 導軌：HGR20 x2；滾珠螺桿 SFU1605 + 煞車",
    "主軸：2.2 kW 水冷 ER20 Ø80 (鋼件建議 ≥2.2kW)",
    "驅動：AC 伺服 Y 750W / X,Z 400W",
    "冷卻：浸入式幫浦 25 L/min + 吹氣",
    "外形 (W x D x H)：%d x %d x %d mm" % (ov["x"], ov["y"], ov["z"]),
    "* 第一版配置圖，尺寸待細部設計確認",
]
for i, t in enumerate(spec):
    label(SX + 4, SY + 8 + i * 12.5, t, 3.4, "start")

# ---------- title block ----------
TX, TY0 = 660, 474
A(f'<rect x="{TX}" y="{TY0}" width="171" height="110" fill="none" stroke="#000" stroke-width="0.6"/>')
for yy in (TY0 + 22, TY0 + 44, TY0 + 66, TY0 + 88):
    A(f'<path d="M{TX},{yy} H{TX+171}" stroke="#000" stroke-width="0.3"/>')
label(TX + 85, TY0 + 15, "三軸龍門 CNC 總組立配置圖", 7, bold=True)
label(TX + 4, TY0 + 35, "圖名：GENERAL ARRANGEMENT (GA)", 4, "start")
label(TX + 4, TY0 + 57, "圖號：CNC-GA-001   版次：A   張數：1/1", 4, "start")
label(TX + 4, TY0 + 79, "比例：1:8   投影法：第三角法   單位：mm", 4, "start")
label(TX + 4, TY0 + 101, "工具：FreeCAD 1.1 (腳本產生)   日期：2026-11-12", 4, "start")
# third-angle symbol
A(f'<g transform="translate({TX+150},{TY0+52})" stroke="#000" stroke-width="0.3" fill="none">'
  '<path d="M0,-5 L10,-3 L10,3 L0,5 Z"/><circle cx="-8" cy="0" r="5"/><circle cx="-8" cy="0" r="2"/></g>')

# ---------- part groups list (BOM summary) ----------
BX, BY = 660, 40
groups = {}
for prt in info["parts"]:
    groups.setdefault(prt["group"], []).append(prt)
A(f'<rect x="{BX}" y="{BY-10}" width="171" height="425" fill="none" stroke="#000" stroke-width="0.4"/>')
label(BX + 4, BY - 3, "零件清單 BOM (摘要)", 4.4, "start", True)
yy = BY + 6
seen = set()
for gname, lst in groups.items():
    label(BX + 4, yy, gname, 3.6, "start", True); yy += 6
    rows = {}
    for prt in lst:
        key = re.sub(r"_(\d+|[LR]\d?|top|low|F|B)$", "", prt["name"])
        key = re.sub(r"_(top|low)_[LRFB]$", "", key)
        rows.setdefault(key, [0, prt["material"]])[0] += 1
    for key, (q, m) in rows.items():
        if yy > BY + 410:
            break
        t = f"{key.replace('_', ' ')}  x{q}  — {m}"
        label(BX + 7, yy, t[:72], 2.6, "start"); yy += 4.6
    yy += 2

A("</svg>")
svgp = os.path.join(OUT, "CNC_Gantry_GA.svg")
open(svgp, "w", encoding="utf-8").write("\n".join(out))
print("SVG", svgp)
