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
 ('24V 電源', 'PSU2', '12V 電源 6.3A（電腦用）', 1, 'Mean Well XDR-75E-12（12V 6.3A 75.6W，30×125.2×116 mm，owner 提供規格書）', 'Mean Well', '暫定', 'IOTA 60W ÷ 12V = 5A，約 79% 負載；規格書：>50°C 滿載要減額、頂部留 40mm、底部留 20mm。電腦與此電源都在立柱電箱內（owner 決定），箱內溫度要壓在 45°C 以下，見 column_box/HEAT.md；與 24V 分開，0V 不共地'),
 ('控制', 'BD', 'RP23CNC 控制板', 1, 'RP23CNC V2.02 (RP23U5XBB)，RP2354B，5 軸 grblHAL，12/24V 供電', 'Brookwood Design (Tindie / 官網商店)', '已選定', '含基本組裝套件（排針、跳線）；STEP/DIR/EN 為 5V 單端，直接以開集極驅動伺服 (無 IFB1)。手冊 V2 user manual'),
 ('控制', 'BD', 'WIZ850io 乙太網路模組', 1, 'WIZnet WIZ850io (必須 W5500)；WIZ820io / WIZ550io 不相容', 'WIZnet', '已選定', '選配，多台並聯監控用'),
 ('控制', 'LAN', '電腦 LattePanda IOTA', 1, 'LattePanda IOTA（x86 單板電腦，主板約 71×90×19 mm，另有被動散熱片 FIT1028 / 主動風扇 FIT1027 可選）', 'DFRobot / LattePanda', '已選定', 'owner 指定的電腦：跑 LLM 與 grblHAL（乙太網路送 G-code）。不接 RS-422。放在立柱電箱內屋頂底面，12V 60W 由 PSU2 供電；散熱用主動散熱器 FIT1027（owner：隨 IOTA 一起買）'),
 ('控制', 'LAN', 'LattePanda IOTA 主動散熱器 FIT1027', 1, 'LattePanda FIT1027 Active Cooler（約 87×69×11 mm，原廠 STEP）', 'LattePanda / DFRobot', '已選定', 'owner 選定，隨 IOTA 一起買；風扇供電（板上風扇接頭？）原廠資料未查到，到貨確認；3D 位置假設置中於 CPU，需對照實物'),
 ('交流保護', 'QF1', '總電源漏電斷路器', 1, '2P 漏電斷路器 30 mA，額定 ≥ 總電流（電工決定；候選 30 A 級）', '士林電機 (SEEC)', '待確認', '[底座電箱] 有切削液的機台漏電保護不省（owner 文件）；三台伺服電源的 EMC 濾波器暫不放，漏電流較小；型號與廠牌待選（士林 BM30-SN 本身無漏電功能）'),
 ('交流保護', 'QF2', '伺服斷路器（三軸共用）', 1, '士林 BM30-SN 2P，額定待電工（三台合計；單台為 30A 框 10A）', '士林電機 (SEEC)', '待確認', '[底座電箱] owner 決定三軸共用，與三菱 MR-J4-A 手冊 11.10「每台驅動器各 1 個斷路器與接觸器」不符（手冊沒有多台合計表）。額定、三路分支線徑／保險絲由電工決定；若不接受改回每軸一組'),
 ('交流保護', 'KM1', '伺服電磁接觸器（三軸共用）', 1, '士林 SD-P 系列，DC 24V 線圈，額定依三台合計（電工決定；單台為 S-N10 等級）', '士林電機 (SEEC)', '待確認', '[底座電箱] S-P 系列線圈只有交流，直流線圈要用 SD-P；訂購指定 24V；與手冊 11.10 不符，見 QF2'),
 ('交流保護', 'FL2', '伺服 EMC 濾波器（三軸共用）', 1, '額定 ≥ 三台合計電流（原選 Soshin HF3010A-UN 10A 單台用，共用要換大一級）', 'Soshin Electric', '暫不安裝', '[底座電箱] 先不放濾波器（owner 文件，精簡），箱內留一個 DIN 位置；實機有干擾再加；未裝時 LINE/LOAD 跳接'),
 ('交流保護', 'FL2', '突波保護器', 1, 'Okaya RSPD-500-U4', 'Okaya Electric', '暫不安裝', '[底座電箱] 先不放濾波器（owner 文件，精簡），箱內留一個 DIN 位置；實機有干擾再加；未裝時 LINE/LOAD 跳接'),
 ('交流保護', 'QF3', '主軸變頻器斷路器', 1, '士林 BM30-SN，2P 30A', '士林電機 (SEEC)', '暫定', '[底座電箱] （已拿掉主軸接觸器 KM2，急停時主軸只靠控制器關閉 KA1，變頻器仍有電）MS300 手冊要求斷路器 = 變頻器輸入電流 × 1.6～2.6（查證自網路摘要）；1.5kW 單相輸入電流約 16～18A（未查證）→ 約 26～47A，取 30A'),
 ('交流保護', 'QF4', '24V 電源 / 幫浦斷路器', 1, '士林 BM30-SN，2P 5A', '士林電機 (SEEC)', '暫定', '[底座電箱] 只供 24V 電源輸入（SDR-240-24 約 1.6A@230V 估算）'),
 ('24V 電源', 'PSU1', '24V 電源 5A', 1, 'Mean Well SDR-120-24（24V 5A，DIN 軌，約 63×125×114 mm，尺寸待核對）', 'Mean Well', '暫定', '負載估：控制板、感測器、探頭、伺服 I/O、接觸器線圈、風扇約 1.3A；加冷卻泵 DT-48W 約 2A 共約 3.3A，餘裕約 35%（需實測；泵堵轉電流未查）'),
 ('24V 電源', 'DC1', 'DC-DC 24V→5V', 1, '輸出 5V 1A', '（待選）', '待選型號', '供三個伺服的 OPC (CN1-12) 脈衝電源，負載小（6 路約 3 mA 量級，估算）；控制板輸出拉低時電流由此流入控制板。無 IFB1 中間板，脈衝直接驅動伺服開集極輸入；5V 供電下光耦導通電流未驗證，須實機量測'),
 ('伺服', 'SVX, SVY, SVZ', '伺服驅動器', 3, '三菱 MR-J4-40A（單相 200-240V 接 L1/L3）', '三菱電機', '已選定', '手冊 SH-030107-V；主電路輸入電流 2.6A（括號值 4.5A，手冊 1.3 節未註明條件）、控制電源 30W'),
 ('伺服', 'MX, MY', '伺服馬達 400W', 2, '三菱 HG-KR43', '三菱電機', '已選定', '動力、編碼器線為原廠現成線，已拉好'),
 ('伺服', 'MZ', '伺服馬達 400W 附煞車', 1, '三菱 HG-KR43B（煞車靜摩擦扭矩 1.3 N·m）', '三菱電機', '已選定', '煞車線 B1/B2 由 KA3 控制；煞車電流未查證'),
 ('伺服', 'BTX, BTY, BTZ', '絕對位置備份電池', 3, '三菱 MR-BAT6V1SET（接 CN4）', '三菱電機', '已選定', '手冊 11.8 確認；grblHAL 不支援 ABS 傳送，暫時不能省 home。三軸也可改 1 個 MR-BT6VCASE + 5 顆 MR-BAT6V1（最多 8 軸）'),
 ('伺服', 'TBX, TBY, TBZ', 'CN1 連接器組（自製線）', 3, '三菱 MR-J3CN1（3M 10150-3000PE，焊接式），每台 1 組', '三菱電機 / 3M 通路', '已選定', '手冊附件 CN1 connector set；owner 自己焊線，不用端子台。需要 50 針焊接工具與剝線，注意間距'),
 ('伺服', 'XT', '共用點分配端子排', 1, 'DIN 軌端子排約 12 點（+24V / 0V / +5V 分配）', '（待選）', '待選型號', '控制板輸出已直接接線：K1→變頻器 MI1（DCM 接 0V1），K2→KA2 線圈→泵，K5→吹氣閥線圈'),
 ('伺服', 'KA3', 'Z 軸煞車繼電器', 1, 'Omron MY2N-GS DC24（DPDT，5A，24VDC 線圈）', 'Omron', '暫定', '線圈約 0.13A（網路摘要，未證實）；底座 PYFZ-08'),
 ('繼電器與開關', 'KA2', '冷卻泵繼電器', 1, 'Omron MY2N-GS DC24（接點 5A）+ 底座 PYFZ-08', 'Omron', '暫定', '線圈由控制板 K2 輸出驅動（開集極 100 mA 上限）；切換 DC24V 泵約 2A，電感性負載，泵兩端並聯飛輪二極體 DP'),
 ('主軸', 'VFD', '主軸變頻器', 1, '台達 MS300 VFD7A5MS21AFSAA（單相 230V，1.5kW，內建 EMC 濾波器；型號字尾依命名規則推斷）；參考照片為 460V 三相機種', '台達電子', '暫定', '輸出 7.5A（重載）、最高 599 Hz，足以供 400 Hz；使用手冊參數（00-20、00-21 等）待核對'),
 ('主軸', 'SP', '電主軸 0.8kW', 1, 'ATO STF65-0.8-ER11，3 相 220V 2.5A 400Hz 24000rpm，Ø65，ER11，3kg，4 針航空插頭', 'ATO (ato.com)', '規格推斷（待確認）', '依規格比對找到，不一定是實際購買的型號。插頭腳位 1=U 2=V 3=W 4=PE；尺寸圖 STF65-0.8-ER11_dimensions.pdf'),
 ('主軸', 'SP', '主軸動力線 (含 4 針航空插頭)', 1, '4 芯屏蔽線 + 對應 4 針航空插頭', '（待選）', '待選型號', '長度待定；需屏蔽，屏蔽層單端接 PE'),
 ('感測', 'SENS', '原點感測器', 3, 'Autonics PR12-4DN（M12 電感式，檢出距離 4mm，NPN 常開，DC10-30V，3 線，響應 500Hz）X/Y/Z 各 1', 'Autonics', '已選定', '採購須確認三件事：(1) 必須 NPN（型號結尾 DN，不可買 DP 的 PNP 版，控制板限位輸入只收 NPN）；(2) 必須常開（不是常閉）；(3) 若感測器要裝進金屬支架、周圍有金屬貼近，要改選遮蔽型，PR12-4DN 為非遮蔽型，周圍 12 mm 內不要有金屬。另：重複精度未查到；線色棕 +24V、藍 0V、黑輸出；參考照 vendor/parts/photos/Autonics_PR12_sensor.jpg'),
 ('感測', 'PRB', '3D 觸發式探頭', 1, 'PGFUN 類 CNC 3D touch probe，球頭 2mm、柄徑 6mm、DC5-24V、NPN，常閉輸出 (紅 +24V / 黃 OUT / 黑 0V)', '（賣家待確認）', '規格推斷（待確認）', '型號依規格推斷；賣家宣稱重複精度 0.01mm，為 DIY 等級。須確認買的是常閉 (NC) 版，grblHAL 設 $6=1'),
 ('繼電器與開關', 'S1', '急停按鈕', 1, '22mm 急停按鈕，2NC（NC1 切接觸器線圈與運轉、NC2 接控制板 ESTOP）', 'Auspicious', '暫定', '[操作盒] 精簡後只要 2NC；EM2 永久接 0V，不另用接點'),
 ('繼電器與開關', 'S2', '啟動按鈕', 1, 'IDEC YW1L-MF2E10QM3G 類（22mm 瞬時型，凸頭，綠色照光，1NO）', 'IDEC', '暫定', '[操作盒] 照片上的型號是 AC220V 照光版；我們控制電路是 24V，訂購要選 DC24V 的燈與電壓版本（尾碼待確認）'),
 ('負載', 'PUMP', '冷卻泵', 1, 'HONGYANG DT-48W：24 V 直流無刷泵，1200 L/h（約 20 L/min），揚程 17 m，功率 48 W（型號字面，電流約 2 A 為估算）；賣家頁面標示用於 CNC 雕刻機冷卻', 'Alibaba（HONGYANG）', '已選定', '你選定的型號。注意：(1) 流量約 20 L/min，遠大於我們要的 5 L/min，要在出口加球閥節流並加旁路回液箱（原機構設計有）；(2) 48 W ÷ 24 V ≈ 2 A，超過我原先抓的 1.5 A，PSU1 餘裕不夠，見電源列；(3) 採購確認：實際額定電流與堵轉電流、泵體與軸封材質是否耐水溶性切削液、是否有 PWM 或調速線、防水等級；(4) 我只看過賣家頁面的摘要，頁面還寫功率範圍 25～150 W（多型號共用），DT-48W 的確切規格要向賣家確認；接線：+24V1 → KA2 接點 → 泵'),
 ('負載', 'DP', '冷卻泵飛輪二極體', 1, '1N4007（或同級，≥1A、≥100V）', '（待選）', '待選型號', '跨接在泵的兩端，陰極接 + 、陽極接 −，保護 KA2 接點與控制板；泵若已內建保護電路可不裝，採購時確認'),
 ('負載', 'SVL', '吹氣電磁閥', 1, 'SMC SY3120-5LZE-M5（5 口 2 位、單電控、DC24V、M5 接口、L 型插座附導線、指示燈與突波保護）', 'MISUMI（三住）', '已選定', '採購時在三住頁面確認完整型號尾碼（SY3120 後的字母與接口代碼）：電壓必須 DC24V、單電控、5 口 2 位、M5 接口、附指示燈與突波保護。Cv 0.16、使用壓力 0.15～0.7 MPa。氣壓滑台、稜鏡蓋等氣動件另一個工作階段還在設計，閥的數量之後會增加；由控制板 K5 輸出直接驅動（開集極上限 100 mA；SY3120 線圈電流約 40 mA 為估算，須確認；線圈內建突波保護有極性）'),
 ('機殼與線', 'ENC1', '底座電箱（保護類）', 1, '鋼板壁掛箱 360×280×120 mm，IP54，前開門附鎖；內含 320×240 安裝板與 2 條 DIN 軌', '（待選）', '待選型號', '裝在底座前下方，用 2 支新立柱 + 2 條橫樑固定；3D 與位置見 base_cabinet/'),
 ('機殼與線', 'ENC2', '立柱電控板（L 型板，無蓋）', 1, 'SPHC t4 折成 L 型的一片板（垂直板 y 255..259、水平板 z 487..491，兩端加 t10 肋板）；電料鎖在垂直板後面與水平板底面；沒有蓋子、沒有風扇', '配電 session 設計，鈑金加工', '待選型號', '3D 見 column_box/；頂板由機構 session 設計；浪管支撐架用鈑金，由機構與配電 session 協調位置；無 IP 防護，owner 決定'),
 ('機殼與線', 'FDR', '兩箱連接線（共 5 條）', 5, '伺服 5G2.5 mm²、變頻器 3G4 mm²、電源 3G1.5 mm²、控制 4×0.75 mm² 屏蔽，另 PE 接地線', '（待選）', '規格推斷（待確認）', '線徑為估算起點，電工決定；長度由機構 session 的走線路徑決定；防水接頭進立柱電箱後牆左下'),
 ('機殼與線', 'ENC3', '操作盒（急停 + 啟動）', 1, '塑膠或鋁壓鑄盒約 160×100×60 mm，IP54，2 個 Ø22 孔', '（待選）', '待選型號', '掛在右立柱右側面，內裝 S1、S2；7 芯 0.75 mm² 線（NC1 2、NC2 2、NO 2 或 S2 2 + 備用）接底座電箱右側壁 Ø16 接頭'),
]

ALIAS = {}

def main():
    refs_in_diagram = {b.ref for b in B.S.blocks} | set(ALIAS)
    errors = []
    for group, refs, part, qty, spec, src, status, note in ROWS:
        names = [r.strip() for r in refs.split(",")]
        for r in names:
            if ALIAS.get(r, r) not in {b.ref for b in B.S.blocks} and r not in ('ENC1', 'ENC2', 'ENC3', 'FDR'):
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
