# CNC DESIGN

固定龍門、工作台移動 (Y) 的三軸 CNC。加工區 300 × 300 mm；換料時工作台再前移 100 mm。外形約 860 × 1205 × 1624 mm（床身 680 × 1065）。
用途：切鋁、刀具 Ø5 以下、人工換刀；以多台並行提高產量。

## v2 設計重點

| 項目 | 規格 |
|---|---|
| 行程 X / Y / Z | 300 / 400 / 100 mm（Y = 加工 300 + 換料 100），進給 ≤ 100 mm/s |
| 線軌 | HIWIN HG，ZA 中預壓、H 級（Y HGR25，X/Z HGR20） |
| 螺桿 | DFU 雙螺帽預壓 C7，導程統一 5 mm（Y DFU2005，X/Z DFU1605） |
| 伺服 | 三菱 HG-KR43 400 W × 3（Z 用 HG-KR43B 附煞車），MR-J4-40A × 3 |
| 主軸 | 0.8 kW 風冷電主軸 Ø65 × 188，ER11，6,000～24,000 rpm，變頻器（台達 MS300 等）|
| 刀具夾持 | ER11 筒夾（Ø1～Ø7，AA 級 ≤0.005），螺帽 Ø19 M13×0.75，人工換刀 |
| 控制 | grblHAL（Teensy 4.1 + T41U5XBB），5 軸，差動脈衝，0.001 mm/step；驅動器與控制板直接鎖在龍門橫樑背面（附護蓋），不另設電控箱 |
| 冷卻 | 浸入式幫浦 25 L/min + 吹氣，集液槽 / 過濾籃 / 100 L 液箱 |

## 檔案

- `cad/cnc_gantry.py`：CadQuery 參數化模型 → `output/CNC_Gantry.step`、`output/cnc_info.json`
- `cad/make_drawing.py`：GA 總組立圖（A1，1:8，第三角法）→ `output/CNC_Gantry_GA.svg`
- `cad/make_spindle_detail.py`：主軸頭細部圖（A3，前視 / 俯視 1:2 + ER11 前端剖面 2:1）→ `output/CNC_Spindle_Detail.svg`
- `freecad/`、`output/v1/`：v1（FreeCAD）的舊腳本與模型，僅供參考，未更新到 v2

## 重新產生

```bash
pip install cadquery
python cad/cnc_gantry.py
python cad/make_drawing.py
python cad/make_spindle_detail.py
```
