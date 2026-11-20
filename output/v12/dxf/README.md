# v12 CNC 加工件 DXF

由 `freecad/v12/09_dxf_extract_v12.py`（抽取）與 `10_dxf_write_v12.py`（輸出）產生。單位 mm，每個視圖原點在左下角。
定位銷、樞軸銷、靠銷、偏心銷與球面軸承的孔標 H7（紅色圖層），並寫公差上下限；標「ream at assembly」的孔在組裝調整後現場配鉸。

| 零件 | 數量 | 外形 (x×y×z) | 孔數 | H7 孔 | 規格 |
|---|---|---|---|---|---|
| Datum_base_plate | 1 | 720x327x20 | 34 | 6 | Q235 t20 720x327 milled datum plate (single face): Y block seats, Y nu |
| Work_table | 1 | 440x473.5x40 | 20 | 6 | 440x473.5x40 (53.5 longer at rear), 5x T-slot 14, work area 300x300; u |
| Column_foot_L | 1 | 80x210x18 | 8 | 1 | steel foot t18, 80x210, front flange 30 (hold-down bolt, push-pull con |
| Column_foot_R | 1 | 80x210x18 | 9 | 1 | steel foot t18, 80x210, front flange 30 (hold-down bolt, push-pull con |
| Gantry_column_L | 1 | 80x160x472 | 5 | 1 | HFS8-80160-472 (z18..490) |
| Gantry_column_R | 1 | 80x160x472 | 4 | 0 | HFS8-80160-472 (z18..490) |
| X_base_plate | 1 | 720x20x260 | 53 | 7 | steel t20 720x260 (z 230..490); X rails z 250 / 470 (spacing 220); X d |
| X_saddle_plate | 1 | 284x12x484 | 27 | 1 | saddle, steel t12 with two ears above the columns: bolted to the 4 X b |
| X_carriage_plate | 1 | 240x17x488 | 42 | 7 | Z plate, steel t17 240x488: Z rails, Z screw, Z motor plate. 1 mm off  |
| Z_slide_plate | 1 | 220x28x230 | 23 | 1 | steel t28, pocket for the Z nut |
| Z_spacer_L | 1 | 50x14x230 | 8 | 0 | steel spacer bar t14 |
| Z_spacer_R | 1 | 50x14x230 | 8 | 0 | steel spacer bar t14 |
| Z_motor_plate | 1 | 120x90x38 | 5 | 0 | block 120x90x38: front part bolted to carriage FRONT face with 4xM6 (s |
| Z_nut_housing | 1 | 52x39.59x32 | 1 | 0 | Z nut housing (CNC): wraps the nut body, flange on its top face, bolte |
| X_nut_bracket | 1 | 37x95.6x52 | 1 | 0 | nut housing (CNC): wraps the C-KBS1505 nut body, flange bolted to the  |
| Y_nut_bracket | 1 | 52x32x67.59 | 1 | 0 | Y nut housing (CNC): wraps the C-KBS1505 nut body, flange on its +y fa |
| X_motor_block | 1 | 38x67x76 | 5 | 0 | Z-style block in the 7 mm pocket of the X base plate REAR face, 4xM6 ( |
| Y_motor_block | 1 | 120x38x95 | 5 | 0 | Z-style block: bolted UP into table underside 4xM6 (same face as rails |
| Spindle_clamp | 1 | 96x83x74 | 7 | 0 | 6061 clamp block 96x83x74: bore D65 at (x0, y-20), rear wall 7.5, fron |
| Spindle_mount_plate | 1 | 156x12x181 | 12 | 0 | flat steel plate 156x181x12, ground both faces, all holes from the fro |
| Base_riser_1 | 4 | 60x60x68.5 | 3 | 0 | steel riser 60x60x68.5 on the pan floor: M12 tap for the machine, 2 co |
| Yaw_push_block | 1 | 40x26x25 | 4 | 0 | steel block 40x26x25 on the datum plate in front of the RIGHT foot fla |
| X_roll_bracket | 1 | 60x24x32 | 3 | 0 | steel block 60x24x32 on the right column rear face (T-slots), under th |
| Z_roll_block_L | 1 | 18x18x32 | 3 | 0 | steel block 18x18x32 on the saddle ear, beside the Z plate edge |
| Z_roll_block_R | 1 | 18x18x32 | 3 | 0 | steel block 18x18x32 on the saddle ear, beside the Z plate edge |
| Spindle_roll_block_L | 1 | 18x20x30 | 2 | 0 | steel block beside the top of the ear |
| Spindle_roll_block_R | 1 | 18x20x30 | 2 | 0 | steel block beside the top of the ear |
