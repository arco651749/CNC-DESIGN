#!/usr/bin/env python3
"""CNC gantry wiring diagram -> KiCad schematic (CNC_wiring.kicad_sch).

Run:  python3 build_wiring.py        (then: kicad-cli sch export pdf CNC_wiring.kicad_sch)
All layout numbers are mm on an A1 sheet; every pin sits on the 2.54 mm grid.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import Block, Sheet, R, Photo, PhotoBlock

S = Sheet("A1")
BRN = (120, 60, 10); BLU = (0, 0, 220); GRN = (0, 140, 0); RED = (220, 0, 0); BLK = (0, 0, 0)
GRY = (110, 110, 110); ORG = (255, 120, 0); PUR = (160, 0, 160); YEL = (170, 135, 0)
TEL = (0, 140, 140); UCL = (200, 50, 0); ANA = (0, 120, 200)
THICK = 0.381

def blk(*a, **k): return S.add(Block(*a, **k))

# ------------------------------------------------------------------ 1. AC in -> breakers -> contactors
AC = blk("AC", "AC 220V 單相 市電", 38.1, 50.8, right=[("L1", 1), ("L2", 2), ("PE", 3)], w=30.48)
QF1 = blk("QF1", "QF1 主斷路器 2P 20A", 88.9, 50.8, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
FL1 = blk("FL1", "FL1 EMI 濾波器", 139.7, 50.8, left=[("L1i", 1, "L1"), ("L2i", 2, "L2"), ("PE", 3)], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
SLOTS = {"X": 35.56, "Y": 73.66, "Z": 111.76}
QF2, KM1 = {}, {}
for ax, top in SLOTS.items():
    QF2[ax] = blk("QF2" + ax, "QF2%s %s軸 MCCB 2P 10A" % (ax, ax), 203.2, top, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")],
                  right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
    KM1[ax] = blk("KM1" + ax, "KM1%s %s軸 接觸器" % (ax, ax), 279.4, top, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")],
                  right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], bottom=[("A1", -2.54), ("A2", 2.54)], w=20.32, tmode="above")

S.conn("AC_L1", BRN, [AC["L1"], QF1["L1i"]], width=THICK)
S.conn("AC_L2", BLU, [AC["L2"], QF1["L2i"]], width=THICK)
S.stub(AC["PE"], "PE", GRN)
S.conn("F_L1", BRN, [QF1["L1o"], FL1["L1i"]], width=THICK)
S.conn("F_L2", BLU, [QF1["L2o"], FL1["L2i"]], width=THICK)
S.stub(FL1["PE"], "PE", GRN)
S.conn("L1_IN", BRN, [FL1["L1o"]] + [QF2[a]["L1i"] for a in "XYZ"], lane=165.1, width=THICK); S.label("L1_IN", "L1_IN", 165.1, 98.04, 180)
S.conn("L2_IN", BLU, [FL1["L2o"]] + [QF2[a]["L2i"] for a in "XYZ"], lane=170.18, width=THICK); S.label("L2_IN", "L2_IN", 170.18, 103.12, 0)
for ax in "XYZ":
    # MCCB out: servo control power L11/L21 (always on, before the contactor) + contactor input
    y1 = SLOTS[ax] + R
    S.conn("L1_CTL_" + ax, BRN, [QF2[ax]["L1o"], KM1[ax]["L1i"]], width=THICK); S.label("L1_CTL_" + ax, "L1_CTL_" + ax, 241.3, y1, 0)
    S.conn("L2_CTL_" + ax, BLU, [QF2[ax]["L2o"], KM1[ax]["L2i"]], width=THICK); S.label("L2_CTL_" + ax, "L2_CTL_" + ax, 241.3, y1 + R, 0)
    S.stub(KM1[ax]["A1"], "KMCOIL", ORG); S.stub(KM1[ax]["A2"], "0V3", BLK)

# ------------------------------------------------------------------ 2. servo drives + terminal blocks + motors (real pictures)
SRV_CX, MOT_CX = 469.9, 596.9
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vendor", "mitsubishi", "photos")
AXES = {"X": 35.56, "Y": 137.16, "Z": 238.76}   # top row of each axis block

# MR-J4-A product picture, cropped to the drive; pin = (id, x px, y px, side, label) on the cropped picture
K_SV = 0.17
SV_PINS = [("L1", 48, 102, "left", "L1"), ("L3", 48, 160, "left", "L3"), ("L11", 48, 339, "left", "L11"), ("L21", 48, 360, "left", "L21"),
           ("U", 48, 390, "left", "U"), ("V", 48, 418, "left", "V"), ("W", 48, 447, "left", "W"), ("PE", 13, 563, "left", "PE"),
           ("ENC", 90, 472, "right", "CN2"), ("BAT", 105, 544, "right", "CN4")]
def make_sv(ax, top):
    ph = S.photo(Photo(os.path.join(PH, "mrj4a_catalog_view.jpg"), SRV_CX, top - 2.56 + 572 * K_SV / 2, K_SV, crop=(252, 62, 395, 634)))
    return S.add(PhotoBlock("SV" + ax, "SV%s MR-J4-40A %s軸（實物圖）" % (ax, ax), ph, SV_PINS))

# TB40-MRJ4A terminal block picture (terminal x in picture px; top row y=279, bottom row y=326; crop origin 20,120)
K_TB = 0.1871
TB_TOP = {"PP": (428, "10"), "PG": (451, "11"), "NP": (386, "35"), "NG": (407, "36"), "SON": (38, "15"),
          "EM2": (170, "42"), "DICOM": (299, "20"), "DOCOM": (320, "46")}
TB_BOT = {"ALM": (157, "48"), "MBR": (92, "23")}
TB_NET = {"PP": ("{ax}_PP", ORG), "PG": ("{ax}_PG", ORG), "NP": ("{ax}_NP", PUR), "NG": ("{ax}_NG", PUR), "SON": ("{ax}_SON", YEL),
          "EM2": ("EM2_COM", ORG), "DICOM": ("+24V3", RED), "DOCOM": ("0V3", BLK), "ALM": ("ALM_{ax}", PUR), "MBR": ("MBR_Z", PUR)}
def make_tb(ax, cy):
    ph = S.photo(Photo(os.path.join(PH, "tb40_mrj4a_terminal_block.png"), 405.0, cy, K_TB, crop=(20, 120, 468, 350)))
    pins = [(pid, x - 20, 159, "top", num) for pid, (x, num) in TB_TOP.items()]
    pins += [(pid, x - 20, 206, "bottom", num) for pid, (x, num) in TB_BOT.items() if pid != "MBR" or ax == "Z"]
    tb = S.add(PhotoBlock("TB" + ax, "TB%s TB40-MRJ4A 端子台 %s軸（實物圖，號碼＝CN1 腳號）" % (ax, ax), ph, pins))
    for pid in tb.pins:
        net, col = TB_NET[pid]; S.stub(tb[pid], net.format(ax=ax), col)
    return tb

def motor(ax, top, brake=False):
    left = [("U", 1), ("V", 2), ("W", 3), ("PE", 4), ("ENC", 6, "ENC CN2")]
    if brake: left += [("B1", 9), ("B2", 10)]
    name = "HG-KR43%s  %s軸馬達" % ("B(附煞車)" if brake else "", ax)
    return blk("M" + ax, name, MOT_CX, top, left=left, w=30.48)

SV = {a: make_sv(a, t) for a, t in AXES.items()}
MT = {a: motor(a, t, a == "Z") for a, t in AXES.items()}
MX, MY, MZ = MT["X"], MT["Y"], MT["Z"]
SVX, SVY, SVZ = SV["X"], SV["Y"], SV["Z"]
TBN = {a: make_tb(a, t + 69.44) for a, t in AXES.items()}
S.text("控制線接在端子台上，端子台以排線接驅動器 CN1（號碼＝CN1 腳號）", 365.0, 120.0 + 13, 1.2)

# main power, single phase: contactor L1/L2 -> drive L1/L3 (L2 left open, manual 3.3.1); CNP1 poles top to bottom: L1 L2 L3 N- P3 P4
MIDS = {"X": (455.0, 452.0), "Y": (345.44, 342.9), "Z": (353.06, 350.52)}
for ax in "XYZ":
    k1, k2, p1, p3 = KM1[ax]["L1o"], KM1[ax]["L2o"], SV[ax]["L1"], SV[ax]["L3"]
    m1, m3 = MIDS[ax]
    S.path("L1_SRV_" + ax, BRN, THICK, [(k1.x, k1.y), (m1, k1.y), (m1, p1.y), (p1.x, p1.y)], [k1, p1])
    S.path("L2_SRV_" + ax, BLU, THICK, [(k2.x, k2.y), (m3, k2.y), (m3, p3.y), (p3.x, p3.y)], [k2, p3])
LONG = 10.16
for ax in "XYZ":
    s, m = SV[ax], MT[ax]
    S.stub(s["L11"], "L1_CTL_" + ax, BRN, LONG); S.stub(s["L21"], "L2_CTL_" + ax, BLU, LONG); S.stub(s["PE"], "PE", GRN, LONG)
    for pid, col in (("U", UCL), ("V", BLK), ("W", GRY)):
        S.stub(s[pid], "%s_%s" % (ax, pid), col, LONG, THICK); S.stub(m[pid], "%s_%s" % (ax, pid), col, R, THICK)
    S.stub(m["PE"], "PE", GRN)
    S.stub(s["ENC"], ax + "_ENC", TEL, LONG); S.stub(m["ENC"], ax + "_ENC", TEL)
# Z brake: MBR drives relay KA3 coil, KA3 switches 24V to the motor brake
KA3 = blk("KA3", "KA3 Z軸煞車繼電器", 533.4, 274.32, left=[("A1", 1), ("A2", 2), ("COM", 3)], right=[("NO", 2)], w=15.24)
S.stub(KA3["A1"], "+24V3", RED); S.stub(KA3["A2"], "MBR_Z", PUR); S.stub(KA3["COM"], "+24V3", RED)
S.conn("BRK_Z", RED, [KA3["NO"], MZ["B1"]])
S.stub(MZ["B2"], "0V3", BLK)
# absolute-position backup batteries on CN4 of each drive (not connected to the controller)
OLV = (150, 100, 0)
for ax, top in AXES.items():
    bt = blk("BT" + ax, "BT%s %s軸電池 (MR-BAT6V1SET)" % (ax, ax), 533.4, top + 13 * R, left=[("CN4", 1, "CN4")], w=20.32)
    S.stub(SV[ax]["BAT"], "BAT_" + ax, OLV, LONG); S.stub(bt["CN4"], "BAT_" + ax, OLV)
    S.text("加電池：保存絕對位置以免做 home\n(須控制器支援 ABS 傳送；\ngrblHAL 暫不支援，仍保留原點感測器)", 497, top + 13 * R + 17.5, 1.3)

# ------------------------------------------------------------------ 3. controller RP23CNC + interface board
BT = 256.54
# RP23CNC V2.02 seen from straight above: real photo (2000 x 2000 px). Screw-head centres: linear fits to the detected heads of each strip.
TOP_X = [334.8 + 67.18 * i for i in range(22)]       # top strip, 22 terminals, left to right
BOT_X = [329.4 + 67.40 * i for i in range(22)]       # bottom strip, 22 terminals, left to right
RIGHT_Y = [344.5 + 67.49 * i for i in range(20)]     # right strip, 20 terminals, top to bottom
TOP_Y, BOT_Y, RIGHT_X = 136.0, 1824.0, 1883.0
A_IDX = {"PWR_G": 0, "PWR_P": 1, "SGND": 6, "S010": 7, "K2S": 14, "K2P": 15, "K5S": 16, "K5P": 17, "K1S": 20, "K1P": 21}   # top strip, left to right
C_IDX = {"Z_GND": 8, "Z_STP": 9, "Z_DIR": 10, "Z_EN": 11, "Y_GND": 12, "Y_STP": 13, "Y_DIR": 14, "Y_EN": 15,
         "X_GND": 16, "X_STP": 17, "X_DIR": 18, "X_EN": 19}    # right strip, top to bottom; inside an axis: GND STEP DIR ENA (silkscreen)
B_IDX = {"ISO_P": 0, "ISO_G": 1, "LZS": 6, "LZG": 7, "LYS": 8, "LYG": 9, "LXS": 10, "LXG": 11, "ES_S": 20, "ES_G": 21}   # bottom strip, left to right
# servo-alarm 2x3 header (pin-tip centres in the photo): top row X Z B, bottom row Y A Gnd (silkscreen)
ALARM_PX = {"AX": (1213.0, 1563.0, "top", 5.08), "AZ": (1262.0, 1563.0, "top", 10.16), "AY": (1211.0, 1614.0, "bottom", 5.08), "AG": (1301.0, 1606.0, "bottom", 5.08)}
bd_pins = [(pid, TOP_X[i], TOP_Y, "top", pid) for pid, i in A_IDX.items()]
bd_pins += [(pid, RIGHT_X, RIGHT_Y[i], "right", pid) for pid, i in C_IDX.items()]
bd_pins += [(pid, BOT_X[i], BOT_Y, "bottom", pid) for pid, i in B_IDX.items()]
bd_pins += [(pid, x, y, side, pid) for pid, (x, y, side, _) in ALARM_PX.items()]
bd_pins.append(("ETH", 538.0, 580.0, "left", "ETH"))
PH_RP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vendor", "rp23cnc", "photos")
BD_PH = S.photo(Photo(os.path.join(PH_RP, "RP23CNC_V2.02_top_photo.jpg"), 148.0, 250.0, 0.0756))
BD = S.add(PhotoBlock("BD", "RP23CNC V2.02 控制板（正上方實拍照，螺絲位置取自照片）", BD_PH, bd_pins, title_dy=16.0))
BD_NET = {"PWR_P": ("+24V1", RED), "PWR_G": ("0V1", BLK), "S010": ("SPD_0-10V", ANA), "SGND": ("SPD_GND", BLK),
          "K1P": ("KA1_A1", RED), "K1S": ("KA1_A2", PUR), "K2P": ("KA2_A1", RED), "K2S": ("KA2_A2", PUR), "K5P": ("KA5_A1", RED), "K5S": ("KA5_A2", PUR),
          "ISO_P": ("+24V2", RED), "ISO_G": ("0V2", BLK), "ES_S": ("ESTOP_SIG", PUR), "ES_G": ("ESTOP_GND", BLK),
          "LXS": ("LIM_X_SIG", BLK), "LXG": ("LIM_X_GND", BLU), "LYS": ("LIM_Y_SIG", BLK), "LYG": ("LIM_Y_GND", BLU),
          "LZS": ("LIM_Z_SIG", BLK), "LZG": ("LIM_Z_GND", BLU),
          "AX": ("ALMIN_X", PUR), "AY": ("ALMIN_Y", PUR), "AZ": ("ALMIN_Z", PUR), "AG": ("ALMIN_G", BLK), "ETH": ("ETH", ANA)}
for ax in "XYZ":
    BD_NET.update({ax + "_STP": (ax + "_STP", ORG), ax + "_DIR": (ax + "_DIR", PUR), ax + "_EN": (ax + "_EN", YEL), ax + "_GND": (ax + "_GND", BLK)})
STAG = [5.08, 10.16, 15.24, 20.32]
for pid, (net, col) in BD_NET.items():
    ln = 5.08 if pid in C_IDX else (ALARM_PX[pid][3] if pid in ALARM_PX else (13.0 if pid in B_IDX else (7.62 if pid in A_IDX else 12.7)))
    S.stub(BD[pid], net, col, ln)
IFB = blk("IFB", "IFB1 MR-J4 介面板", 330.2, BT, w=40.64,
          left=[("X_STP", 1, "X STP"), ("X_DIR", 2, "X DIR"), ("X_EN", 3, "X EN"), ("X_GND", 4, "X GND"),
                ("Y_STP", 6, "Y STP"), ("Y_DIR", 7, "Y DIR"), ("Y_EN", 8, "Y EN"), ("Y_GND", 9, "Y GND"),
                ("Z_STP", 11, "Z STP"), ("Z_DIR", 12, "Z DIR"), ("Z_EN", 13, "Z EN"), ("Z_GND", 14, "Z GND"),
                ("V5", 16, "+5V"), ("G5", 17, "GND5"), ("G3", 18, "0V3")],
          right=[("%s_%s" % (a, n), r0 + i + 1, "%s %s" % (a, n))
                 for a, r0 in (("X", 0), ("Y", 6), ("Z", 12)) for i, n in enumerate(("PP", "PG", "NP", "NG", "SON"))])
for ax in "XYZ":
    for n in ("STP", "DIR", "EN", "GND"):
        S.stub(IFB["%s_%s" % (ax, n)], BD_NET["%s_%s" % (ax, n)][0], BD_NET["%s_%s" % (ax, n)][1])
S.stub(IFB["V5"], "+5V", RED); S.stub(IFB["G5"], "0V1", BLK); S.stub(IFB["G3"], "0V3", BLK)
for ax in "XYZ":
    for n, col in (("PP", ORG), ("PG", ORG), ("NP", PUR), ("NG", PUR), ("SON", YEL)):
        S.stub(IFB["%s_%s" % (ax, n)], "%s_%s" % (ax, n), col)
LAN = blk("LAN", "LAN 交換器 / 監控 PC（接 WIZ850io 模組的 RJ45）", 38.1, 210.82, right=[("RJ", 1, "RJ45")], w=20.32)
S.stub(LAN["RJ"], "ETH", ANA)

# relays driven by the board relay outputs (coil between +V and SIG)
KA1 = blk("KA1", "KA1 主軸 ON/OFF 繼電器", 304.8, 190.5, left=[("A1", 1), ("A2", 2)], right=[("COM", 1), ("NO", 2)], w=20.32)
KA2 = blk("KA2", "KA2 冷卻幫浦繼電器", 304.8, 210.82, left=[("A1", 1), ("A2", 2)], right=[("COM", 1), ("NO", 2)], w=20.32)
KA5 = blk("KA5", "KA5 吹氣閥繼電器", 304.8, 231.14, left=[("A1", 1), ("A2", 2)], right=[("COM", 1), ("NO", 2)], w=20.32)
for k in (KA1, KA2, KA5):
    S.stub(k["A1"], k.ref + "_A1", RED); S.stub(k["A2"], k.ref + "_A2", PUR)
S.stub(KA1["COM"], "VFD_COM", BLK); S.stub(KA1["NO"], "VFD_FWD", ORG)
S.stub(KA2["COM"], "L1_AUX", BRN, R, THICK)
S.stub(KA5["COM"], "+24V1", RED)
PUMP = blk("PUMP", "冷卻幫浦 220V 單相", 304.8, 129.54, right=[("L2", 1), ("PE", 2), ("L1", 3)], w=20.32)
SVL = blk("SVL", "SV1 吹氣電磁閥 24V", 304.8, 160.02, right=[("N", 1, "−"), ("P", 2, "+")], w=20.32)
S.stub(PUMP["L2"], "L2_AUX", BLU, R, THICK); S.stub(PUMP["PE"], "PE", GRN)
S.conn("PUMP_L1", BRN, [KA2["NO"], PUMP["L1"]], lane=340.36, width=THICK)
S.stub(SVL["N"], "0V1", BLK)
S.conn("SV_PLUS", RED, [KA5["NO"], SVL["P"]], lane=345.44)

# ------------------------------------------------------------------ 4. home sensors, e-stop input, servo alarms (board bottom)
ALM = blk("ALM", "KA4 伺服報警反相繼電器 (3路模組)", 292.1, 360.68,
          left=[("AG", 1, "COM GND"), ("AZ", 2, "NC Z"), ("AY", 3, "NC Y"), ("AX", 4, "NC X")],
          right=[("A1", 1, "A1 +24V"), ("A2X", 2, "A2 X"), ("A2Y", 3, "A2 Y"), ("A2Z", 4, "A2 Z")], w=25.4)
SENS = blk("SENS", "原點感測器 X/Y/Z (NPN 24V 3線 ×3)", 292.1, 401.32,
           left=[("ZBU", 1, "Z BU 0V"), ("ZBK", 2, "Z BK OUT"), ("YBU", 3, "Y BU 0V"), ("YBK", 4, "Y BK OUT"), ("XBU", 5, "X BU 0V"), ("XBK", 6, "X BK OUT")],
           right=[("XBN", 1, "X BN +24V"), ("YBN", 3, "Y BN +24V"), ("ZBN", 5, "Z BN +24V")], w=30.48)
for ax in "XYZ":
    S.stub(SENS["%sBK" % ax], "LIM_%s_SIG" % ax, BLK); S.stub(SENS["%sBU" % ax], "LIM_%s_GND" % ax, BLU)
    S.stub(SENS["%sBN" % ax], "+24V2", BRN)
    S.stub(ALM["A%s" % ax], "ALMIN_" + ax, PUR)
S.stub(ALM["AG"], "ALMIN_G", BLK)
S.stub(ALM["A1"], "+24V3", RED)
for ax in "XYZ": S.stub(ALM["A2%s" % ax], "ALM_" + ax, PUR)

# ------------------------------------------------------------------ 5. spindle VFD
VFD = blk("VFD", "台達 MS300 變頻器 (單相230V，1.5kW級 VFD7A5MS21系列)", SRV_CX, 363.22,
          left=[("RL1", 1, "R/L1"), ("SL2", 2, "S/L2"), ("PE", 3)],
          right=[("U", 1), ("V", 2), ("W", 3), ("RPE", 4, "PE")], w=30.48)
SP = blk("SP", "主軸 0.8kW 風冷電主軸 (3相)", MOT_CX, 363.22, left=[("U", 1), ("V", 2), ("W", 3), ("PE", 4)], w=30.48)
QF3 = blk("QF3", "QF3 主軸 MCCB 2P 10A", 368.3, 363.22, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
KM2 = blk("KM2", "KM2 接觸器 (主軸)", 419.1, 363.22, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")],
          bottom=[("A1", -2.54), ("A2", 2.54)], w=20.32, tmode="above")
S.stub(QF3["L1i"], "L1_IN", BRN, R, THICK); S.stub(QF3["L2i"], "L2_IN", BLU, R, THICK)
S.conn("L1_KM2", BRN, [QF3["L1o"], KM2["L1i"]], width=THICK); S.conn("L2_KM2", BLU, [QF3["L2o"], KM2["L2i"]], width=THICK)
S.conn("L1_VFD", BRN, [KM2["L1o"], VFD["RL1"]], width=THICK)
S.conn("L2_VFD", BLU, [KM2["L2o"], VFD["SL2"]], width=THICK)
S.stub(KM2["A1"], "KMCOIL", ORG); S.stub(KM2["A2"], "0V3", BLK)
S.stub(VFD["PE"], "PE", GRN)
# control terminals drawn on the real MS300 pictures from the Delta catalogue (pin px measured on the picture)
PH_D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vendor", "delta", "photos")
PH_V1 = S.photo(Photo(os.path.join(PH_D, "MS300_control_terminals_front.png"), 735.0, 330.0, 0.2))
VFA = S.add(PhotoBlock("VFA", "VFA MS300 控制端子（Delta 型錄實物照，正拍）：AVI、ACM、DCM", PH_V1,
    [("AVI", 123.8, 160.0, "bottom", "AVI"), ("ACM", 102.5, 160.0, "bottom", "ACM"), ("DCM", 130.0, 62.0, "top", "DCM")], title_dy=2.0))
PH_V2 = S.photo(Photo(os.path.join(PH_D, "MS300_control_terminals_angled.png"), 735.0, 400.0, 0.2))
VFB = S.add(PhotoBlock("VFB", "VFB MS300 控制端子（Delta 型錄實物照，斜拍）：MI1", PH_V2,
    [("MI1", 70.6, 148.0, "left", "MI1")], title_dy=2.0))
S.stub(VFA["AVI"], "SPD_0-10V", ANA, 10.16); S.stub(VFA["ACM"], "SPD_GND", BLK, 15.24)
S.stub(VFB["MI1"], "VFD_FWD", ORG, 8.0); S.stub(VFA["DCM"], "VFD_COM", BLK, 8.0)
S.text("照片解析度低：MI1 位置為估計，DCM 在紅色接頭（STO 區）的第 4 個孔；\n接線前請以機身端子絲印為準（型錄第 13 頁）", 702.0, 425.0, 1.2)
S.conn("SP_U", UCL, [VFD["U"], SP["U"]], width=THICK)
S.conn("SP_V", BLK, [VFD["V"], SP["V"]], width=THICK)
S.conn("SP_W", GRY, [VFD["W"], SP["W"]], width=THICK)
S.conn("SP_PE", GRN, [VFD["RPE"], SP["PE"]], width=THICK)

# ------------------------------------------------------------------ 6. 24V supplies, e-stop circuit
QF4 = blk("QF4", "QF4 24V電源/幫浦 MCCB 2P 6A", 50.8, 358.14, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
S.stub(QF4["L1i"], "L1_IN", BRN, R, THICK); S.stub(QF4["L2i"], "L2_IN", BLU, R, THICK)
S.stub(QF4["L1o"], "L1_AUX", BRN, R, THICK); S.stub(QF4["L2o"], "L2_AUX", BLU, R, THICK)
PSU1 = blk("PSU1", "PSU1 24V 3A (控制板/繼電器/5V)", 50.8, 396.24, left=[("L1", 1), ("L2", 2), ("PE", 3)], right=[("P", 1, "+24V"), ("N", 2, "0V")], w=20.32)
PSU2 = blk("PSU2", "PSU2 24V 1A (隔離輸入/感測器)", 50.8, 441.96, left=[("L1", 1), ("L2", 2), ("PE", 3)], right=[("P", 1, "+24V"), ("N", 2, "0V")], w=20.32)
PSU3 = blk("PSU3", "PSU3 24V 5A (伺服I/O/煞車/急停)", 50.8, 487.68, left=[("L1", 1), ("L2", 2), ("PE", 3)], right=[("P", 1, "+24V"), ("N", 2, "0V")], w=20.32)
for i, p in enumerate((PSU1, PSU2, PSU3), 1):
    S.stub(p["L1"], "L1_AUX", BRN, R, THICK); S.stub(p["L2"], "L2_AUX", BLU, R, THICK); S.stub(p["PE"], "PE", GRN)
    S.stub(p["P"], "+24V%d" % i, RED); S.stub(p["N"], "0V%d" % i, BLK)
DC1 = blk("DC1", "DC1 DC-DC 24V→5V 1A", 127.0, 396.24, left=[("P", 1, "+24V"), ("N", 2, "0V")], right=[("P5", 1, "+5V"), ("N5", 2, "0V")], w=20.32)
S.stub(DC1["P"], "+24V1", RED); S.stub(DC1["N"], "0V1", BLK); S.stub(DC1["P5"], "+5V", RED); S.stub(DC1["N5"], "0V1", BLK)
S1 = blk("S1", "S1 急停按鈕 (2NC+1NO)", 127.0, 462.28, left=[("A1", 1, "NC1"), ("A2", 2, "NC2"), ("A3", 3, "NO")], right=[("B1", 1, "NC1"), ("B2", 2, "NC2"), ("B3", 3, "NO")], w=20.32)
S2 = blk("S2", "S2 啟動按鈕 (NO)", 203.2, 462.28, left=[("A", 1)], right=[("B", 1)], w=20.32)
AUX = blk("AUX", "KM1X 輔助接點 13-14 (自保)", 203.2, 482.6, left=[("A", 1, "13")], right=[("B", 1, "14")], w=20.32)
S.stub(S1["A1"], "+24V3", RED); S.stub(S1["A2"], "0V3", BLK); S.stub(S1["A3"], "ESTOP_SIG", PUR)
S.stub(S1["B2"], "EM2_COM", ORG); S.stub(S1["B3"], "ESTOP_GND", BLK)
S.conn("N1", RED, [S1["B1"], S2["A"], AUX["A"]], lane=165.1)
S.conn("KMCOIL", ORG, [S2["B"], AUX["B"]], lane=228.6, label="KMCOIL")

# ------------------------------------------------------------------ annotations: headers, cable notes, legend, notes
H = 2.6
S.text("① 市電輸入 / 分路 / 接觸器", 20, 29, H, True)
S.text("② 伺服驅動器 + 馬達 (X/Y/Z)", 400, 29, H, True)
S.text("③ 控制板 RP23CNC + MR-J4 介面板", 20, 176, H, True)
S.text("④ 繼電器輸出：主軸 / 冷卻 / 吹氣", 232, 162, H, True)
S.text("⑤ 主軸變頻器 + 電主軸", 440, 355, H, True)
S.text("⑥ 感測器 / 報警 / 急停輸入", 20, 345, H, True)
S.text("⑦ 24V 電源 + 急停回路", 20, 389, H, True)
for top in (35.56, 137.16, 238.76):
    S.text("動力線 U/V/W + PE (屏蔽，原廠線)", 497, top + 0.3, 1.4)
    S.text("編碼器線 (原廠)", 520, top + 28.6, 1.4)
S.text("屏蔽線 3相 + PE", 513, 361.5, 1.4)
S.text("煞車線 24V", 552, 281.8, 1.4)
S.text("Cat5e 屏蔽", 134, 259.0, 1.4)

# colour legend (short sample wires on their own nets)
lx, ly = 650, 40
S.text("線色圖例", lx, ly - 5, 2.2, True)
legend = [("L1 相線", BRN), ("L2 相線", BLU), ("PE 接地", GRN), ("+24V", RED), ("0V / 負極", BLK),
          ("馬達 U", UCL), ("馬達 W", GRY), ("脈衝 PP/PG、STEP", ORG), ("方向 NP/NG、DIR、報警、SIG", PUR),
          ("致能 EN / 伺服 SON", YEL), ("編碼器", TEL), ("類比 0-10V、乙太網路", ANA), ("絕對位置備份電池 (CN4)", OLV)]
for i, (t, c) in enumerate(legend):
    y = ly + i * 5.08
    S.seg("LEG%d" % i, c, 0.381, lx, y, lx + 12.7, y)
    S.text(t, lx + 15.24, y + 0.8, 1.5)

notes = (
"假設與待核對事項\n"
"1. 電源：單相 220V (現場已確認)，兩條相線標 L1/L2，不假設有 N。\n"
"2. 容量為初估：PSU1 24V/3A、PSU2 24V/1A、PSU3 24V/5A；斷路器與接觸器額定值待負載核算。\n"
"3. MR-J4-40A 單相 200-240V 接 L1 與 L3，L2 空接 (手冊 3.3.1)。手冊要求每台驅動器各配 1 個 MCCB 與 1 個接觸器 (11.10：30A 框 10A、保險絲 15A、接觸器 S-N10 等級)。L11/L21 取自接觸器之前。 CNP1 孔位由上而下：L1、L2、L3、N-、P3、P4 (手冊 9-3)，圖上標籤位置為示意。\n"
"4. CN1 腳位依 MR-J4-A 手冊 3.4 節 (PP10 PG11 NP35 NG36 SON15 EM2 42 ALM48 DICOM20/21 DOCOM46/47)；MBR 非固定腳位，需設 Pr.PD24 讓 CN1-23 輸出 MBR。ALM 報警時斷開 (手冊 3.5)，與圖上反相處理一致。\n"
"5. RP23CNC 的 STEP/DIR/EN 為 5V 單端：IFB1 內含 RS-422 線驅動 (差動 PP/PG、NP/NG) 與 EN→SON 光耦，需自製或選購。\n"
"6. 伺服報警：假設 MR-J4 ALM 正常導通、報警斷開；KA4 反相後以 NC 接點吸入控制板 ALM 輸入 (待核對)。\n"
"7. grblHAL：$0=3 (脈衝寬度 µs，100 kHz 必須調小)；$14=70 (反轉 EStop/Feed Hold/Cycle Start)；0-10V 以 RV1 校準到 10V。\n"
"8. 主軸 (台達 MS300 型錄第20頁)：0-10V 接 AVI/ACM；KA1 接點接 MI1 與 DCM (MI1 出廠為 FWD/STOP，輸入為 NPN/SINK 模式，接點短接 DCM 即動作)。S1/S2/+24V 的出廠短路片不可拆 (STO)。最高輸出 599 Hz，足以供 24,000 rpm (400 Hz)。頻率來源為 Pr.00-20 (Delta FAQ 確認為「主頻率指令來源」)，需改為外部類比 AVI；運轉指令來源 (我記得是 Pr.00-21) 需改為外部端子，兩者的設定值與 00-21 待核對完整使用手冊。\n"
"9. 急停 S1：NC1 切斷 KM1/KM2 線圈，NC2 接 EM2，NO 接控制板 ESTOP。硬線切斷伺服與主軸，不依賴控制器。\n"
"10. 感測器用 NPN 型 24V 近接開關 (控制板限位輸入為 NPN 或機械開關，不支援 PNP)。\n"
"11. 佈線：動力線與信號線分槽、間距 100 mm 以上；馬達線、變頻器輸出線、脈衝線 (PP/PG、NP/NG 各一對) 用屏蔽雙絞線，屏蔽層單端接 PE；繼電器線圈與煞車並聯續流二極體。\n"
"12. 電池 (MR-BAT6V1SET，CN4)：目的是保存絕對位置以免做 home。但驅動器要把位置交給控制器，須由控制器依 ABS 傳送協定讀取 (CN1 ABSM17/ABSR18/ABSB0 22/ABSB1 23/ABST25，Pr.PA03)；grblHAL 目前不支援，故暫時仍保留原點感測器。三軸也可改用 1 個 MR-BT6VCASE 加 5 顆 MR-BAT6V1 共用 (最多 8 軸)。\n"
"13. 貼圖說明：MR-J4 為三菱目錄外觀圖、端子台為 TB40-MRJ4A 照片、RP23CNC 為作者實拍照。圖上端子位置為在照片上量測，RP23CNC 螺絲孔為透視內插 (誤差約 1 mm)，接線時一切以實物絲印為準。"
)
S.text(notes, 345, 450, 1.5)
rails = (
"24V 分配\n"
"+24V1/0V1 (PSU1)：控制板主電源、DC1 (5V)、KA1/KA2/KA5 線圈、SV1 吹氣閥。\n"
"+24V2/0V2 (PSU2)：控制板隔離輸入、原點感測器 (BN)。\n"
"+24V3/0V3 (PSU3)：MR-J4 DICOM/DOCOM、EM2/SON、Z 煞車、KA3/KA4 與 KM1/KM2 線圈、急停回路。\n"
"L1_AUX/L2_AUX：PSU1~3 輸入與冷卻幫浦 (經 KA2)。同名標籤代表同一條線。"
)
S.text(rails, 345, 531, 1.5)

if __name__ == "__main__":
    errs = S.verify()
    print("blocks %d wires %d labels %d" % (len(S.blocks), len(S.wires), len(S.labels)))
    for e in errs: print("ERR", e)
    print("verify:", "OK" if not errs else "%d problems" % len(errs))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CNC_wiring.kicad_sch")
    S.write(out, "CNC 龍門銑床 電氣配線圖",
            ["單相 220V (已確認)；L1/L2 為兩條相線；MR-J4 端子名稱依原廠手冊確認", "控制器 RP23CNC V2.02 (grblHAL)；差動脈衝由 IFB1 線驅動板提供", "Rev A 2026-11-13"])
    print("wrote", out)
