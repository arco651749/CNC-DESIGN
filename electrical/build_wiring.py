#!/usr/bin/env python3
"""CNC gantry wiring diagram -> KiCad schematic (CNC_wiring.kicad_sch).

Run:  python3 build_wiring.py        (then: kicad-cli sch export pdf CNC_wiring.kicad_sch)
All layout numbers are mm on an A1 sheet; every pin sits on the 2.54 mm grid.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadgen import Block, Sheet, R

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
QF2 = blk("QF2", "QF2 伺服 2P 10A", 203.2, 35.56, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
QF3 = blk("QF3", "QF3 主軸 2P 10A", 203.2, 83.82, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
QF4 = blk("QF4", "QF4 24V電源/幫浦 2P 6A", 203.2, 132.08, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")], w=20.32)
KM1 = blk("KM1", "KM1 接觸器 (伺服主電)", 279.4, 35.56, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")],
          bottom=[("A1", -2.54), ("A2", 2.54)], w=20.32, tmode="above")
KM2 = blk("KM2", "KM2 接觸器 (主軸)", 279.4, 83.82, left=[("L1i", 1, "L1"), ("L2i", 2, "L2")], right=[("L1o", 1, "L1"), ("L2o", 2, "L2")],
          bottom=[("A1", -2.54), ("A2", 2.54)], w=20.32, tmode="above")

S.conn("AC_L1", BRN, [AC["L1"], QF1["L1i"]], width=THICK)
S.conn("AC_L2", BLU, [AC["L2"], QF1["L2i"]], width=THICK)
S.stub(AC["PE"], "PE", GRN)
S.conn("F_L1", BRN, [QF1["L1o"], FL1["L1i"]], width=THICK)
S.conn("F_L2", BLU, [QF1["L2o"], FL1["L2i"]], width=THICK)
S.stub(FL1["PE"], "PE", GRN)
S.conn("L1_IN", BRN, [FL1["L1o"], QF2["L1i"], QF3["L1i"], QF4["L1i"]], lane=165.1, width=THICK)
S.conn("L2_IN", BLU, [FL1["L2o"], QF2["L2i"], QF3["L2i"], QF4["L2i"]], lane=170.18, width=THICK)
# QF2 out: servo control power (L11/L21, always on) + KM1 main contactor
S.conn("L1_CTL", BRN, [QF2["L1o"], KM1["L1i"]], width=THICK); S.label("L1_CTL", "L1_CTL", 241.3, 40.64, 0)
S.conn("L2_CTL", BLU, [QF2["L2o"], KM1["L2i"]], width=THICK); S.label("L2_CTL", "L2_CTL", 241.3, 45.72, 0)
S.conn("L1_KM2", BRN, [QF3["L1o"], KM2["L1i"]], width=THICK)
S.conn("L2_KM2", BLU, [QF3["L2o"], KM2["L2i"]], width=THICK)
S.stub(QF4["L1o"], "L1_AUX", BRN, 10.16, THICK)
S.stub(QF4["L2o"], "L2_AUX", BLU, 10.16, THICK)
S.stub(KM1["A1"], "KMCOIL", ORG); S.stub(KM1["A2"], "0V3", BLK)
S.stub(KM2["A1"], "KMCOIL", ORG); S.stub(KM2["A2"], "0V3", BLK)

# ------------------------------------------------------------------ 2. servo drives + motors
SRV_CX, MOT_CX = 469.9, 596.9
def servo(ax, top, brake=False):
    left = [("L1", 1), ("L2", 2), ("L11", 3), ("L21", 4), ("PE", 5), ("PP", 7), ("PG", 8), ("NP", 9), ("NG", 10),
            ("DICOM", 12), ("DOCOM", 13), ("EM2", 14), ("SON", 15), ("ALM", 16)]
    if brake: left.append(("MBR", 17))
    return blk("SV" + ax, "MR-J4-40A  %s軸 (SV%s)" % (ax, ax), SRV_CX, top, left=left,
               right=[("U", 1), ("V", 2), ("W", 3), ("MPE", 4, "PE"), ("ENC", 6, "CN2 ENC")], w=30.48)
def motor(ax, top, brake=False):
    left = [("U", 1), ("V", 2), ("W", 3), ("PE", 4), ("ENC", 6, "ENC CN2")]
    if brake: left += [("B1", 9), ("B2", 10)]
    name = "HG-KR43%s  %s軸馬達" % ("B(附煞車)" if brake else "", ax)
    return blk("M" + ax, name, MOT_CX, top, left=left, w=30.48)
SVX, SVY, SVZ = servo("X", 35.56), servo("Y", 137.16), servo("Z", 238.76, True)
MX, MY, MZ = motor("X", 35.56), motor("Y", 137.16), motor("Z", 238.76, True)
SV = {"X": SVX, "Y": SVY, "Z": SVZ}; MT = {"X": MX, "Y": MY, "Z": MZ}

S.conn("L1_SRV", BRN, [KM1["L1o"], SVX["L1"], SVY["L1"], SVZ["L1"]], lane=411.48, width=THICK)
S.conn("L2_SRV", BLU, [KM1["L2o"], SVX["L2"], SVY["L2"], SVZ["L2"]], lane=408.94, width=THICK)
for ax in "XYZ":
    s, m = SV[ax], MT[ax]
    S.stub(s["L11"], "L1_CTL", BRN); S.stub(s["L21"], "L2_CTL", BLU); S.stub(s["PE"], "PE", GRN)
    S.stub(s["DICOM"], "+24V3", RED); S.stub(s["DOCOM"], "0V3", BLK); S.stub(s["EM2"], "EM2_COM", ORG)
    S.stub(s["ALM"], "ALM_" + ax, PUR)
    S.conn("%s_U" % ax, UCL, [s["U"], m["U"]], width=THICK)
    S.conn("%s_V" % ax, BLK, [s["V"], m["V"]], width=THICK)
    S.conn("%s_W" % ax, GRY, [s["W"], m["W"]], width=THICK)
    S.conn("%s_MPE" % ax, GRN, [s["MPE"], m["PE"]], width=THICK)
    S.conn("%s_ENC" % ax, TEL, [s["ENC"], m["ENC"]])
S.stub(SVZ["MBR"], "MBR_Z", PUR)
# Z brake: MBR drives relay KA3 coil, KA3 switches 24V to the motor brake
KA3 = blk("KA3", "KA3 Z軸煞車繼電器", 533.4, 274.32, left=[("A1", 1), ("A2", 2), ("COM", 3)], right=[("NO", 2)], w=15.24)
S.stub(KA3["A1"], "+24V3", RED); S.stub(KA3["A2"], "MBR_Z", PUR); S.stub(KA3["COM"], "+24V3", RED)
S.conn("BRK_Z", RED, [KA3["NO"], MZ["B1"]])
S.stub(MZ["B2"], "0V3", BLK)

# ------------------------------------------------------------------ 3. controller RP23CNC + interface board
BX, BT = 215.9, 256.54
bt = lambda i: i * 5.08 - 22.86
bb = lambda i: (i - 6.5) * 5.08
BD = blk("BD", "RP23CNC 控制板", BX, BT, w=91.44, tmode="above",
         left=[("ETH", 1, "ETH RJ45")],
         right=[("X_STP", 1, "X STP"), ("X_DIR", 2, "X DIR"), ("X_EN", 3, "X EN"), ("X_GND", 4, "X GND"),
                ("Y_STP", 6, "Y STP"), ("Y_DIR", 7, "Y DIR"), ("Y_EN", 8, "Y EN"), ("Y_GND", 9, "Y GND"),
                ("Z_STP", 11, "Z STP"), ("Z_DIR", 12, "Z DIR"), ("Z_EN", 13, "Z EN"), ("Z_GND", 14, "Z GND")],
         topp=[("PWR_P", bt(0), "+V MAIN"), ("PWR_G", bt(1), "GND MAIN"), ("S010", bt(2), "0-10V"), ("SGND", bt(3), "GND SPD"),
               ("K1P", bt(4), "SPDL +V"), ("K1S", bt(5), "SPDL SIG"), ("K2P", bt(6), "FLOOD +V"), ("K2S", bt(7), "FLOOD SIG"),
               ("K5P", bt(8), "MIST +V"), ("K5S", bt(9), "MIST SIG")],
         bottom=[("ISO_P", bb(0), "ISO +V"), ("ISO_G", bb(1), "ISO GND"), ("ES_S", bb(2), "ESTOP SIG"), ("ES_G", bb(3), "ESTOP GND"),
                 ("LXS", bb(4), "LIM X SIG"), ("LXG", bb(5), "LIM X GND"), ("LYS", bb(6), "LIM Y SIG"), ("LYG", bb(7), "LIM Y GND"),
                 ("LZS", bb(8), "LIM Z SIG"), ("LZG", bb(9), "LIM Z GND"),
                 ("AX", bb(10), "ALM X"), ("AY", bb(11), "ALM Y"), ("AZ", bb(12), "ALM Z"), ("AG", bb(13), "ALM GND")])
IFB = blk("IFB", "IFB1 MR-J4 介面板", 330.2, BT, w=40.64,
          left=[("X_STP", 1, "X STP"), ("X_DIR", 2, "X DIR"), ("X_EN", 3, "X EN"), ("X_GND", 4, "X GND"),
                ("Y_STP", 6, "Y STP"), ("Y_DIR", 7, "Y DIR"), ("Y_EN", 8, "Y EN"), ("Y_GND", 9, "Y GND"),
                ("Z_STP", 11, "Z STP"), ("Z_DIR", 12, "Z DIR"), ("Z_EN", 13, "Z EN"), ("Z_GND", 14, "Z GND"),
                ("V5", 16, "+5V"), ("G5", 17, "GND5"), ("G3", 18, "0V3")],
          right=[("%s_%s" % (a, n), r0 + i + 1, "%s %s" % (a, n))
                 for a, r0 in (("X", 0), ("Y", 6), ("Z", 12)) for i, n in enumerate(("PP", "PG", "NP", "NG", "SON"))])
for ax in "XYZ":
    S.conn("%s_STP" % ax, ORG, [BD["%s_STP" % ax], IFB["%s_STP" % ax]])
    S.conn("%s_DIR" % ax, PUR, [BD["%s_DIR" % ax], IFB["%s_DIR" % ax]])
    S.conn("%s_EN" % ax, YEL, [BD["%s_EN" % ax], IFB["%s_EN" % ax]])
    S.conn("%s_GND" % ax, BLK, [BD["%s_GND" % ax], IFB["%s_GND" % ax]])
S.stub(IFB["V5"], "+5V", RED); S.stub(IFB["G5"], "0V1", BLK); S.stub(IFB["G3"], "0V3", BLK)
lane = 360.68
for ax in "XYZ":
    for n, col in (("PP", ORG), ("PG", ORG), ("NP", PUR), ("NG", PUR), ("SON", YEL)):
        S.conn("%s_%s" % (ax, n), col, [IFB["%s_%s" % (ax, n)], SV[ax][n]], lane=lane)
        lane += 2.54
# board power / spindle analog / ethernet
S.stub(BD["PWR_P"], "+24V1", RED); S.stub(BD["PWR_G"], "0V1", BLK)
S.stub(BD["S010"], "SPD_0-10V", ANA); S.stub(BD["SGND"], "SPD_GND", BLK)
LAN = blk("LAN", "LAN 交換器 / 監控 PC", 116.84, BT, right=[("RJ", 1, "RJ45")], w=20.32)
S.conn("ETH", ANA, [LAN["RJ"], BD["ETH"]])

# relays driven by the board relay outputs (coil between +V and SIG)
KA1 = blk("KA1", "KA1 主軸 ON/OFF 繼電器", 292.1, 190.5, left=[("A1", 1), ("A2", 2)], right=[("COM", 1), ("NO", 2)], w=20.32)
KA2 = blk("KA2", "KA2 冷卻幫浦繼電器", 292.1, 210.82, left=[("A1", 1), ("A2", 2)], right=[("COM", 1), ("NO", 2)], w=20.32)
KA5 = blk("KA5", "KA5 吹氣閥繼電器", 292.1, 231.14, left=[("A1", 1), ("A2", 2)], right=[("COM", 1), ("NO", 2)], w=20.32)
for k, (p, sg) in ((KA1, ("K1P", "K1S")), (KA2, ("K2P", "K2S")), (KA5, ("K5P", "K5S"))):
    S.L("%s_A1" % k.ref, RED, BD[p], k["A1"])
    S.L("%s_A2" % k.ref, PUR, BD[sg], k["A2"])
S.stub(KA1["COM"], "VFD_COM", BLK); S.stub(KA1["NO"], "VFD_FWD", ORG)
S.stub(KA2["COM"], "L1_AUX", BRN, R, THICK)
S.stub(KA5["COM"], "+24V1", RED)
PUMP = blk("PUMP", "冷卻幫浦 220V 單相", 292.1, 129.54, right=[("L2", 1), ("PE", 2), ("L1", 3)], w=20.32)
SVL = blk("SVL", "SV1 吹氣電磁閥 24V", 292.1, 160.02, right=[("N", 1, "−"), ("P", 2, "+")], w=20.32)
S.stub(PUMP["L2"], "L2_AUX", BLU, R, THICK); S.stub(PUMP["PE"], "PE", GRN)
S.conn("PUMP_L1", BRN, [KA2["NO"], PUMP["L1"]], lane=340.36, width=THICK)
S.stub(SVL["N"], "0V1", BLK)
S.conn("SV_PLUS", RED, [KA5["NO"], SVL["P"]], lane=345.44)

# ------------------------------------------------------------------ 4. home sensors, e-stop input, servo alarms (board bottom)
S.stub(BD["ISO_P"], "+24V2", RED); S.stub(BD["ISO_G"], "0V2", BLK)
S.stub(BD["ES_S"], "ESTOP_SIG", PUR); S.stub(BD["ES_G"], "ESTOP_GND", BLK)
ALM = blk("ALM", "KA4 伺服報警反相繼電器 (3路模組)", 292.1, 360.68,
          left=[("AG", 1, "COM GND"), ("AZ", 2, "NC Z"), ("AY", 3, "NC Y"), ("AX", 4, "NC X")],
          right=[("A1", 1, "A1 +24V"), ("A2X", 2, "A2 X"), ("A2Y", 3, "A2 Y"), ("A2Z", 4, "A2 Z")], w=25.4)
SENS = blk("SENS", "原點感測器 X/Y/Z (NPN 24V 3線 ×3)", 292.1, 401.32,
           left=[("ZBU", 1, "Z BU 0V"), ("ZBK", 2, "Z BK OUT"), ("YBU", 3, "Y BU 0V"), ("YBK", 4, "Y BK OUT"), ("XBU", 5, "X BU 0V"), ("XBK", 6, "X BK OUT")],
           right=[("XBN", 1, "X BN +24V"), ("YBN", 3, "Y BN +24V"), ("ZBN", 5, "Z BN +24V")], w=30.48)
for ax in "XYZ":
    S.L("LIM_%s_SIG" % ax, BLK, BD["L%sS" % ax], SENS["%sBK" % ax])
    S.L("LIM_%s_GND" % ax, BLU, BD["L%sG" % ax], SENS["%sBU" % ax])
    S.stub(SENS["%sBN" % ax], "+24V2", BRN)
for ax in "XYZ": S.L("ALMIN_%s" % ax, PUR, BD["A%s" % ax], ALM["A%s" % ax])
S.L("ALMIN_G", BLK, BD["AG"], ALM["AG"])
S.stub(ALM["A1"], "+24V3", RED)
for ax in "XYZ": S.stub(ALM["A2%s" % ax], "ALM_" + ax, PUR)

# ------------------------------------------------------------------ 5. spindle VFD
VFD = blk("VFD", "台達 MS300 變頻器", SRV_CX, 363.22,
          left=[("RL1", 1, "R/L1"), ("SL2", 2, "S/L2"), ("PE", 3), ("AVI", 5), ("ACM", 6), ("MI1", 7), ("DCM", 8)],
          right=[("U", 1), ("V", 2), ("W", 3), ("RPE", 4, "PE")], w=30.48)
SP = blk("SP", "主軸 0.8kW 風冷電主軸 (3相)", MOT_CX, 363.22, left=[("U", 1), ("V", 2), ("W", 3), ("PE", 4)], w=30.48)
S.conn("L1_VFD", BRN, [KM2["L1o"], VFD["RL1"]], lane=403.86, width=THICK)
S.conn("L2_VFD", BLU, [KM2["L2o"], VFD["SL2"]], lane=401.32, width=THICK)
S.stub(VFD["PE"], "PE", GRN)
S.stub(VFD["AVI"], "SPD_0-10V", ANA); S.stub(VFD["ACM"], "SPD_GND", BLK)
S.stub(VFD["MI1"], "VFD_FWD", ORG); S.stub(VFD["DCM"], "VFD_COM", BLK)
S.conn("SP_U", UCL, [VFD["U"], SP["U"]], width=THICK)
S.conn("SP_V", BLK, [VFD["V"], SP["V"]], width=THICK)
S.conn("SP_W", GRY, [VFD["W"], SP["W"]], width=THICK)
S.conn("SP_PE", GRN, [VFD["RPE"], SP["PE"]], width=THICK)

# ------------------------------------------------------------------ 6. 24V supplies, e-stop circuit
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
AUX = blk("AUX", "KM1 輔助接點 13-14 (自保)", 203.2, 482.6, left=[("A", 1, "13")], right=[("B", 1, "14")], w=20.32)
S.stub(S1["A1"], "+24V3", RED); S.stub(S1["A2"], "0V3", BLK); S.stub(S1["A3"], "ESTOP_SIG", PUR)
S.stub(S1["B2"], "EM2_COM", ORG); S.stub(S1["B3"], "ESTOP_GND", BLK)
S.conn("N1", RED, [S1["B1"], S2["A"], AUX["A"]], lane=165.1)
S.conn("KMCOIL", ORG, [S2["B"], AUX["B"]], lane=228.6, label="KMCOIL")

# ------------------------------------------------------------------ annotations: headers, cable notes, legend, notes
H = 2.6
S.text("① 市電輸入 / 分路 / 接觸器", 20, 29, H, True)
S.text("② 伺服驅動器 + 馬達 (X/Y/Z)", 400, 29, H, True)
S.text("③ 控制板 RP23CNC + MR-J4 介面板", 130, 246, H, True)
S.text("④ 繼電器輸出：主軸 / 冷卻 / 吹氣", 250, 121, H, True)
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
          ("致能 EN / 伺服 SON", YEL), ("編碼器", TEL), ("類比 0-10V、乙太網路", ANA)]
for i, (t, c) in enumerate(legend):
    y = ly + i * 5.08
    S.seg("LEG%d" % i, c, 0.381, lx, y, lx + 12.7, y)
    S.text(t, lx + 15.24, y + 0.8, 1.5)

notes = (
"假設與待核對事項\n"
"1. 電源：單相 220V (現場已確認)，兩條相線標 L1/L2，不假設有 N。\n"
"2. 容量為初估：PSU1 24V/3A、PSU2 24V/1A、PSU3 24V/5A；斷路器與接觸器額定值待負載核算。\n"
"3. MR-J4-40A 單相接 L1/L2 (L3 不接)；L11/L21 控制電源取自接觸器之前，急停後驅動器仍保持供電與顯示。\n"
"4. MR-J4 的 PP/PG/NP/NG/SON/EM2/ALM/MBR/DICOM/DOCOM 為信號名，接腳編號與輸入輸出極性請依 MR-J4-A 手冊核對。\n"
"5. RP23CNC 的 STEP/DIR/EN 為 5V 單端：IFB1 內含 RS-422 線驅動 (差動 PP/PG、NP/NG) 與 EN→SON 光耦，需自製或選購。\n"
"6. 伺服報警：假設 MR-J4 ALM 正常導通、報警斷開；KA4 反相後以 NC 接點吸入控制板 ALM 輸入 (待核對)。\n"
"7. grblHAL：$0=3 (脈衝寬度 µs，100 kHz 必須調小)；$14=70 (反轉 EStop/Feed Hold/Cycle Start)；0-10V 以 RV1 校準到 10V。\n"
"8. 主軸：0-10V 類比 + KA1 正轉接點。MS300 的 AVI/ACM/MI1/DCM 端子名請依手冊核對，並設定外部類比速度與外部端子運轉。\n"
"9. 急停 S1：NC1 切斷 KM1/KM2 線圈，NC2 接 EM2，NO 接控制板 ESTOP。硬線切斷伺服與主軸，不依賴控制器。\n"
"10. 感測器用 NPN 型 24V 近接開關 (控制板限位輸入為 NPN 或機械開關，不支援 PNP)。\n"
"11. 佈線：動力線與信號線分槽、間距 100 mm 以上；馬達線、變頻器輸出線、脈衝線 (PP/PG、NP/NG 各一對) 用屏蔽雙絞線，屏蔽層單端接 PE；繼電器線圈與煞車並聯續流二極體。"
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
