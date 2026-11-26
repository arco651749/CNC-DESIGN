# -*- coding: utf-8 -*-
"""Shared data for the electrical cabinet + base interface (machine coordinates of the v13 base: floor z=-790,
front = -y, legs at x=+-517.5). Dimensions of bought parts are catalog values from memory / vendor photos and
are marked APPROX where not read from a manual: confirm on the vendor drawing before cutting the plate."""

# ---- the back plate IS the electrical cabinet (owner decision): one box, floor standing beside the right side of the base ----
# box (steel, IP54, hinged door on the +x side): W along y, H along z, D along x.  Plate 580 x 540 on the back wall (x = 560).
PLATE_W, PLATE_H = 580, 540
CAB_W, CAB_H, CAB_D = 620, 580, 250
CAB_X0, CAB_Y0, CAB_Z0 = 560.0, -CAB_W / 2, -730.0   # back wall at x=560 (22 mm outside the right legs), bottom on 4 levelling feet at floor+60, top z=-40

# ---- parts on the plate: (designator, name, W, H, D, source) ---------------------------------------
# source: M = Mitsubishi manual / vendor STEP, A = approx catalog value (confirm)
P = {
 'QF':   ('QF1/2/3/4', 'Shihlin BM30-SN 2P', 50, 91, 68, 'A'),
 'KM':   ('KM1 (shared)', 'Shihlin SD-P, size for 3 drives (electrician)', 55, 95, 95, 'A'),
 'PSU12': ('PSU2', 'Mean Well XDR-75E-12 (12 V 6.3 A, for the PC; datasheet 30 x 125.2 x 116)', 30, 125, 116, 'M'),
 'FLS':  ('FL2 (shared)', 'EMC filter sized for 3 drives', 120, 65, 45, 'A'),
 'PSU': ('PSU1', 'Mean Well SDR-240-24 (24 V 10 A, single supply)', 86, 125, 114, 'A'),
 'KA':   ('KA3/KA4', 'Omron MY2N-GS + PYFZ-08 (Z brake, alarm)', 28, 62, 62, 'A'),
 'DC1':  ('DC1', 'DC-DC 24V->5V 1A', 25, 55, 25, 'A'),
 'SV':   ('SVX/Y/Z', 'Mitsubishi MR-J4-40A (vendor STEP 40 x 168 x 175.9)', 40, 168, 176, 'M'),
 'VFD':  ('VFD', 'Delta MS300 frame A', 72, 174, 136, 'A'),
 'BD':   ('BD', 'RP23CNC V2.02 + standoffs (STEP 96 x 97)', 96, 97, 35, 'M'),
 'PC':   ('PC', 'LattePanda IOTA (computer; STEP board 71 x 90 x 19, with heatsink ~40 deep)', 71, 90, 40, 'M'),
 'XT':   ('XT', 'DIN terminal strip: commons + outputs to outside (spindle, pump, valve)', 170, 45, 45, 'A'),
 'TBP':  ('X1', 'power terminals + PE bar (DIN)', 150, 45, 45, 'A'),
}

DUCT = 25           # wiring duct height (W 30 x H 40 open slot, 25 clear gap beside it)
MARGIN = 10
GAP = 6             # side gap between DIN-rail neighbours
SERVO_GAP = 10      # Mitsubishi: leave a gap between drives and 40 mm above/below (manual 3.x) -> duct counts
SERVO_TOP = 40; SERVO_VCLEAR = 30   # vertical clearance used above the drives (duct) -- manual asks 40 mm: flagged in README


def rows():
    return [
        ('R1', 'DIN 1  breakers, contactor, DC-DC, relays', [('QF', 4), ('KM', 1), ('DC1', 1), ('KA', 2)]),
        ('R2', 'DIN 2  24 V supply, filter, terminals', [('PSU', 1), ('PSU12', 1), ('FLS', 1), ('XT', 1)]),
        ('R3', 'plate  drives, VFD, controller', [('SV', 3), ('VFD', 1), ('BD', 1), ('PC', 1), ('TBP', 1)]),
    ]


def place():
    """Pack the rows; return (list of placed parts, report lines, ok)."""
    out, rep = [], []
    y = MARGIN
    ok = True
    for rid, title, items in rows():
        y += (SERVO_TOP if rid == 'R3' else DUCT)   # duct above the row (40 above the drives)
        x = MARGIN
        hmax = max(P[k][3] for k, n in items)
        for k, n in items:
            des, name, w, h, d, src = P[k]
            for i in range(n):
                gap = SERVO_GAP if k == 'SV' else GAP
                out.append(dict(key=k, des=des, name=name, x=x, y=y, w=w, h=h, d=d, src=src, row=rid, idx=i + 1))
                x += w + gap
        xend = x - GAP
        rep.append('%s %-45s width used %4d / %d   height %3d' % (rid, title, xend - MARGIN, PLATE_W - 2 * MARGIN, hmax))
        if xend > PLATE_W - MARGIN: ok = False; rep.append('   !! row too wide')
        y += hmax
    y += DUCT                                      # duct under the last row
    rep.append('total plate height used %d / %d' % (y + MARGIN, PLATE_H))
    if y + MARGIN > PLATE_H: ok = False; rep.append('   !! plate too short')
    return out, rep, ok


if __name__ == '__main__':
    o, r, ok = place()
    print('\n'.join(r)); print('FITS' if ok else 'DOES NOT FIT')
