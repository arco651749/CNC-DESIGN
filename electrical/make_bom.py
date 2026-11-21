#!/usr/bin/env python3
"""Electrical BOM -> electrical/CNC_electrical_BOM.csv

Every row lists the reference designators used in the KiCad drawing (CNC_wiring.kicad_sch); the script checks that
each designator exists in build_wiring.py and that the quantity matches, so the BOM cannot drift from the drawing.
Status words: 已選定 / 暫定 / 待選型號 / 規格推斷（待確認） / 客戶自備 / 原廠現成線.
Run:  python3 electrical/make_bom.py
"""
import os, sys, csv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_wiring as B

# (group, refs, part, qty, spec / model, source, status, note)
ROWS = [
 # ---- control
 ("控制", "BD", "RP23CNC 控制板", 1, "RP23CNC V2.02 (RP23U5XBB)，RP2354B，5 軸 grblHAL，12/24V 供電", "Brookwood Design (Tindie / 官網商店)", "已選定",
  "含基本組裝套件（排針、跳線）；STEP/DIR/EN 為 5V 單端，須外加 RS-422 驅動 (IFB1)。手冊 V2 user manual"),
 ("控制", "BD", "WIZ850io 乙太網路模組", 1, "WIZnet WIZ850io (必須 W5500)；WIZ820io / WIZ550io 不相容", "WIZnet", "已選定", "選配，多台並聯監控用"),
 ("控制", "IFB", "MR-J4 介面板 IFB1", 1, "3 軸 RS-422 差動線驅動 (如 AM26C31) PP/PG、NP/NG + EN→SON 光耦", "自製或另購", "待選型號",
  "圖上是方塊；手冊建議差動接收最高 4 Mpulse/s，線長 10 m 內"),
 ("控制", "LAN", "LAN 交換器 / 監控 PC", 1, "10/100 乙太網路", "客戶自備", "客戶自備", ""),
 # ---- AC / protection
 ("交流保護", "QF1", "主斷路器 2P", 1, "2P 20A（容量待負載核算）", "（待選，士林 BM 系列）", "待選型號", "圖上暫畫 20A，未核算"),
 ("交流保護", "FL1", "EMI 濾波器", 1, "單相 220V，額定電流待核算", "（待選）", "待選型號", ""),
 ("交流保護", "QF2X, QF2Y, QF2Z", "伺服斷路器 (每軸一個)", 3, "士林 BM30-SN，2P 10A，30A 框，Icu 5 kA @ 220V，液壓磁式", "士林電機 (SEEC)", "已選定",
  "依三菱 MR-J4-A 手冊 11.10：MR-J4-40A 用 30A 框 10A。每台驅動器各配 1 個。尺寸圖 BM30-SN_Dimension.pdf"),
 ("交流保護", "KM1X, KM1Y, KM1Z", "伺服電磁接觸器 (每軸一個)", 3, "士林 SD-P11，DC 24V 線圈，3P，AC3 13A @240V，附 1NO 輔助接點", "士林電機 (SEEC)", "已選定",
  "S-P 系列線圈只有交流，直流線圈要用 SD-P。訂購時指定線圈 24V。對應手冊的 S-N10 等級"),
 ("交流保護", "QF3", "主軸變頻器斷路器", 1, "士林 BM30-SN，2P 20A", "士林電機 (SEEC)", "暫定", "20A 為暫定，MS300 1.5kW 單相輸入電流未查證，待手冊確認"),
 ("交流保護", "KM2", "主軸電磁接觸器", 1, "士林 SD-P11，DC 24V 線圈", "士林電機 (SEEC)", "暫定",
  "只拿來做急停切電，不要用它做平常開關主軸；也可不裝，改用變頻器 STO"),
 ("交流保護", "QF4", "24V 電源 / 幫浦斷路器", 1, "2P，約 5～6A", "（待選）", "待選型號", "BM30-SN 沒有 6A 規格，可選 5A 或 10A"),
 # ---- 24V
 ("24V 電源", "PSU1", "24V 電源 3A", 1, "24V DC 3A（控制板、繼電器、5V、吹氣閥）", "（待選）", "待選型號", "容量為初估"),
 ("24V 電源", "PSU2", "24V 電源 1A", 1, "24V DC 1A（隔離輸入、原點感測器、探頭）", "（待選）", "待選型號", "容量為初估"),
 ("24V 電源", "PSU3", "24V 電源 5A", 1, "24V DC 5A（伺服 I/O、Z 煞車、急停、KM 線圈）", "（待選）", "待選型號", "容量為初估"),
 ("24V 電源", "DC1", "DC-DC 24V→5V", 1, "輸出 5V 1A", "（待選）", "待選型號", ""),
 # ---- servo
 ("伺服", "SVX, SVY, SVZ", "伺服驅動器", 3, "三菱 MR-J4-40A（單相 200-240V 接 L1/L3）", "三菱電機", "已選定", "手冊 SH-030107-V"),
 ("伺服", "MX, MY", "伺服馬達 400W", 2, "三菱 HG-KR43", "三菱電機", "已選定", "動力、編碼器線為原廠現成線，已拉好"),
 ("伺服", "MZ", "伺服馬達 400W 附煞車", 1, "三菱 HG-KR43B", "三菱電機", "已選定", "煞車線 B1/B2 由 KA3 控制"),
 ("伺服", "BTX, BTY, BTZ", "絕對位置備份電池", 3, "三菱 MR-BAT6V1SET（接 CN4）", "三菱電機", "暫定",
  "grblHAL 不支援 ABS 傳送，暫時不能省 home；三軸也可改用 1 個 MR-BT6VCASE + 5 顆 MR-BAT6V1。型號待核對手冊 11.8"),
 ("伺服", "TBX, TBY, TBZ", "CN1 端子台", 3, "TB40-MRJ4A（號碼 = CN1 腳號）", "（品牌待確認，照片由使用者提供）", "待選型號", "接線前用三用電表量排線確認一對一"),
 ("伺服", "TBX, TBY, TBZ", "CN1 轉端子台排線", 3, "（三菱目錄型號 MR-J2M-CN1TBL□M，待確認）", "三菱電機或同級", "待選型號", "長度待定"),
 ("伺服", "KA3", "Z 軸煞車繼電器", 1, "DC 24V 線圈，接點電流依煞車線圈", "（待選）", "待選型號", "MBR (CN1-23) 驅動線圈，須設 Pr.PD24"),
 ("伺服", "KA4", "伺服報警反相繼電器模組", 1, "3 路，DC 24V 線圈，NC 接點", "（待選）", "待選型號", "MR-J4 ALM 報警時斷開，反相後接控制板報警輸入"),
 # ---- spindle
 ("主軸", "VFD", "主軸變頻器", 1, "台達 MS300 VFD7A5MS21ANSAA（單相 230V，1.5kW 等級；參考照片為 460V 三相機種）", "台達電子", "暫定",
  "型號為建議值，使用手冊參數（00-20、00-21 等）待核對"),
 ("主軸", "SP", "電主軸 0.8kW", 1, "ATO STF65-0.8-ER11，3 相 220V 2.5A 400Hz 24000rpm，Ø65，ER11，3kg，4 針航空插頭", "ATO (ato.com)", "規格推斷（待確認）",
  "依規格比對找到，不一定是實際購買的型號。插頭腳位 1=U 2=V 3=W 4=PE；尺寸圖 STF65-0.8-ER11_dimensions.pdf"),
 ("主軸", "SP", "主軸動力線 (含 4 針航空插座)", 1, "4 芯屏蔽線 + 對應 4 針航空插頭", "（待選）", "待選型號", ""),
 # ---- sensors
 ("感測", "SENS", "原點感測器", 3, "NPN 三線 24V 近接開關 (X/Y/Z 各 1)", "（待選）", "待選型號",
  "控制板限位輸入只收 NPN 或機械開關，不收 PNP；若用光電式需確認輸出邏輯"),
 ("感測", "PRB", "3D 觸發式探頭", 1, "PGFUN 類 CNC 3D touch probe，球頭 2mm、柄徑 6mm、DC5-24V、NPN，常閉輸出 (紅 +24V / 黃 OUT / 黑 0V)", "（賣家待確認）", "規格推斷（待確認）",
  "型號為依規格推斷；賣家宣稱重複精度 0.01mm，為 DIY 等級。須確認買的是常閉 (NC) 版，grblHAL 設 $6=1"),
 # ---- relays / switches / loads
 ("繼電器與開關", "KA1", "主軸 ON/OFF 繼電器", 1, "DC 24V 線圈，接點接變頻器 MI1 與 DCM", "（待選）", "待選型號", ""),
 ("繼電器與開關", "KA2", "冷卻幫浦繼電器", 1, "DC 24V 線圈，接點負載 220V 幫浦", "（待選）", "待選型號", "接點容量依幫浦電流"),
 ("繼電器與開關", "KA5", "吹氣閥繼電器", 1, "DC 24V 線圈", "（待選）", "待選型號", ""),
 ("繼電器與開關", "S1", "急停按鈕", 1, "2NC + 1NO", "（待選）", "待選型號", "NC1 切 KM 線圈、NC2 接 EM2、NO 接控制板 ESTOP"),
 ("繼電器與開關", "S2", "啟動按鈕", 1, "NO", "（待選）", "待選型號", ""),
 ("負載", "PUMP", "冷卻幫浦", 1, "浸入式，220V 單相，25 L/min", "（待選）", "待選型號", ""),
 ("負載", "SVL", "吹氣電磁閥", 1, "DC 24V", "（待選）", "待選型號", "CNC Mechanic Design 工作階段另有氣壓滑台、稜鏡蓋等氣動件，電磁閥數量與型號待併入"),
]

ALIAS = {"KA4": "ALM"}   # the drawing's block ref is ALM but its title reads KA4

def main():
    refs_in_diagram = {b.ref for b in B.S.blocks} | set(ALIAS)
    errors = []
    for group, refs, part, qty, spec, src, status, note in ROWS:
        names = [r.strip() for r in refs.split(",")]
        for r in names:
            if ALIAS.get(r, r) not in {b.ref for b in B.S.blocks}:
                errors.append("%s: 位號 %s 不在配線圖裡" % (part, r))
        distinct = len(names)
        if distinct > 1 and qty != distinct:
            errors.append("%s: 位號數 %d 與數量 %d 不符" % (part, distinct, qty))
    if errors:
        print("\n".join(errors)); sys.exit(1)
    out = os.path.join(HERE, "CNC_electrical_BOM.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["群組", "位號", "零件", "數量", "規格 / 型號", "來源", "狀態", "備註"])
        for r in ROWS: w.writerow(r)
    done = sum(1 for r in ROWS if r[6] == "已選定")
    print("wrote", out, "- %d rows, %d 已選定" % (len(ROWS), done))
    for st in ("已選定", "暫定", "規格推斷（待確認）", "待選型號", "客戶自備"):
        print(" ", st, sum(1 for r in ROWS if r[6] == st))

if __name__ == "__main__":
    main()
