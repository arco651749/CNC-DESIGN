# -*- coding: utf-8 -*-
"""Base protection cabinet (second cabinet, in the front bay of the base). MACHINE coordinates, front = -y, floor z=-790.
It holds the protection / mains parts only (RCD, branch breakers, shared contactor, filter slot, mains terminals, e-stop and start buttons on the door);
all control parts are in the column box (column_box/).
Cabinet: 360 W x 280 H x 120 D wall box (S1/S2 moved to a separate operator box), IP54, door to the front. Back plate bolted to two 40x40 rails at y -560..-520 between two new uprights at x +-230 (y -600..-560).
Part = (des, name, W, H, D, source); placed in rows on the plate seen from the front (u -> +x, v down -> -z)."""
CAB_W, CAB_H, CAB_D = 360, 280, 120
CAB_X0, CAB_Y0, CAB_Z0 = -180.0, -680.0, -510.0      # x min, front face y (door), bottom z ; back face y = -560
PLATE_W, PLATE_H = 320, 240                          # mounting plate 2.5 t
RAIL, DUCT, MARGIN, GAP = 7.5, 20, 8, 6
PARTS = {
 'RCD': ('RCD', '2P earth-leakage breaker 30 mA (mains)', 70, 91, 68, 'A'),
 'QF2': ('QF2', 'Shihlin BM30-SN 2P (servo branch, shared)', 50, 91, 68, 'A'),
 'QF3': ('QF3', 'Shihlin BM30-SN 2P (VFD branch)', 50, 91, 68, 'A'),
 'QF4': ('QF4', 'Shihlin BM30-SN 2P (24 V / 12 V supplies)', 50, 91, 68, 'A'),
 'KM1': ('KM1', 'Shihlin SD-P (3 drives, DC24 V coil, shared)', 55, 95, 95, 'A'),
 'X0':  ('X0', 'mains in + PE bar + feeder terminals (DIN)', 150, 45, 45, 'A'),
 'FL2': ('FL2', 'EMC filter slot, reserved (rated for 3 drives)', 120, 65, 45, 'A'),
}
ROWS = [('DIN 1  breakers + contactor', ['RCD', 'QF2', 'QF3', 'QF4', 'KM1']), ('DIN 2  terminals + filter slot', ['X0', 'FL2'])]
def place():
    out, y = [], MARGIN
    for title, keys in ROWS:
        y += DUCT; x = MARGIN; hmax = max(PARTS[k][3] for k in keys)
        for k in keys:
            des, name, w, h, d, src = PARTS[k]; out.append(dict(key=k, des=des, name=name, x=x, y=y, w=w, h=h, d=d, src=src)); x += w + GAP
        y += hmax
    y += DUCT + MARGIN
    return out, y
if __name__ == '__main__':
    o, h = place(); print('plate height used %d / %d' % (h, PLATE_H)); [print(p['des'], p['x'], p['y']) for p in o]
