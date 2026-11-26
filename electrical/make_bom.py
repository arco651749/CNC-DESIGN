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
 ('控制', 'BD', 'RP23CNC 控制板', 1, 'RP23CNC V2.02 (RP23U5XBB)，RP2354B，5 軸 grblHAL，12/24V 供電', 'Brookwood Design (Tindie / 官網商店)', '已選定', '含基本組裝套件（排針、跳線）；STEP/DIR/EN 為 5V 單端，直接以開集極驅動伺服 (無 IFB1)。手冊 V2 user manual'),
 ('控制', 'BD', 'WIZ850io 乙太網路模組', 1, 'WIZnet WIZ850io (必須 W5500)；WIZ820io / WIZ550io 不相容', 'WIZnet', '已選定', '選配，多台並聯監控用'),
 ('控制', 'LAN', '電腦 LattePanda IOTA', 1, 'LattePanda IOTA（x86 單板電腦，主板約 71×90×19 mm，另有被動散熱片 FIT1028 / 主動風扇 FIT1027 可選）', 'DFRobot / LattePanda', '已選定', 'owner 指定的電腦：跑 LLM 與 grblHAL（乙太網路送 G-code）。不接 RS-422（owner 決定：只用 STEP/DIR 脈衝，不讀伺服資料）。電源規格與散熱片選用待確認（官網連不上）；3D：vendor/lattepanda/iota_mainboard.stp'),
 ('交流保護', 'QF1', '主斷路器', 1, '士林 BM30-SN，2P 30A，30A 框，Icu 5 kA @ 220V', '士林電機 (SEEC)', '暫定', '實際負載約 18A 量級（見負載核算），30A 有餘裕；現場電源迴路需 ≥30A。各分路另有斷路器保護'),
 ('交流保護', 'QF2', '伺服斷路器（三軸共用）', 1, '士林 BM30-SN 2P，額定待電工（三台合計；單台為 30A 框 10A）', '士林電機 (SEEC)', '待確認', 'owner 決定三軸共用，與三菱 MR-J4-A 手冊 11.10「每台驅動器各 1 個斷路器與接觸器」不符（手冊沒有多台合計表）。額定、三路分支線徑／保險絲由電工決定；若不接受改回每軸一組'),
 ('交流保護', 'KM1', '伺服電磁接觸器（三軸共用）', 1, '士林 SD-P 系列，DC 24V 線圈，額定依三台合計（電工決定；單台為 S-N10 等級）', '士林電機 (SEEC)', '待確認', 'S-P 系列線圈只有交流，直流線圈要用 SD-P；訂購指定 24V；與手冊 11.10 不符，見 QF2'),
 ('交流保護', 'FL2', '伺服 EMC 濾波器（三軸共用）', 1, '額定 ≥ 三台合計電流（原選 Soshin HF3010A-UN 10A 單台用，共用要換大一級）', 'Soshin Electric', '待確認', '手冊 11.16；HF 系列需配突波保護器；漏電流隨濾波器'),
 ('交流保護', 'FL2', '突波保護器', 1, 'Okaya RSPD-500-U4', 'Okaya Electric', '已選定', '與 HF3010A-UN 成套（手冊 11.16 註）'),
 ('交流保護', 'QF3', '主軸變頻器斷路器', 1, '士林 BM30-SN，2P 30A', '士林電機 (SEEC)', '暫定', '（已拿掉主軸接觸器 KM2，急停時主軸只靠控制器關閉 KA1，變頻器仍有電）MS300 手冊要求斷路器 = 變頻器輸入電流 × 1.6～2.6（查證自網路摘要）；1.5kW 單相輸入電流約 16～18A（未查證）→ 約 26～47A，取 30A'),
 ('交流保護', 'QF4', '24V 電源 / 幫浦斷路器', 1, '士林 BM30-SN，2P 5A', '士林電機 (SEEC)', '暫定', '只供 24V 電源輸入（SDR-240-24 約 1.6A@230V 估算）'),
 ('24V 電源', 'PSU1', '24V 電源 10A（唯一電源）', 1, 'Mean Well SDR-240-24（24V 10A，DIN 軌）', 'Mean Well', '暫定', '全部 24V 負載合計估約 4.5A（控制板、感測器、探頭、伺服 I/O、接觸器線圈、報警與煞車繼電器、泵與閥經 XT 外接），需實際核算；單一電源使控制板隔離輸入與邏輯共 0V，隔離減弱'),
 ('24V 電源', 'DC1', 'DC-DC 24V→5V', 1, '輸出 5V 1A', '（待選）', '待選型號', '供三個伺服的 OPC (CN1-12) 脈衝電源，負載小（6 路約 3 mA 量級，估算）；控制板輸出拉低時電流由此流入控制板。無 IFB1 中間板，脈衝直接驅動伺服開集極輸入；5V 供電下光耦導通電流未驗證，須實機量測'),
 ('伺服', 'SVX, SVY, SVZ', '伺服驅動器', 3, '三菱 MR-J4-40A（單相 200-240V 接 L1/L3）', '三菱電機', '已選定', '手冊 SH-030107-V；主電路輸入電流 2.6A（括號值 4.5A，手冊 1.3 節未註明條件）、控制電源 30W'),
 ('伺服', 'MX, MY', '伺服馬達 400W', 2, '三菱 HG-KR43', '三菱電機', '已選定', '動力、編碼器線為原廠現成線，已拉好'),
 ('伺服', 'MZ', '伺服馬達 400W 附煞車', 1, '三菱 HG-KR43B（煞車靜摩擦扭矩 1.3 N·m）', '三菱電機', '已選定', '煞車線 B1/B2 由 KA3 控制；煞車電流未查證'),
 ('伺服', 'BTX, BTY, BTZ', '絕對位置備份電池', 3, '三菱 MR-BAT6V1SET（接 CN4）', '三菱電機', '已選定', '手冊 11.8 確認；grblHAL 不支援 ABS 傳送，暫時不能省 home。三軸也可改 1 個 MR-BT6VCASE + 5 顆 MR-BAT6V1（最多 8 軸）'),
 ('伺服', 'TBX, TBY, TBZ', 'CN1 連接器組（自製線）', 3, '三菱 MR-J3CN1（3M 10150-3000PE，焊接式），每台 1 組', '三菱電機 / 3M 通路', '已選定', '手冊附件 CN1 connector set；owner 自己焊線，不用端子台。需要 50 針焊接工具與剝線，注意間距'),
 ('伺服', 'XT', '訊號端子排', 1, 'DIN 軌端子排約 24 點（共用 +24V/0V/+5V、控制板 K1/K2/K5 輸出拉到箱外、感測器）', '（待選）', '待選型號', '控制板的主軸 ON/OFF、冷卻泵、吹氣閥輸出接這裡，箱外自行接線，要自己做短路保護'),
 ('伺服', 'KA3', 'Z 軸煞車繼電器', 1, 'Omron MY2N-GS DC24（DPDT，5A，24VDC 線圈）', 'Omron', '暫定', '線圈約 0.13A（網路摘要，未證實）；底座 PYFZ-08'),
 ('伺服', 'KA4', '伺服報警繼電器（三台 ALM 串聯）', 1, 'Omron MY2N-GS DC24 ×1（DPDT）+ 底座 PYFZ-08', 'Omron', '暫定', '三台 ALM 輸出串聯驅動線圈：NO1 串進接觸器線圈迴路（任一軸報警三軸斷電），NC2 送控制板報警輸入；串聯壓降與輸出電流限制須對照手冊 3.9'),
 ('主軸', 'VFD', '主軸變頻器', 1, '台達 MS300 VFD7A5MS21AFSAA（單相 230V，1.5kW，內建 EMC 濾波器；型號字尾依命名規則推斷）；參考照片為 460V 三相機種', '台達電子', '暫定', '輸出 7.5A（重載）、最高 599 Hz，足以供 400 Hz；使用手冊參數（00-20、00-21 等）待核對'),
 ('主軸', 'SP', '電主軸 0.8kW', 1, 'ATO STF65-0.8-ER11，3 相 220V 2.5A 400Hz 24000rpm，Ø65，ER11，3kg，4 針航空插頭', 'ATO (ato.com)', '規格推斷（待確認）', '依規格比對找到，不一定是實際購買的型號。插頭腳位 1=U 2=V 3=W 4=PE；尺寸圖 STF65-0.8-ER11_dimensions.pdf'),
 ('主軸', 'SP', '主軸動力線 (含 4 針航空插頭)', 1, '4 芯屏蔽線 + 對應 4 針航空插頭', '（待選）', '待選型號', '長度待定；需屏蔽，屏蔽層單端接 PE'),
 ('感測', 'SENS', '原點感測器', 3, 'Autonics PR12-4DN（M12 電感式，檢出距離 4mm，NPN 常開，DC10-30V，3 線，響應 500Hz）X/Y/Z 各 1', 'Autonics', '已選定', '採購須確認三件事：(1) 必須 NPN（型號結尾 DN，不可買 DP 的 PNP 版，控制板限位輸入只收 NPN）；(2) 必須常開（不是常閉）；(3) 若感測器要裝進金屬支架、周圍有金屬貼近，要改選遮蔽型，PR12-4DN 為非遮蔽型，周圍 12 mm 內不要有金屬。另：重複精度未查到；線色棕 +24V、藍 0V、黑輸出；參考照 vendor/parts/photos/Autonics_PR12_sensor.jpg'),
 ('感測', 'PRB', '3D 觸發式探頭', 1, 'PGFUN 類 CNC 3D touch probe，球頭 2mm、柄徑 6mm、DC5-24V、NPN，常閉輸出 (紅 +24V / 黃 OUT / 黑 0V)', '（賣家待確認）', '規格推斷（待確認）', '型號依規格推斷；賣家宣稱重複精度 0.01mm，為 DIY 等級。須確認買的是常閉 (NC) 版，grblHAL 設 $6=1'),
 ('繼電器與開關', 'S1', '急停按鈕', 1, 'Auspicious（台灣）22mm 急停按鈕，Ø40 紅色蘑菇頭，旋轉復位，2 組接點塊（照片）', 'Auspicious', '暫定', '圖上需要 2NC+1NO：NC1 切接觸器線圈、NC2 接 EM2、NO 接控制板 ESTOP。照片的接點塊看起來是 2 組，不確定共幾個接點，要確認能裝到 3 個（2NC+1NO）；型號沒有，需向你確認'),
 ('繼電器與開關', 'S2', '啟動按鈕', 1, 'IDEC YW1L-MF2E10QM3G 類（22mm 瞬時型，凸頭，綠色照光，1NO）', 'IDEC', '暫定', '照片上的型號是 AC220V 照光版；我們控制電路是 24V，訂購要選 DC24V 的燈與電壓版本（尾碼待確認）'),
 ('負載', 'PUMP', '冷卻泵', 1, 'HONGYANG DT-48W：24 V 直流無刷泵，1200 L/h（約 20 L/min），揚程 17 m，功率 48 W（型號字面，電流約 2 A 為估算）；賣家頁面標示用於 CNC 雕刻機冷卻', 'Alibaba（HONGYANG）', '已選定', '你選定的型號。注意：(1) 流量約 20 L/min，遠大於我們要的 5 L/min，要在出口加球閥節流並加旁路回液箱（原機構設計有）；(2) 48 W ÷ 24 V ≈ 2 A，超過我原先抓的 1.5 A，PSU1 餘裕不夠，見電源列；(3) 採購確認：實際額定電流與堵轉電流、泵體與軸封材質是否耐水溶性切削液、是否有 PWM 或調速線、防水等級；(4) 我只看過賣家頁面的摘要，頁面還寫功率範圍 25～150 W（多型號共用），DT-48W 的確切規格要向賣家確認'),
 ('負載', 'DP', '冷卻泵飛輪二極體', 1, '1N4007（或同級，≥1A、≥100V）', '（待選）', '待選型號', '跨接在泵的兩端，陰極接 + 、陽極接 −，保護 KA2 接點與控制板；泵若已內建保護電路可不裝，採購時確認'),
 ('負載', 'SVL', '吹氣電磁閥', 1, 'SMC SY3120-5LZE-M5（5 口 2 位、單電控、DC24V、M5 接口、L 型插座附導線、指示燈與突波保護）', 'MISUMI（三住）', '已選定', '採購時在三住頁面確認完整型號尾碼（SY3120 後的字母與接口代碼）：電壓必須 DC24V、單電控、5 口 2 位、M5 接口、附指示燈與突波保護。Cv 0.16、使用壓力 0.15～0.7 MPa。氣壓滑台、稜鏡蓋等氣動件另一個工作階段還在設計，閥的數量之後會增加'),
]

ALIAS = {}

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
    for st in ("已選定", "暫定", "規格推斷（待確認）", "待確認", "待選型號", "待客戶決定", "客戶自備"):
        print(" ", st, sum(1 for r in ROWS if r[6] == st))

if __name__ == "__main__":
    main()
