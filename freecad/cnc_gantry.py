# -*- coding: utf-8 -*-
"""
Gantry 3-axis CNC (fixed gantry, moving table) - parametric layout model.
Run:  freecadcmd.exe cnc_gantry.py
Outputs (../output): CNC_Gantry.FCStd, CNC_Gantry.step, part list JSON for the drawing.

Coordinates: X = left/right, Y = front(-)/back(+), Z = up. Units mm.
Work area 300 x 300, Z travel 100. Y travel 600 = 300 machining + 300 loading zone (front).
"""
import os, json, math
import FreeCAD as App
import Part
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "output")
os.makedirs(OUT, exist_ok=True)

# ---------------- parameters ----------------
P = dict(
    travel_x=300, travel_y=600, travel_z=100,
    work=300,                       # usable work area (square)
    stand_h=700,                    # floor -> top of stand
    bed_h=160,                      # steel weldment bed height
    bed_w=820, bed_l=1400,
    rail_y_gap=320,                 # Y rails centre distance (HGR25)
    table_w=440, table_l=420, table_t=40,
    spindle_y=120,                  # spindle axis Y (machining centre)
    col_w=140, col_d=200,           # gantry columns
    beam_h=220, beam_d=180,         # gantry beam (welded box)
    clear=220,                      # table top -> beam underside
    spindle_d=80, spindle_l=230,
)
p = P
Z_BED = p["stand_h"]
Z_BEDTOP = Z_BED + p["bed_h"]
RAIL_H = 40                         # rail+block height HGR25
Z_TABLE = Z_BEDTOP + RAIL_H
Z_TABLETOP = Z_TABLE + p["table_t"]
# table centre Y range: work position (under spindle) .. load position (front)
TABLE_Y_WORK = p["spindle_y"]
TABLE_Y_LOAD = p["spindle_y"] - p["travel_y"]
Y_BED0 = -p["bed_l"] / 2 - 100      # bed front edge
Y_BED1 = Y_BED0 + p["bed_l"]

parts = []   # (name, shape, group, material, note)


def box(name, sx, sy, sz, x, y, z, group, mat="", note=""):
    s = Part.makeBox(sx, sy, sz, V(x, y, z))
    parts.append((name, s, group, mat, note))
    return s


def cyl(name, r, h, base, axis, group, mat="", note=""):
    s = Part.makeCylinder(r, h, base, axis)
    parts.append((name, s, group, mat, note))
    return s


def tube(name, sx, sy, sz, x, y, z, t, axis, group, mat="Q235 tube", note=""):
    """Rectangular hollow section along axis 'x'|'y'|'z'."""
    outer = Part.makeBox(sx, sy, sz, V(x, y, z))
    d = {"x": (0, t, t), "y": (t, 0, t), "z": (t, t, 0)}[axis]
    inner = Part.makeBox(sx - 2 * d[0], sy - 2 * d[1], sz - 2 * d[2],
                         V(x + d[0], y + d[1], z + d[2]))
    s = outer.cut(inner)
    parts.append((name, s, group, mat, note))
    return s


# ======================= 1. STAND (contains coolant tank) =================
leg = 80
sw, sl = p["bed_w"] + 80, p["bed_l"]
sx0, sy0 = -sw / 2, Y_BED0
for i, (lx, ly) in enumerate([(sx0, sy0), (sx0 + sw - leg, sy0),
                              (sx0, sy0 + sl - leg), (sx0 + sw - leg, sy0 + sl - leg)]):
    tube(f"Stand_leg_{i+1}", leg, leg, p["stand_h"] - 60, lx, ly, 0, 4, "z",
         "01 Stand", "Q235 80x80x4")
# top & bottom rings
for zz, tag in [(p["stand_h"] - 60, "top"), (120, "low")]:
    tube(f"Stand_{tag}_L", leg, sl, 60, sx0, sy0, zz, 4, "y", "01 Stand", "Q235 80x60x4")
    tube(f"Stand_{tag}_R", leg, sl, 60, sx0 + sw - leg, sy0, zz, 4, "y", "01 Stand", "Q235 80x60x4")
    tube(f"Stand_{tag}_F", sw - 2 * leg, leg, 60, sx0 + leg, sy0, zz, 4, "x", "01 Stand", "Q235 80x60x4")
    tube(f"Stand_{tag}_B", sw - 2 * leg, leg, 60, sx0 + leg, sy0 + sl - leg, zz, 4, "x", "01 Stand", "Q235 80x60x4")
for i, (lx, ly) in enumerate([(sx0, sy0), (sx0 + sw - leg, sy0),
                              (sx0, sy0 + sl - leg), (sx0 + sw - leg, sy0 + sl - leg)]):
    cyl(f"Leveling_foot_{i+1}", 30, 20, V(lx + leg / 2, ly + leg / 2, -20), V(0, 0, 1),
        "01 Stand", "M16 leveling foot")
    # (stand sits on feet; feet go below z=0 for clarity)

# ======================= 2. BED (steel weldment) =========================
bw, bl = p["bed_w"], p["bed_l"]
bx0 = -bw / 2
box("Bed_top_plate", bw, bl, 30, bx0, Y_BED0, Z_BEDTOP - 30, "02 Bed", "Q235 t30, stress relieved, rails face milled")
box("Bed_bottom_plate", bw, bl, 20, bx0, Y_BED0, Z_BED, "02 Bed", "Q235 t20")
for i, xx in enumerate([bx0, -p["rail_y_gap"] / 2 - 10, p["rail_y_gap"] / 2 - 10, bx0 + bw - 20]):
    box(f"Bed_long_web_{i+1}", 20, bl, p["bed_h"] - 50, xx, Y_BED0, Z_BED + 20, "02 Bed", "Q235 t20")
n_ribs = 7
for i in range(n_ribs):
    yy = Y_BED0 + i * (bl - 20) / (n_ribs - 1)
    box(f"Bed_cross_rib_{i+1}", bw - 40, 20, p["bed_h"] - 50, bx0 + 20, yy, Z_BED + 20, "02 Bed", "Q235 t20")

# ======================= 3. Y AXIS (moving table) =========================
y_rail_l = 1200
yr0 = Y_BED0 + (bl - y_rail_l) / 2
for side, xc in (("L", -p["rail_y_gap"] / 2), ("R", p["rail_y_gap"] / 2)):
    box(f"Y_rail_{side}", 23, y_rail_l, 22, xc - 11.5, yr0, Z_BEDTOP, "03 Y-axis", "HGR25 L=1200")
    for k, dy in enumerate((-110, 110)):
        box(f"Y_block_{side}{k+1}", 48, 84, 18, xc - 24, TABLE_Y_WORK + dy - 42, Z_BEDTOP + 22,
            "03 Y-axis", "HGH25CA")
# ball screw SFU2010 in centre
ys_l = 1150
cyl("Y_ballscrew", 10, ys_l, V(0, Y_BED0 + (bl - ys_l) / 2, Z_BEDTOP + 30), V(0, 1, 0),
    "03 Y-axis", "SFU2010 L=1150, C7")
box("Y_nut_housing", 70, 60, 50, -35, TABLE_Y_WORK - 30, Z_BEDTOP + 5, "03 Y-axis", "DSG20H nut seat")
box("Y_BK_support", 90, 40, 60, -45, Y_BED0 + 60, Z_BEDTOP, "03 Y-axis", "BK15 fixed end (front)")
box("Y_BF_support", 90, 40, 60, -45, Y_BED1 - 100, Z_BEDTOP, "03 Y-axis", "BF15 floating end (rear)")
box("Y_motor", 86, 120, 86, -43, Y_BED0 - 120 + 20, Z_BEDTOP + 30 - 43, "03 Y-axis", "Servo 750W / NEMA34, belt or direct")
# moving table (T-slot) + bellows covers
tx0 = -p["table_w"] / 2
tbl = Part.makeBox(p["table_w"], p["table_l"], p["table_t"],
                   V(tx0, TABLE_Y_WORK - p["table_l"] / 2, Z_TABLE))
for k in range(5):  # T-slots along Y
    sx = tx0 + 60 + k * 80
    tbl = tbl.cut(Part.makeBox(14, p["table_l"], 12, V(sx - 7, TABLE_Y_WORK - p["table_l"] / 2, Z_TABLETOP - 12)))
parts.append(("Work_table", tbl, "03 Y-axis", "HT250 / Q235 t40, 5x T-slot 14", "440x420 table, work area 300x300"))
# work area outline (thin plate for visualisation only)
box("Work_area_300x300", p["work"], p["work"], 0.5, -p["work"] / 2, TABLE_Y_WORK - p["work"] / 2,
    Z_TABLETOP, "03 Y-axis", "reference", "usable 300x300")
cov_w = p["rail_y_gap"] + 80
front_len = (TABLE_Y_WORK - p["table_l"] / 2) - (Y_BED0 + 40)
rear_len = (Y_BED1 - 40) - (TABLE_Y_WORK + p["table_l"] / 2)
box("Y_bellows_front", cov_w, front_len, 60, -cov_w / 2, Y_BED0 + 40, Z_BEDTOP, "03 Y-axis",
    "Bellows way cover (coolant proof)")
box("Y_bellows_rear", cov_w, rear_len, 60, -cov_w / 2, TABLE_Y_WORK + p["table_l"] / 2, Z_BEDTOP,
    "03 Y-axis", "Bellows way cover (coolant proof)")

# ======================= 4. FIXED GANTRY =================================
z_beam0 = Z_TABLETOP + p["clear"]
beam_y0 = p["spindle_y"] + 178          # beam front face (spindle sits in front of Z plate)
span_in = p["travel_x"] + 260 + 80      # inner span between columns
col_x_in = span_in / 2
for side, sgn in (("L", -1), ("R", 1)):
    x0 = col_x_in if sgn > 0 else -col_x_in - p["col_w"]
    tube(f"Gantry_column_{side}", p["col_w"], p["col_d"], z_beam0 + p["beam_h"] - Z_BEDTOP,
         x0, beam_y0 - 10, Z_BEDTOP, 12, "z", "04 Gantry", "Welded box 140x200 t12 (Q235)")
beam_l = span_in + 2 * p["col_w"]
tube("Gantry_beam", beam_l, p["beam_d"], p["beam_h"], -beam_l / 2, beam_y0, z_beam0, 12, "x",
     "04 Gantry", "Welded box 220x180 t12, filled epoxy granite optional")

# ======================= 5. X AXIS ========================================
x_rail_l = beam_l - 40
for k, zz in enumerate((z_beam0 + 30, z_beam0 + p["beam_h"] - 50)):
    box(f"X_rail_{k+1}", x_rail_l, 22, 23, -x_rail_l / 2, beam_y0 - 22, zz, "05 X-axis", "HGR20")
cyl("X_ballscrew", 8, x_rail_l - 60, V(-(x_rail_l - 60) / 2, beam_y0 - 30, z_beam0 + p["beam_h"] / 2),
    V(1, 0, 0), "05 X-axis", "SFU1605, C7")
box("X_motor", 120, 86, 86, beam_l / 2, beam_y0 - 73, z_beam0 + p["beam_h"] / 2 - 43, "05 X-axis",
    "Servo 400W / NEMA23-34")
xc_w, xc_h = 240, 380
xc_y0 = beam_y0 - 22 - 18 - 30
box("X_carriage_plate", xc_w, 30, xc_h, -xc_w / 2, xc_y0, z_beam0 - 120, "05 X-axis", "6061-T6 / steel t30")

# ======================= 6. Z AXIS + SPINDLE ==============================
for side, xx in (("L", -80), ("R", 80)):
    box(f"Z_rail_{side}", 20, 18, xc_h, xx - 10, xc_y0 - 18, z_beam0 - 120, "06 Z-axis", "HGR20")
cyl("Z_ballscrew", 8, xc_h - 40, V(0, xc_y0 - 25, z_beam0 - 100), V(0, 0, 1), "06 Z-axis", "SFU1605")
box("Z_motor", 86, 86, 120, -43, xc_y0 - 68, z_beam0 + xc_h - 120, "06 Z-axis", "Servo 400W w/ brake")
zs_y0 = xc_y0 - 18 - 30
z_slide_z = Z_TABLETOP + p["travel_z"] + 140   # Z at top: tool tip = table top + 120
box("Z_slide_plate", 200, 30, 300, -100, zs_y0, z_slide_z, "06 Z-axis", "Steel t30")
sp_y = p["spindle_y"]
box("Spindle_clamp", 130, zs_y0 - (sp_y - 65), 70, -65, sp_y - 65, z_slide_z + 30, "06 Z-axis",
    "Clamp D80")
cyl("Spindle", p["spindle_d"] / 2, p["spindle_l"], V(0, sp_y, z_slide_z - 60), V(0, 0, 1), "06 Z-axis",
    "2.2kW water-cooled ER20 D80")
cyl("Tool_ER20", 5, 60, V(0, sp_y, z_slide_z - 120), V(0, 0, 1), "06 Z-axis", "Tool stick-out ref")

# ======================= 7. COOLANT / AIR / CHIP SYSTEM ===================
grp = "07 Coolant & Air"
# splash guard enclosure on bed (open front for loading)
g_h, g_t = 320, 2
gx = bw / 2 + 10
box("Guard_side_L", g_t, bl, g_h, -gx - g_t, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 t2 splash guard")
box("Guard_side_R", g_t, bl, g_h, gx, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 t2 splash guard")
box("Guard_rear", 2 * gx, g_t, g_h, -gx, Y_BED1, Z_BEDTOP - 40, grp, "SUS304 t2")
box("Guard_front_lip", 2 * gx, g_t, 120, -gx, Y_BED0 - g_t, Z_BEDTOP - 40, grp, "SUS304 t2 low lip (loading side)")
box("Guard_window_L", g_t, 500, 200, -gx - g_t - 0.1, p["spindle_y"] - 250, Z_BEDTOP + 60, grp,
    "PC window 5mm")
# coolant collection trough: sloped pan around bed perimeter -> drain at rear
box("Coolant_trough_L", 60, bl, 40, -gx, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 trough, slope 1:100 to rear")
box("Coolant_trough_R", 60, bl, 40, gx - 60, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 trough, slope 1:100 to rear")
box("Coolant_trough_rear", 2 * gx, 80, 40, -gx, Y_BED1 - 80, Z_BEDTOP - 40, grp, "collects to drain")
drain_x, drain_y = gx - 30, Y_BED1 - 40
cyl("Drain_pipe", 20, Z_BEDTOP - 40 - 520, V(drain_x, drain_y, 520), V(0, 0, 1), grp, "PVC D40 drain")
# coolant tank (inside stand, rear half)
tank_l, tank_w, tank_h = 620, 560, 330
tank_y0 = Y_BED1 - 80 - tank_l
tk = Part.makeBox(tank_w, tank_l, tank_h, V(-tank_w / 2, tank_y0, 185))
tk = tk.cut(Part.makeBox(tank_w - 6, tank_l - 6, tank_h, V(-tank_w / 2 + 3, tank_y0 + 3, 188)))
parts.append(("Coolant_tank", tk, grp, "SUS304 t3, ~100 L (fill 80 L)", "on castors, slides out rear"))
# chip filter: basket + magnetic/mesh, sits on tank, receives drain
fb = Part.makeBox(220, 220, 180, V(drain_x - 110 - 60, drain_y - 220 + 30, 515 - 180 + 5))
fb = fb.cut(Part.makeBox(210, 210, 180, V(drain_x - 105 - 60, drain_y - 215 + 30, 515 - 180 + 10)))
parts.append(("Chip_filter_basket", fb, grp, "SUS304 perforated basket + 60 mesh bag",
              "removable, catches Al/steel chips"))
box("Filter_baffle", tank_w - 6, 3, tank_h - 60, -tank_w / 2 + 3, tank_y0 + tank_l / 2, 188, grp,
    "Settling baffle (dirty | clean side)")
# pump on clean side of tank
cyl("Coolant_pump", 45, 160, V(-150, tank_y0 + 140, 185 + tank_h - 120), V(0, 0, 1), grp,
    "Immersion pump 90W, 25 L/min, 0.2 MPa")
cyl("Pump_motor", 55, 110, V(-150, tank_y0 + 140, 185 + tank_h), V(0, 0, 1), grp, "pump motor")
# coolant supply hose: pump -> up stand -> along guard -> drag chain -> spindle nozzle
hose_pts = [V(-150, tank_y0 + 140, 185 + tank_h + 110), V(-150, tank_y0 + 140, 640),
            V(-gx + 30, Y_BED1 - 60, 640), V(-gx + 30, Y_BED1 - 60, z_beam0 + p["beam_h"] + 40),
            V(-60, xc_y0 + 15, z_beam0 + p["beam_h"] + 40)]
hose = None
for a, b in zip(hose_pts[:-1], hose_pts[1:]):
    seg = Part.makeCylinder(6, (b - a).Length, a, (b - a))
    hose = seg if hose is None else hose.fuse(seg)
parts.append(("Coolant_hose", hose, grp, "PU 12x8 hose in drag chain", ""))
# nozzles on spindle clamp (coolant x2 loc-line, air x1)
for k, (ang, name, note) in enumerate([(200, "Coolant_nozzle_1", "Loc-Line 1/4\" coolant"),
                                       (340, "Coolant_nozzle_2", "Loc-Line 1/4\" coolant"),
                                       (270, "Air_blow_nozzle", "Air blast / mist, 0.5 MPa")]):
    a = math.radians(ang)
    base = V(55 * math.cos(a), sp_y + 55 * math.sin(a), z_slide_z - 10)
    tip = V(12 * math.cos(a), sp_y + 12 * math.sin(a), z_slide_z - 100)
    cyl(name, 4, (tip - base).Length, base, tip - base, grp, note)
box("Air_solenoid_FRL", 60, 40, 120, -gx - 130, Y_BED1 - 120, 560, grp,
    "FRL + 24V solenoid valve (M7/M8 coolant/air via controller)")
box("Drag_chain_X", beam_l - 100, 40, 30, -(beam_l - 100) / 2, beam_y0 + 30, z_beam0 + p["beam_h"], grp,
    "Drag chain 25x38 (cables, coolant, air)")

# ======================= build document ==================================
doc = App.newDocument("CNC_Gantry")
groups = {}
for name, shape, group, mat, note in parts:
    if group not in groups:
        groups[group] = doc.addObject("App::DocumentObjectGroup", group.replace(" ", "_").replace("&", "and"))
        groups[group].Label = group
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.addProperty("App::PropertyString", "Material", "CNC").Material = mat
    o.addProperty("App::PropertyString", "Note", "CNC").Note = note
    groups[group].addObject(o)
for k, v in P.items():
    pass
doc.recompute()
fc = os.path.join(OUT, "CNC_Gantry.FCStd")
doc.saveAs(fc)
Part.export([o for o in doc.Objects if o.TypeId == "Part::Feature"], os.path.join(OUT, "CNC_Gantry.step"))

# key dimensions for drawing/report
info = dict(
    params=P,
    overall=dict(),
    z_levels=dict(bed=Z_BED, bed_top=Z_BEDTOP, table_top=Z_TABLETOP, beam_bottom=z_beam0,
                  beam_top=z_beam0 + p["beam_h"]),
    table_y=dict(work=TABLE_Y_WORK, load=TABLE_Y_LOAD),
    parts=[dict(name=n, group=g, material=m, note=t) for n, s, g, m, t in parts],
)
comp = Part.makeCompound([s for _, s, _, _, _ in parts])
bb = comp.BoundBox
info["overall"] = dict(x=round(bb.XLength), y=round(bb.YLength), z=round(bb.ZLength),
                       xmin=bb.XMin, ymin=bb.YMin, zmin=bb.ZMin, xmax=bb.XMax, ymax=bb.YMax, zmax=bb.ZMax)
with open(os.path.join(OUT, "cnc_info.json"), "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=1)
print("OK", fc, info["overall"])
