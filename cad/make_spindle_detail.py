# -*- coding: utf-8 -*-
"""Spindle head detail drawing (A3, third-angle): head 1:2, belt drive top view 1:2, ER11 nose section 2:1.
Run: python cad/make_spindle_detail.py  -> ../output/CNC_Spindle_Detail.svg
"""
import os, math, runpy
import cadquery as cq
from cadquery import Vector as V
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "output")
M = runpy.run_path(os.path.join(HERE, "cnc_gantry.py"), run_name="lib")
P = {n: (s, m) for n, s, g, m, _ in M["parts"]}
sp_y, sp_z0 = M["sp_y"], M["sp_z0"]
W, H = 420, 297

HEAD = [n for n in P if n.startswith(("Spindle", "ER11", "Tool", "Belt", "Z_slide", "Coolant_nozzle", "Air_blow"))]
VIEWS = {"front": ((0, -1, 0), (1, 0, 0)), "top": ((0, 0, 1), (1, 0, 0))}


def project(shape, view):
    n, u = VIEWS[view]
    algo = HLRBRep_Algo(); algo.Add(shape.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*n), gp_Dir(*u))))
    algo.Update(); algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    lines = []
    for c in (h.VCompound(), h.OutLineVCompound()):
        if c is None or c.IsNull():
            continue
        for e in cq.Shape.cast(c).Edges():
            k = 1 if e.geomType() == "LINE" else max(8, int(e.Length() / 2))
            lines.append([(q.x, q.y) for q in (e.positionAt(i / k) for i in range(k + 1))])
    return lines


out = []
A = out.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" '
  'font-family="Arial, Microsoft JhengHei, sans-serif">')
A('<defs><marker id="ar" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" '
  'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,2 L10,5 L0,8 z" fill="#000"/></marker>')
for pid, ang, col in (("h1", 45, "#555"), ("h2", -45, "#555"), ("h3", 45, "#d26a10"), ("h4", -45, "#0a6cd6")):
    A(f'<pattern id="{pid}" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate({ang})">'
      f'<line x1="0" y1="0" x2="0" y2="1.6" stroke="{col}" stroke-width="0.25"/></pattern>')
A('</defs>')
A(f'<rect width="{W}" height="{H}" fill="#fff"/>')
A(f'<rect x="10" y="8" width="{W-18}" height="{H-16}" fill="none" stroke="#000" stroke-width="0.6"/>')


def T(x, y, txt, fs=3, anchor="middle", bold=False, color="#000"):
    txt = str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    fw = ' font-weight="bold"' if bold else ""
    A(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{fs}" text-anchor="{anchor}" fill="{color}"{fw}>{txt}</text>')


def draw(lines, m, sc, color="#000", sw=0.25):
    d = " ".join("M" + " L".join(f"{m(a, b)[0]:.2f} {m(a, b)[1]:.2f}" for a, b in l) for l in lines)
    A(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>')


def mapper(cx, cy, uc, vc, sc):
    return lambda u, v: (cx + (u - uc) * sc, cy - (v - vc) * sc)


def hdim(m, u1, u2, v, off, txt, fs=2.6, side=False):
    (x1, y1), (x2, _) = m(u1, v), m(u2, v)
    y = y1 + off
    A(f'<path d="M{x1:.2f},{y1:.2f} V{y:.2f} M{x2:.2f},{y1:.2f} V{y:.2f}" stroke="#000" stroke-width="0.13"/>')
    if side:
        A(f'<path d="M{x2 + 12:.2f},{y:.2f} H{x1:.2f}" stroke="#000" stroke-width="0.18" marker-end="url(#ar)"/>'
          f'<path d="M{x1 - 5:.2f},{y:.2f} H{x2:.2f}" stroke="#000" stroke-width="0.18" marker-end="url(#ar)"/>')
        T(x2 + 1.5, y - 0.8, txt, fs, "start")
    else:
        A(f'<path d="M{x1:.2f},{y:.2f} H{x2:.2f}" stroke="#000" stroke-width="0.18" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        T((x1 + x2) / 2, y - 0.8, txt, fs)


def vdim(m, u, v1, v2, off, txt, fs=2.6):
    (x1, y1), (_, y2) = m(u, v1), m(u, v2)
    x = x1 + off
    A(f'<path d="M{x1:.2f},{y1:.2f} H{x:.2f} M{x1:.2f},{y2:.2f} H{x:.2f}" stroke="#000" stroke-width="0.13"/>')
    A(f'<path d="M{x:.2f},{y1:.2f} V{y2:.2f}" stroke="#000" stroke-width="0.18" marker-start="url(#ar)" marker-end="url(#ar)"/>')
    A(f'<text x="{x-0.8:.2f}" y="{(y1+y2)/2:.2f}" font-size="{fs}" text-anchor="middle" '
      f'transform="rotate(-90 {x-0.8:.2f} {(y1+y2)/2:.2f})">{txt}</text>')


def leader(m, u, v, tx, ty, txt, fs=2.7, anchor="start", color="#000"):
    px, py = m(u, v)
    A(f'<path d="M{px:.2f},{py:.2f} L{tx:.2f},{ty:.2f} H{tx + (14 if anchor == "start" else -14):.2f}" '
      f'stroke="{color}" stroke-width="0.18" fill="none"/><circle cx="{px:.2f}" cy="{py:.2f}" r="0.5" fill="{color}"/>')
    T(tx + (1 if anchor == "start" else -1), ty - 0.8, txt, fs, anchor, color=color)


# ------------------------------------------------ view 1: spindle head front 1:2
S1 = 0.5
head = cq.Compound.makeCompound([P[n][0] for n in HEAD])
bb = head.BoundingBox()
m1 = mapper(110, 105, (bb.xmin + bb.xmax) / 2, (bb.zmin + bb.zmax) / 2, S1)
RX1 = m1(bb.xmax, 0)[0] + 6; LX1 = m1(bb.xmin, 0)[0] - 4
draw(project(head, "front"), m1, S1)
spin_only = cq.Compound.makeCompound([P[n][0] for n in HEAD if n.startswith(("Spindle", "ER11", "Tool", "Belt"))])
T(110, 14.5, "主軸頭 前視圖 FRONT  1:2", 4, bold=True)
mx = M["mx"]; pz0 = M["pz0"]
tip = sp_z0 - 43
vdim(m1, bb.xmax, tip, sp_z0, 4, "43")
hdim(m1, 0, mx, pz0 + 32, -8, f"皮帶中心距 {mx}")
leader(m1, mx, pz0 + 10, RX1, m1(0, pz0 + 40)[1], "皮帶輪 Ø96/Ø32，PJ 帶 1:3")
leader(m1, mx + 20, pz0 - 60, RX1, m1(0, pz0 - 40)[1], "主軸馬達 HG-KR43")
leader(m1, 50, M["z_slide_z"] + 65, RX1, m1(0, M["z_slide_z"] + 40)[1], "主軸夾座")
leader(m1, -31, sp_z0 + 100, LX1, m1(0, sp_z0 + 150)[1], "ER11 主軸頭 Ø62", anchor="end")
leader(m1, 0, sp_z0 - 9, LX1, m1(0, sp_z0 - 5)[1], "詳圖 A (ER11)", anchor="end", color="#d26a10")
leader(m1, 0, tip + 5, LX1, m1(0, tip - 8)[1], "刀具 Ø5 (柄 Ø6)", anchor="end")
cx, cy = m1(0, sp_z0 - 10)
A(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="9" fill="none" stroke="#d26a10" stroke-width="0.35" stroke-dasharray="1.5,1"/>')
T(cx + 11, cy + 9, "A", 4, bold=True, color="#d26a10")

# ------------------------------------------------ view 2: belt drive top view 1:2 (guard removed)
belt = cq.Compound.makeCompound([P[n][0] for n in ("Spindle_pulley", "Spindle_motor_pulley", "Spindle_belt",
                                                     "Spindle_motor", "Spindle_motor_bracket", "Spindle_cartridge",
                                                     "Spindle_clamp", "Z_slide_plate")])
bb2 = belt.BoundingBox()
m2 = mapper(110, 240, (bb2.xmin + bb2.xmax) / 2, (bb2.ymin + bb2.ymax) / 2, S1)
draw(project(belt, "top"), m2, S1)
T(110, 199, "皮帶傳動 俯視圖 TOP  1:2 (皮帶罩移除)", 3.6, bold=True)
leader(m2, -16, sp_y, m2(bb2.xmin, 0)[0] - 6, m2(0, sp_y + 30)[1], "Ø32 主軸端", anchor="end")
leader(m2, mx + 48, M["my"], m2(bb2.xmax, 0)[0] + 6, m2(0, M["my"] - 30)[1], "Ø96 馬達端，長孔調張力")

# ------------------------------------------------ view 3: ER11 nose section 2:1
S3 = 2.0
NOSE = ["Spindle_cartridge", "Spindle_nose", "ER11_collet", "ER11_nut", "Tool_D5"]
FILL = {"Spindle_cartridge": "url(#h1)", "Spindle_nose": "url(#h2)", "ER11_collet": "url(#h3)",
        "ER11_nut": "url(#h4)", "Tool_D5": "#e9e2cf"}
crop = cq.Solid.makeBox(44, 40, 70, V(-22, sp_y, sp_z0 - 50))
secs = {n: P[n][0].intersect(crop) for n in NOSE}
m3 = mapper(250, 128, 0, sp_z0 - 15, S3)
for n in NOSE:  # section faces (y = sp_y) filled + hatched
    for f in secs[n].Faces():
        c = f.Center()
        if abs(c.y - sp_y) > 1e-3 or abs(f.normalAt(c).y) < 0.99:
            continue
        d = ""
        for w in [f.outerWire()] + f.innerWires():
            pts = []
            for e in w.Edges():
                k = 1 if e.geomType() == "LINE" else 16
                seg = [e.positionAt(i / k) for i in range(k + 1)]
                if pts and (pts[-1] - seg[0]).Length > (pts[-1] - seg[-1]).Length:
                    seg.reverse()
                pts += seg
            d += "M" + " L".join(f"{m3(q.x, q.z)[0]:.2f} {m3(q.x, q.z)[1]:.2f}" for q in pts) + " Z "
        A(f'<path d="{d}" fill="{FILL[n]}" fill-rule="evenodd" stroke="none"/>')
draw(project(cq.Compound.makeCompound(list(secs.values())), "front"), m3, S3, sw=0.3)
(ax, ay), (bx, by_) = m3(0, sp_z0 + 22), m3(0, sp_z0 - 48)
A(f'<path d="M{ax:.2f},{ay:.2f} V{by_:.2f}" stroke="#000" stroke-width="0.18" stroke-dasharray="4,1,1,1"/>')
T(250, 20, "詳圖 A  ER11 前端剖面  2:1", 4, bold=True, color="#d26a10")
hdim(m3, -9.5, 9.5, sp_z0 - 16, 6, "Ø19 螺帽", side=True)
hdim(m3, -2.5, 2.5, sp_z0 - 43, 8, "Ø5")
hdim(m3, -3, 3, sp_z0 - 22, 4, "Ø6 刀柄", side=True)
hdim(m3, -6.5, 6.5, sp_z0, -12, "M13×0.75")
vdim(m3, -12, sp_z0 - 14, sp_z0 + 4, -16, "18 筒夾長")
vdim(m3, 12, sp_z0 - 43, sp_z0 - 16, 22, "27 伸出")
leader(m3, 4.9, sp_z0 - 4, 296, 72, "ER11 筒夾 Ø11.5，8° 錐度，AA ≤0.005", color="#d26a10")
leader(m3, 6.2, sp_z0 - 5, 296, 84, "主軸鼻端，M13×0.75 外螺紋")
leader(m3, -8.5, sp_z0 - 12, 204, 150, "ER11 螺帽 A 型 Ø19，扳手槽 ×4", anchor="end", color="#0a6cd6")
leader(m3, 18, sp_z0 + 12, 296, 58, "主軸頭本體 (錐孔偏擺 ≤0.003)")
leader(m3, 2.5, sp_z0 - 38, 268, 192, "刀具：鋁用 2 刃 Ø5 × 柄 Ø6")

# ------------------------------------------------ ER11 table + title block
TX, TY = 316, 196
A(f'<rect x="{TX}" y="{TY}" width="96" height="44" fill="none" stroke="#000" stroke-width="0.4"/>')
T(TX + 3, TY + 5.5, "ER11 筒夾規格 (ISO 15488)", 3.2, "start", True)
rows = ["夾持範圍：Ø1～Ø7，每支 0.5 mm", "外徑 Ø11.5，長 18，錐角 8°", "螺帽 A 型 Ø19，M13×0.75",
        "精度：AA 級偏擺 ≤ 0.005 mm", "依「刀柄直徑」選筒夾", "建議備品：Ø3 / Ø4 / Ø6 AA 級", "換刀：人工，ER11 扳手 ×2"]
for i, r in enumerate(rows):
    T(TX + 3, TY + 11 + i * 4.6, r, 2.7, "start")
BX, BY = 316, 244
A(f'<rect x="{BX}" y="{BY}" width="96" height="45" fill="none" stroke="#000" stroke-width="0.5"/>')
for yy in (BY + 12, BY + 23, BY + 34):
    A(f'<path d="M{BX},{yy} H{BX+96}" stroke="#000" stroke-width="0.25"/>')
T(BX + 48, BY + 8, "主軸頭細部圖 SPINDLE DETAIL", 4, bold=True)
T(BX + 3, BY + 19, "圖號：CNC-SP-001   版次：A   張數：1/1", 2.9, "start")
T(BX + 3, BY + 30, "比例：1:2 / 2:1   第三角法   單位：mm", 2.9, "start")
T(BX + 3, BY + 41, "工具：CadQuery 2.8 (腳本產生)   日期：2026-11-12", 2.9, "start")

A("</svg>")
p = os.path.join(OUT, "CNC_Spindle_Detail.svg")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("SVG", p, os.path.getsize(p))
