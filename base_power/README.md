# 底座 + 配電（base_power）

分工：機構 session 負責 CNC 本體；本資料夾由「底座 / 支架 / 配電」這邊負責。座標與 `freecad/v13|v14/06_base_coolant` 相同（地板 z=-790，前方 = -y，立柱 x=±517.5）。

## 目前決定（owner 2026-11）
1. **背板就是電控箱，沒有另外的電控箱。** 所有電控零件裝在一塊 620×650 安裝板上（箱體後壁），箱體 250 深 × 660 寬 × 690 高，IP54，門朝 +x。
2. **伺服斷路器 / 接觸器 / EMC 濾波器三軸共用（QF2、KM1、FL2 各一）。** 這與三菱手冊 11.10 不符（手冊：每台驅動器各一個斷路器、一個接觸器；沒有多台合計表）。
   規格由電工決定，並已在檢查單標示；若電工不接受，改回每軸一組，板面也放得下（多 2 個斷路器、2 個接觸器、2 個濾波器）。
3. 三台 ALM 串成一條，驅動一個繼電器（KA4）：任一軸報警 → 繼電器釋放 → 切斷 KM1 線圈（和急停同一迴路），另一組接點給控制板報警輸入。L11/L21 取自 KM1 之前。
4. 箱體位置：底座右側外面落地，4 個調平腳，兩塊 3 t 支架鎖到立柱 3（y=40）。低前樑、低環維持原狀（箱體不再放前下方）。箱體頂 z=-40，低於桌面；不碰導流板（x=527）。
5. 機構那份 `freecad/v14/20_panel_v14.py`（290×260 背板，3 驅動器 + 控制板）不再使用，被本資料夾的整合板取代。需要機構 session 知道。

## 精簡（owner 回覆）
- 24V 電源 3 顆 → **1 顆 Mean Well SDR-240-24（10 A）**。總負載估約 4.5 A（估算，需照實際負載複核）。
- **不用 CN1 端子台 TB40。** 自己用連接器組 MR-J3CN1（3M 10150-3000PE，焊接式）一條一條焊線；共用點與外出訊號走一條小 DIN 端子排 XT。
- **電池 BTX/Y/Z 固定在驅動器上，** 不佔板面。
- **KA1/KA2/KA5 取消：** 主軸 ON/OFF、冷卻泵、吹氣閥的控制訊號拉到 XT 端子排，由箱外自行接線再去驅動。板上只留 KA3（Z 煞車）、KA4（報警）。

## 板面（`panel_layout.png`）
| 排 | 內容 |
|---|---|
| DIN 1 | QF1、QF2(共用)、QF3、QF4、KM1(共用)、DC1、KA3、KA4 |
| DIN 2 | PSU1(SDR-240-24)、FL2(共用)、X1 電源端子、XT 訊號端子排 |
| 板面 | SVX/Y/Z（MR-J4-40A，STEP 尺寸）、VFD（MS300）、BD（RP23CNC，STEP 尺寸）、PC（LattePanda IOTA） |
板高用 529 / 540 mm；驅動器上方 40、下方 52 mm（手冊 40）。零件由 38 件降為 26 件，再加電腦 LattePanda IOTA（板 71×90×19，STEP 在 vendor/lattepanda，未進 git）。

## 檔案
- `layout.py` 零件尺寸與排列（`*` = 估算，下單前以廠商圖面確認）
- `build.py` → `panel_layout.svg/.png`、`base_iso.svg/.png`、`CABLE_LIST.csv`、`panel_check.txt`
- `build_step.py`（FreeCAD）→ `base_power.step`、`step_check.txt`（干涉 0 處）
- 重新產生：`python3 base_power/build.py`；`CNC_ROOT=$PWD /opt/freecad/bin/freecadcmd base_power/build_step.py`

## 待辦 / 風險
- `electrical/` 的接線圖、BOM、檢查單已改成共用 QF2/KM1/FL2、單一 24V、ALM 串聯 KA4、XT 端子排。尚未畫進圖：LattePanda IOTA 的電源與 RS-422 介面卡；圖上 CN1 仍用 TB40 照片示意（實際是 MR-J3CN1 焊線）。
- 共用 QF2/KM1/FL2 的規格、各台分支線徑 / 保險絲、RCD：電工決定。
- 所有 `*` 尺寸是估算；箱內發熱約 160 W 未實測，箱壁自然散熱約 100 W → 加濾網風扇。
- 箱體與機器之間的線槽、右側導流板穿線板、拖鏈介面：要和機構 session 對齊。
- 驅動器深 176 mm + 板上 3 mm 標準件，箱深 250 夠；箱重（約 25–30 kg 零件 + 箱體）與支架強度未計算。
