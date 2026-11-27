# -*- coding: utf-8 -*-
"""Gantry-column electrical box: part placement in MACHINE coordinates (mm). Front = -y, floor z=-790.
Envelope given by the mechanical session (docs/handoff_electrical_box_v14.md): x -380..380, y 255..495, z 250..488,
back wall inner face y=495, roof underside z=488, removable bottom cover z~245.
Part = (key, designator, name, x0, y0, z0, dx, dy, dz, mount, orientation, source)
 'W' = on the back wall (back face on y=495; depth runs toward -y), 'R' = on the roof underside (back face on z=488; depth runs down).
 Sizes: M = Mitsubishi vendor STEP/manual, S = datasheet supplied by owner, A = approx catalog value (confirm)."""
ENV = (-380, 380, 255, 495, 249, 487)
WALL_Y, ROOF_Z = 259.0, 487.0          # WALL_Y = rear face of the vertical plate (y 255..259); parts hang toward +y

RAIL = 7.5                                   # 35 mm DIN rail height: DIN-mounted parts sit this much further out
def wall(des, name, x0, dx, dy, dz, z0, orient, src, key=None, rail=False):
    return (key or des, des, name, x0, WALL_Y + (RAIL if rail else 0), z0, dx, dy, dz, 'vertical plate (rear face)', orient, src)
def roof(des, name, x0, y0, dx, dy, dz, orient, src, key=None, rail=True):
    return (key or des, des, name, x0, y0, ROOF_Z - dz - (RAIL if rail else 0), dx, dy, dz, 'roof underside', orient, src)

PARTS = [
    # --- back wall: one tidy row. Servos and VFD screw into the wall (bottoms at z 284); DIN-mounted parts hang on ONE horizontal rail (centre z 347.5).
    wall('X1', 'power / PE terminals (feeders from the base cabinet)', -205, 150, 45, 45, 325, 'DIN rail on the wall, horizontal', 'A', rail=True),
    wall('AIRV', 'SVL = SMC SY3120-5LZE-M5 air valve (tubes leave by the two bellows)', -40, 20, 65, 60, 317, 'DIN rail on the wall, upright', 'A catalog (confirm)', rail=True),
    wall('PSU1', 'Mean Well SDR-120-24 (24 V 5 A)', -5, 63, 114, 125, 285, 'DIN rail, upright', 'A catalog 63x125x114 (confirm)', rail=True),
    wall('PSU2', 'Mean Well XDR-75E-12 (12 V 6.3 A, for the PC)', 78, 30, 116, 125, 285, 'DIN rail, upright', 'S owner datasheet 30x125.2x116', rail=True),
    wall('VFD', 'Delta MS300 (frame A)', 128, 72, 136, 174, 284, 'upright (check manual)', 'A catalog 72x174x136'),
    wall('SVX', 'Mitsubishi MR-J4-40A', 225, 40, 176, 168, 284, 'upright, connectors face the rear (+y)', 'M vendor STEP 40x168x175.9'),
    wall('SVY', 'Mitsubishi MR-J4-40A', 275, 40, 176, 168, 284, 'upright, connectors face the rear (+y)', 'M vendor STEP 40x168x175.9'),
    wall('SVZ', 'Mitsubishi MR-J4-40A', 325, 40, 176, 168, 284, 'upright, connectors face the rear (+y)', 'M vendor STEP 40x168x175.9'),
    # --- upper band on a second wall DIN rail (centre z 445): everything stays under the flange pull nuts (z 478)
    wall('DC1', 'DC-DC 24 V -> 5 V', -250, 25, 25, 55, 417.5, 'DIN rail, upright', 'A', rail=True),
    wall('KA2', 'Omron MY2N-GS + PYFZ-08 (pump)', -213, 28, 62, 62, 414, 'DIN rail, upright', 'A', rail=True),
    wall('KA3', 'Omron MY2N-GS + PYFZ-08 (Z brake)', -173, 28, 62, 62, 414, 'DIN rail, upright', 'A', rail=True),
    wall('XT', 'DIN terminal strip (+24 V / 0 V / +5 V distribution)', -133, 100, 45, 45, 422.5, 'DIN rail, horizontal', 'A', rail=True),
    # --- left column: the two boards, on standoffs (components face the rear)
    wall('BD', 'RP23CNC V2.02 on 4 M3 standoffs', -355, 96, 35, 97, 378, 'standoffs on the plate, components face the rear', 'M vendor STEP 96x97'),
    wall('PC', 'LattePanda IOTA (12 V 60 W) with FIT1027 cooler', -355, 71, 40, 90, 270, 'standoffs on the plate, ports face the rear', 'M vendor STEP board 71x90x19 + cooler'),
]
FLAGS = set()

# wiring ducts on the rear face of the vertical plate: (name, x0, x1, z0, z1), all 40 deep (y 259..299), open slot, lid on the rear.
# None under or beside the drives / VFD (their 35 mm top / bottom and 10 mm side airflow clearances stay free) and none inside the Y-bellows keep-out.
DUCTS = [
    ('Duct_H1', -255, -12, 383, 408),     # above X1 / AIRV, below the DC1..XT row; links the left column, the upper row and X1
    ('Duct_V1', -250, -225, 265, 383),    # between the boards and X1; links H1 with D3
    ('Duct_D3', -360, -170, 245, 265),    # under the IOTA computer; ends at the Y-bellows keep-out (x -165)
    ('Duct_D4', -70, 110, 245, 265),      # under the supplies; starts after the keep-out (x -75); bottom clearance 20 mm to the XDR
    ('Duct_V2', 110, 126, 245, 470),      # between PSU2 and the VFD, 16 wide
]
DUCT_DEPTH = 40.0                                   # reserved space, not a part

# openings (machine x, y, z): purpose
OPENINGS = [
    ('roof flange', 0, 390, 491, 'X conduit PA-29 (KSS PAQ-2929, PG29): hole D45 at (0, 390); plus 2 x D5.5 at (32, 375) and (32, 405) for the bracket screws, nuts under the flange (z 483..487)'),
    ('open', -120, 330, 241, 'Y bellows NW23: conduit support bracket on the front of the vertical plate (2 x D5.5 at x -140 / -100, z 265); no cover'),
    ('open', -392, 330, 270, 'power feeders F1/F2/F3 + PE: KSS PAQ-3636 on the feeder entry plate outside the top-plate left flange (x -395.5..-392.5), facing -x, z 270; the cables enter at the LEFT END of the L plate and run in the air behind the boards to X1'),
    ('open', -392, 410, 270, 'control cable F4: KSS PAQ-1716, same plate, y 410, z 270'),
]
