# -*- coding: utf-8 -*-
"""Gantry-column electrical box: part placement in MACHINE coordinates (mm). Front = -y, floor z=-790.
Envelope given by the mechanical session (docs/handoff_electrical_box_v14.md): x -380..380, y 255..495, z 250..488,
back wall inner face y=495, roof underside z=488, removable bottom cover z~245.
Part = (key, designator, name, x0, y0, z0, dx, dy, dz, mount, orientation, source)
 'W' = on the back wall (back face on y=495; depth runs toward -y), 'R' = on the roof underside (back face on z=488; depth runs down).
 Sizes: M = Mitsubishi vendor STEP/manual, S = datasheet supplied by owner, A = approx catalog value (confirm)."""
ENV = (-380, 380, 255, 495, 249, 487)
WALL_Y, ROOF_Z = 495.0, 487.0

RAIL = 7.5                                   # 35 mm DIN rail height: DIN-mounted parts sit this much further out
def wall(des, name, x0, dx, dy, dz, z0, orient, src, key=None, rail=False):
    return (key or des, des, name, x0, WALL_Y - dy - (RAIL if rail else 0), z0, dx, dy, dz, 'back wall', orient, src)
def roof(des, name, x0, y0, dx, dy, dz, orient, src, key=None, rail=True):
    return (key or des, des, name, x0, y0, ROOF_Z - dz - (RAIL if rail else 0), dx, dy, dz, 'roof underside', orient, src)

PARTS = [
    # --- back wall: one tidy row. Servos and VFD screw into the wall (bottoms at z 284); DIN-mounted parts hang on ONE horizontal rail (centre z 347.5).
    wall('X1', 'power / PE terminals (feeders from the base cabinet)', -205, 150, 45, 45, 325, 'DIN rail on the wall, horizontal', 'A', rail=True),
    wall('AIRV', 'SVL = SMC SY3120-5LZE-M5 air valve (tubes leave by the two bellows)', -40, 20, 65, 60, 317, 'DIN rail on the wall, upright', 'A catalog (confirm)', rail=True),
    wall('PSU1', 'Mean Well SDR-120-24 (24 V 5 A)', -5, 63, 114, 125, 285, 'DIN rail, upright', 'A catalog 63x125x114 (confirm)', rail=True),
    wall('PSU2', 'Mean Well XDR-75E-12 (12 V 6.3 A, for the PC)', 78, 30, 116, 125, 285, 'DIN rail, upright', 'S owner datasheet 30x125.2x116', rail=True),
    wall('VFD', 'Delta MS300 (frame A)', 128, 72, 136, 174, 284, 'upright (check manual)', 'A catalog 72x174x136'),
    wall('SVX', 'Mitsubishi MR-J4-40A', 225, 40, 176, 168, 284, 'upright, connectors to the front', 'M vendor STEP 40x168x175.9'),
    wall('SVY', 'Mitsubishi MR-J4-40A', 275, 40, 176, 168, 284, 'upright, connectors to the front', 'M vendor STEP 40x168x175.9'),
    wall('SVZ', 'Mitsubishi MR-J4-40A', 325, 40, 176, 168, 284, 'upright, connectors to the front', 'M vendor STEP 40x168x175.9'),
    # --- roof underside, hanging down. Row A: one roof DIN rail (centre y 300), parts centred on it. Row B: boards, tops aligned at y 385.
    roof('DC1', 'DC-DC 24 V -> 5 V', -360, 272.5, 25, 55, 25, 'DIN rail, hanging', 'A'),
    roof('KA2', 'Omron MY2N-GS + PYFZ-08 (pump)', -320, 269, 28, 62, 62, 'DIN rail, hanging', 'A'),
    roof('KA3', 'Omron MY2N-GS + PYFZ-08 (Z brake)', -277, 269, 28, 62, 62, 'DIN rail, hanging', 'A'),
    roof('XT', 'DIN terminal strip (+24 V / 0 V / +5 V distribution)', -234, 277.5, 100, 45, 45, 'DIN rail, hanging', 'A'),
    roof('BD', 'RP23CNC V2.02 on 4 M3 standoffs', -360, 385, 96, 97, 35, 'standoffs on the roof, components down', 'M vendor STEP 96x97', rail=False),
    roof('PC', 'LattePanda IOTA (12 V 60 W) with heatsink', -240, 385, 71, 90, 40, 'hanging on standoffs, ports toward the front', 'M vendor STEP board 71x90x19 + heatsink ~40 deep', rail=False),
]
FLAGS = set()                                   # reserved space, not a part

# openings (machine x, y, z): purpose
OPENINGS = [
    ('bottom cover', -340, 270, 244, 'feeders from the base cabinet (servo power + control power, VFD, 24 V supply, control cable): cable gland plate 80x40 with 5 sealed glands'),
    ('bottom cover', -120, 330, 241, 'Y bellows NW23 fixed fitting (mechanical session): Y motor, encoder, brake, 2 prism-cover air tubes, cover switch; hole D45'),
    ('bottom cover', 350, 262, 244, 'X motor + home sensors (right side)'),
    ('roof', 50, 390, 494, 'X bellows NW29 elbow fitting (mechanical session): spindle 4-core, camera, probe, 3 air tubes, Z motor; hole D45; keep a 45 mm column free below it'),
    ('back wall', -280, 495, 400, 'fan intake 120 mm + filter, opening D110 centred x -280, z 400 (fan x -340..-220, z 340..460; the top plate rear flange covers z 471..491, so the fan stays below it); far from the work zone, 345 mm from the exhaust'),
    ('back wall', 170, 495, 471, 'exhaust louvre + filter 90x25 at x 125..215, z 459..484 above the VFD (not on the roof: the X bellows ring is there; PC and PSUs keep clear)'),
]
