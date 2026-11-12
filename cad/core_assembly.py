# -*- coding: utf-8 -*-
"""Core assembly (no big base): datum plate + Y axis + aluminium-extrusion gantry + X/Z axes + spindle.
Run: python cad/core_assembly.py
Outputs (../output/core): CNC_Core.step (named, coloured assembly), CNC_Core_BOM.csv (grouped parts with sourcing).
"""
import os, csv, re, runpy
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "output", "core")
os.makedirs(OUT, exist_ok=True)
M = runpy.run_path(os.path.join(HERE, "cnc_gantry.py"), run_name="lib")

CORE_GROUPS = ("03 Y-axis", "04 Gantry", "05 X-axis", "06 Z-axis & Spindle")
CORE_EXTRA = ("Datum_base_plate",)
DROP = ("Work_area_300x300", "Y_drag_chain")
core = [(n, s, g, m, t) for n, s, g, m, t in M["parts"]
        if (g in CORE_GROUPS or n in CORE_EXTRA) and n not in DROP]

# sourcing: (name regex, source, status)
SRC = [
    (r"^Gantry_(column|beam)", "三住 MISUMI", "型號已查：HFS8-80160（8 系列、槽寬 10），長度可指定 0.5 mm"),
    (r"^(Y|X|Z)_rail(_[LR]|_\d)?$", "HIWIN（或三住同級線軌）", "Y: HGR35，X/Z: HGR20；長度依清單"),
    (r"^(Y|X|Z)_block", "HIWIN（或三住同級線軌）", "Y: HGH35CA，X/Z: HGH20CA，ZA 預壓、H 級"),
    (r"ballscrew", "三住 MISUMI 或 HIWIN", "DFU1605 C7 雙螺帽預壓，兩端軸頭依圖加工（待選型號）"),
    (r"_(BK|BF)_support", "三住 MISUMI 或 HIWIN", "BK12 / BF12 同級支撐座（三住對應型號待確認）"),
    (r"coupling", "三住 MISUMI", "聯軸器 Ø25，8×12 / 8×14（待選型號）"),
    (r"_motor$", "三菱電機", "HG-KR43（Z 軸 HG-KR43B 附煞車）"),
    (r"^Spindle$|Spindle_fan|Spindle_connector|Spindle_nose", "電主軸廠（Sorotec / GDF65 等）", "0.8 kW 風冷 Ø65×188 ER11，24,000 rpm"),
    (r"^ER11|^Tool", "刀具 / 夾頭商", "ER11 AA 級筒夾、螺帽 Ø19、刀具 Ø5×柄 Ø6"),
    (r"nut_housing", "自製加工（或三住螺帽座）", "依螺帽法蘭尺寸加工"),
]


def source(n):
    for rx, src, st in SRC:
        if re.search(rx, n):
            return src, st
    return "自製加工（可用三住 meviy / 板材加工）", "依 STEP 尺寸加工"


rows = {}
for n, s, g, m, t in core:
    key = re.sub(r"_(L|R|\d+|L\d|R\d|\d\d)$", "", n)
    b = s.BoundingBox()
    size = f"{b.xlen:.0f}×{b.ylen:.0f}×{b.zlen:.0f}"
    k = (g, key, m)
    if k not in rows:
        src, st = source(n)
        rows[k] = dict(group=g, part=key, qty=0, spec=m, size=size, source=src, status=st, note=t)
    rows[k]["qty"] += 1

bom_path = os.path.join(OUT, "CNC_Core_BOM.csv")
with open(bom_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["群組", "零件", "數量", "規格 / 型號", "外形尺寸 (mm)", "來源", "狀態 / 備註", "說明"])
    for r in sorted(rows.values(), key=lambda r: (r["group"], r["part"])):
        w.writerow([r["group"], r["part"], r["qty"], r["spec"], r["size"], r["source"], r["status"], r["note"]])
    # fasteners not modelled
    w.writerow(["04 Gantry", "T-nuts / bolts", "約 60", "8 系列後入式 T 型螺帽 M8 + 內六角螺栓", "-", "三住 MISUMI", "型號待確認", "立柱、橫樑、連接板、滑軌座板"])

assy = cq.Assembly(name="CNC_Core")
for n, s, g, m, t in core:
    assy.add(s, name=n, color=cq.Color(*M["COLORS"][g]))
step_path = os.path.join(OUT, "CNC_Core.step")
assy.export(step_path)
bb = cq.Compound.makeCompound([s for _, s, *_ in core]).BoundingBox()
print("OK core", len(core), "parts,", len(rows), "BOM lines | envelope",
      round(bb.xlen), "x", round(bb.ylen), "x", round(bb.zlen), "mm")
print(step_path, bom_path)
