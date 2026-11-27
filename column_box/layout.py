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
    # --- roof underside, hanging down. Row A: one roof DIN rail (centre y 300), parts centred on it. Row B: boards, tops aligned at y 385.
    roof('DC1', 'DC-DC 24 V -> 5 V', -360, 282.5, 25, 55, 25, 'DIN rail, hanging', 'A'),
    roof('KA2', 'Omron MY2N-GS + PYFZ-08 (pump)', -320, 279, 28, 62, 62, 'DIN rail, hanging', 'A'),
    roof('KA3', 'Omron MY2N-GS + PYFZ-08 (Z brake)', -277, 279, 28, 62, 62, 'DIN rail, hanging', 'A'),
    roof('XT', 'DIN terminal strip (+24 V / 0 V / +5 V distribution)', -234, 287.5, 100, 45, 45, 'DIN rail, hanging', 'A'),
    roof('BD', 'RP23CNC V2.02 on 4 M3 standoffs', -360, 385, 96, 97, 35, 'standoffs on the roof, components down', 'M vendor STEP 96x97', rail=False),
    roof('PC', 'LattePanda IOTA (12 V 60 W) with heatsink', -240, 385, 71, 90, 40, 'hanging on standoffs, ports toward the front', 'M vendor STEP board 71x90x19 + heatsink ~40 deep', rail=False),
]
FLAGS = set()                                   # reserved space, not a part

# openings (machine x, y, z): purpose
OPENINGS = [
    ('roof flange', 50, 390, 491, 'X bellows NW29 elbow fitting (mechanical session): hole D45 in the L plate flange; keep a 45 mm column free below it'),
    ('open', -120, 330, 241, 'Y bellows NW23: its fixed fitting was on the bottom cover; there is no cover any more -> a conduit support bracket (mechanical session decides where)'),
    ('open', -340, 259, 270, 'power feeders F1/F2/F3 + PE: conduit NW36, ends on a support bracket near the lower left of the L plate (mechanical session)'),
    ('open', -260, 259, 270, 'control cable F4: conduit NW17, ends on a support bracket next to the power conduit (mechanical session)'),
]
