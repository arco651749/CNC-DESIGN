# -*- coding: utf-8 -*-
"""r6 collision sweep (18 poses) + clearances
Run from the repository root:  freecadcmd freecad/revisions/07_motion_check_r6.py
(steps 01..07 in order; each opens the previous output in output/v3/)"""
import os
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
LOG = os.path.join(ROOT, 'output', 'v3', 'logs'); os.makedirs(LOG, exist_ok=True)
import os, itertools
import FreeCAD as App
from FreeCAD import Vector as V

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "v3")
doc = App.openDocument(ROOT+"/output/v3/CNC_v3_r6.FCStd")
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
          ("X_ballscrew", "X_nut_bracket"), ("X_journal","X_support_fixed"), ("Y_journal","Y_support_fixed"), ("Z_journal","Z_support_fixed")}


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
for dy, dx, dz in itertools.product((-250, -50, 150), (-150, 0, 150), (-50, 50)):
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
open(LOG+"/r6_motion.txt", "w", encoding="utf-8").write("\n".join(lines) or "none")
print("MOTION_HITS", len(hits))
for l in lines:
    print("  ", l)
rep=[]
d=lambda a,b,S=P: S[a].distToShape(S[b])[0]
rep.append("Y_motor - datum %.1f | Y_motor_plate - datum %.1f | Y_coupling - datum %.1f | Y_support - Y_nut_bracket (dy-250) %.1f" % (d("Y_motor","Datum_base_plate"),d("Y_motor_block","Datum_base_plate"),d("Y_coupling","Datum_base_plate"),d("Y_support_fixed","Y_nut_bracket",pose(-250,0,0))))
S=pose(150,0,0); rep.append("dy+150: Y_motor - Servo_amp_Y %.1f, Y_motor - Column_foot_R %.1f" % (d("Y_motor","Servo_amp_Y",S),d("Y_motor","Column_foot_R",S)))
S=pose(0,150,0); rep.append("dx+150: X_nut_bracket - X_support_fixed %.1f, X_carriage - X_support_fixed %.1f, X_carriage - joint_plate_R %.1f" % (d("X_nut_bracket","X_support_fixed",S),d("X_carriage_plate","X_support_fixed",S),d("X_carriage_plate","Gantry_joint_plate_R",S)))
rep.append("Z_motor_plate - Z_support_fixed %.1f, Z_coupling - Z_support_fixed %.1f" % (d("Z_motor_bracket","Z_support_fixed"),d("Z_coupling","Z_support_fixed")))
S=pose(0,0,50); rep.append("dz+50: Z_block_R2 - Z_support_fixed %.1f, Z_slide - Z_support %.1f" % (d("Z_block_R2","Z_support_fixed",S),d("Z_slide_plate","Z_support_fixed",S)))
open(LOG+"/r6_clear.txt","w").write("\n".join(rep))
extra=["Z_motor_bracket - Z_rail_R %.1f, Z_motor_bracket - Z_coupling %.1f" % (d("Z_motor_bracket","Z_rail_R"), d("Z_motor_bracket","Z_coupling"))]
S=pose(0,0,50); extra.append("dz+50: Z_motor_bracket - Z_slide %.1f" % d("Z_motor_bracket","Z_slide_plate",S))
open(LOG+"/r6_clear.txt","a").write("\n"+"\n".join(extra))
S=pose(-250,0,0); extra2=["dy-250: Y_support - Y_nut_bracket %.1f" % d("Y_support_fixed","Y_nut_bracket",S)]
S=pose(150,0,0); extra2.append("dy+150: Work_table - Servo_amp_Y %.1f, Work_table - Gantry_column_R %.1f, Y_motor - Servo %.1f" % (d("Work_table","Servo_amp_Y",S), d("Work_table","Gantry_column_R",S), d("Y_motor","Servo_amp_Y",S)))
open(LOG+"/r6_clear.txt","a").write("\n"+"\n".join(extra2))
S=pose(-250,0,0); e=["dy-250: Y_motor - Datum %.1f, Work_table - Datum %.1f" % (d("Y_motor","Datum_base_plate",S), d("Work_table","Datum_base_plate",S))]
open(LOG+"/r6_clear.txt","a").write("\n"+"\n".join(e))
S=pose(0,0,-50); e=["dz-50: Spindle_clamp bottom z %.0f, Z_slide bottom z %.0f, carriage bottom z %.0f, spindle body bottom z %.0f, tool tip z %.0f" % (S["Spindle_clamp"].BoundBox.ZMin,S["Z_slide_plate"].BoundBox.ZMin,S["X_carriage_plate"].BoundBox.ZMin,S["Spindle_body"].BoundBox.ZMin,S["Tool_D5"].BoundBox.ZMin)]
e.append("dz+50: Spindle_fan_cover - Z_ball_nut %.1f, Spindle_body - Z_ballscrew %.1f" % (d("Spindle_fan_cover","Z_ball_nut",pose(0,0,50)), d("Spindle_body","Z_ballscrew",pose(0,0,50))))
open(LOG+"/r6_clear.txt","a").write("\n"+"\n".join(e))
e=["Y_motor_block - Y_coupling %.1f, Y_motor_block - Y_support %.1f, Y_motor_block - Y_rail_R %.1f" % (d("Y_motor_block","Y_coupling"),d("Y_motor_block","Y_support_fixed"),d("Y_motor_block","Y_rail_R"))]
S=pose(-250,0,0); e.append("dy-250: Y_motor_block - Y_nut_bracket %.1f, Y_motor_block - datum %.1f" % (d("Y_motor_block","Y_nut_bracket",S), d("Y_motor_block","Datum_base_plate",S)))
S=pose(0,150,0); e.append("dx+150: X_carriage - X_motor_block %.1f; X_motor_block - X_support %.1f, X_motor_block - joint_plate_R %.1f" % (d("X_carriage_plate","X_motor_block",S), d("X_motor_block","X_support_fixed"), d("X_motor_block","Gantry_joint_plate_R")))
open(LOG+"/r6_clear.txt","a").write("\n"+"\n".join(e))
