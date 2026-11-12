# -*- coding: utf-8 -*-
"""Line-drawing views of the v3 assembly (front / right / top / iso), coloured by group -> output/v3/CNC_v3_views.svg"""
import os, re, math
import FreeCAD as App, Part, TechDraw
from FreeCAD import Vector as V, Matrix

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "v3")
doc = App.openDocument(os.path.join(OUT, "CNC_v3.FCStd"))
COL = {"01": "#555", "02": "#1f6fd1", "03": "#7a7a7a", "04": "#d1561f", "05": "#2a9d3a", "06": "#8e44ad", "07": "#c9a400"}
groups = {}
for g in doc.Objects:
    if g.TypeId == "App::DocumentObjectGroup":
        groups[g.Label[:2]] = [o.Shape for o in g.Group]


def nrm(v):
    l = math.sqrt(sum(c * c for c in v)); return [c / l for c in v]


def mat(r):
    m = Matrix()
    (m.A11, m.A12, m.A13), (m.A21, m.A22, m.A23), (m.A31, m.A32, m.A33) = r
    return m


VIEWS = {"front": mat([(1, 0, 0), (0, 0, 1), (0, -1, 0)]),
         "right": mat([(0, 1, 0), (0, 0, 1), (1, 0, 0)]),
         "top": mat([(1, 0, 0), (0, 1, 0), (0, 0, 1)]),
         "iso": mat([nrm((1, 1, 0)), nrm((-1, 1, 2)), nrm((1, -1, 1))])}
allc = Part.makeCompound([s for l in groups.values() for s in l])
S = 0.32
W, H = 760, 560
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="100%%" viewBox="0 0 %d %d" '
       'font-family="Arial, Microsoft JhengHei, sans-serif">' % (W, H), '<rect width="%d" height="%d" fill="#fff"/>' % (W, H)]


def view(name, cx, cy, scale, title):
    ref = allc.copy(); ref.transformShape(VIEWS[name]); bb = ref.BoundBox
    uc, vc = (bb.XMin + bb.XMax) / 2, (bb.YMin + bb.YMax) / 2
    tx, ty = cx - uc * scale, cy + vc * scale
    # draw back-to-front isn't possible with HLR per group; project the whole set once for hidden-line removal,
    # then overlay each group's visible edges in colour (thin) for identification
    for key in sorted(groups):
        comp = Part.makeCompound(groups[key]); comp.transformShape(VIEWS[name])
        svg = TechDraw.projectToSVG(comp, V(0, 0, 1))
        out.append('<g transform="translate(%.2f,%.2f) scale(%g,%g)" fill="none" stroke="%s" stroke-width="%.2f">'
                   % (tx, ty, scale, -scale, COL.get(key, "#000"), 0.35 / scale))
        for grp in re.findall(r"<g(.*?)</g>", svg, re.S):
            if "stroke-dasharray" in grp:
                continue
            for d in re.findall(r'd="([^"]*)"', grp):
                out.append('<path d="%s"/>' % d)
        out.append("</g>")
    out.append('<text x="%d" y="%d" font-size="11" text-anchor="middle" font-weight="bold">%s</text>' % (cx, 22 if cy < 280 else 548, title))


view("iso", 200, 150, 0.30, "立體 ISO")
view("front", 560, 150, 0.30, "前視 FRONT")
view("right", 200, 410, 0.30, "右視 RIGHT (左=前)")
view("top", 560, 410, 0.28, "俯視 TOP (下=前)")
lg = [("01", "基準底板"), ("02", "Y 軸 (三住 SE42 / C-KBS / 三菱)"), ("03", "龍門 (三住 HFS8)"), ("04", "X 軸 (三住 SX28)"),
      ("05", "Z 軸"), ("06", "電主軸 (依規格建模)"), ("07", "MR-J4-40A x3")]
for i, (k, t) in enumerate(lg):
    out.append('<rect x="%d" y="%d" width="10" height="4" fill="%s"/><text x="%d" y="%d" font-size="8">%s</text>'
               % (20, 470 + i * 12, COL[k], 34, 474 + i * 12, t))
out.append("</svg>")
open(os.path.join(OUT, "CNC_v3_views.svg"), "w", encoding="utf-8").write("\n".join(out))
print("SVG done")
