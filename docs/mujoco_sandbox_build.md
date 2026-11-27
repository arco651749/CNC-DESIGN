# v14 MuJoCo 沙盒：建置紀錄

建立日期 2026-11-27（機構 session）。用途：給 AI（Claude）規劃量測動作的沙盒，例如相機拍照、探針探測。
AI 在這裡先跑一遍，確認不撞機、到得了、量得到，再上真機。它不模擬切削，也不取代設計干涉檢查：
精確的間隙判定仍以 `freecad/v14/02 / 07 / 12` 為準。

使用方式見 `sandbox/README.md`，這份文件記錄的是**怎麼建出來的、為什麼這樣做、踩過哪些坑**。

---

## 1. 環境

雲端容器（Ubuntu 24.04，4 CPU，無顯示器）。

```bash
pip install mujoco pillow numpy                 # 測試版本 mujoco 4.0.1
apt-get install -y libegl1 libgl1 libosmesa6    # 無頭渲染需要；沒有的話 Renderer 會出現 eglQueryString / glGetError 錯誤
export MUJOCO_GL=egl                            # 用 EGL 渲染（OSMesa 在這台試過不行）
```

FreeCAD 用環境裡的 `/opt/freecad/bin/freecadcmd`（自帶 Python 3.11 和 numpy），MuJoCo 則跑在系統的 `python3`。
兩邊分開：FreeCAD 只負責匯出網格和設定檔，MuJoCo 那邊不需要 FreeCAD。

## 2. 流程（三支程式）

```
CNC_v14_base.FCStd ──(26_export_mujoco_v14.py, freecadcmd)──> meshes/*.stl + manifest.json
                    ──(sandbox/build_mjcf.py, python3)──────> cnc_v14.xml (MJCF)
                    ──(sandbox/cnc_sandbox.py, python3)─────> AI 用的 API：放工件、跑動作清單、回報
```

輸出都在 `output/v14/mujoco/`。機構改了以後，依序重跑前兩支即可同步。

### 2.1 `freecad/v14/26_export_mujoco_v14.py`（FreeCAD → 網格 + manifest）

1. **讀模型**：開 `output/v14/CNC_v14_base.FCStd`（機台加底座）。如果本地有 `column_box/` 和 `base_cabinet/` 的 STEP，也讀進來當外觀。
2. **零件分到 6 個 body**（判斷規則跟干涉檢查 02 / 07 的 `cls()` 相同，先看零件的 `Motion` 屬性，沒有再看名稱）：

   | body | 依據 |
   |---|---|
   | table | Motion `y`，或名稱 `Y_rail / Work_table / Y_ballscrew / Y_support / Y_coupling / Y_motor` 開頭 |
   | carriage | Motion `x`，或 `X_block / X_carriage / X_ball_nut / X_nut_bracket / X_saddle / Z_` 開頭 |
   | head | Motion `z`，或 `Z_block / Z_spacer / Z_slide / Z_ball_nut / Z_nut_housing / Spindle / ER11 / Tool` 開頭 |
   | probe | 探針滑台上會動的零件（跟 12 的 `MOVE` 清單相同：Probe_body / holder / stem / slide_table 和它們的螺絲） |
   | cover | `Mirror_cover`（稜鏡護蓋） |
   | base | 其餘（固定不動） |

3. **外觀網格**：同一個 body、同一個顏色的零件合併成一個 STL，目前共 19 個。小螺絲、銷不畫。
4. **碰撞網格**：AI 的動作可能撞到的零件，每個各輸出一個 STL，用正規表示式 `HEAD_COLL` / `OBST_COLL` 指定：
   - 工具頭側：主軸、夾座、ER11 螺帽、刀具、相機、氣環、噴嘴、探針、滑台、浪管工具頭支架。
   - 障礙物側：稜鏡座、稜鏡、護蓋、氣缸、接頭。
   - 工作台面和工件不在這裡，由 MJCF 和沙盒用精確形狀加上去。
5. **探針本體只取上半部**：`Probe_body` 的 STEP 包含測針和探針球。用凸包的話，會把探針球包進去，球還沒碰到工件，本體就先「撞」了。
   所以碰撞網格只取探針球底往上 24 mm 以上（本體 + 柄），測針和探針球另外用精確形狀做成「觸發」幾何（見 2.2）。
6. **網格精度**：用 `MeshPart.meshFromShape`，同時限制線性和角度偏差：
   - 外觀：`LinearDeflection = max(1.0, 0.008 × 零件最大尺寸)`、`AngularDeflection = 0.7`
   - 碰撞：`0.3 / 0.35`
   - 廠商的細零件先丟掉體積 < 150 mm³ 的小實體（螺絲、標籤）。
   最初用 `Shape.tessellate()` 只限線性偏差，小孔和圓角會產生大量三角形，網格一度有 165 萬個三角形、79 MB。
   換成 MeshPart 加角度偏差後，降到約 26 萬個、13 MB。
7. **manifest.json**：關節行程、各 body 的父子關係、工作台面範圍、探針球位置（Ø2，測針 26）、刀尖位置、
   相機參數（光軸 (-32.5, -20)、鏡頭前緣 z、WD 120、DOF 5.3、視野 16.8 × 14.0、2448 × 2048 像素），以及外觀與碰撞網格清單。
   單位都是 mm。

### 2.2 `sandbox/build_mjcf.py`（manifest → MJCF）

- **單位**：MuJoCo 慣例用公尺，網格用 `scale=".001 .001 .001"` 換算，所有位置除以 1000。
- **原點**：每個 body 的原點都在世界原點，關節值為 0 時就是機台原點。所以網格不用平移，零件座標直接沿用 FreeCAD 的機台座標。
- **關節**（都是 slide）：

  | 關節 | body | 軸向 | 行程 |
  |---|---|---|---|
  | Y | table | +Y | -250..150 |
  | X | carriage | +X | -182.5..182.5 |
  | Z | head（掛在 carriage 下） | +Z | -50..50 |
  | P | probe（掛在 head 下） | **-Z** | 0..60（伸出為正） |
  | C | cover（掛在 table 下） | +Y | 0..30 |

- **碰撞分類**：用 contype / conaffinity，只讓工具頭側和障礙物之間產生接觸，同一側的零件互相不檢查：
  - 工具頭側：`contype=1 conaffinity=0`
  - 障礙物（含工件）：`contype=0 conaffinity=1`
  - 外觀網格：`contype=0 conaffinity=0`，只用來看。
- **工具頭側加 margin 0.5 mm**：距離 0.5 mm 以內就會產生接觸資料（距離 > 0），沙盒用它發出「間隙不足」警告；距離 < 0 才算撞到。
- **精確形狀**：
  - 工作台面：box（T 型槽忽略）。
  - 探針球：sphere，半徑 1。
  - 測針：capsule，半徑 1。
  - 探針球和測針都算「觸發」幾何，碰到時是探針觸發，不是撞機。
- **相機**：放在 head body，位置在光軸上、鏡頭前緣下 3 mm（避開氣環），朝下看，`xyaxes="1 0 0 0 1 0"`，所以影像往右 = +X、往上 = +Y。
  用 `projection="orthographic"`，`fovy` 填視野高度 0.014 m，模擬遠心鏡頭。
- **其他**：
  - 同軸光：在相機位置加一盞向下的 spotlight。
  - site 標記（刀尖、探針球中心、焦點）設成透明、放在 group 5，不出現在影像裡。
  - 致動器：每個關節都有位置伺服（kp 20000），目前沙盒用不到，留給之後做動力學。

### 2.3 `sandbox/cnc_sandbox.py`（AI 用的 API）

- **運動學模擬，不是動力學**：直接設定關節值（`qpos`），然後呼叫 `mj_kinematics` + `mj_collision` 讀接觸。
  不積分、沒有慣性，所以結果每次都一樣，速度也快，一份 25 步的計畫約 1 秒內跑完。
- **移動檢查**：在軸空間走直線，每 0.5 mm 檢查一次。遇到撞機就退回上一個安全位置，回報撞到的兩個零件、接觸點（工作台座標）和停住的位置。
- **探測移動**（`probe_move`，等同 G38.2）：先確認探針已伸出。移動中測針或探針球一接觸，就在「最後沒碰到」和「剛碰到」兩個位置之間二分逼近到 1 µm，
  回報觸發時的三軸位置、探針球中心和接觸點。如果其他零件先撞到，回報撞機；走到終點都沒碰到，回報 `no_trigger`。
- **放工件**：用 `mujoco.MjSpec` 在 table body 加 geom，再重新編譯模型，工件就會跟著 Y 軸移動。
  - 方塊（box）是精確形狀。
  - STL 網格用凸包，凹的工件要拆成幾個凸塊再放。
- **拍照**：
  - 用 `mujoco.Renderer` 從 `cam` 相機渲染，關掉陰影（同軸光不會有投影陰影）、不畫 site。
  - 對焦檢查：在視野內取 7 × 7 個點，各往下打一條射線（`mj_ray`），找到第一個面，算它離焦點多遠，
    回報畫面裡每個面佔的比例和是否在景深 ±2.65 mm 內。
- **座標換算**：
  - 工作台座標 = Y = 0 時的機台座標。
  - `camera_over / probe_at / tool_at` 把工作台上的點換算成三軸目標，`where()` 反過來回報目前刀尖、探針球、焦點在工作台上的位置。

## 3. 踩過的坑

| 問題 | 原因 | 解法 |
|---|---|---|
| `Renderer` 出現 `eglQueryString` / `glGetError` 錯誤 | 容器裡沒有 GL 函式庫 | `apt-get install libegl1 libgl1`，並設 `MUJOCO_GL=egl` |
| `camera` 的 `orthographic` 屬性報 schema 錯誤 | 這個版本的屬性名稱是 `projection="orthographic"` | 改用 `projection`；正投影時 `fovy` 是視野高度（長度單位），不是角度 |
| 網格 79 MB、165 萬個三角形 | `tessellate()` 只限線性偏差，小孔和圓角切得很細 | 改用 `MeshPart.meshFromShape`，加上角度偏差 |
| 探針伸出時反而往上 60 mm | P 關節的軸已經是 -Z，程式又把值乘了 -1，負負得正 | 直接用正值 |
| 探針還沒碰到工件就報 `Probe_body` 撞機 | 探針本體的凸包把測針和探針球包進去了 | 碰撞網格只取本體上半部，測針和探針球改用精確的觸發幾何 |
| 對準工件角落拍照時，對焦判斷錯 | 只在影像中心打一條射線，剛好落在工件邊上 | 改成 7 × 7 個點 |
| 相機影像有陰影、工件過亮 | 世界光源的陰影加上三盞燈疊加 | 拍照時關陰影，調暗 headlight 和相機燈 |
| 網格不能 commit | 網格裡有 TraceParts 和廠商的模型，只能內部使用 | 把 `output/v14/mujoco/meshes/` 加進 `.gitignore`，用之前先跑 26 匯出 |

## 4. 驗證（`sandbox/demo_plan.py`）

範例：方塊 120 × 80 × 25，中心放在工作台 (20, 10)，轉 5°。

- **量測計畫**（`runs/demo_ok/`）：拍兩個角，再探測 -X 面、-Y 面和頂面。
  量到的面跟幾何真值比較，-X 面 -40.232（真值 -40.229），-Y 面 -30.156（真值 -30.153），頂面 134.999（真值 135.0）。
  兩張照片中，工件頂面在焦點上，工作台面離焦 25 mm。
- **撞機計畫**（`runs/demo_crash/`）：探針伸出時直接快速往下，沙盒在探針球碰到工件時停住，回報撞機。
- **高度限制**：40 mm 高的方塊，相機要對焦頂面得把 Z 拉到 +60，超出 +50 的行程，沙盒回報 `out_of_travel`。這是實機真正的限制。

改了機構或沙盒程式之後，重跑 demo，結果應該跟上面相同。真值的算法寫在 demo 裡。

## 5. 已知限制與可擴充方向

- **沒有動力學**：沒有加減速，時間是用路徑長度除以速度估的（快速移動先假設 5000 mm/min）。要做動力學的話，可以改用 MJCF 裡已經有的位置伺服加 `mj_step`。
- **不模擬的東西**：切削、切削液、浪管、對刀稜鏡的光路。
- **凸包誤差**：除了探針、工作台面、方塊工件以外，碰撞都用凸包，凹的地方會偏保守幾 mm。
- **機台結構只有外觀**：在行程內，AI 的動作碰不到機台結構，所以沒做碰撞。
- **授權**：網格含廠商模型，沙盒只能在專案內部使用，不要公開發布。
