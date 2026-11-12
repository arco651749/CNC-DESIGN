# -*- coding: utf-8 -*-
"""
CNC v3 assembly in FreeCAD with vendor STEP parts (MISUMI + Mitsubishi).
Run:  freecadcmd.exe freecad/assemble_v3.py
Out:  output/v3/CNC_v3.FCStd, CNC_v3.step, CNC_v3_BOM.csv, interference report (stdout + txt)

Bed weldment removed: the machine stands on the datum base plate (top face = z 0).
Axes: X left/right, Y front(-)/back(+), Z up. Spindle axis at x=0, y=0.
Model state: table at work-centre (work area centred under the spindle), X centred, Z mid-travel.
Vendor CAD stays in vendor/ (not in git: MISUMI / Mitsubishi CAD terms).
"""
import os, glob, math, csv
import FreeCAD as App
import Part
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VEND = os.path.join(ROOT, "vendor")
OUT = os.path.join(ROOT, "output", "v3")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- helpers
_cache = {}


def vendor(name):
    """List of solids of a vendor STEP (cached)."""
    if name not in _cache:
        f = glob.glob(os.path.join(VEND, "*", name, "step", "**", "*.st*p"), recursive=True)
        if not f:
            raise FileNotFoundError(name)
        _cache[name] = Part.read(f[0]).Solids
    return [s.copy() for s in _cache[name]]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def put(shape, ex, ey, ref, target):
    """Rigidly map local axes X->ex, Y->ey (Z->ex x ey) and local point ref onto machine point target."""
    ez = cross(ex, ey)
    m = App.Matrix(ex[0], ey[0], ez[0], 0,
                   ex[1], ey[1], ez[1], 0,
                   ex[2], ey[2], ez[2], 0,
                   0, 0, 0, 1)
    s = shape.copy()
    s.translate(V(*ref) * -1)
    s.transformShape(m)
    s.translate(V(*target))
    return s


def shifted(shape, dx=0, dy=0, dz=0):
    s = shape.copy()
    s.translate(V(dx, dy, dz))
    return s


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cylx(x0, x1, y, z, r):
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def cyly(y0, y1, x, z, r):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def cylz(z0, z1, x, y, r):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))


def cut_screw(solids, length):
    """C-KBS STEP = [shaft (local X 0..L, D16), nut]. Trim the shaft to `length` (shaft is a plain cylinder in the
    vendor model, so trimming keeps the vendor geometry; the real screw is ordered at this length)."""
    shaft, nut = solids[0], solids[1]
    shaft = shaft.common(box(0, length, -20, 20, -20, 20))
    return shaft, nut


PARTS = []   # (name, group, shape, source, spec)


def add(name, group, shape, source, spec):
    PARTS.append((name, group, shape, source, spec))
    return shape


MIS, MEL, OWN = "MISUMI", "Mitsubishi Electric", "custom (machined)"

# ---------------------------------------------------------------- key dimensions
Z_TB = 58.0            # table underside (rail base 42 + 16 carrier bar)
Z_TT = Z_TB + 40       # table top = 98
CLEAR = 220            # table top -> beam underside
Z_BEAM0 = Z_TT + CLEAR  # 318
BEAM_H = 160
Z_BEAM1 = Z_BEAM0 + BEAM_H
YRP = 192.0            # X rail base plane = rail plate front face
YXB = YRP - 28         # X block mount face 164
YC1 = YXB - 30         # carriage rear face (30 mm spacer bars) 134
YC0 = YC1 - 30         # carriage front face 104 (= Z rail base)
YZB = YC0 - 28         # Z block mount face 76
YS1 = YZB - 14         # slide rear face (14 mm spacer bars) 62
YS0 = YS1 - 28         # slide front face 34
X_SCREW_Y = YRP - 25   # 167 (support bore height 25)
X_SCREW_Z = Z_BEAM0 + 80
X_RAIL_Z = (Z_BEAM0 + 20, Z_BEAM0 + 140)
Z_SCREW_Y = YC0 - 25   # 79
COL_X_IN = 240         # table 440 + 2 x 20 clearance
Y_SCREW_Z = 33.0
TIP_Z = Z_TT + 70      # tool tip at mid Z travel

# ================================================================ 1. datum base plate (bed removed)
add("Datum_base_plate", "01 Base", box(-345, 345, -210, 385, -30, 0), OWN,
    "Q235 t30 690x595 milled datum plate: Y block seats, Y nut seat, column feet (bed weldment removed)")

# ================================================================ 2. Y axis (inverted guide, moving table)
grp = "02 Y-axis"
YR = vendor("SE2RZ42-680")               # rail X[-20,660], blocks s1/s3 + grease nipples s2/s4
EX_Y, EY_Y = (0, 1, 0), (0, 0, -1)       # rail along +Y, block mount face (local Y=42) down on the plate
for side, xr in (("L", -160), ("R", 160)):
    tgt = (xr, -270, 0)                  # local x=-20 (rail front end) at y=-290
    add(f"Y_rail_{side}", grp, put(YR[0], EX_Y, EY_Y, (0, 42, 0), tgt), MIS, "SE2RZ42-680 rail (inverted, moves with table)")
    for k, (blk, nip, c0, yc) in enumerate(((YR[1], YR[2], 48.3, -65), (YR[3], YR[4], 165.1, 65))):
        dx = (yc + 270) - c0
        add(f"Y_block_{side}{k+1}", grp, put(shifted(blk.fuse(nip), dx), EX_Y, EY_Y, (0, 42, 0), tgt), MIS,
            "SE2RZ42 block (fixed on datum plate)")
    add(f"Y_carrier_bar_{side}", grp, box(xr - 20, xr + 20, -210, 210, 42, Z_TB), OWN, "steel bar t16, rail -> table")

tbl = box(-220, 220, -210, 210, Z_TB, Z_TT)
for xs in (-160, -80, 0, 80, 160):
    tbl = tbl.cut(box(xs - 7, xs + 7, -210, 210, Z_TT - 12, Z_TT))
add("Work_table", grp, tbl, OWN, "440x420x40, 5x T-slot 14, work area 300x300")

# Y screw: fixed-free, rides with the table; nut fixed on the plate
ys, yn = cut_screw(vendor("C-KBS1505-545"), 545)
EX_S, EY_S = (0, 1, 0), (-1, 0, 0)       # nut flats (local Z) vertical
add("Y_ballscrew", grp, put(ys, EX_S, EY_S, (0, 0, 0), (0, -375, Y_SCREW_Z)), MIS, "C-KBS1505-545 (D16 lead 5, C5)")
add("Y_ball_nut", grp, put(shifted(yn, 225 - 65.3), EX_S, EY_S, (0, 0, 0), (0, -375, Y_SCREW_Z)), MIS,
    "C-KBS1505 nut, fixed (y=-150)")
nb = box(-60, 60, -129, -114, 0, 54).cut(cyly(-130, -113, 0, Y_SCREW_Z, 18))
add("Y_nut_bracket", grp, nb, OWN, "steel t15, nut flange seat on datum plate")
# fixed support hangs under the table rear, base up
add("Y_support_fixed", grp, put(vendor("C-TEK12")[0].fuse(vendor("C-TEK12")[4]), (0, 1, 0), (0, 0, -1), (0, 25, 0),
                                 (0, 170, Y_SCREW_Z)), MIS, "C-TEK12 fixed support (under table)")
add("Y_journal", grp, cyly(170, 233.5, 0, Y_SCREW_Z, 6), MIS, "screw end journal D12 (part of C-KBS end machining)")
cpl = vendor("CPJC40-RD-12-14")
cpl = cpl[0].fuse(cpl[1]).fuse(cpl[2])
add("Y_coupling", grp, put(cpl, (0, 1, 0), (0, 0, 1), (0, 0, 0), (0, 208.5, Y_SCREW_Z)), MIS, "CPJC40-RD-12-14")
add("Y_motor", grp, put(vendor("HG-KR43")[0], (-1, 0, 0), (0, 0, -1), (0, 0, 0), (0, 279.5, Y_SCREW_Z)), MEL,
    "HG-KR43 400 W, rides with the table")
yb = box(-45, 45, 195, 279.5, Z_TT, Z_TT + 15).fuse(box(-45, 45, 264.5, 279.5, 3, Z_TT + 15))
yb = yb.cut(cyly(260, 285, 0, Y_SCREW_Z, 25.05))   # spigot bore D50 (motor pilot)
add("Y_motor_bracket", grp, yb, OWN, "L-bracket steel t15 on table top rear, spigot bore D50")

# ================================================================ 3. gantry
grp = "03 Gantry"
for side, xc in (("L", -280), ("R", 280)):
    add(f"Column_foot_{side}", grp, box(xc - 40, xc + 40, YRP - 5, YRP + 175, 0, 18), OWN, "steel foot plate t18")
    add(f"Gantry_column_{side}", grp, put(vendor("HFS8-80160-300")[0], (0, 0, 1), (0, 1, 0), (0, 0, 0),
                                          (xc, YRP + 15 + 80, 18)), MIS, "HFS8-80160-300")
    jx = (320, 332) if xc > 0 else (-332, -320)
    add(f"Gantry_joint_plate_{side}", grp, box(jx[0], jx[1], YRP + 15, YRP + 175, Z_BEAM0 - 100, Z_BEAM1), OWN,
        "Al plate t12, column + beam ends")
for k in range(2):
    add(f"Gantry_beam_{k+1}", grp, put(vendor("HFS8-80160-640")[0], (1, 0, 0), (0, 0, 1), (0, 0, 0),
                                       (-320, YRP + 15 + 40 + 80 * k, Z_BEAM0 + 80)), MIS, "HFS8-80160-640")
add("X_rail_plate", grp, box(-320, 320, YRP, YRP + 15, Z_BEAM0, Z_BEAM1), OWN, "steel t15, front face milled (X rail datum)")

# ================================================================ 4. X axis
grp = "04 X-axis"
XR = vendor("SX2RNL28-600")              # rail X[-30,570], blocks centre 23.5 / 157
for k, zc in enumerate(X_RAIL_Z):
    tgt = (-270, YRP, zc)
    add(f"X_rail_{k+1}", grp, put(XR[0], (1, 0, 0), (0, -1, 0), (0, 0, 0), tgt), MIS, "SX2RNL28-600 rail")
    for j, (blk, c0, xc) in enumerate(((XR[1], 23.5, -60), (XR[2], 157, 60))):
        add(f"X_block_{k+1}{j+1}", grp, put(shifted(blk, (xc + 270) - c0), (1, 0, 0), (0, -1, 0), (0, 0, 0), tgt),
            MIS, "SX2RNL28 block")
    add(f"X_spacer_{k+1}", grp, box(-120, 120, YC1, YXB, zc - 21, zc + 21), OWN, "steel spacer bar t30")
add("X_carriage_plate", grp, box(-120, 120, YC0, YC1, 160, 540), OWN, "steel t30, 240x380")
xs, xn = cut_screw(vendor("C-KBS1505-615"), 540)
EXX, EYX = (1, 0, 0), (0, 0, 1)          # nut flats along Y
add("X_ballscrew", grp, put(xs, EXX, EYX, (0, 0, 0), (-295, X_SCREW_Y, X_SCREW_Z)), MIS, "C-KBS1505-540 (D16 lead 5)")
add("X_ball_nut", grp, put(shifted(xn, 295 - 65.3), EXX, EYX, (0, 0, 0), (-295, X_SCREW_Y, X_SCREW_Z)), MIS,
    "C-KBS1505 nut")
add("X_nut_bracket", grp, box(21, 36, YC1, YRP - 2, X_SCREW_Z - 30, X_SCREW_Z + 30).cut(
    cylx(20, 37, X_SCREW_Y, X_SCREW_Z, 10)), OWN, "steel t15, nut flange -> carriage rear")
tek = vendor("C-TEK12")
add("X_support_fixed", grp, put(tek[0].fuse(tek[4]), (1, 0, 0), (0, -1, 0), (0, 25, 0), (245, X_SCREW_Y, X_SCREW_Z)),
    MIS, "C-TEK12 fixed support")
tef = vendor("C-TEF12")
add("X_support_float", grp, put(tef[0], (1, 0, 0), (0, -1, 0), (10, 25, 0), (-295, X_SCREW_Y, X_SCREW_Z)), MIS,
    "C-TEF12 floating support")
add("X_journal", grp, cylx(245, 308.5, X_SCREW_Y, X_SCREW_Z, 6), MIS, "screw end journal D12")
add("X_coupling", grp, put(cpl, (1, 0, 0), (0, 1, 0), (0, 0, 0), (283.5, X_SCREW_Y, X_SCREW_Z)), MIS, "CPJC40-RD-12-14")
add("X_motor", grp, put(vendor("HG-KR43")[0], (0, 1, 0), (0, 0, -1), (0, 0, 0), (354.5, X_SCREW_Y, X_SCREW_Z)), MEL,
    "HG-KR43 400 W")
xb = box(339.5, 354.5, X_SCREW_Y - 45, YRP + 1, X_SCREW_Z - 35, X_SCREW_Z + 35).cut(
    cylx(335, 360, X_SCREW_Y, X_SCREW_Z, 25.05)).fuse(box(320, 339.5, YRP, YRP + 15, X_SCREW_Z - 35, X_SCREW_Z + 35))
add("X_motor_bracket", grp, xb, OWN, "steel t15 motor plate + arm to rail plate end")

# ================================================================ 5. Z axis + spindle
grp = "05 Z-axis"
ZR = vendor("SX2RNL28-380")              # rail X[-10,370], blocks centre 23.5 / 157
SL0 = 205.0                              # slide plate bottom at mid travel
for side, xr in (("L", -80), ("R", 80)):
    tgt = (xr, YC0, 170)
    add(f"Z_rail_{side}", grp, put(ZR[0], (0, 0, 1), (0, -1, 0), (0, 0, 0), tgt), MIS, "SX2RNL28-380 rail")
    for j, (blk, c0, zc) in enumerate(((ZR[1], 23.5, SL0 + 55), (ZR[2], 157, SL0 + 180))):
        add(f"Z_block_{side}{j+1}", grp, put(shifted(blk, (zc - 170) - c0), (0, 0, 1), (0, -1, 0), (0, 0, 0), tgt),
            MIS, "SX2RNL28 block")
    add(f"Z_spacer_{side}", grp, box(xr - 25, xr + 25, YS1, YZB, SL0, SL0 + 230), OWN, "steel spacer bar t14")
NUT_ZC = SL0 + 115
sl = box(-110, 110, YS0, YS1, SL0, SL0 + 230).cut(box(-28, 28, 54, YS1 + 1, NUT_ZC - 23, NUT_ZC + 23))
add("Z_slide_plate", grp, sl, OWN, "steel t28, pocket for the Z nut")
zs, zn = cut_screw(vendor("C-KBS1505-395"), 330)
EXZ, EYZ = (0, 0, 1), (1, 0, 0)          # nut flats along Y
ZS0 = 504.5 - 330                        # screw bottom (free end)
add("Z_ballscrew", grp, put(zs, EXZ, EYZ, (0, 0, 0), (0, Z_SCREW_Y, ZS0)), MIS, "C-KBS1505-330 (fixed-free)")
add("Z_ball_nut", grp, put(shifted(zn, (NUT_ZC - ZS0) - 65.3), EXZ, EYZ, (0, 0, 0), (0, Z_SCREW_Y, ZS0)), MIS,
    "C-KBS1505 nut (in slide pocket)")
add("Z_support_fixed", grp, put(tek[0].fuse(tek[4]), (0, 0, 1), (0, -1, 0), (0, 25, 0), (0, Z_SCREW_Y, 504.5)), MIS,
    "C-TEK12 fixed support (top)")
add("Z_journal", grp, cylz(504.5, 568, 0, Z_SCREW_Y, 6), MIS, "screw end journal D12")
add("Z_coupling", grp, put(cpl, (0, 0, 1), (1, 0, 0), (0, 0, 0), (0, Z_SCREW_Y, 543)), MIS, "CPJC40-RD-12-14")
add("Z_motor", grp, put(vendor("HG-KR43B")[0], (1, 0, 0), (0, -1, 0), (0, 0, 0), (0, Z_SCREW_Y, 614)), MEL,
    "HG-KR43B 400 W with brake")
zb = box(-48, 48, YS0, YC0, 599, 614).cut(cylz(595, 620, 0, Z_SCREW_Y, 25.05))
for sx in (-1, 1):
    zb = zb.fuse(box(min(sx * 37, sx * 48), max(sx * 37, sx * 48), YC0 - 15, YC0, 520, 599))   # clear of TEK (+-35)
add("Z_motor_bracket", grp, zb, OWN, "steel t15 motor plate + 2 arms on carriage front")

# spindle from spec: 0.8 kW air-cooled, D65 x 188 body, ER11, fan cover, aviation plug
grp = "06 Spindle"
SB = TIP_Z + 41                          # spindle body bottom face
add("Spindle_body", grp, cylz(SB, SB + 188, 0, 0, 32.5), "spindle vendor (modelled from spec)",
    "0.8 kW air-cooled D65x188, 24,000 rpm, 220 V 400 Hz (e.g. HQD GDF65-24Z/0.8)")
add("Spindle_fan_cover", grp, cylz(SB + 188, SB + 214, 0, 0, 32.5).cut(cylz(SB + 196, SB + 215, 0, 0, 26)),
    "spindle vendor (modelled from spec)", "fan cover")
add("Spindle_plug", grp, box(32.5, 52, -8, 8, SB + 186, SB + 206), "spindle vendor (modelled from spec)",
    "aviation plug 4-pin")
add("Spindle_nose", grp, cylz(SB - 5, SB, 0, 0, 11), "spindle vendor (modelled from spec)", "ER11 nose")
add("ER11_nut", grp, cylz(SB - 19, SB - 5, 0, 0, 9.5), "tooling", "ER11 nut D19 M13x0.75")
add("Tool_D5", grp, cylz(TIP_Z, SB - 19, 0, 0, 2.5), "tooling", "end mill D5 (reference)")  # noqa
cl = box(-48, 48, -47, YS0, SB + 110, SB + 180).cut(cylz(SB + 100, SB + 190, 0, 0, 32.5)).cut(
    box(-1, 1, -48, -30, SB + 100, SB + 190))
add("Spindle_clamp", grp, cl, OWN, "split clamp D65, Al, bolted to slide front")

# ================================================================ 6. electrics on the beam rear
grp = "07 Electrics"
for i, xc in enumerate((-120, -60, 0)):
    add(f"Servo_amp_{'XYZ'[i]}", grp, put(vendor("MR-J4-40A")[0].fuse(vendor("MR-J4-40A")[1]), (-1, 0, 0), (0, 0, 1),
                                         (0, 0, 0), (xc, YRP + 175, X_SCREW_Z)), MEL, "MR-J4-40A")

# ================================================================ build document + checks
doc = App.newDocument("CNC_v3")
groups = {}
objs = []
for name, group, shape, src, spec in PARTS:
    if group not in groups:
        g = doc.addObject("App::DocumentObjectGroup", "G_" + group.split()[0])
        g.Label = group
        groups[group] = g
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.addProperty("App::PropertyString", "Source", "CNC").Source = src
    o.addProperty("App::PropertyString", "Spec", "CNC").Spec = spec
    groups[group].addObject(o)
    objs.append(o)
doc.recompute()
doc.saveAs(os.path.join(OUT, "CNC_v3.FCStd"))
Part.export(objs, os.path.join(OUT, "CNC_v3.step"))

# interference: pairwise common volume (bbox prefilter)
EXPECT = {  # touching / nested by design (fits, bores, clamps)
    ("Y_ballscrew", "Y_ball_nut"), ("X_ballscrew", "X_ball_nut"), ("Z_ballscrew", "Z_ball_nut"),
    ("Y_journal", "Y_support_fixed"), ("Y_journal", "Y_coupling"), ("X_journal", "X_support_fixed"),
    ("X_journal", "X_coupling"), ("Z_journal", "Z_support_fixed"), ("Z_journal", "Z_coupling"),
    ("X_ballscrew", "X_support_float"), ("Y_coupling", "Y_motor"), ("X_coupling", "X_motor"), ("Z_coupling", "Z_motor"),
}
rep = []
n = len(PARTS)
for i in range(n):
    for j in range(i + 1, n):
        a, b = PARTS[i], PARTS[j]
        if (a[0], b[0]) in EXPECT or (b[0], a[0]) in EXPECT:
            continue
        ba, bb = a[2].BoundBox, b[2].BoundBox
        if not ba.intersect(bb):
            continue
        try:
            v = a[2].common(b[2]).Volume
        except Exception:
            v = -1
        if v > 1.0 or v < 0:
            rep.append((v, a[0], b[0]))
rep.sort(reverse=True)
lines = ["%10.0f mm3  %s  x  %s" % r for r in rep]
open(os.path.join(OUT, "interference.txt"), "w", encoding="utf-8").write("\n".join(lines) or "none")
print("INTERFERENCES", len(rep))
for l in lines[:40]:
    print("  ", l)

# BOM
rows = {}
for name, group, shape, src, spec in PARTS:
    import re as _re
    key = (group, _re.split(r"[,(]", spec)[0].strip() if src in (MIS, MEL) else name.rstrip("0123456789_LR"), src)
    rows.setdefault(key, [0, spec])[0] += 1
with open(os.path.join(OUT, "CNC_v3_BOM.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["group", "item", "qty", "source", "spec"])
    for (g, item, src), (q, spec) in sorted(rows.items()):
        w.writerow([g, item, q, src, spec])
bb = Part.makeCompound([p[2] for p in PARTS]).BoundBox
print("PARTS", len(PARTS), "ENVELOPE %.0f x %.0f x %.0f" % (bb.XLength, bb.YLength, bb.ZLength),
      "Z[%.0f,%.0f]" % (bb.ZMin, bb.ZMax))
