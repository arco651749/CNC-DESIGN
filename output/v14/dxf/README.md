# v14 CNC 加工件 DXF

由 `freecad/v14/09_dxf_extract_v14.py`（抽取）與 `10_dxf_write_v14.py`（輸出）產生。單位 mm，每個視圖原點在左下角。

每張圖都有：

- 最大長寬高的尺寸標註（板件另加側視圖標厚度）；
- H7 孔：孔徑與公差上下限，孔位從左下兩邊標尺寸，位置公差 ±0.02（基準邊要加工成直角）；
- 每組孔一條引線，寫規格（攻牙尺寸與牙距、給幾號螺絲的過孔、沉頭、深度、從哪一面）；
- 研磨面在側視圖用紫色粗線加 GROUND 標出，並寫在註記欄；
- 只標外觀尺寸、精度孔（H7）、螺絲孔和研磨面；精度孔和螺絲孔有編號（A1、A2…），孔位表列出 X、Y（從該視圖左下角量）；
- 研磨：只有 Y 軸滑台（Work_table）兩面研磨，其他零件只磨線軌安裝面；
- 標題欄寫材質、表面處理與該零件的加工註記（例如成對加工）。

標「ream at assembly」的孔在組裝調整後現場配鉸，不標孔位。

RBPB8 座孔 Ø22 H7：外環 h6，用固持膠（Loctite 641）黏固，不壓入。

| 零件 | 數量 | 外形 X × Y × Z | 孔數 | H7 孔 | 研磨 | 規格 |
|---|---|---|---|---|---|---|
| Datum_base_plate | 1 | 785 × 327 × 20 | 38 | 6 | top face ground (Y block seats) | Q235 t20 785x327 datum plate, top face ground (Y block seats |
| Work_table | 1 | 440 × 473.5 × 40 | 26 | 6 | Y slide table: BOTH faces ground - underside = Y rail face | 440x473.5x40 (53.5 longer at rear), 5x T-slot 14 DIN 650 (ne |
| Column_foot_L | 1 | 80 × 210 × 18 | 8 | 1 | — | steel foot t18, 80x210, front flange 30 (hold-down bolt, pus |
| Column_foot_R | 1 | 80 × 210 × 18 | 9 | 1 | — | steel foot t18, 80x210, front flange 30 (hold-down bolt, pus |
| Gantry_column_L | 1 | 80 × 160 × 472 | 1 | 1 | — | HFS8-80160-472 (z18..490) |
| Gantry_column_R | 1 | 80 × 160 × 472 | 0 | 0 | — | HFS8-80160-472 (z18..490) |
| X_base_plate | 1 | 785 × 20 × 260 | 65 | 7 | front face ground (X rail face) | steel t20 785x260 (z 230..490); X rails z 250 / 470 (spacing |
| X_saddle_plate | 1 | 284 × 12 × 484 | 37 | 1 | rear face ground (X block face) | saddle, steel t12 with two ears above the columns: bolted to |
| X_carriage_plate | 1 | 200 × 17 × 488 | 48 | 7 | front face ground (Z rail face) | Z plate, steel t17 200x488: Z rails, Z screw, Z motor plate. |
| Z_slide_plate | 1 | 180 × 28 × 260 | 27 | 1 | rear face ground (spacer / Z block face) | steel t28, pocket for the Z nut; v13: 30 longer at the botto |
| Z_spacer_L | 1 | 50 × 14 × 230 | 8 | 0 | Z block face ground | steel spacer bar t14 |
| Z_spacer_R | 1 | 50 × 14 × 230 | 8 | 0 | Z block face ground | steel spacer bar t14 |
| Z_motor_plate | 1 | 120 × 90 × 38 | 9 | 1 | — | block 120x90x38: front part bolted to carriage FRONT face wi |
| Z_nut_housing | 1 | 52 × 45.6 × 32 | 11 | 1 | — | Z nut housing (CNC, steel) 52 x 45.6 x 32 = the nut flange o |
| X_nut_bracket | 1 | 37 × 95.6 × 52 | 11 | 1 | — | nut housing (CNC): wraps the C-KBS1505 nut body, flange bolt |
| Y_nut_bracket | 1 | 52 × 32 × 67.59 | 11 | 1 | — | Y nut housing (CNC): wraps the C-KBS1505 nut body, flange on |
| X_motor_block | 1 | 38 × 67 × 76 | 9 | 1 | — | Z-style block in the 7 mm pocket of the X base plate REAR fa |
| Y_motor_block | 1 | 120 × 38 × 95 | 11 | 1 | — | Z-style block: bolted UP into table underside 4xM6 (same fac |
| Spindle_clamp | 1 | 96 × 83 × 74 | 17 | 3 | — | 6061 clamp block 96x83x74: bore D65 H7 at (x+32.5, y-20), re |
| Spindle_mount_plate | 1 | 176 × 12 × 212 | 16 | 2 | — | tool-head module plate, flat steel t12 (116 wide z 288..500  |
| Base_riser_1 | 4 | 60 × 60 × 68.5 | 3 | 0 | — | steel riser 60x60x68.5 on the pan floor: M12 tap for the mac |
| Yaw_push_block | 1 | 40 × 26 × 25 | 4 | 0 | — | steel block 40x26x25 on the datum plate in front of the RIGH |
| X_roll_bracket | 1 | 60 × 24 × 32 | 3 | 0 | — | steel block 60x24x32 on the right column rear face (T-slots) |
| Z_roll_block_L | 1 | 18 × 18 × 32 | 3 | 0 | — | steel block 18x18x32 on the saddle ear, beside the Z plate e |
| Z_roll_block_R | 1 | 18 × 18 × 32 | 3 | 0 | — | steel block 18x18x32 on the saddle ear, beside the Z plate e |
| Spindle_roll_block_L | 1 | 18 × 20 × 30 | 2 | 0 | — | steel block beside the top of the ear |
| Spindle_roll_block_R | 1 | 18 × 20 × 30 | 2 | 0 | — | steel block beside the top of the ear |
| Camera_bracket | 1 | 27.75 × 73.5 × 28 | 4 | 0 | — | camera bracket base (CNC, 6061 block 27.75 x 73.5 x 28) on t |
| Camera_bracket_cap | 1 | 30.75 × 67 × 28 | 2 | 0 | — | camera bracket cap (CNC, 6061 block 30.75 x 67 x 28) on the  |
| Probe_stem | 1 | 15 × 19 × 42.5 | 4 | 0 | — | probe stem (CNC, 6061 flat 15 x 19, 42 long) under the probe |
| Camera_air_ring | 1 | 55 × 51 × 10 | 2 | 0 | — | lens air ring (CNC, 6061) on the D45 lens nose, 2 x M3 set s |
| Mirror_bracket | 1 | 118.5 × 101.5 × 29 | 4 | 0 | — | prism holder (CNC, steel t8, base ground): on the table T-sl |
| Probe_holder | 1 | 46 × 19 × 10 | 6 | 0 | — | probe plate (CNC, 6061 t10, 46 x 19) under the MXH10 rod-end |
| Box_top_plate | 1 | 785 × 501 × 20 | 34 | 0 | — | SPHC t3 laser cut + bent: 785 x 498, rear and side flanges 2 |
| Box_top_shim_L | 2 | 80 × 160 × 1 | 4 | 0 | — | stainless shim t1, 80 x 160, 4 x D9: lifts the box top plate |
| Conduit_Y_bracket | 1 | 80 × 147 × 56.04 | 3 | 0 | — | SPHC t3 bent: Y conduit end bracket on the Y motor block top |
| Conduit_head_bracket | 1 | 100 × 39 × 115.6 | 4 | 0 | — | SPHC t3 bent: Z conduit end bracket on the spindle clamp fro |
| Conduit_carriage_bracket | 1 | 52 × 100 × 140 | 3 | 0 | — | SPHC t3 bent: on the saddle ear front face (2 x M5, beside t |
| Conduit_X_arm | 1 | 73 × 121 × 203 | 4 | 0 | — | SPHC t3 bent: X conduit carriage arm on the saddle ear back  |
| Conduit_Y_top_bracket | 1 | 80 × 113 × 45 | 3 | 0 | — | SPHC t3 bent: Y conduit top end, on the column box L-plate f |
| Feeder_entry_plate | 1 | 180 × 23 × 244 | 4 | 0 | — | SPHC t3 bent: feeder conduit entry plate on the box top plat |
| Conduit_X_roof_tab | 1 | 25 × 50 × 58 | 3 | 0 | — | SPHC t3 bent: tab on the box top plate (2 x M5) carrying the |
