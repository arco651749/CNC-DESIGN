# 立柱電箱（column_box）

取代底座電箱（`base_power/` 已作廢，保留作歷史）。機構 session 交接：`docs/handoff_electrical_box_v14.md`（分支 `claude/exciting-fermat-76sspv`）。座標為機台座標（地板 z=-790，前方 = -y）。

## 決定（owner：1:a 2:b 3:b）
1. 所有電料放進立柱電箱（龍門立柱頂，x -380..380、y 255..495、z 250..488）。
2. 伺服報警：ALM 直接接控制板，不串聯、不加反相繼電器（接觸器只由急停控制）。
3. 伺服上下間隙縮為 35 mm（手冊 40 mm），由電工確認。

## 佈置（`placement.csv`、`column_box_views.svg`、`column_box.step`）
- 後牆（背貼 y=495）直立：SVX/SVY/SVZ（x 225/275/325，z 285..453）、VFD（x 120..192）、PSU1（x 20..106）。
- 屋頂底面朝下：RCD、QF2、QF3、QF4、KM1、DC1、KA3、XT、BD、X1、PC（LattePanda IOTA），另留 FL2 濾波器位置；後牆還有 PSU1（XDR-75E-24）、PSU2（XDR-75E-12，給電腦）。
- 檢查：無重疊、全在包絡內；伺服正面 y=319，距障礙 y=242 有 77 mm 配線空間（≥60）。
- 進線口與出風口（`openings.csv`）：Y 浪管 底蓋 (x -120, y 330)、X 浪管 屋頂 (x 50, y 390)（兩者由機構 session 指定）；進線 220 V 底蓋 (x -340, y 270)；X 馬達/感測器 底蓋 (x 350, y 262)；風扇進風 底蓋 (x -250, y 400，Ø130)；出風 後牆 x 125..215、z 460..485（變頻器上方，不在屋頂 x -95..385、y 205..415 的托盤範圍）。
- 吹氣閥 SVL 裝在後牆 DIN 軌（x -300..-280，z 350..410），氣管從兩個浪管口出去。IOTA 移到屋頂 x -85..-14；濾波器預留位移到 x 30..150、y 262..327。

## 散熱（`HEAT.md`）
最壞發熱約 237 W（伺服用手冊 35 W×3，電腦 60 W 與 12 V 電源在箱內，owner 決定）；120 mm 風扇 ≥ 100 m³/h 時箱內溫升約 6 K（環境 35 °C 時約 41 °C）；60 m³/h 約 45 °C，30 m³/h 約 51 °C 太高。進風底蓋 Ø130，出風後牆 x 125..215 z 460..485（在變頻器上方）。

## 未決 / 風險
- 多數零件尺寸是估算（`placement.csv` 的來源欄 A）；VFD、斷路器的安裝方向（直立或倒掛）要查手冊。
- 屋頂倒掛的斷路器 / 接觸器是否允許，電工確認。
- 風扇型號採購時選；沒有風扇故障偵測。
- 立柱上電箱的重量與振動（電料約 20 kg）未計算，機構側確認。
- EM2 永久接 0 V（只有 2NC 急停）：急停時伺服無受控減速，只靠切電與 Z 煞車。
- `electrical/` 接線圖、BOM、檢查單已依此更新；電腦與 12 V 電源在箱內。
- **24 V 電源 XDR-75E-24 只有 3.2 A**：估算負載（含冷卻泵 2 A）約 3.3 A，超過額定；泵若另接一顆電源就沒問題。

## 3D（由配電 session 繪製，機構 session 不用畫）
- `column_box.step`：鈑金箱（屋頂 t3 + 安裝板 t4、後牆 t5、兩側 t3、可拆前蓋、可拆底蓋含 4 個進線孔）、DIN 軌、三台 MR-J4 與 RP23CNC 板（原廠 STEP）、其餘電料（目錄尺寸方塊）、風扇、出風濾網。機台座標。干涉檢查 0 處（`step_check.txt`）。
- 預覽：`column_box_3d_below.png`、`column_box_3d_above.png`（前蓋、底蓋、右側板隱藏）。
- 重新產生：`CNC_ROOT=$PWD SERVO_STEP=<mr-j4-40ab.stp 路徑> /opt/freecad/bin/freecadcmd column_box/build_step.py`，再 `python3 column_box/render.py`。
- DIN 軌上的零件已加 7.5 mm 軌高；電腦（IOTA）的固定支架還沒畫。
