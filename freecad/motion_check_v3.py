# -*- coding: utf-8 -*-
"""Collision sweep of the v3 assembly at the travel ends (Y -250/+150, X +-150, Z +-50)."""
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "v3")
doc = App.openDocument(os.path.join(OUT, "CNC_v3.FCStd"))
P = {o.Name: o.Shape for o in doc.Objects if o.TypeId == "Part::Feature"}

Y_MOV = [n for n in P if n.startswith(("Y_rail", "Y_carrier", "Work_table", "Y_ballscrew", "Y_support", "Y_journal",
                                       "Y_coupling", "Y_motor"))]
Z_MOV = [n for n in P if n.startswith(("Z_block", "Z_spacer", "Z_slide", "Z_ball_nut", "Spindle", "ER11", "Tool"))]
X_MOV = [n for n in P if n.startswith(("X_block", "X_spacer", "X_carriage", "X_ball_nut", "X_nut_bracket", "Z_"))
         or n in Z_MOV]
X_MOV = sorted(set(X_MOV))
# pairs that move together or are coaxial by design
SAME = [set(Y_MOV), set(X_MOV), set(Z_MOV)]
EXPECT = {("Y_ballscrew", "Y_ball_nut"), ("X_ballscrew", "X_ball_nut"), ("Z_ballscrew", "Z_ball_nut"),
          ("X_rail_1", "X_block_11"), ("X_rail_1", "X_block_12"), ("X_rail_2", "X_block_21"), ("X_rail_2", "X_block_22"),
          ("Z_rail_L", "Z_block_L1"), ("Z_rail_L", "Z_block_L2"), ("Z_rail_R", "Z_block_R1"), ("Z_rail_R", "Z_block_R2"),
          ("Y_rail_L", "Y_block_L1"), ("Y_rail_L", "Y_block_L2"), ("Y_rail_R", "Y_block_R1"), ("Y_rail_R", "Y_block_R2"),
          ("X_ballscrew", "X_nut_bracket")}


def pose(dy, dx, dz):
    out = {}
    for n, s in P.items():
        t = V(0, 0, 0)
        if n in Y_MOV:
            t += V(0, dy, 0)
        if n in X_MOV:
            t += V(dx, 0, 0)
        if n in Z_MOV:
            t += V(0, 0, dz)
        s2 = s.copy()
        s2.translate(t)
        out[n] = s2
    return out


hits = {}
names = sorted(P)
for dy, dx, dz in itertools.product((-250, 150), (-150, 150), (-50, 50)):
    S = pose(dy, dx, dz)
    for a, b in itertools.combinations(names, 2):
        if (a, b) in EXPECT or (b, a) in EXPECT:
            continue
        if any(a in g and b in g for g in SAME):
            continue
        if not S[a].BoundBox.intersect(S[b].BoundBox):
            continue
        v = S[a].common(S[b]).Volume
        if v > 1:
            key = (a, b)
            hits.setdefault(key, []).append((dy, dx, dz, round(v)))
lines = []
for (a, b), poses in sorted(hits.items()):
    lines.append("%s x %s : %s" % (a, b, poses))
open(os.path.join(OUT, "motion_check.txt"), "w", encoding="utf-8").write("\n".join(lines) or "none")
print("MOTION_HITS", len(hits))
for l in lines:
    print("  ", l)
