# -*- coding: utf-8 -*-
"""Shared data for the electrical cabinet + base interface (machine coordinates of the v13 base: floor z=-790,
front = -y, legs at x=+-517.5). Dimensions of bought parts are catalog values from memory / vendor photos and
are marked APPROX where not read from a manual: confirm on the vendor drawing before cutting the plate."""

# ---- cabinet (steel wall box, IP54, 2 doors, sloped roof) ------------------------------------------
CAB_W, CAB_H, CAB_D = 940, 540, 250
PLATE_W, PLATE_H = 880, 480                      # mounting plate (galvanised, 2.5 t)
CAB_X0, CAB_Y0, CAB_Z0 = -CAB_W / 2, -540.0, -690.0   # front face y=-540, bottom on two cross rails (z -730..-690), top 20 below the top ring

# ---- parts on the plate: (designator, name, W, H, D, source) ---------------------------------------
# source: M = Mitsubishi manual, A = approx catalog value (confirm)
P = {
 'QF':   ('QF1/2X/2Y/2Z/3/4', 'Shihlin BM30-SN 2P', 50, 91, 68, 'A'),
 'KM':   ('KM1X/Y/Z', 'Shihlin SD-P11', 45, 80, 85, 'A'),
 'PSU1': ('PSU1/PSU3', 'Mean Well SDR-120-24', 63, 125, 114, 'A'),
 'PSU2': ('PSU2', 'Mean Well SDR-75-24', 53, 125, 114, 'A'),
 'KA':   ('KA1-5', 'Omron MY2N-GS + PYFZ-08', 28, 62, 62, 'A'),
 'DC1':  ('DC1', 'DC-DC 24V->5V 1A', 25, 55, 25, 'A'),
 'SV':   ('SVX/Y/Z', 'Mitsubishi MR-J4-40A', 50, 168, 135, 'M'),
 'VFD':  ('VFD', 'Delta MS300 frame A', 72, 174, 136, 'A'),
 'FL':   ('FL2X/Y/Z', 'Soshin HF3010A-UN', 114, 58, 40, 'A'),
 'FLV':  ('FL2X/Y/Z', 'Soshin HF3010A-UN (stood up)', 58, 114, 40, 'A'),
 'TB':   ('TBX/Y/Z', 'TB40-MRJ4A terminal block', 125, 70, 50, 'A'),
 'BD':   ('BD', 'RP23CNC + WIZ850io (standoffs)', 160, 100, 35, 'A'),
 'TBP':  ('X1', 'power terminals + PE bar (DIN)', 150, 45, 45, 'A'),
}

DUCT = 25           # wiring duct height (W 30 x H 40 open slot, 25 clear gap beside it)
MARGIN = 10
GAP = 6             # side gap between DIN-rail neighbours
SERVO_GAP = 12      # Mitsubishi: leave a gap between drives and 40 mm above/below (manual 3.x) -> duct counts
SERVO_TOP = 40; SERVO_VCLEAR = 30   # vertical clearance used above the drives (duct) -- manual asks 40 mm: flagged in README


def rows():
    """Return rows of (key, count) top to bottom."""
    return [
        ('R1', 'DIN 1  breakers + contactors + 24 V',
         [('QF', 6), ('KM', 3), ('DC1', 1)]),
        ('R2', 'DIN 2  relays + terminals',
         [('KA', 7), ('TB', 3), ('TBP', 1)]),
        ('R3', 'plate  drives, VFD, filters, controller',
         [('FLV', 3), ('SV', 3), ('VFD', 1), ('PSU1', 2), ('PSU2', 1), ('BD', 1)]),
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
