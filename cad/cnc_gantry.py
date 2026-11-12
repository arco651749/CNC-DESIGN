# -*- coding: utf-8 -*-
"""
Gantry 3-axis CNC v2 (fixed gantry, moving table) - parametric layout model, CadQuery.
Run:  python cad/cnc_gantry.py
Outputs (../output): CNC_Gantry.step (named + coloured assembly), cnc_info.json (parts / key dims).

Coordinates: X = left/right, Y = front(-)/back(+), Z = up. Units mm.
Work area 300 x 300, Z travel 100. Y travel 600 = 300 machining + 300 loading zone (front).

v2 changes vs v1 (FreeCAD):
  - aluminium, tools <= D5, manual tool change, feed <= 100 mm/s
  - all 5 motors Mitsubishi HG-KR43 400 W (Z: HG-KR43B with brake), drivers MR-J4-40A
  - spindle: HG-KR43 servo + PJ poly-V belt 1:3 -> ER11 belt-driven spindle cartridge ~13,500 rpm
  - ball screws: DFU double-nut preload, lead 5 on all axes (Y DFU2005, X/Z DFU1605)
  - linear guides: HIWIN HG, ZA preload, H accuracy; X/Z blocks, supports and couplings added
  - electrical cabinet: grblHAL (Teensy 4.1 + T41U5XBB) + 4x MR-J4-40A
"""
import os, json, math
import cadquery as cq
from cadquery import Vector as V

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
    spindle_d=62, spindle_l=200,    # ER11 belt-driven spindle cartridge
    belt_ratio=3,                   # motor : spindle speed = 1 : 3
    servo_sq=60,                    # HG-KR43 flange
    servo_l=98, servo_l_brake=132,  # HG-KR43 / HG-KR43B body length (approx.)
)
p = P
Z_BED = p["stand_h"]
Z_BEDTOP = Z_BED + p["bed_h"]
RAIL_H = 40                         # rail+block height HGR25
Z_TABLE = Z_BEDTOP + RAIL_H
Z_TABLETOP = Z_TABLE + p["table_t"]
# Y travel 600 = machining 300 (spindle covers the whole 300 work area) + 300 loading stroke.
# Table centre: +270 = spindle over work-area FRONT edge, +120 = centre, -30 = REAR edge, -330 = loading.
TABLE_Y_WORK = p["spindle_y"]                         # model is built at this position
TABLE_Y_MAX = p["spindle_y"] + p["work"] / 2          # +270
TABLE_Y_CUT_MIN = p["spindle_y"] - p["work"] / 2      # -30
TABLE_Y_LOAD = TABLE_Y_MAX - p["travel_y"]            # -330
Y_BED0 = -p["bed_l"] / 2 - 100      # bed front edge
Y_BED1 = Y_BED0 + p["bed_l"]

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
sw, sl = p["bed_w"] + 80, p["bed_l"]
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
box("Bed_top_plate", bw, bl, 30, bx0, Y_BED0, Z_BEDTOP - 30, "02 Bed", "Q235 t30, stress relieved, rails face milled")
box("Bed_bottom_plate", bw, bl, 20, bx0, Y_BED0, Z_BED, "02 Bed", "Q235 t20")
for i, xx in enumerate([bx0, -p["rail_y_gap"] / 2 - 10, p["rail_y_gap"] / 2 - 10, bx0 + bw - 20]):
    box(f"Bed_long_web_{i+1}", 20, bl, p["bed_h"] - 50, xx, Y_BED0, Z_BED + 20, "02 Bed", "Q235 t20")
n_ribs = 7
for i in range(n_ribs):
    yy = Y_BED0 + i * (bl - 20) / (n_ribs - 1)
    box(f"Bed_cross_rib_{i+1}", bw - 40, 20, p["bed_h"] - 50, bx0 + 20, yy, Z_BED + 20, "02 Bed", "Q235 t20")

# ======================= 3. Y AXIS (moving table) =========================
grp = "03 Y-axis"
y_rail_l = 1200
yr0 = Y_BED0 + (bl - y_rail_l) / 2
for side, xc in (("L", -p["rail_y_gap"] / 2), ("R", p["rail_y_gap"] / 2)):
    box(f"Y_rail_{side}", 23, y_rail_l, 22, xc - 11.5, yr0, Z_BEDTOP, grp, "HGR25 L=1200, H")
    for k, dy in enumerate((-110, 110)):
        box(f"Y_block_{side}{k+1}", 48, 84, 18, xc - 24, TABLE_Y_WORK + dy - 42, Z_BEDTOP + 22,
            grp, "HGH25CA, ZA preload, H")
ys_axis_z = Z_BEDTOP + 22
ys0, ys1 = Y_BED0 - 20, Y_BED1 - 70
cyl("Y_ballscrew", 10, ys1 - ys0, V(0, ys0, ys_axis_z), V(0, 1, 0), grp, "DFU2005 double-nut preload, C7")
box("Y_nut_housing", 80, 110, 34, -40, TABLE_Y_WORK - 55, Z_BEDTOP + 5, grp, "DFU2005 nut seat")
box("Y_BK_support", 70, 25, 45, -35, Y_BED0 + 40, Z_BEDTOP, grp, "BK15 fixed end (front)")
box("Y_BF_support", 70, 20, 45, -35, Y_BED1 - 100, Z_BEDTOP, grp, "BF15 floating end (rear)")
tube("Y_motor_mount", 76, 40, 76, -38, Y_BED0 - 40, ys_axis_z - 38, 8, "y", grp, "Motor bracket t8")
cyl("Y_coupling", 12.5, 30, V(0, Y_BED0 - 35, ys_axis_z), V(0, 1, 0), grp, "Coupling D25, 8x14")
servo("Y_motor", (0, Y_BED0 - 40, ys_axis_z), (0, -1, 0), p["servo_l"], grp, MOTOR, "direct drive, lead 5")
# moving table (T-slot) + bellows covers
tx0 = -p["table_w"] / 2
tbl = cq.Solid.makeBox(p["table_w"], p["table_l"], p["table_t"], V(tx0, TABLE_Y_WORK - p["table_l"] / 2, Z_TABLE))
for k in range(5):
    sx = tx0 + 60 + k * 80
    tbl = tbl.cut(cq.Solid.makeBox(14, p["table_l"], 12, V(sx - 7, TABLE_Y_WORK - p["table_l"] / 2, Z_TABLETOP - 12)))
add("Work_table", tbl, grp, "HT250 / Q235 t40, 5x T-slot 14", "440x420 table, work area 300x300")
box("Work_area_300x300", p["work"], p["work"], 0.5, -p["work"] / 2, TABLE_Y_WORK - p["work"] / 2,
    Z_TABLETOP, grp, "reference", "usable 300x300")
cov_w = p["rail_y_gap"] + 80
front_len = (TABLE_Y_WORK - p["table_l"] / 2) - (Y_BED0 + 70)
rear_len = (Y_BED1 - 40) - (TABLE_Y_WORK + p["table_l"] / 2)
box("Y_bellows_front", cov_w, front_len, 60, -cov_w / 2, Y_BED0 + 70, Z_BEDTOP, grp,
    "Bellows way cover (coolant proof)")
box("Y_bellows_rear", cov_w, rear_len, 60, -cov_w / 2, TABLE_Y_WORK + p["table_l"] / 2, Z_BEDTOP,
    grp, "Bellows way cover (coolant proof)")

# ======================= 4. FIXED GANTRY =================================
grp = "04 Gantry"
z_beam0 = Z_TABLETOP + p["clear"]
beam_y0 = p["spindle_y"] + 178          # beam front face
span_in = p["travel_x"] + 260 + 80      # inner span between columns
col_x_in = span_in / 2
for side, sgn in (("L", -1), ("R", 1)):
    x0 = col_x_in if sgn > 0 else -col_x_in - p["col_w"]
    tube(f"Gantry_column_{side}", p["col_w"], p["col_d"], z_beam0 + p["beam_h"] - Z_BEDTOP,
         x0, beam_y0, Z_BEDTOP, 12, "z", grp, "Welded box 140x200 t12 (Q235)")
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
zp_x0, zp_w, zp_h = -110, 250, 230
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

# spindle: ER11 belt-driven cartridge, tool tip at z_slide_z - 120 (same as v1)
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
body = cq.Solid.makeCylinder(sp_r, p["spindle_l"], V(0, sp_y, sp_z0), V(0, 0, 1))
body = body.cut(cq.Solid.makeCylinder(4.4, 30, V(0, sp_y, sp_z0), V(0, 0, 1)))       # collet taper end + shank bore
add("Spindle_cartridge", body, grp,
    "ER11 belt-driven spindle cartridge D62, >=15,000 rpm, P4 angular contact bearings, taper runout <=0.003",
    "~13,500 rpm at motor 4,500 rpm")
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
clamp = cq.Solid.makeBox(110, zs_y0 - (sp_y - 50), 70, V(-55, sp_y - 50, z_slide_z + 30))
clamp = clamp.cut(cq.Solid.makeCylinder(sp_r, 70, V(0, sp_y, z_slide_z + 30), V(0, 0, 1)))
add("Spindle_clamp", clamp, grp, "Clamp D62, steel")
pz0 = sp_z0 + p["spindle_l"] + 10          # pulley bottom
cyl("Spindle_shaft", 7.5, 10, V(0, sp_y, sp_z0 + p["spindle_l"]), V(0, 0, 1), grp, "spindle shaft end D15")
cyl("Spindle_pulley", 16, 20, V(0, sp_y, pz0), V(0, 0, 1), grp, "PJ poly-V pulley D32 (balanced)")
mx, my = 90, sp_y - 10                     # motor axis (belt centre distance ~90)
cyl("Spindle_motor_pulley", 48, 20, V(mx, my, pz0), V(0, 0, 1), grp, "PJ poly-V pulley D96 (balanced)")
cyl("Spindle_motor_shaft", 7, 10, V(mx, my, pz0 - 10), V(0, 0, 1), grp, "motor shaft D14")
brk_x0 = mx - 30
box("Spindle_motor_bracket", 60, zs_y0 - (my - 30), 12, brk_x0, my - 30, pz0 - 22, grp,
    "Motor bracket t12, slotted for belt tension")
servo("Spindle_motor", (mx, my, pz0 - 22), (0, 0, -1), p["servo_l"], grp, MOTOR,
      "speed mode, 0-10 V from grblHAL, 1:3 belt")
add("Spindle_belt", belt_loop((0, sp_y), 16, (mx, my), 48, 4, pz0 + 2, 16), grp, "PJ poly-V belt (e.g. 6PJ)")
guard = cq.Solid.makeBox(174, zs_y0 - 2 - (my - 58), 36, V(-28, my - 58, pz0 - 4))
guard = guard.cut(cq.Solid.makeBox(168, zs_y0 - 2 - (my - 58) - 6, 33, V(-25, my - 55, pz0 - 4)))
add("Belt_guard", guard, grp, "Belt guard, Al sheet t1.5")

# ======================= 7. COOLANT / AIR / CHIP SYSTEM ===================
grp = "07 Coolant & Air"
g_h, g_t = 320, 2
gx = bw / 2 + 10
box("Guard_side_L", g_t, bl, g_h, -gx - g_t, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 t2 splash guard")
box("Guard_side_R", g_t, bl, g_h, gx, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 t2 splash guard")
box("Guard_rear", 2 * gx, g_t, g_h, -gx, Y_BED1, Z_BEDTOP - 40, grp, "SUS304 t2")
lip = cq.Solid.makeBox(2 * gx, g_t, 120, V(-gx, Y_BED0 - g_t, Z_BEDTOP - 40))
lip = lip.cut(cq.Solid.makeBox(90, 10, 90, V(-45, Y_BED0 - 6, ys_axis_z - 45)))
add("Guard_front_lip", lip, grp, "SUS304 t2 low lip (loading side), cut-out for Y motor")
box("Guard_window_L", g_t, 500, 200, -gx - g_t - 0.1, p["spindle_y"] - 250, Z_BEDTOP + 60, grp, "PC window 5mm")
box("Coolant_trough_L", 60, bl, 40, -gx, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 trough, slope 1:100 to rear")
box("Coolant_trough_R", 60, bl, 40, gx - 60, Y_BED0, Z_BEDTOP - 40, grp, "SUS304 trough, slope 1:100 to rear")
box("Coolant_trough_rear", 2 * gx, 80, 40, -gx, Y_BED1 - 80, Z_BEDTOP - 40, grp, "collects to drain")
drain_x, drain_y = gx - 30, Y_BED1 - 40
cyl("Drain_pipe", 20, Z_BEDTOP - 40 - 520, V(drain_x, drain_y, 520), V(0, 0, 1), grp, "PVC D40 drain")
tank_l, tank_w, tank_h = 620, 560, 330
tank_y0 = Y_BED1 - 80 - tank_l
tk = cq.Solid.makeBox(tank_w, tank_l, tank_h, V(-tank_w / 2, tank_y0, 185))
tk = tk.cut(cq.Solid.makeBox(tank_w - 6, tank_l - 6, tank_h, V(-tank_w / 2 + 3, tank_y0 + 3, 188)))
add("Coolant_tank", tk, grp, "SUS304 t3, ~100 L (fill 80 L)", "on castors, slides out rear")
fb = cq.Solid.makeBox(220, 220, 180, V(drain_x - 170, drain_y - 190, 340))
fb = fb.cut(cq.Solid.makeBox(210, 210, 180, V(drain_x - 165, drain_y - 185, 345)))
add("Chip_filter_basket", fb, grp, "SUS304 perforated basket + 60 mesh bag", "removable, catches Al chips")
box("Filter_baffle", tank_w - 6, 3, tank_h - 60, -tank_w / 2 + 3, tank_y0 + tank_l / 2, 188, grp,
    "Settling baffle (dirty | clean side)")
cyl("Coolant_pump", 45, 160, V(-150, tank_y0 + 140, 185 + tank_h - 120), V(0, 0, 1), grp,
    "Immersion pump 90W, 25 L/min, 0.2 MPa")
cyl("Pump_motor", 55, 110, V(-150, tank_y0 + 140, 185 + tank_h), V(0, 0, 1), grp, "pump motor")
hose_pts = [V(-150, tank_y0 + 140, 185 + tank_h + 110), V(-150, tank_y0 + 140, 640),
            V(-gx + 30, Y_BED1 - 60, 640), V(-gx + 30, Y_BED1 - 60, z_beam0 + p["beam_h"] + 40),
            V(-60, xc_y0 + 15, z_beam0 + p["beam_h"] + 40)]
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
box("Air_solenoid_FRL", 60, 40, 120, -gx - 130, Y_BED1 - 120, 560, grp,
    "FRL + 24V solenoid valve (M7/M8 coolant/air via controller)")
box("Drag_chain_X", beam_l - 100, 40, 30, -(beam_l - 100) / 2, beam_y0 + 30, z_beam0 + p["beam_h"], grp,
    "Drag chain 25x38 (cables, coolant, air)")

# ======================= 8. ELECTRICAL =====================================
grp = "08 Electrical"
cab_w, cab_d, cab_h = 220, 500, 600
cab = cq.Solid.makeBox(cab_w, cab_d, cab_h, V(sw / 2, -380, 80))
add("Electrical_cabinet", cab, grp,
    "SPCC cabinet IP54: grblHAL Teensy 4.1 + T41U5XBB, 4x MR-J4-40A, line drivers, 24V PSU, breaker",
    "1 PC can supervise several machines over Ethernet")

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
