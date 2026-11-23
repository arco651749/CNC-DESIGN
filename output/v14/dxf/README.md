# v14 CNC 加工件 DXF

由 `freecad/v14/09_dxf_extract_v14.py`（抽取）與 `10_dxf_write_v14.py`（輸出）產生。單位 mm，每個視圖原點在左下角。

每張圖都有：

- 最大長寬高的尺寸標註（板件另加側視圖標厚度）；
- H7 孔：孔徑與公差上下限，孔位從左下兩邊標尺寸，位置公差 ±0.02（基準邊要加工成直角）；
- 每組孔一條引線，寫規格（攻牙尺寸與牙距、給幾號螺絲的過孔、沉頭、深度、從哪一面）；
- 研磨面在側視圖用紫色粗線加 GROUND 標出，並寫在註記欄。

標「ream at assembly」的孔在組裝調整後現場配鉸，不標孔位。

RBPB8 座孔 Ø22 H7：外環 h6，用固持膠（Loctite 641）黏固，不壓入。

| 零件 | 數量 | 外形 X × Y × Z | 孔數 | H7 孔 | 研磨 | 規格 |
|---|---|---|---|---|---|---|
| Datum_base_plate | 1 | 785 × 327 × 20 | 38 | 6 | top face ground (Y block seats) | Q235 t20 785x327 datum plate, top face ground (Y block seats |
| Work_table | 1 | 440 × 473.5 × 40 | 26 | 6 | Y slide table: BOTH faces ground - underside = Y rail face | 440x473.5x40 (53.5 longer at rear), 5x T-slot 14 DIN 650 (ne |
| Column_foot_L | 1 | 80 × 210 × 18 | 8 | 1 | — | steel foot t18, 80x210, front flange 30 (hold-down bolt, pus |
| Column_foot_R | 1 | 80 × 210 × 18 | 9 | 1 | — | steel foot t18, 80x210, front flange 30 (hold-down bolt, pus |
| Gantry_column_L | 1 | 80 × 160 × 472 | 5 | 1 | — | HFS8-80160-472 (z18..490) |
| Gantry_column_R | 1 | 80 × 160 × 472 | 4 | 0 | — | HFS8-80160-472 (z18..490) |
| X_base_plate | 1 | 785 × 20 × 260 | 65 | 7 | front face ground (X rail face) | steel t20 785x260 (z 230..490); X rails z 250 / 470 (spacing |
| X_saddle_plate | 1 | 284 × 12 × 484 | 31 | 1 | rear face ground (X block face) | saddle, steel t12 with two ears above the columns: bolted to |
| X_carriage_plate | 1 | 240 × 17 × 488 | 48 | 7 | front face ground (Z rail face) | Z plate, steel t17 240x488: Z rails, Z screw, Z motor plate. |
| Z_slide_plate | 1 | 220 × 28 × 260 | 27 | 1 | rear face ground (spacer / Z block face) | steel t28, pocket for the Z nut; v13: 30 longer at the botto |
| Z_spacer_L | 1 | 50 × 14 × 230 | 8 | 0 | both faces ground | steel spacer bar t14 |
| Z_spacer_R | 1 | 50 × 14 × 230 | 8 | 0 | both faces ground | steel spacer bar t14 |
| Z_motor_plate | 1 | 120 × 90 × 38 | 9 | 1 | — | block 120x90x38: front part bolted to carriage FRONT face wi |
| Z_nut_housing | 1 | 88 × 45.6 × 32 | 11 | 1 | — | Z nut housing (CNC, steel): wraps the nut body, nut flange o |
| X_nut_bracket | 1 | 37 × 95.6 × 52 | 11 | 1 | — | nut housing (CNC): wraps the C-KBS1505 nut body, flange bolt |
| Y_nut_bracket | 1 | 52 × 32 × 67.59 | 11 | 1 | — | Y nut housing (CNC): wraps the C-KBS1505 nut body, flange on |
| X_motor_block | 1 | 38 × 67 × 76 | 9 | 1 | — | Z-style block in the 7 mm pocket of the X base plate REAR fa |
| Y_motor_block | 1 | 120 × 38 × 95 | 9 | 1 | — | Z-style block: bolted UP into table underside 4xM6 (same fac |
| Spindle_clamp | 1 | 96 × 83 × 74 | 13 | 3 | — | 6061 clamp block 96x83x74: bore D65 H7 at (x+32.5, y-20), re |
| Spindle_mount_plate | 1 | 216 × 12 × 212 | 16 | 2 | both faces ground | tool-head module plate, flat steel t12 (156 wide z 319..500  |
| Base_riser_1 | 4 | 60 × 60 × 68.5 | 3 | 0 | — | steel riser 60x60x68.5 on the pan floor: M12 tap for the mac |
| Yaw_push_block | 1 | 40 × 26 × 25 | 4 | 0 | — | steel block 40x26x25 on the datum plate in front of the RIGH |
| X_roll_bracket | 1 | 60 × 24 × 32 | 3 | 0 | — | steel block 60x24x32 on the right column rear face (T-slots) |
| Z_roll_block_L | 1 | 18 × 18 × 32 | 3 | 0 | — | steel block 18x18x32 on the saddle ear, beside the Z plate e |
| Z_roll_block_R | 1 | 18 × 18 × 32 | 3 | 0 | — | steel block 18x18x32 on the saddle ear, beside the Z plate e |
| Spindle_roll_block_L | 1 | 18 × 20 × 30 | 2 | 0 | — | steel block beside the top of the ear |
| Spindle_roll_block_R | 1 | 18 × 20 × 30 | 2 | 0 | — | steel block beside the top of the ear |
| Camera_bracket | 1 | 52 × 76 × 30 | 4 | 0 | — | camera bracket (CNC, 6061): flange on the module plate (2 x  |
| Camera_air_ring | 1 | 55 × 51 × 10 | 2 | 0 | — | lens air ring (CNC, 6061) on the D45 lens nose, 2 x M3 set s |
| Mirror_bracket | 1 | 118.5 × 101.5 × 29 | 4 | 0 | — | prism holder (CNC, steel t8, base ground): on the table T-sl |
| Probe_holder | 1 | 16 × 22 × 103.5 | 6 | 1 | — | probe plate (CNC, 6061 t8, 19 wide, 104 long) on the MXH10 t |
