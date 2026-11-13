# CNC DESIGN

固定龍門、工作台移動 (Y) 的三軸 CNC。加工區 300 × 300 mm；換料時工作台再前移 100 mm。外形約 820 × 1113 × 1619 mm（床身 640 × 1055）；核心組件約 790 × 666 × 789 mm。
用途：切鋁、刀具 Ø5 以下、人工換刀；以多台並行提高產量。

## v2 設計重點

| 項目 | 規格 |
|---|---|
| 行程 X / Y / Z | 300 / 400 / 100 mm（Y = 加工 300 + 換料 100），進給 ≤ 100 mm/s |
| 線軌 | HIWIN HG，ZA 中預壓、H 級（Y HG35 倒裝：滑軌鎖工作台、滑塊鎖基準板；X/Z HG20） |
| 龍門 | 三住鋁擠型 HFS8-80160：立柱 ×2、橫樑 ×2 並排；前面 t15 銑平鋼板當 X 滑軌基準 |
| 床身 | 焊接框架＋t3 不鏽鋼底盤；一整塊基準底板（立柱座、Y 滑塊座、固定 Y 螺帽座，一次裝夾銑出）；Y 螺桿倒裝：DFU1605 固定－自由，L 型馬達座鎖在工作台後緣（內建固定端軸承），不另設支撐座；選 HG35 線軌（H=55），滑軌直接鎖工作台、不用墊高塊，基準板免開槽 |
| 螺桿 | DFU1605 雙螺帽預壓 C7，三軸統一 |
| 伺服 | 三菱 HG-KR43 400 W × 3（Z 用 HG-KR43B 附煞車），MR-J4-40A × 3 |
| 主軸 | 0.8 kW 風冷電主軸 Ø65 × 188，ER11，6,000～24,000 rpm，變頻器（台達 MS300 等）|
| 刀具夾持 | ER11 筒夾（Ø1～Ø7，AA 級 ≤0.005），螺帽 Ø19 M13×0.75，人工換刀 |
| 控制 | grblHAL（Teensy 4.1 + T41U5XBB），5 軸，差動脈衝，0.001 mm/step；驅動器與控制板直接鎖在龍門橫樑背面（附護蓋），不另設電控箱 |
| 冷卻 | 浸入式幫浦 25 L/min + 吹氣，集液槽 / 過濾籃 / 100 L 液箱 |
| Y 防護 | 待定（伸縮護罩已拿掉；倒裝滑軌面朝下） |

## 檔案

- `cad/cnc_gantry.py`：CadQuery 參數化模型 → `output/CNC_Gantry.step`、`output/cnc_info.json`
- `cad/core_assembly.py`：核心組件（不含大底座）→ `output/core/CNC_Core.step`、`output/core/CNC_Core_BOM.csv`（含三住型號與來源）
- `cad/make_drawing.py`：GA 總組立圖（A1，1:8，第三角法）→ `output/CNC_Gantry_GA.svg`
- `cad/make_spindle_detail.py`：主軸頭細部圖（A3，前視 / 俯視 1:2 + ER11 前端剖面 2:1）→ `output/CNC_Spindle_Detail.svg`
- `freecad/`、`output/v1/`：v1（FreeCAD）的舊腳本與模型，僅供參考，未更新到 v2

## 電氣配線圖（KiCad）

`electrical/CNC_wiring.kicad_sch`：整機配線圖（A1），含單相 220V 分路與急停接觸器、三組 MR-J4-40A 與馬達線（含編碼器、Z 煞車）、主軸變頻器、三組獨立 24V 電源、RP23CNC 控制板與 MR-J4 介面板、原點感測器、伺服報警反相、冷卻幫浦與吹氣閥。圖上同名標籤代表同一條線；右下角與圖內備註列出假設與待核對事項。

- `electrical/CNC_wiring.pdf`、`CNC_wiring_preview.png`：匯出檔
- `electrical/build_wiring.py`、`kicadgen.py`：產生器，改接線請改腳本再重跑，不要手改 `.kicad_sch`
- 中文字型用 `WenQuanYi Zen Hei`；在別台機器可用環境變數 `WIRING_FONT="Microsoft JhengHei"` 重新產生

```bash
python3 electrical/build_wiring.py
kicad-cli sch export pdf -o electrical/CNC_wiring.pdf electrical/CNC_wiring.kicad_sch
```

## 重新產生

```bash
pip install cadquery
python cad/cnc_gantry.py
python cad/make_drawing.py
python cad/core_assembly.py
python cad/make_spindle_detail.py
```

## text-to-cad 工具（結構分析、工程圖、廠商 STEP）

`.claude/skills/` 內含 [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad)（MIT）的三個 skill：
`cad`（build123d 建模、讀廠商 STEP、干涉 / 可加工性檢查）、`fea`（CalculiX 結構分析）、`engineering-drawing`（PDF 工程圖）。

它和 CadQuery 用的 OpenCascade 版本不同，請裝在獨立的虛擬環境：

```bash
python3 -m venv /opt/ttc
/opt/ttc/bin/pip install "cad[build123d]==0.11.9" "cad-server==0.11.9"
/opt/ttc/bin/cad telemetry off
/opt/ttc/bin/cad update auto off
```

廠商 STEP（三住、HIWIN、三菱）請放在 `vendor/`。
