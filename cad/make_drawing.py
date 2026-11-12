# -*- coding: utf-8 -*-
"""General-arrangement drawing (A1, 1:8, third-angle) from the CadQuery model.
Run: python cad/make_drawing.py  -> ../output/CNC_Gantry_GA.svg
(Run cnc_gantry.py first if parameters changed; this script rebuilds the model in-process.)
"""
import os, re, json, math, runpy
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "output")
M = runpy.run_path(os.path.join(HERE, "cnc_gantry.py"), run_name="lib")
info = json.load(open(os.path.join(OUT, "cnc_info.json"), encoding="utf-8"))
PARTS = {n: (s, g, m) for n, s, g, m, _ in M["parts"]}
objs = [s for n, (s, g, m) in PARTS.items() if n != "Work_area_300x300"]
cool = [s for n, (s, g, m) in PARTS.items() if g.startswith("07")]
spin = [s for n, (s, g, m) in PARTS.items() if n.startswith(("Spindle", "Belt", "Tool"))]
comp_all = cq.Compound.makeCompound(objs)
comp_cool = cq.Compound.makeCompound(cool)
comp_spin = cq.Compound.makeCompound(spin)

S = 1 / 8.0          # drawing scale
W, H = 841, 594      # A1 landscape


def nrm(v):
    l = math.sqrt(sum(c * c for c in v)); return tuple(c / l for c in v)


VIEWS = {  # (towards viewer, screen-u); screen-v = n x u
    "front": ((0, -1, 0), (1, 0, 0)),
    "right": ((1, 0, 0), (0, 1, 0)),
    "top":   ((0, 0, 1), (1, 0, 0)),
    "iso":   (nrm((1, -1, 1)), nrm((1, 1, 0))),
}
_cache = {}


def project(shape, view):
    """Visible edges of shape seen from view -> (list of polylines [(u,v)...], bbox)."""
    key = (id(shape), view)
    if key in _cache:
        return _cache[key]
    n, u = VIEWS[view]
    algo = HLRBRep_Algo()
    algo.Add(shape.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*n), gp_Dir(*u))))
    algo.Update(); algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    lines = []
    for c in (h.VCompound(), h.OutLineVCompound()):
        if c is None or c.IsNull():
            continue
        for e in cq.Shape.cast(c).Edges():
            if e.geomType() == "LINE":
                pts = [e.startPoint(), e.endPoint()]
            else:
                k = max(6, int(e.Length() / 8))
                pts = [e.positionAt(i / k) for i in range(k + 1)]
            lines.append([(q.x, q.y) for q in pts])
    us = [q[0] for l in lines for q in l]; vs = [q[1] for l in lines for q in l]
    res = (lines, (min(us), max(us), min(vs), max(vs)))
    _cache[key] = res
    return res


def place(view, cx, cy, shape=comp_all, color="#000", sw=0.25, ref=None, S=S):
    """Draw view so the bbox centre of `ref` (default comp_all) lands at sheet (cx,cy)."""
    lines, _ = project(shape, view)
    _, (u0, u1, v0, v1) = project(ref or comp_all, view)
    uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
    tx, ty = cx - uc * S, cy + vc * S
    d = " ".join("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in l) for l in lines)
    g = (f'<g transform="translate({tx:.2f},{ty:.2f}) scale({S},{-S})" fill="none" stroke="{color}" '
         f'stroke-width="{sw / S:.2f}" stroke-linejoin="round" stroke-linecap="round"><path d="{d}"/></g>')
    m = lambda uu, vv: (tx + uu * S, ty - vv * S)
    return g, m


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
    (x1, y1), (x2, y2) = p1, p2
    if horiz:
        y = y1 + off
        A(f'<path d="M{x1:.2f},{y1:.2f} V{y:.2f} M{x2:.2f},{y2:.2f} V{y:.2f}" stroke="#000" stroke-width="0.18"/>')
        A(f'<path d="M{x1:.2f},{y:.2f} H{x2:.2f}" stroke="#000" stroke-width="0.25" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        A(f'<text x="{(x1+x2)/2:.2f}" y="{y-1.2:.2f}" font-size="{fs}" text-anchor="middle">{txt}</text>')
    else:
        x = x1 + off
        A(f'<path d="M{x1:.2f},{y1:.2f} H{x:.2f} M{x2:.2f},{y2:.2f} H{x:.2f}" stroke="#000" stroke-width="0.18"/>')
        A(f'<path d="M{x:.2f},{y1:.2f} V{y2:.2f}" stroke="#000" stroke-width="0.25" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        A(f'<text x="{x-1.2:.2f}" y="{(y1+y2)/2:.2f}" font-size="{fs}" text-anchor="middle" '
          f'transform="rotate(-90 {x-1.2:.2f} {(y1+y2)/2:.2f})">{txt}</text>')


def label(x, y, txt, fs=4, anchor="middle", bold=False, color=None):
    fw = ' font-weight="bold"' if bold else ""
    fc = f' fill="{color}"' if color else ""
    txt = str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    A(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{fs}" text-anchor="{anchor}"{fw}{fc}>{txt}</text>')


def callout(px, py, tx, ty, n, col="#c00"):
    A(f'<path d="M{px:.2f},{py:.2f} L{tx:.2f},{ty:.2f}" stroke="{col}" stroke-width="0.25" marker-start="url(#dot)"/>')
    A(f'<circle cx="{tx:.2f}" cy="{ty:.2f}" r="3.6" fill="#fff" stroke="{col}" stroke-width="0.35"/>')
    A(f'<text x="{tx:.2f}" y="{ty+1.4:.2f}" font-size="3.8" text-anchor="middle" fill="{col}" font-weight="bold">{n}</text>')


zl, ov, pr = info["z_levels"], info["overall"], info["params"]
BLUE, ORANGE = "#0a6cd6", "#d26a10"

# ---------- views (third angle: top above front, right to the right) ----------
FX, FY = 130, 395
RX = 350
TY = 150
IX, IY = 345, 160
mp = {}
for v, cx, cy, sw, sc in (("front", FX, FY, 0.25, S), ("right", RX, FY, 0.25, S), ("top", FX, TY, 0.25, S),
                          ("iso", IX, IY, 0.18, 1 / 10.0)):
    g, mp[v] = place(v, cx, cy, comp_all, "#000", sw, S=sc); A(g)
    g, _ = place(v, cx, cy, comp_cool, BLUE, sw + 0.05, S=sc); A(g)
    g, _ = place(v, cx, cy, comp_spin, ORANGE, sw + 0.05, S=sc); A(g)
mF, mR, mT = mp["front"], mp["right"], mp["top"]
label(FX, 568, "前視圖 FRONT VIEW  1:8", 5, bold=True)
label(RX, 568, "右視圖 RIGHT VIEW  1:8  (左=前/換料側)", 5, bold=True)
label(FX, 36, "俯視圖 TOP VIEW  1:8", 5, bold=True)
label(IX, 36, "立體圖 ISOMETRIC 1:10 (參考)", 5, bold=True)

# ---------- dimensions ----------
xmin, xmax, ymin, ymax, zmin, zmax = ov["xmin"], ov["xmax"], ov["ymin"], ov["ymax"], ov["zmin"], ov["zmax"]
dim(mF(xmin, zmin), mF(xmax, zmin), 12, f"{ov['x']}")
dim(mF(xmin, zmin), mF(xmin, zmax), -14, f"{ov['z']}", horiz=False)
dim(mF(xmax, 0), mF(xmax, zl["table_top"]), 10, f"台面高 {zl['table_top']:.0f}", horiz=False)
dim(mF(xmax + 40, zl["table_top"]), mF(xmax + 40, zl["beam_bottom"]), 14, f"{pr['clear']}", horiz=False)
dim(mF(-pr["work"] / 2, zl["table_top"]), mF(pr["work"] / 2, zl["table_top"]), -66, "加工區 300 (X行程)")
dim(mR(ymin, zmin), mR(ymax, zmin), 12, f"{ov['y']}")
ty0 = info["table_y"]["load"]; ty1 = info["table_y"]["work"]
dim(mR(ty0, zl["table_top"]), mR(ty1, zl["table_top"]), -78, "Y 行程 600 (換料 300 + 加工 300)")
dim(mR(ty1 - 150, zl["table_top"]), mR(ty1 + 150, zl["table_top"]), -62, "加工區 300")
dim(mT(xmin, ymin), mT(xmax, ymin), 10, f"{ov['x']}")
dim(mT(xmin, ymin), mT(xmin, ymax), -12, f"{ov['y']}", horiz=False)
for (y0, y1, txt, col) in ((ty0 - 150, ty0 + 150, "換料區 LOADING ZONE", "#e08a00"),
                           (ty1 - 150, ty1 + 150, "加工區 MACHINING 300x300", "#2a9d3a")):
    (ax, ay), (bx, by) = mT(-150, y1), mT(150, y0)
    A(f'<rect x="{ax:.2f}" y="{ay:.2f}" width="{bx-ax:.2f}" height="{by-ay:.2f}" fill="{col}" fill-opacity="0.12" '
      f'stroke="{col}" stroke-width="0.35" stroke-dasharray="2,1"/>')
    label((ax + bx) / 2, (ay + by) / 2 + 1.2, txt, 3, bold=True)
fx, fy = mT(0, ymin)
label(fx, fy + 17, "▲ 操作者 / 前方 (開放裝卸側)", 3.6)


def ctr(name):
    b = PARTS[name][0].BoundingBox()
    return ((b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2, (b.zmin + b.zmax) / 2)


# ---------- spindle callouts on front view (orange) ----------
sp_items = [("Spindle_motor", "A"), ("Spindle_belt", "B"), ("Spindle_cartridge", "C"), ("Z_motor", "D")]
for i, (n, k) in enumerate(sp_items):
    x, y, z = ctr(n)
    px, py = mF(x, z)
    callout(px, py, mF(xmin, 0)[0] - 4 + 0 * i, mF(0, zmax)[1] + 10 + i * 10, k, ORANGE)

# ---------- coolant callouts on right view ----------
items = [("Coolant_nozzle_1", 1), ("Air_blow_nozzle", 2), ("Guard_side_R", 3), ("Coolant_trough_rear", 4),
         ("Drain_pipe", 5), ("Chip_filter_basket", 6), ("Filter_baffle", 7), ("Coolant_tank", 8),
         ("Coolant_pump", 9), ("Coolant_hose", 10), ("Air_solenoid_FRL", 11), ("Y_bellows_front", 12)]
rx_right = mR(ymax, 0)[0] + 18
for i, (n, k) in enumerate(items):
    x, y, z = ctr(n)
    px, py = mR(y, z)
    callout(px, py, rx_right, 300 + i * 20, k)

# ---------- legend ----------
LX, LY = 478, 300
A(f'<rect x="{LX}" y="{LY-10}" width="172" height="262" fill="none" stroke="{BLUE}" stroke-width="0.4"/>')
label(LX + 4, LY - 3, "冷卻液 / 吹氣 / 排屑系統 (藍色)", 4.4, "start", True)
legend = [
    (1, "冷卻液噴嘴 x2 (Loc-Line 1/4\")，對準刀具"),
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
    yy = LY + 8 + i * 11
    A(f'<circle cx="{LX+8}" cy="{yy-1.3}" r="3.3" fill="#fff" stroke="#c00" stroke-width="0.3"/>')
    label(LX + 8, yy, str(k), 3.4, bold=True)
    label(LX + 15, yy, t, 3.2, "start")
yy = LY + 8 + 12 * 11 + 2
label(LX + 4, yy, "主軸 / Z 軸 (橘色)", 4.0, "start", True, ORANGE)
sp_leg = [("A", "主軸馬達 三菱 HG-KR43 400 W (速度模式，0-10 V)"),
          ("B", "PJ 多楔帶 1:3，皮帶輪 Ø96 / Ø32 (動平衡)，附護罩"),
          ("C", "ER11 皮帶式主軸頭 Ø62，約 13,500 rpm，人工換刀"),
          ("D", "Z 軸馬達 三菱 HG-KR43B (附煞車)")]
for i, (k, t) in enumerate(sp_leg):
    y2 = yy + 8 + i * 10
    A(f'<circle cx="{LX+8}" cy="{y2-1.3}" r="3.3" fill="#fff" stroke="{ORANGE}" stroke-width="0.3"/>')
    label(LX + 8, y2, k, 3.4, bold=True, color=ORANGE)
    label(LX + 15, y2, t, 3.2, "start")
y3 = yy + 8 + 4 * 10 + 2
label(LX + 4, y3, "冷卻循環：液箱 → 幫浦 → 噴嘴 → 集液槽 → 過濾籃 → 液箱", 3.1, "start")

# ---------- spec block ----------
SX, SY = 478, 50
A(f'<rect x="{SX}" y="{SY-10}" width="172" height="232" fill="none" stroke="#000" stroke-width="0.4"/>')
label(SX + 4, SY - 3, "主要規格 SPECIFICATION (v2)", 4.4, "start", True)
spec = [
    "形式：龍門固定、工作台移動 (Y)；多台並行生產用",
    "加工：鋁材，刀具 Ø5 以下，人工換刀",
    "行程 X / Y / Z：300 / 600 / 100 mm；進給 ≤ 100 mm/s",
    "加工區：300 x 300 mm；換料區：前方 300 mm",
    "工作台：440 x 420 x 40，T 槽 14 x5",
    "台面高：%.0f mm，龍門淨空：%d mm" % (zl["table_top"], pr["clear"]),
    "床身：Q235 鋼板焊接 (t30 面板, t20 筋)，退火去應力",
    "線軌：HIWIN HG，ZA 中預壓，H 級 (Y HGR25 / X,Z HGR20)",
    "螺桿：DFU 雙螺帽預壓 C7，導程 5 (Y DFU2005 / X,Z DFU1605)",
    "伺服：三菱 HG-KR43 400 W x5 (Z 附煞車)，MR-J4-40A x4",
    "主軸：HG-KR43 + PJ 皮帶 1:3，ER11 主軸頭 ~13,500 rpm",
    "控制：grblHAL (Teensy 4.1 + T41U5XBB)，5 軸，差動脈衝",
    "解析度：0.001 mm/step (電子齒輪 5,000 p/rev)",
    "冷卻：浸入式幫浦 25 L/min + 吹氣 (客戶要求保留)",
    "外形 (W x D x H)：%d x %d x %d mm" % (ov["x"], ov["y"], ov["z"]),
    "* 配置圖，尺寸待細部設計確認",
]
for i, t in enumerate(spec):
    label(SX + 4, SY + 8 + i * 13, t, 3.3, "start")

# ---------- title block ----------
TX, TY0 = 660, 474
A(f'<rect x="{TX}" y="{TY0}" width="171" height="110" fill="none" stroke="#000" stroke-width="0.6"/>')
for yy in (TY0 + 22, TY0 + 44, TY0 + 66, TY0 + 88):
    A(f'<path d="M{TX},{yy} H{TX+171}" stroke="#000" stroke-width="0.3"/>')
label(TX + 85, TY0 + 15, "三軸龍門 CNC 總組立配置圖 v2", 7, bold=True)
label(TX + 4, TY0 + 35, "圖名：GENERAL ARRANGEMENT (GA)", 4, "start")
label(TX + 4, TY0 + 57, "圖號：CNC-GA-001   版次：B   張數：1/1", 4, "start")
label(TX + 4, TY0 + 79, "比例：1:8   投影法：第三角法   單位：mm", 4, "start")
label(TX + 4, TY0 + 101, "工具：CadQuery 2.8 (腳本產生)   日期：2026-11-12", 4, "start")
A(f'<g transform="translate({TX+150},{TY0+52})" stroke="#000" stroke-width="0.3" fill="none">'
  '<path d="M0,-5 L10,-3 L10,3 L0,5 Z"/><circle cx="-8" cy="0" r="5"/><circle cx="-8" cy="0" r="2"/></g>')

# ---------- BOM summary ----------
BX, BY = 660, 40
groups = {}
for prt in info["parts"]:
    groups.setdefault(prt["group"], []).append(prt)
A(f'<rect x="{BX}" y="{BY-10}" width="171" height="428" fill="none" stroke="#000" stroke-width="0.4"/>')
label(BX + 4, BY - 3, "零件清單 BOM (摘要)", 4.4, "start", True)
yy = BY + 5
for gname, lst in groups.items():
    label(BX + 4, yy, gname, 3.3, "start", True); yy += 5
    rows = {}
    for prt in lst:
        key = re.sub(r"_(top|low)_[LRFB]$", "", prt["name"])
        key = re.sub(r"_(\d+|[LR]\d?|\d\d)$", "", key)
        rows.setdefault(key, [0, prt["material"]])[0] += 1
    for key, (q, m) in rows.items():
        if yy > BY + 414:
            break
        t = f"{key.replace('_', ' ')}  x{q}  — {m}"
        label(BX + 7, yy, t[:78], 2.4, "start"); yy += 3.9
    yy += 1.5

A("</svg>")
svgp = os.path.join(OUT, "CNC_Gantry_GA.svg")
open(svgp, "w", encoding="utf-8").write("\n".join(out))
print("SVG", svgp, os.path.getsize(svgp))
