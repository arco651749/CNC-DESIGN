# -*- coding: utf-8 -*-
"""
Gantry 3-axis CNC v2 (fixed gantry, moving table) - parametric layout model, CadQuery.
Run:  python cad/cnc_gantry.py
Outputs (../output): CNC_Gantry.step (named + coloured assembly), cnc_info.json (parts / key dims).

Coordinates: X = left/right, Y = front(-)/back(+), Z = up. Units mm.
Work area 300 x 300, Z travel 100. Y travel 400 = 300 machining + 100 loading stroke (front).

v2 changes vs v1 (FreeCAD):
  - aluminium, tools <= D5, manual tool change, feed <= 100 mm/s
  - axis motors Mitsubishi HG-KR43 400 W x3 (Z: HG-KR43B with brake), drivers MR-J4-40A x3
  - spindle: 0.8 kW air-cooled electro-spindle D65 x 188, ER11, 24,000 rpm, VFD (e.g. Delta MS300)
  - ball screws: DFU double-nut preload, lead 5 on all axes (Y DFU2005, X/Z DFU1605)
  - linear guides: HIWIN HG, ZA preload, H accuracy; X/Z blocks, supports and couplings added
  - electrics on the gantry beam rear: grblHAL (Teensy 4.1 + T41U5XBB), 3x MR-J4-40A, spindle VFD
"""
import os, json, math
import cadquery as cq
from cadquery import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "output")
os.makedirs(OUT, exist_ok=True)

# ---------------- parameters ----------------
P = dict(
    travel_x=300, travel_y=400, travel_z=100,  # Y = machining 300 + loading 100
    work=300,                       # usable work area (square)
    stand_h=700,                    # floor -> top of stand
    bed_h=160,                      # steel weldment bed height
    rail_y_gap=320,                 # Y rails centre distance (HGR25, inverted)
    table_w=440, table_l=420, table_t=40,
    spindle_y=120,                  # spindle axis Y (machining centre)
    col_w=100, col_d=200,           # gantry columns
    table_gap=20,                   # table <-> column clearance each side (the head runs IN FRONT of the columns)
    trough_w=40,                    # coolant trough outside the bed, each side + rear
    beam_h=220, beam_d=180,         # gantry beam (welded box)
    clear=220,                      # table top -> beam underside
    spindle_d=65, spindle_l=188,    # 0.8 kW air-cooled electro-spindle, ER11
    servo_sq=60,                    # HG-KR43 flange
    servo_l=98, servo_l_brake=132,  # HG-KR43 / HG-KR43B body length (approx.)
)
p = P
Z_BED = p["stand_h"]
Z_BEDTOP = Z_BED + p["bed_h"]
# Y guide INVERTED: blocks bolted to the base (fixed), rails bolted under the table on carrier bars (moving).
# Only the block pad needs precision machining. Stack: block 18 + rail 22 + carrier bar 20.
RAIL_H = 18 + 22 + 20
Y_BLK = (10, 130)                   # fixed block centres (Y), right under the machining zone
Y_BLK_X = 160                       # rail / block centre |x| (rail_y_gap / 2)
Z_TABLE = Z_BEDTOP + RAIL_H
Z_TABLETOP = Z_TABLE + p["table_t"]
# Y travel 400 = machining 300 (spindle covers the whole 300 work area) + 100 loading stroke:
# at loading the work-area rear edge sits ~30 mm in front of the spindle head (nozzles).
# Table centre: +270 = spindle over work-area FRONT edge, +120 = centre, -30 = REAR edge, -130 = loading.
TABLE_Y_WORK = p["spindle_y"]                         # model is built at this position
TABLE_Y_MAX = p["spindle_y"] + p["work"] / 2          # +270
TABLE_Y_CUT_MIN = p["spindle_y"] - p["work"] / 2      # -30
TABLE_Y_LOAD = TABLE_Y_MAX - p["travel_y"]            # -130
# bed length from the table stroke: bellows keep >= 15 % of their extended length when compressed
BELLOW_MIN = 0.15
_t_front_load = TABLE_Y_LOAD - p["table_l"] / 2       # table front edge at loading
_t_front_max = TABLE_Y_MAX - p["table_l"] / 2
_t_rear_max = TABLE_Y_MAX + p["table_l"] / 2
_t_rear_load = TABLE_Y_LOAD + p["table_l"] / 2
BELLOW_F = math.floor((_t_front_load - BELLOW_MIN * _t_front_max) / (1 - BELLOW_MIN) / 5) * 5 - 5   # front fixed end
BELLOW_R = math.ceil((_t_rear_max - BELLOW_MIN * _t_rear_load) / (1 - BELLOW_MIN) / 5) * 5 + 5      # rear fixed end
Y_BED0 = BELLOW_F - 40              # bed front edge (BF15 floating end in front)
Y_BED1 = BELLOW_R + 45              # bed rear edge (BK15 fixed end + Y motor at the rear)
P["bed_l"] = Y_BED1 - Y_BED0
P["span_in"] = p["table_w"] + 2 * p["table_gap"]      # columns only need to clear the moving table
P["bed_w"] = p["span_in"] + 2 * p["col_w"]           # columns sit fully on the bed

parts = []   # (name, shape, group, material, note)

MOTOR = "Mitsubishi HG-KR43 400W"
MOTOR_B = "Mitsubishi HG-KR43B 400W w/ brake"


def add(name, shape, group, mat="", note=""):
    parts.append((name, shape, group, mat, note))
    return shape


def box(name, sx, sy, sz, x, y, z, group, mat="", note=""):
    return add(name, cq.Solid.makeBox(sx, sy, sz, V(x, y, z)), group, mat, note)


def cyl(name, r, h, base, axis, group, mat="", note=""):
    return add(name, cq.Solid.makeCylinder(r, h, base, axis), group, mat, note)


def tube_shape(sx, sy, sz, x, y, z, t, axis):
    outer = cq.Solid.makeBox(sx, sy, sz, V(x, y, z))
    d = {"x": (0, t, t), "y": (t, 0, t), "z": (t, t, 0)}[axis]
    inner = cq.Solid.makeBox(sx - 2 * d[0], sy - 2 * d[1], sz - 2 * d[2],
                             V(x + d[0], y + d[1], z + d[2]))
    return outer.cut(inner)


def tube(name, sx, sy, sz, x, y, z, t, axis, group, mat="Q235 tube", note=""):
    """Rectangular hollow section along axis 'x'|'y'|'z'."""
    return add(name, tube_shape(sx, sy, sz, x, y, z, t, axis), group, mat, note)


def servo(name, axis_pt, direction, length, group, mat, note=""):
    """Servo motor body: square flange body along 'direction' starting at axis_pt (flange face)."""
    s = p["servo_sq"]
    d = V(*direction).normalized()
    # build along +Z then rotate
    body = cq.Solid.makeBox(s, s, length, V(-s / 2, -s / 2, 0))
    if abs(d.z - 1) < 1e-9:
        pass
    elif abs(d.z + 1) < 1e-9:
        body = body.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    elif abs(d.x - 1) < 1e-9:
        body = body.rotate(V(0, 0, 0), V(0, 1, 0), 90)
    elif abs(d.x + 1) < 1e-9:
        body = body.rotate(V(0, 0, 0), V(0, 1, 0), -90)
    elif abs(d.y - 1) < 1e-9:
        body = body.rotate(V(0, 0, 0), V(1, 0, 0), -90)
    elif abs(d.y + 1) < 1e-9:
        body = body.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    return add(name, body.translate(V(*axis_pt)), group, mat, note)


def hull2d(pts):
    pts = sorted(set(pts))
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], q) <= 0: hi.pop()
        hi.append(q)
    return lo[:-1] + hi[:-1]


def belt_loop(c1, r1, c2, r2, t, z0, h):
    def ring(r_a, r_b):
        pts = []
        for k in range(72):
            a = 2 * math.pi * k / 72
            pts.append((round(c1[0] + r_a * math.cos(a), 3), round(c1[1] + r_a * math.sin(a), 3)))
            pts.append((round(c2[0] + r_b * math.cos(a), 3), round(c2[1] + r_b * math.sin(a), 3)))
        hp = hull2d(pts)
        return cq.Workplane("XY").workplane(offset=z0).polyline(hp).close().extrude(h).val()
    return ring(r1 + t, r2 + t).cut(ring(r1, r2))


# ======================= 1. STAND (contains coolant tank) =================
leg = 80
sw, sl = p["bed_w"], p["bed_l"]                       # legs right under the bed edges
sx0, sy0 = -sw / 2, Y_BED0
corners = [(sx0, sy0), (sx0 + sw - leg, sy0), (sx0, sy0 + sl - leg), (sx0 + sw - leg, sy0 + sl - leg)]
for i, (lx, ly) in enumerate(corners):
    tube(f"Stand_leg_{i+1}", leg, leg, p["stand_h"] - 60, lx, ly, 0, 4, "z", "01 Stand", "Q235 80x80x4")
for zz, tag in [(p["stand_h"] - 60, "top"), (120, "low")]:
    tube(f"Stand_{tag}_L", leg, sl, 60, sx0, sy0, zz, 4, "y", "01 Stand", "Q235 80x60x4")
    tube(f"Stand_{tag}_R", leg, sl, 60, sx0 + sw - leg, sy0, zz, 4, "y", "01 Stand", "Q235 80x60x4")
    tube(f"Stand_{tag}_F", sw - 2 * leg, leg, 60, sx0 + leg, sy0, zz, 4, "x", "01 Stand", "Q235 80x60x4")
    tube(f"Stand_{tag}_B", sw - 2 * leg, leg, 60, sx0 + leg, sy0 + sl - leg, zz, 4, "x", "01 Stand", "Q235 80x60x4")
for i, (lx, ly) in enumerate(corners):
    cyl(f"Leveling_foot_{i+1}", 30, 20, V(lx + leg / 2, ly + leg / 2, -20), V(0, 0, 1),
        "01 Stand", "M16 leveling foot")

# ======================= 2. BED (steel weldment) =========================
bw, bl = p["bed_w"], p["bed_l"]
bx0 = -bw / 2
PAD_T = 30                                  # machined pads, top = Z_BEDTOP
FLOOR_Z = Z_BEDTOP - PAD_T                  # floor sheet top (on the webs)
_beam_y0 = p["spindle_y"] + 178
pads = {  # name: (x0, y0, sx, sy, note)
    "Y_block_pad": (-Y_BLK_X - 40, Y_BLK[0] - 60, 2 * Y_BLK_X + 80, Y_BLK[1] - Y_BLK[0] + 120,
                    "ONLY precision-machined face: 4 fixed Y blocks (flat + parallel)"),
    "Column_pad_L": (-p["span_in"] / 2 - p["col_w"], _beam_y0, p["col_w"], p["col_d"], "column seat, milled"),
    "Column_pad_R": (p["span_in"] / 2, _beam_y0, p["col_w"], p["col_d"], "column seat, milled"),
    "Y_screw_pad_F": (-45, BELLOW_F - 40, 90, 40, "BF15 seat, milled"),
    "Y_screw_pad_R": (-45, BELLOW_R, 90, 45, "BK15 seat, milled"),
}
floor = cq.Solid.makeBox(bw, bl, 3, V(bx0, Y_BED0, FLOOR_Z - 3))
for n_, (x0, y0, sx_, sy_, note_) in pads.items():
    box(n_, sx_, sy_, PAD_T, x0, y0, FLOOR_Z, "02 Bed", "Q235 t30 pad welded through the floor to the webs", note_)
add("Bed_floor_sheet", floor, "02 Bed", "SUS304 t3 floor / coolant tray, NOT machined", "drains to side troughs")
box("Bed_bottom_plate", bw, bl, 20, bx0, Y_BED0, Z_BED, "02 Bed", "Q235 t20")
for i, xx in enumerate([bx0, -p["rail_y_gap"] / 2 - 10, p["rail_y_gap"] / 2 - 10, bx0 + bw - 20]):
    box(f"Bed_long_web_{i+1}", 20, bl, p["bed_h"] - 53, xx, Y_BED0, Z_BED + 20, "02 Bed", "Q235 t20")
n_ribs = max(4, round(bl / 220))
for i in range(n_ribs):
    yy = Y_BED0 + i * (bl - 20) / (n_ribs - 1)
    box(f"Bed_cross_rib_{i+1}", bw - 40, 20, p["bed_h"] - 53, bx0 + 20, yy, Z_BED + 20, "02 Bed", "Q235 t20")

# ======================= 3. Y AXIS (moving table) =========================
grp = "03 Y-axis"
# rail length so both fixed blocks stay engaged over the whole stroke (rail centred on the table)
y_rail_l = math.ceil(((TABLE_Y_MAX - TABLE_Y_LOAD) + (Y_BLK[1] - Y_BLK[0]) + 84 + 10) / 20) * 20
yr0 = TABLE_Y_WORK - y_rail_l / 2
for side, xc in (("L", -Y_BLK_X), ("R", Y_BLK_X)):
    box(f"Y_rail_carrier_{side}", 50, y_rail_l, 20, xc - 25, yr0, Z_TABLE - 20, grp,
        f"Steel bar 50x20 L={y_rail_l:.0f}, bolted under the table, rail seat ground", "moves with table")
    box(f"Y_rail_{side}", 23, y_rail_l, 22, xc - 11.5, yr0, Z_TABLE - 42, grp,
        f"HGR25 L={y_rail_l:.0f}, H - inverted, moves with table")
    for k, yb in enumerate(Y_BLK):
        box(f"Y_block_{side}{k+1}", 48, 84, 18, xc - 24, yb - 42, Z_BEDTOP, grp,
            "HGH25CA, ZA preload, H - inverted, fixed on the block pad", "double seals (rail face points down)")
ys_axis_z = Z_BEDTOP + 40
ys0, ys1 = Y_BED0 + 15, Y_BED1 + 20
cyl("Y_ballscrew", 10, ys1 - ys0, V(0, ys0, ys_axis_z), V(0, 1, 0), grp, "DFU2005 double-nut preload, C7")
box("Y_nut_housing", 80, 110, Z_TABLE - (ys_axis_z - 28), -40, TABLE_Y_WORK - 55, ys_axis_z - 28, grp, "DFU2005 nut seat, hangs under the table")
box("Y_BF_support", 70, 20, ys_axis_z + 25 - Z_BEDTOP, -35, BELLOW_F - 25, Z_BEDTOP, grp, "BF15 floating end (front) on riser")
box("Y_BK_support", 70, 25, ys_axis_z + 25 - Z_BEDTOP, -35, BELLOW_R + 5, Z_BEDTOP, grp, "BK15 fixed end (rear, motor side) on riser")
tube("Y_motor_mount", 76, 40, 76, -38, Y_BED1, ys_axis_z - 38, 8, "y", grp, "Motor bracket t8 on bed rear face")
cyl("Y_coupling", 12.5, 30, V(0, Y_BED1 + 5, ys_axis_z), V(0, 1, 0), grp, "Coupling D25, 8x14")
servo("Y_motor", (0, Y_BED1 + 40, ys_axis_z), (0, 1, 0), p["servo_l"], grp, MOTOR, "rear mounted, direct drive, lead 5")
# moving table (T-slot) + bellows covers
tx0 = -p["table_w"] / 2
tbl = cq.Solid.makeBox(p["table_w"], p["table_l"], p["table_t"], V(tx0, TABLE_Y_WORK - p["table_l"] / 2, Z_TABLE))
for k in range(5):
    sx = tx0 + 60 + k * 80
    tbl = tbl.cut(cq.Solid.makeBox(14, p["table_l"], 12, V(sx - 7, TABLE_Y_WORK - p["table_l"] / 2, Z_TABLETOP - 12)))
add("Work_table", tbl, grp, "HT250 / Q235 t40, 5x T-slot 14", "440x420 table, work area 300x300")
box("Work_area_300x300", p["work"], p["work"], 0.5, -p["work"] / 2, TABLE_Y_WORK - p["work"] / 2,
    Z_TABLETOP, grp, "reference", "usable 300x300")
cov_w = 2 * Y_BLK_X - 80                  # between the rail carriers: covers the screw only
cov_h = Z_TABLETOP - 5 - (Z_BEDTOP + 5)
front_len = (TABLE_Y_WORK - p["table_l"] / 2) - BELLOW_F
rear_len = BELLOW_R - (TABLE_Y_WORK + p["table_l"] / 2)
box("Y_bellows_front", cov_w, front_len, cov_h, -cov_w / 2, BELLOW_F, Z_BEDTOP + 5, grp,
    "Bellows over the ball screw (coolant proof)")
box("Y_bellows_rear", cov_w, rear_len, cov_h, -cov_w / 2, TABLE_Y_WORK + p["table_l"] / 2, Z_BEDTOP + 5,
    grp, "Bellows over the ball screw (coolant proof)")

# ======================= 4. FIXED GANTRY =================================
grp = "04 Gantry"
z_beam0 = Z_TABLETOP + p["clear"]
beam_y0 = p["spindle_y"] + 178          # beam front face
span_in = p["span_in"]                  # inner span between columns
col_x_in = span_in / 2
for side, sgn in (("L", -1), ("R", 1)):
    x0 = col_x_in if sgn > 0 else -col_x_in - p["col_w"]
    tube(f"Gantry_column_{side}", p["col_w"], p["col_d"], z_beam0 + p["beam_h"] - Z_BEDTOP,
         x0, beam_y0, Z_BEDTOP, 12, "z", grp, "Welded box 100x200 t12 (Q235)")
beam_l = span_in + 2 * p["col_w"]
tube("Gantry_beam", beam_l, p["beam_d"], p["beam_h"], -beam_l / 2, beam_y0, z_beam0, 12, "x",
     grp, "Welded box 220x180 t12, filled epoxy granite optional")

# ======================= 5. X AXIS ========================================
grp = "05 X-axis"
x_rail_l = beam_l - 40
x_rail_z = (z_beam0 + 30, z_beam0 + p["beam_h"] - 53)
for k, zz in enumerate(x_rail_z):
    box(f"X_rail_{k+1}", x_rail_l, 22, 23, -x_rail_l / 2, beam_y0 - 22, zz, grp, "HGR20, H")
    for j, xx in enumerate((-60, 60)):
        box(f"X_block_{k+1}{j+1}", 77.5, 18, 44, xx - 38.75, beam_y0 - 40, zz + 11.5 - 22, grp,
            "HGH20CA, ZA preload, H")
xs_z = z_beam0 + p["beam_h"] / 2
xs_y = beam_y0 - 26
xs0, xs1 = -x_rail_l / 2 + 10, beam_l / 2 + 5
cyl("X_ballscrew", 8, xs1 - xs0, V(xs0, xs_y, xs_z), V(1, 0, 0), grp, "DFU1605 double-nut preload, C7")
box("X_BK_support", 25, 34, 60, beam_l / 2 - 45, beam_y0 - 40, xs_z - 30, grp, "BK12 fixed end")
box("X_BF_support", 20, 34, 60, -x_rail_l / 2, beam_y0 - 40, xs_z - 30, grp, "BF12 floating end")
tube("X_motor_mount", 40, 76, 76, beam_l / 2, xs_y - 38, xs_z - 38, 8, "x", grp, "Motor bracket t8")
cyl("X_coupling", 12.5, 30, V(beam_l / 2 + 5, xs_y, xs_z), V(1, 0, 0), grp, "Coupling D25, 8x12")
servo("X_motor", (beam_l / 2 + 40, xs_y, xs_z), (1, 0, 0), p["servo_l"], grp, MOTOR, "direct drive, lead 5")
xc_w, xc_h = 240, 380
xc_y0 = beam_y0 - 40 - 30
box("X_carriage_plate", xc_w, 30, xc_h, -xc_w / 2, xc_y0, z_beam0 - 120, grp, "6061-T6 / steel t30")
box("X_nut_housing", 100, 28, 44, -50, beam_y0 - 40, xs_z - 22, grp, "DFU1605 nut seat (on carriage back)")

# ======================= 6. Z AXIS + SERVO BELT SPINDLE ===================
grp = "06 Z-axis & Spindle"
zc0 = z_beam0 - 120                      # carriage plate bottom
for side, xx in (("L", -80), ("R", 80)):
    box(f"Z_rail_{side}", 20, 18, xc_h, xx - 10, xc_y0 - 18, zc0, grp, "HGR20, H")
zs_y0 = xc_y0 - 18 - 12 - 30             # Z slide plate front face
z_slide_z = Z_TABLETOP + p["travel_z"] + 140   # Z slide bottom at Z top position
zp_x0, zp_w, zp_h = -110, 220, 230
box("Z_slide_plate", zp_w, 30, zp_h, zp_x0, zs_y0, z_slide_z, grp, "Steel t30")
for side, xx in (("L", -80), ("R", 80)):
    for k, zz in enumerate((z_slide_z + 15, z_slide_z + 140)):
        box(f"Z_block_{side}{k+1}", 44, 12, 77.5, xx - 22, zs_y0 + 30, zz, grp, "HGH20CA, ZA preload, H")
zsc_y = xc_y0 - 14
zsc0, zsc1 = zc0 + 15, zc0 + xc_h + 30
cyl("Z_ballscrew", 8, zsc1 - zsc0, V(0, zsc_y, zsc0), V(0, 0, 1), grp, "DFU1605 double-nut preload, C7")
box("Z_nut_housing", 70, zsc_y - (zs_y0 + 30) - 8, 90, -35, zs_y0 + 30, z_slide_z + 100, grp, "DFU1605 nut seat")
box("Z_BF_support", 60, 28, 20, -30, zsc_y - 14, zc0 + 5, grp, "BF12 floating end (bottom)")
box("Z_BK_support", 60, 28, 25, -30, zsc_y - 14, zc0 + xc_h - 30, grp, "BK12 fixed end (top)")
box("Z_motor_base", 120, 58, 12, -60, zsc_y - 29 + 14, zc0 + xc_h, grp, "Motor base plate t12")
tube("Z_motor_mount", 76, 76, 40, -38, zsc_y - 38, zc0 + xc_h + 12, 8, "z", grp, "Motor bracket t8")
cyl("Z_coupling", 12.5, 30, V(0, zsc_y, zc0 + xc_h + 17), V(0, 0, 1), grp, "Coupling D25, 8x14")
servo("Z_motor", (0, zsc_y, zc0 + xc_h + 52), (0, 0, 1), p["servo_l_brake"], grp, MOTOR_B,
      "brake holds spindle head at power-off")

# spindle: 0.8 kW air-cooled electro-spindle D65 x 188, ER11; tool tip at z_slide_z - 120 (same as v1)
sp_y = p["spindle_y"]
sp_r = p["spindle_d"] / 2
sp_z0 = z_slide_z - 77
def revolve(name, prof, group, mat="", note="", z0=None):
    """Solid of revolution about the spindle axis; prof = [(r, dz), ...] relative to sp_z0."""
    s = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    s = s.translate(V(0, sp_y, sp_z0 if z0 is None else z0))
    return add(name, s, group, mat, note) if name else s


# ER11 nose (ISO 15488): collet D11.5 x 18, 8 deg taper, 30 deg front cone; nut D19, M13x0.75
T8 = math.tan(math.radians(8))
body = cq.Solid.makeCylinder(sp_r, p["spindle_l"] - 38, V(0, sp_y, sp_z0), V(0, 0, 1))
body = body.cut(cq.Solid.makeCylinder(4.4, 30, V(0, sp_y, sp_z0), V(0, 0, 1)))       # collet taper end + shank bore
add("Spindle", body, grp,
    "0.8 kW air-cooled electro-spindle D65, ER11, 220 V 400 Hz, 6,000-24,000 rpm, 2x7002C + 2x7000C bearings",
    "runout <=0.005 mm requested; e.g. Sorotec HFSAC-6508 / GDF65-24Z-0.8")
fan = cq.Solid.makeCylinder(sp_r, 38, V(0, sp_y, sp_z0 + p["spindle_l"] - 38), V(0, 0, 1))
for k in range(12):                                                                  # cooling slots
    a = 2 * math.pi * k / 12
    fan = fan.cut(cq.Solid.makeBox(4, 12, 26, V(-2, sp_r - 3, sp_z0 + p["spindle_l"] - 32))
                  .rotate(V(0, 0, 0), V(0, 0, 1), math.degrees(a)).translate(V(0, sp_y, 0)))
add("Spindle_fan_cover", fan, grp, "Fan cover (air intake on top, keep away from chips)")
cyl("Spindle_connector", 8, 22, V(-sp_r + 0.5, sp_y, z_slide_z + 18), V(-1, 0, 0), grp,
    "Aviation plug 4-pin (U/V/W/PE) to VFD")
revolve("Spindle_nose", [(5.75, -10), (6.5, -10), (6.5, 0), (5.75 - 10 * T8, 0)], grp,
        "Spindle nose: ER11 8 deg collet seat + M13x0.75 thread (part of spindle shaft)")
revolve("ER11_collet", [(3, -14), (4.25, -14), (5.75, -10), (5.75 - 14 * T8, 4), (3, 4)], grp,
        "ER11 collet D6 (5.5-6.0), AA grade runout <=0.005 mm", "choose by tool SHANK diameter, 1-7 mm")
nut = revolve(None, [(4.5, -16), (9.5, -16), (9.5, -2), (6.5, -2), (6.5, -10.5), (6.0, -10.5), (4.5, -14.5)], grp)
for k in range(4):
    a = math.radians(45 + 90 * k)
    slot = cq.Solid.makeBox(3, 3.5, 14, V(8.2, -1.75, 0)).rotate(V(0, 0, 0), V(0, 0, 1), math.degrees(a))
    nut = nut.cut(slot.translate(V(0, sp_y, sp_z0 - 16)))
add("ER11_nut", nut, grp, "ER11 nut type A, D19, M13x0.75, hook-wrench slots x4")
revolve("Tool_D5", [(0, -43), (2.5, -43), (2.5, -24), (3, -24), (3, 2), (0, 2)], grp,
        "End mill D5 x shank D6, carbide 2-flute for Al (reference)", "stick-out 27 from nut face")
clamp = cq.Solid.makeBox(96, zs_y0 - (sp_y - 46), 60, V(-48, sp_y - 46, z_slide_z + 30))
clamp = clamp.cut(cq.Solid.makeCylinder(sp_r, 60, V(0, sp_y, z_slide_z + 30), V(0, 0, 1)))
clamp = clamp.cut(cq.Solid.makeBox(3, 50, 60, V(-1.5, sp_y - 46, z_slide_z + 30)))  # split clamp slot
add("Spindle_clamp", clamp, grp, "D65 spindle mount, cast Al, split clamp, bolted to Z slide")

# ======================= 7. COOLANT / AIR / CHIP SYSTEM ===================
grp = "07 Coolant & Air"
g_h, g_t = 320, 2
tw = p["trough_w"]
gx = bw / 2 + tw                          # guards stand on the outer trough edge
gy1 = Y_BED1 + tw                         # rear guard behind the rear trough
gz0 = FLOOR_Z - 40                         # trough bottom; trough top level with the floor sheet
box("Guard_side_L", g_t, gy1 - Y_BED0, g_h, -gx - g_t, Y_BED0, gz0, grp, "SUS304 t2 splash guard")
box("Guard_side_R", g_t, gy1 - Y_BED0, g_h, gx, Y_BED0, gz0, grp, "SUS304 t2 splash guard")
rg = cq.Solid.makeBox(2 * gx, g_t, g_h, V(-gx, gy1, gz0))
rg = rg.cut(cq.Solid.makeBox(90, 10, 90, V(-45, gy1 - 4, ys_axis_z - 45)))
add("Guard_rear", rg, grp, "SUS304 t2, cut-out for Y motor")
box("Guard_front_lip", 2 * gx, g_t, 120, -gx, Y_BED0 - g_t, gz0, grp, "SUS304 t2 low lip (loading side)")
box("Guard_window_L", g_t, 400, 200, -gx - g_t - 0.1, p["spindle_y"] - 200, Z_BEDTOP + 40, grp, "PC window 5mm")
box("Coolant_trough_L", tw, gy1 - Y_BED0, 40, -gx, Y_BED0, gz0, grp, "SUS304 trough outside bed, slope 1:100 to rear")
box("Coolant_trough_R", tw, gy1 - Y_BED0, 40, bw / 2, Y_BED0, gz0, grp, "SUS304 trough outside bed, slope 1:100 to rear")
box("Coolant_trough_rear", bw, tw, 40, -bw / 2, Y_BED1, gz0, grp, "rear trough, collects to drain")
drain_x, drain_y = bw / 2 - leg - 60, Y_BED1 + tw / 2   # behind the stand, clear of the legs
cyl("Drain_pipe", 20, gz0 - 560, V(drain_x, drain_y, 560), V(0, 0, 1), grp, "PVC D40 drain (behind stand)")
tank_l, tank_h = 620, 330
tank_w = sw - 2 * leg - 20                # fits between the stand legs (~100 L)
tank_y0 = Y_BED1 - 80 - tank_l
tk = cq.Solid.makeBox(tank_w, tank_l, tank_h, V(-tank_w / 2, tank_y0, 185))
tk = tk.cut(cq.Solid.makeBox(tank_w - 6, tank_l - 6, tank_h, V(-tank_w / 2 + 3, tank_y0 + 3, 188)))
add("Coolant_tank", tk, grp, "SUS304 t3, ~100 L (fill 80 L)", "on castors, slides out rear")
fbx, fby = tank_w / 2 - 235, tank_y0 + tank_l - 240
fb = cq.Solid.makeBox(220, 220, 180, V(fbx, fby, 340))
fb = fb.cut(cq.Solid.makeBox(210, 210, 180, V(fbx + 5, fby + 5, 345)))
_d0, _d1 = V(drain_x, drain_y, 560), V(fbx + 110, fby + 110, 525)
cyl("Drain_pipe_2", 20, (_d1 - _d0).Length, _d0, _d1 - _d0, grp, "PVC D40 elbow to filter basket")
add("Chip_filter_basket", fb, grp, "SUS304 perforated basket + 60 mesh bag", "removable, catches Al chips")
box("Filter_baffle", tank_w - 6, 3, tank_h - 60, -tank_w / 2 + 3, tank_y0 + tank_l / 2, 188, grp,
    "Settling baffle (dirty | clean side)")
cyl("Coolant_pump", 45, 160, V(-150, tank_y0 + 140, 185 + tank_h - 120), V(0, 0, 1), grp,
    "Immersion pump 90W, 25 L/min, 0.2 MPa")
cyl("Pump_motor", 55, 110, V(-150, tank_y0 + 140, 185 + tank_h), V(0, 0, 1), grp, "pump motor")
hz = z_beam0 + p["beam_h"] + 60
h0 = 185 + tank_h + 117
hxr = -(bw / 2 - leg) + 20                # riser x: inside the leg line, beside the cabinet
hose_pts = [V(-150, tank_y0 + 140, 185 + tank_h + 110), V(-150, tank_y0 + 140, h0), V(hxr, gy1 + 10, h0),
            V(hxr, gy1 + 10, hz), V(-60, xc_y0 + 15, hz)]
hose = None
for a, b in zip(hose_pts[:-1], hose_pts[1:]):
    seg = cq.Solid.makeCylinder(6, (b - a).Length, a, (b - a))
    hose = seg if hose is None else hose.fuse(seg)
add("Coolant_hose", hose.clean(), grp, "PU 12x8 hose in drag chain")
tip_z = sp_z0 - 43
for ang, name, note in [(200, "Coolant_nozzle_1", "Loc-Line 1/4\" coolant"),
                        (300, "Coolant_nozzle_2", "Loc-Line 1/4\" coolant"),
                        (250, "Air_blow_nozzle", "Air blast / mist, 0.5 MPa")]:
    a = math.radians(ang)
    base = V(70 * math.cos(a), sp_y + 70 * math.sin(a), z_slide_z - 60)
    tip = V(8 * math.cos(a), sp_y + 8 * math.sin(a), tip_z + 8)
    cyl(name, 4, (tip - base).Length, base, tip - base, grp, note)
box("Air_solenoid_FRL", 60, 40, 120, -col_x_in - 80, beam_y0 + p["col_d"], z_beam0 - 260, grp,
    "FRL + 24V solenoid valve (M7/M8 coolant/air via controller)")
box("Drag_chain_X", beam_l - 100, 40, 30, -(beam_l - 100) / 2, beam_y0 + 30, z_beam0 + p["beam_h"], grp,
    "Drag chain 25x38 (cables, coolant, air)")

# ======================= 8. ELECTRICAL =====================================
grp = "08 Electrical"
# no separate cabinet: drives + controller on a plate bolted to the beam rear face, between the columns,
# under a thin sheet cover (Al chips are conductive, 220 V terminals). 4x MR-J4-40A ~40x168x135 each.
pnl_w, pnl_h, pnl_d = 440, 260, 150
pnl_y0 = beam_y0 + p["beam_d"]
box("Electrical_panel", pnl_w, 3, pnl_h, -pnl_w / 2, pnl_y0, z_beam0 + p["beam_h"] - pnl_h, grp,
    "Mounting plate t3 on beam rear: 3x MR-J4-40A (X/Y/Z), spindle VFD 0.75-1.5 kW (e.g. Delta MS300, "
    ">=400 Hz), Teensy 4.1 + T41U5XBB, line drivers, 24V PSU, breaker, terminals", "1 PC can supervise several machines over Ethernet")
cov = cq.Solid.makeBox(pnl_w, pnl_d - 3, pnl_h, V(-pnl_w / 2, pnl_y0 + 3, z_beam0 + p["beam_h"] - pnl_h))
cov = cov.cut(cq.Solid.makeBox(pnl_w - 3, pnl_d - 6, pnl_h, V(-pnl_w / 2 + 1.5, pnl_y0 + 3, z_beam0 + p["beam_h"] - pnl_h - 1.5)))
add("Electrical_cover", cov, grp, "Sheet cover t1.5, open vented bottom, hinged for service")

# ======================= export ===========================================
COLORS = {
    "01 Stand": (0.35, 0.38, 0.40, 1), "02 Bed": (0.55, 0.58, 0.60, 1),
    "03 Y-axis": (0.18, 0.42, 0.62, 1), "04 Gantry": (0.30, 0.36, 0.42, 1),
    "05 X-axis": (0.16, 0.55, 0.52, 1), "06 Z-axis & Spindle": (0.85, 0.45, 0.15, 1),
    "07 Coolant & Air": (0.35, 0.65, 0.90, 0.55), "08 Electrical": (0.45, 0.45, 0.48, 1),
}


def build():
    assy = cq.Assembly(name="CNC_Gantry_v2")
    for name, shape, group, mat, note in parts:
        assy.add(shape, name=name, color=cq.Color(*COLORS[group]))
    return assy


if __name__ == "__main__":
    build().export(os.path.join(OUT, "CNC_Gantry.step"))
    comp = cq.Compound.makeCompound([s for _, s, _, _, _ in parts])
    bb = comp.BoundingBox()
    info = dict(
        version="v2 (CadQuery)",
        params=P,
        overall=dict(x=round(bb.xlen), y=round(bb.ylen), z=round(bb.zlen),
                     xmin=round(bb.xmin, 1), ymin=round(bb.ymin, 1), zmin=round(bb.zmin, 1),
                     xmax=round(bb.xmax, 1), ymax=round(bb.ymax, 1), zmax=round(bb.zmax, 1)),
        z_levels=dict(bed=Z_BED, bed_top=Z_BEDTOP, table_top=Z_TABLETOP, beam_bottom=z_beam0,
                      beam_top=z_beam0 + p["beam_h"]),
        table_y=dict(work=TABLE_Y_WORK, max=TABLE_Y_MAX, cut_min=TABLE_Y_CUT_MIN, load=TABLE_Y_LOAD),
        parts=[dict(name=n, group=g, material=m, note=t) for n, s, g, m, t in parts],
    )
    with open(os.path.join(OUT, "cnc_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    print("OK", len(parts), "parts", info["overall"])
