# -*- coding: utf-8 -*-
"""Gantry-column electrical box: part placement in MACHINE coordinates (mm). Front = -y, floor z=-790.
Envelope given by the mechanical session (docs/handoff_electrical_box_v14.md): x -380..380, y 255..495, z 250..488,
back wall inner face y=495, roof underside z=488, removable bottom cover z~245.
Part = (key, designator, name, x0, y0, z0, dx, dy, dz, mount, orientation, source)
 'W' = on the back wall (back face on y=495; depth runs toward -y), 'R' = on the roof underside (back face on z=488; depth runs down).
 Sizes: M = Mitsubishi vendor STEP/manual, S = datasheet supplied by owner, A = approx catalog value (confirm)."""
ENV = (-380, 380, 255, 495, 250, 488)
WALL_Y, ROOF_Z = 495.0, 488.0

RAIL = 7.5                                   # 35 mm DIN rail height: DIN-mounted parts sit this much further out
def wall(des, name, x0, dx, dy, dz, z0, orient, src, key=None, rail=False):
    return (key or des, des, name, x0, WALL_Y - dy - (RAIL if rail else 0), z0, dx, dy, dz, 'back wall', orient, src)
def roof(des, name, x0, y0, dx, dy, dz, orient, src, key=None, rail=True):
    return (key or des, des, name, x0, y0, ROOF_Z - dz - (RAIL if rail else 0), dx, dy, dz, 'roof underside', orient, src)

PARTS = [
    # --- back wall, upright
    wall('SVX', 'Mitsubishi MR-J4-40A', 225, 40, 176, 168, 285, 'upright, connectors to the front', 'M vendor STEP 40x168x175.9'),
    wall('SVY', 'Mitsubishi MR-J4-40A', 275, 40, 176, 168, 285, 'upright, connectors to the front', 'M vendor STEP 40x168x175.9'),
    wall('SVZ', 'Mitsubishi MR-J4-40A', 325, 40, 176, 168, 285, 'upright, connectors to the front', 'M vendor STEP 40x168x175.9'),
    wall('VFD', 'Delta MS300 (frame A)', 120, 72, 136, 174, 282, 'upright (check manual)', 'A catalog 72x174x136'),
    wall('PSU1', 'Mean Well SDR-120-24 (24 V 5 A)', -50, 63, 114, 125, 306, 'DIN rail, upright', 'A catalog 63x125x114 (confirm)', rail=True),
    wall('PSU2', 'Mean Well XDR-75E-12 (12 V 6.3 A, for the PC)', 20, 30, 116, 125, 306, 'DIN rail, upright', 'S owner datasheet 30x125.2x116', rail=True),
    wall('AIRV', 'SVL = SMC SY3120-5LZE-M5 air valve (probe/tool + prism cover tubes leave by the two bellows)', -300, 20, 65, 60, 350, 'DIN rail on the wall, upright', 'A catalog (confirm)', rail=True),
    # --- roof underside, hanging down
    roof('RCD', 'RCD 2P 30 mA (main)', -370, 265, 70, 91, 68, 'DIN rail, hanging (check mounting position)', 'A'),
    roof('QF2', 'Shihlin BM30-SN 2P (servo branch)', -296, 265, 50, 91, 68, 'DIN rail, hanging', 'A'),
    roof('QF3', 'Shihlin BM30-SN 2P (VFD branch)', -242, 265, 50, 91, 68, 'DIN rail, hanging', 'A'),
    roof('QF4', 'Shihlin BM30-SN 2P (24 V supply branch)', -188, 265, 50, 91, 68, 'DIN rail, hanging', 'A'),
    roof('KM1', 'Shihlin SD-P (3 drives, DC24 V coil)', -134, 265, 55, 95, 95, 'DIN rail, hanging', 'A'),
    roof('DC1', 'DC-DC 24 V -> 5 V', -75, 265, 25, 55, 25, 'DIN rail, hanging', 'A'),
    roof('KA3', 'Omron MY2N-GS + PYFZ-08 (Z brake)', -46, 265, 28, 62, 62, 'DIN rail, hanging', 'A'),
    roof('KA2', 'Omron MY2N-GS + PYFZ-08 (pump)', -14, 265, 28, 62, 62, 'DIN rail, hanging', 'A'),
    roof('XT', 'DIN terminal strip (+24 V / 0 V / +5 V distribution)', -370, 385, 170, 45, 45, 'DIN rail, hanging', 'A'),
    roof('BD', 'RP23CNC V2.02 on 4 M3 standoffs', -190, 385, 96, 97, 35, 'standoffs on the roof, components down', 'M vendor STEP 96x97', rail=False),
    roof('X1', 'power terminals + PE bar', -370, 440, 150, 45, 45, 'DIN rail, hanging', 'A'),
    roof('FL2', 'EMC filter slot (reserved, not fitted)', 30, 262, 120, 65, 45, 'reserved', 'A', rail=False),
    roof('PC', 'LattePanda IOTA (12 V 60 W) with heatsink', -85, 395, 71, 90, 40, 'hanging on standoffs, ports toward the front', 'M vendor STEP board 71x90x19 + heatsink ~40 deep', rail=False),
]
FLAGS = {'FL2'}                                   # reserved space, not a part

# openings (machine x, y, z): purpose
OPENINGS = [
    ('bottom cover', -340, 270, 245, 'mains inlet 220 V (cable gland M25)'),
    ('bottom cover', -120, 330, 245, 'Y bellows NW23 fixed fitting (mechanical session): Y motor, encoder, brake, 2 prism-cover air tubes, cover switch; hole D45'),
    ('bottom cover', 350, 262, 245, 'X motor + home sensors (right side)'),
    ('bottom cover', -250, 400, 245, 'fan intake + filter, cut-out 130 mm (120 mm fan)'),
    ('roof', 50, 390, 495, 'X bellows NW29 elbow fitting (mechanical session): spindle 4-core, camera, probe, 3 air tubes, Z motor; hole D45; keep a 45 mm column free below it'),
    ('back wall', 170, 495, 472, 'exhaust louvre + filter 90x25 at x 125..215, z 460..485 above the VFD (not on the roof: the X bellows ring is there; PC and PSUs keep clear)'),
]
