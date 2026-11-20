#!/usr/bin/env python3
"""Per-part wiring cards (PDF). The 'connects to' tables come straight from the same
netlist the KiCad drawing is built from (build_wiring.py), so cards and drawing cannot disagree.

Usage: python3 make_cards.py            -> cards/<REF>_card.pdf (+ .png preview)
Add a part: give it an entry in PARTS (image, zones, pin map, notes).
"""
import os, sys, collections, textwrap
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, Polygon
from PIL import Image
import build_wiring as B

FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
    plt.rcParams["font.family"] = "WenQuanYi Zen Hei"
plt.rcParams["axes.unicode_minus"] = False
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import warnings; warnings.filterwarnings("ignore")

COLORNAME = {(120, 60, 10): "棕", (0, 0, 220): "藍", (0, 140, 0): "綠", (220, 0, 0): "紅", (0, 0, 0): "黑",
             (110, 110, 110): "灰", (255, 120, 0): "橙", (160, 0, 160): "紫", (170, 135, 0): "黃褐",
             (0, 140, 140): "青", (0, 120, 200): "淺藍", (200, 50, 0): "橙紅"}
COLORRGB = {k: tuple(c / 255 for c in v) for k, v in {"棕": (120, 60, 10), "藍": (0, 0, 220), "綠": (0, 140, 0), "紅": (220, 0, 0),
            "黑": (0, 0, 0), "灰": (110, 110, 110), "橙": (255, 120, 0), "紫": (160, 0, 160), "黃褐": (170, 135, 0),
            "青": (0, 140, 140), "淺藍": (0, 120, 200), "橙紅": (200, 50, 0)}.items()}

# ---- netlist from the drawing model -------------------------------------------------------
nets = collections.defaultdict(list)
for b in B.S.blocks:
    for p in b.pins.values():
        nets[p.net].append((b, p))
wirecolor = {}
for w in B.S.wires: wirecolor.setdefault(w["net"], COLORNAME.get(tuple(w["color"]), "?"))
DISP = {"ALM": "KA4", "IFB": "IFB1", "SVL": "SV1", "BD": "BD", "BTX": "BTX", "BTY": "BTY", "BTZ": "BTZ"}
def disp(b): return DISP.get(b.ref, b.ref)
RAIL_TEXT = {"+24V1": "PSU1 +24V（網路 +24V1）", "0V1": "PSU1 0V（網路 0V1）", "+24V2": "PSU2 +24V（網路 +24V2）", "0V2": "PSU2 0V（網路 0V2）",
             "+24V3": "PSU3 +24V（網路 +24V3）", "0V3": "PSU3 0V（網路 0V3）", "+5V": "DC1 +5V（網路 +5V）",
             "EM2_COM": "S1[NC2] 對 0V3（三軸共用）", "PE": "盤面 PE 排"}
def short(b): return "%s %s" % (b.ref, b.title.split(" ", 1)[1] if " " in b.title else b.title)
USED = set()
def dests(blk, pin, limit=5):
    if pin.net in RAIL_TEXT: return RAIL_TEXT[pin.net]
    others = [(b, p) for (b, p) in nets[pin.net] if not (b is blk and p is pin)]
    if not others: return "（本機內部）"
    for b, _ in others[:limit]: USED.add(b)
    txt = "、".join("%s[%s]" % (disp(b), p.label.replace("−", "-")) for b, p in others[:limit])
    if len(others) > limit: txt += " …共 %d 點" % (len(others))
    return txt

# ---- part definitions ---------------------------------------------------------------------
PARTS = {}
PARTS["BD"] = dict(
    title="RP23CNC V2.02 控制板（grblHAL）  代號 BD",
    photo=dict(path=os.path.join(HERE, "..", "vendor", "rp23cnc", "photos", "RP23CNC_V2_photo.jpg"), ref_w=900,
               polys={"A": [(55, 190), (462, 95), (472, 170), (70, 245)],
                      "C": [(497, 105), (832, 238), (842, 268), (505, 170)],
                      "B": [(422, 440), (858, 272), (890, 322), (432, 494)]},
               badge={"A": (40, 175), "C": (845, 225), "B": (905, 305)},
               note="圖：RP23CNC V2 加選配組裝套件的實物照片（作者實拍，來源 github.com/phil-barrett/RP23CNC）。\n後左長排＝上排 A、後右長排＝右排 C、前方長排＝下排 B。"),
    ref=dict(path=os.path.join(HERE, "..", "vendor", "rp23cnc", "photos", "RP23CNC_V2.02_labelled_drawing.png"),
             note="原廠製圖（非照片），只用來對照板上絲印與 D、E 位置。"),
    zones={  # letter: (x0, y0, x1, y1, name) in the labelled drawing's pixels (1255 x 1262)
        "A": (118, 10, 1228, 88, "上排螺絲端子（22 位）"),
        "B": (118, 1180, 1228, 1255, "下排螺絲端子（22 位）"),
        "C": (1164, 178, 1245, 1100, "右排螺絲端子（20 位）"),
        "D": (718, 1010, 815, 1066, "伺服報警輸入排針（2×3，2.54 mm）"),
        "E": (314, 209, 579, 523, "WIZ850io 乙太網路模組座（選配，必須是 W5500）"),
    },
    pinmap=[  # (zone, pid, silkscreen text on the board)
        ("A", "PWR_P", "+V（12/24V 主電源，標示在 GND 旁）"), ("A", "PWR_G", "GND（與 +V 同組）"),
        ("A", "S010", "0-10（主軸類比輸出）"), ("A", "SGND", "GND（0-10 旁）"),
        ("A", "K1P", "SPDL EN 的 +V（繼電器電壓）"), ("A", "K1S", "SPDL EN 的 SIG"),
        ("A", "K2P", "FLOOD 的 +V"), ("A", "K2S", "FLOOD 的 SIG"),
        ("A", "K5P", "MIST 的 +V"), ("A", "K5S", "MIST 的 SIG"),
        ("B", "ISO_P", "+V（隔離輸入電源，最左側）"), ("B", "ISO_G", "GND（隔離輸入電源）"),
        ("B", "ES_S", "ESTOP 的 SIG（最右側）"), ("B", "ES_G", "ESTOP 的 GND"),
        ("B", "LXS", "LIM X 的 SIG"), ("B", "LXG", "LIM X 的 GND"),
        ("B", "LYS", "LIM Y 的 SIG"), ("B", "LYG", "LIM Y 的 GND"),
        ("B", "LZS", "LIM Z 的 SIG"), ("B", "LZG", "LIM Z 的 GND"),
        ("C", "X_STP", "Axis X 的 STEP"), ("C", "X_DIR", "Axis X 的 DIR"), ("C", "X_EN", "Axis X 的 ENA"), ("C", "X_GND", "Axis X 的 GND"),
        ("C", "Y_STP", "Axis Y 的 STEP"), ("C", "Y_DIR", "Axis Y 的 DIR"), ("C", "Y_EN", "Axis Y 的 ENA"), ("C", "Y_GND", "Axis Y 的 GND"),
        ("C", "Z_STP", "Axis Z 的 STEP"), ("C", "Z_DIR", "Axis Z 的 DIR"), ("C", "Z_EN", "Axis Z 的 ENA"), ("C", "Z_GND", "Axis Z 的 GND"),
        ("D", "AX", "Servo Alarm Input：X"), ("D", "AY", "Servo Alarm Input：Y"), ("D", "AZ", "Servo Alarm Input：Z"), ("D", "AG", "Servo Alarm Input：Gnd"),
        ("E", "ETH", "WIZ850io RJ45（Cat5e 屏蔽線到 LAN 交換器）"),
    ],
    setup=[
        "出廠前的跳線設定（依手冊第 17、33、34 頁）",
        "- 5V SRC 跳線 → EXT（板載 5V）。USB 5V 只用於桌上測試。",
        "- Relay Voltage 跳線 → 12/24V（本機繼電器線圈為 24V）。",
        "- 「Join 12/24V Iso 與 Main」兩個跳線 → 不插（隔離側由 PSU2 獨立供電）。",
        "- RV1「0-10V Adjust」：以 M3 S1000 開主軸，量 0-10 與 GND 端子，調到 10 V（9.90–10.10 V）。",
        "- 韌體：grblHAL Web Builder 選 RP23U5XBB；設定 $0=3（脈衝寬度 µs）、$14=70（反轉 EStop/Feed Hold/Cycle Start）。",
        "- 電源：必須是穩壓 12/24V 電源，不可熱插拔，極性勿接反；每條絞線端要壓 22 AWG 端子（Ferrule）。",
    ],
    caution=["本表的「接到」欄來自配線圖（CNC_wiring.kicad_sch）的網表；端子的左右順序我沒有逐一驗證，請以板上絲印為準。"],
)

def make_card(ref):
    P = PARTS[ref]
    blk = next(b for b in B.S.blocks if b.ref == ref)
    fig = plt.figure(figsize=(16.54, 11.69), dpi=110)  # A3 landscape
    fig.text(0.02, 0.965, P["title"], fontsize=18, weight="bold", va="top")
    fig.text(0.02, 0.938, "零件接線卡　｜　專案：CNC 龍門銑床　｜　單相 220V　｜　圖紙版本 Rev A", fontsize=9.5, color="#444", va="top")
    # ---- real photo (primary) with zone outlines, plus the author's labelled drawing for the silkscreen
    ph = P["photo"]
    im = Image.open(ph["path"]).convert("RGB")
    ax = fig.add_axes([0.02, 0.565, 0.41, 0.345]); ax.imshow(im); ax.axis("off")
    k = im.size[0] / ph["ref_w"]
    for letter, pts in ph["polys"].items():
        ax.add_patch(Polygon([(x * k, y * k) for x, y in pts], closed=True, fill=False, ec="#e6007e", lw=2.6))
        bx, by = ph["badge"][letter]
        ax.text(bx * k, by * k, letter, color="white", fontsize=12, weight="bold", ha="center", va="center",
                bbox=dict(boxstyle="circle,pad=0.25", fc="#e6007e", ec="none"))
    fig.text(0.02, 0.563, ph["note"], fontsize=8, color="#555", va="top", linespacing=1.4)
    rf = P["ref"]
    ri = Image.open(rf["path"]).convert("RGB")
    rx = fig.add_axes([0.02, 0.295, 0.255, 0.255]); rx.imshow(ri); rx.axis("off")
    for letter, (a_, b_, c_, d_, name) in P["zones"].items():
        rx.add_patch(Rectangle((a_, b_), c_ - a_, d_ - b_, fill=False, ec="#e6007e", lw=1.8))
        rx.text(a_ + 4, b_ + 4, letter, color="white", fontsize=9, weight="bold", ha="left", va="top",
                bbox=dict(boxstyle="circle,pad=0.2", fc="#e6007e", ec="none"))
    fig.text(0.02, 0.292, rf["note"], fontsize=7.6, color="#555", va="top")
    yy = 0.555
    fig.text(0.295, yy, "圖中標示的區域", fontsize=10.5, weight="bold", va="top"); yy -= 0.022
    for letter, (a_, b_, c_, d_, name) in P["zones"].items():
        fig.text(0.295, yy, " %s " % letter, fontsize=9, color="white", weight="bold", va="top", bbox=dict(boxstyle="circle,pad=0.2", fc="#e6007e", ec="none"))
        fig.text(0.315, yy, textwrap.fill(name, 19), fontsize=8.6, va="top", linespacing=1.15); yy -= 0.021 * (textwrap.fill(name, 19).count("\n") + 1)
    yy = 0.265
    for i, line in enumerate(P["setup"]):
        wrapped = textwrap.fill(line, 56) if i else line
        fig.text(0.02, yy, wrapped, fontsize=10.2 if i == 0 else 8.0, weight="bold" if i == 0 else None, va="top", linespacing=1.2)
        yy -= 0.0155 * (wrapped.count("\n") + 1) + (0.005 if i else 0.008)
    for line in P["caution"]:
        fig.text(0.445, 0.028, "※ " + textwrap.fill(line, 90), fontsize=8, color="#a00", va="bottom")
    # ---- table
    pins = {p.pid: p for p in blk.pins.values()}
    rows = [(z, pins[pid], silk) for z, pid, silk in P["pinmap"]]
    assert len(rows) == len(blk.pins), "pinmap does not cover every pin of %s (%d/%d)" % (ref, len(rows), len(blk.pins))
    tx = 0.445; colx = [tx, tx + 0.020, tx + 0.205, tx + 0.245]
    top = 0.925; rh = 0.0188
    fig.text(colx[0], top, "區", fontsize=9, weight="bold", va="top"); fig.text(colx[1], top, "板上端子（絲印）", fontsize=9, weight="bold", va="top")
    fig.text(colx[2], top, "線色", fontsize=9, weight="bold", va="top"); fig.text(colx[3], top, "接到（零件.接點，同名線以標籤相連）", fontsize=9, weight="bold", va="top")
    y = top - 0.026
    fig.add_artist(plt.Line2D([tx - 0.003, 0.985], [y + 0.004, y + 0.004], color="#888", lw=0.8))
    last = None
    for z, p, silk in rows:
        if z != last:
            y -= 0.004
            fig.text(colx[0], y, z, fontsize=8.5, color="white", weight="bold", va="top", bbox=dict(boxstyle="circle,pad=0.2", fc="#e6007e", ec="none"))
            fig.text(colx[1], y, P["zones"][z][4], fontsize=8.8, weight="bold", va="top", color="#e6007e")
            y -= rh * 0.95; last = z
        col = wirecolor.get(p.net, "?")
        fig.text(colx[1], y, silk, fontsize=8.3, va="top")
        fig.add_artist(Rectangle((colx[2], y - 0.0125), 0.011, 0.012, transform=fig.transFigure, fc=COLORRGB.get(col, (.5, .5, .5)), ec="#333", lw=0.5))
        fig.text(colx[2] + 0.014, y, col, fontsize=8.3, va="top")
        fig.text(colx[3], y, dests(blk, p), fontsize=8.1, va="top")
        y -= rh
    legend = "零件代號：" + "；".join("%s＝%s" % (disp(b), b.title.split(" ", 1)[1] if " " in b.title else b.title)
                                       for b in sorted(USED, key=lambda b: disp(b)))
    fig.text(tx, 0.085, textwrap.fill(legend, 100), fontsize=7.8, color="#333", va="top", linespacing=1.3)
    out = os.path.join(HERE, "cards"); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "%s_card.pdf" % ref)); fig.savefig(os.path.join(out, "%s_card.png" % ref), dpi=110)
    plt.close(fig)
    print("wrote", os.path.join(out, "%s_card.pdf" % ref), "rows", len(rows))

if __name__ == "__main__":
    for ref in (sys.argv[1:] or PARTS): make_card(ref)


# =====================================================================================
# MR-J4-40A servo drive card (X / Y / Z in one table). Figures come from the Mitsubishi
# manual SH-030107-V (pages 3-29 and 9-3), rendered from the PDF in vendor/ (not committed).
# =====================================================================================
import subprocess, tempfile, shutil
MANUAL = os.path.join(HERE, "..", "vendor", "mitsubishi", "MR-J4-A_manual_SH-030107-V.pdf")

def _page_png(pdf_page, dpi=130):
    d = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(pdf_page), "-l", str(pdf_page), "-png", MANUAL, os.path.join(d, "p")], check=True)
    f = [x for x in os.listdir(d) if x.endswith(".png")][0]
    im = Image.open(os.path.join(d, f)).convert("RGB"); shutil.rmtree(d)
    return im

def _cn1_xy(n):  # pixel position of a CN1 pin on page 3-29 at 130 dpi
    if n % 2 == 1 and n <= 25: return 843, 487 + (n - 1) // 2 * 41
    if n % 2 == 1: return 889, 503 + (n - 27) // 2 * 41
    if n <= 24: return 797, 503 + (n - 2) // 2 * 41
    return 935, 487 + (n - 26) // 2 * 41

SERVO_ROWS = [  # (connector, pin, function, pid or None, static text for X/Y/Z when pid is None)
    ("CNP1", "L1", "主電源 L1（單相）", "L1", None),
    ("CNP1", "L2", "單相時空接", None, "空接（手冊 3.3.1）"),
    ("CNP1", "L3", "主電源（單相接 L1 與 L3）", "L3", None),
    ("CNP1", "N- / P3 / P4", "P3-P4 出廠短接，不裝直流電抗器", None, "保持原狀"),
    ("CNP2", "P+ / D", "出廠短接，用內建再生電阻", None, "保持原狀"),
    ("CNP2", "L11", "控制電源 L11（接觸器之前）", "L11", None),
    ("CNP2", "L21", "控制電源 L21（接觸器之前）", "L21", None),
    ("CNP3", "U", "馬達 U", "U", None), ("CNP3", "V", "馬達 V", "V", None), ("CNP3", "W", "馬達 W", "W", None),
    ("PE", "PE ×2", "接地：盤面 PE 與馬達 PE", "MPE", None),
    ("CN1", "10", "PP 指令脈衝（差動）", "PP", None), ("CN1", "11", "PG 指令脈衝（差動）", "PG", None),
    ("CN1", "35", "NP 方向脈衝（差動）", "NP", None), ("CN1", "36", "NG 方向脈衝（差動）", "NG", None),
    ("CN1", "15", "SON 伺服 ON", "SON", None),
    ("CN1", "20 或 21", "DICOM 輸入共同端 +24V", "DICOM", None),
    ("CN1", "42", "EM2 緊急停止（對 0V 閉合＝可運轉）", "EM2", None),
    ("CN1", "46 或 47", "DOCOM 輸出共同端 0V", "DOCOM", None),
    ("CN1", "48", "ALM 報警（報警時斷開）", "ALM", None),
    ("CN1", "23", "MBR 煞車連鎖（Pr.PD24 設為 MBR）", "MBR", "不用"),
    ("CN1", "12", "OPC（開集極才用，差動不接）", None, "不接"),
    ("CN2", "—", "編碼器", "ENC", None),
    ("CN4", "—", "備份電池", "BAT", None),
    ("CN8", "—", "STO 短路接頭（原廠附，須插著）", None, "插著"),
    ("CN3 / CN5", "—", "RS-422 / USB（試機設定用）", None, "未接"),
]

def make_servo_card():
    axes = {a: next(b for b in B.S.blocks if b.ref == "SV" + a) for a in "XYZ"}
    motors = {a: "M" + a for a in "XYZ"}
    fig = plt.figure(figsize=(16.54, 11.69), dpi=110)
    fig.text(0.02, 0.965, "三菱 MR-J4-40A 伺服驅動器接線卡  代號 SVX / SVY / SVZ", fontsize=18, weight="bold", va="top")
    fig.text(0.02, 0.938, "零件接線卡　｜　單相 220V　｜　圖：三菱 MR-J4-A 使用說明書 SH-030107-V（第 3-29、9-3 頁）", fontsize=9.5, color="#444", va="top")
    # ---- figure A: front view + CN1 pin layout, with the pins we use marked
    ax = fig.add_axes([0.02, 0.43, 0.41, 0.49])
    pa = _page_png(112); ax.imshow(pa.crop((150, 215, 990, 1065))); ax.axis("off")
    ox, oy = 150, 215
    for n, c in ((10, "#e6007e"), (11, "#e6007e"), (35, "#e6007e"), (36, "#e6007e"), (15, "#00863d"), (20, "#c47a00"), (21, "#c47a00"),
                 (42, "#c40000"), (46, "#555"), (47, "#555"), (48, "#7a00a8"), (23, "#00a0a0")):
        x, y = _cn1_xy(n); ax.add_patch(plt.Circle((x - ox, y - oy), 17, fill=False, ec=c, lw=2.4))
    ax.add_patch(Rectangle((180 - ox, 560 - oy), 215, 120, fill=False, ec="#0060c0", lw=2.4)); ax.text(185 - ox, 722 - oy, "▲ 藍框＝CN2 編碼器", color="#0060c0", fontsize=9, weight="bold", va="bottom")
    ax.add_patch(Rectangle((510 - ox, 650 - oy), 95, 115, fill=False, ec="#8a6000", lw=2.4)); ax.text(430 - ox, 800 - oy, "▲ 褐框＝CN4 電池", color="#8a6000", fontsize=9, weight="bold", va="bottom")
    fig.text(0.02, 0.425, "圈起的 CN1 腳：粉紅＝脈衝 10/11/35/36　綠＝SON 15　橙＝DICOM 20/21　紅＝EM2 42\n灰＝DOCOM 46/47　紫＝ALM 48　青＝MBR 23（僅 Z 軸）", fontsize=7.8, color="#333", va="top", linespacing=1.5)
    # ---- figure B: power connector pin list
    bx = fig.add_axes([0.02, 0.085, 0.17, 0.30])
    pb = _page_png(374); bx.imshow(pb.crop((100, 815, 520, 1240))); bx.axis("off")
    ox2, oy2 = 100, 815
    for name, y, c in (("L1", 860, "#8a3c00"), ("L3", 901, "#0000dc"), ("L11", 1068, "#8a3c00"), ("L21", 1088, "#0000dc"),
                       ("U", 1128, "#c83200"), ("V", 1148, "#000"), ("W", 1168, "#6e6e6e")):
        bx.add_patch(Rectangle((128 - ox2, y - 11 - oy2), 32, 22, fill=False, ec=c, lw=2.2))
    for y in (1005, 1046): bx.add_patch(Rectangle((128 - ox2, y - 11 - oy2), 32, 22, fill=False, ec="#999", lw=1.6, ls="--"))
    for x in (144, 176): bx.add_patch(Rectangle((x - 17 - ox2, 1213 - 14 - oy2), 34, 28, fill=False, ec="#008800", lw=2.2))
    fig.text(0.02, 0.083, "實線＝要接線；虛線＝出廠短接，保持原狀；PE 兩個螺絲都可接地", fontsize=7.8, color="#333", va="top")
    # ---- notes next to figure B
    notes = [
        ("安裝與接線（手冊 9-3、3.3.3、11.9）", True),
        ("- 外形 寬 40 × 高 168 mm，M5 螺絲 ×2，孔距 156±0.5 mm，重 1.0 kg。", False),
        ("- 電源接頭 CNP1/2/3 要拔下來再接線；每個孔只插 1 條線或 1 個端子。", False),
        ("- 線徑：L1/L3 2 mm²（AWG14）；L11/L21 1.25～2 mm²；U/V/W AWG18～14。", False),
        ("- 剝線 9 mm，開孔工具 JST J-FAT-OT；CN1 屏蔽層接到接地板並固定在接頭外殼。", False),
        ("- 脈衝線 PP/PG、NP/NG 各一對屏蔽雙絞線，長度 10 m 以內（手冊 3.9.2）。", False),
        ("試機要設的參數（名稱依手冊）", True),
        ("- PA13：指令脈衝形式與邏輯（對照 IFB1 輸出極性）。", False),
        ("- PA06 / PA07：電子齒輪 CMX/CDV = 4194304 ÷ 5000 = 524288/625，", False),
        ("  使 5,000 脈衝 = 馬達 1 轉（22 位元編碼器 4194304 脈衝/轉）。", False),
        ("  CMX/CDV 的允許範圍：1/10 < CMX/CDV < 4000。", False),
        ("- PD24：把 CN1-23 設成 MBR（Z 軸）；PC16：煞車動作延遲。", False),
        ("- PA03：加電池並要用絕對位置時才設定；grblHAL 不支援 ABS 傳送，暫不啟用。", False),
    ]
    y = 0.375
    for t, hdr in notes:
        fig.text(0.205, y, t, fontsize=9.8 if hdr else 8.2, weight="bold" if hdr else None, va="top"); y -= 0.0235 if hdr else 0.0195
    # ---- table
    tx = 0.455; cx = [tx, tx + 0.052, tx + 0.205, tx + 0.232, tx + 0.325, tx + 0.418]
    top = 0.925
    hx = [cx[0], cx[1], cx[1] + 0.045, cx[3], cx[4], cx[5]]
    for i, h in enumerate(("接頭", "腳位", "功能", "X 軸 (SVX) 接到", "Y 軸 (SVY) 接到", "Z 軸 (SVZ) 接到")):
        fig.text(hx[i], top, h, fontsize=8.8, weight="bold", va="top")
    # shift header for 'function' column
    y = top - 0.026
    fig.add_artist(plt.Line2D([tx - 0.004, 0.985], [y + 0.004, y + 0.004], color="#888", lw=0.8))
    rh = 0.0207; last = None
    for conn, pin, fn, pid, static in SERVO_ROWS:
        if conn != last:
            y -= 0.003; last = conn
        fig.text(cx[0], y, conn, fontsize=8, weight="bold", va="top"); fig.text(cx[1], y, pin, fontsize=7.8, va="top")
        # function text placed in its own column (between pin and X) -> compact layout: put function under pin column width
        fig.text(cx[1] + 0.045, y, fn, fontsize=7.6, va="top")
        col = None
        for k, a in enumerate("XYZ"):
            blk = axes[a]
            if pid and pid in blk.pins and getattr(blk.pins[pid], "net", None):
                if pid == "MPE":
                    txt = "%s[PE]、盤面 PE" % motors[a]
                else:
                    txt = dests(blk, blk.pins[pid], limit=3)
                col = col or wirecolor.get(blk.pins[pid].net)
            else:
                txt = static or "不用"
            fig.text(cx[3 + k] + 0.0, y, txt, fontsize=7.6, va="top")
        y -= rh
    legend = "零件代號：" + "；".join("%s＝%s" % (disp(b), b.title.split(" ", 1)[1] if " " in b.title else b.title)
                                       for b in sorted(USED, key=lambda b: disp(b)))
    fig.text(tx, 0.285, textwrap.fill(legend, 100), fontsize=7.6, color="#333", va="top", linespacing=1.3)
    chk = [("上電前檢查（手冊 3.3、4.1.2、11.8）", True),
           ("- L1/L3 接單相電源、L2 空接；L11/L21 有電；P3-P4 與 P+/D 的出廠短接片還在。", False),
           ("- DICOM 接 +24V、DOCOM 接 0V、EM2 對 0V 閉合；CN8 的 STO 短路接頭插著。", False),
           ("- 上電後正常時 ALM 約 2.5～3.5 秒後導通；報警時 ALM 斷開。", False),
           ("- 換電池只在控制電源開著時做（斷電換會丟絕對位置）；換前先關主電源並等 15 分鐘到 CHARGE 燈熄滅。", False)]
    yy = 0.205
    for t, hdr in chk:
        fig.text(tx, yy, t, fontsize=9.6 if hdr else 8.2, weight="bold" if hdr else None, va="top"); yy -= 0.024 if hdr else 0.0195
    fig.text(tx, 0.03, "※ 「接到」欄來自配線圖（CNC_wiring.kicad_sch）的網表。腳位與參數來自手冊；馬達線與編碼器線為原廠現成線，不另畫。", fontsize=8, color="#a00", va="bottom")
    out = os.path.join(HERE, "cards"); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "SERVO_card.pdf")); fig.savefig(os.path.join(out, "SERVO_card.png"), dpi=110)
    plt.close(fig); print("wrote", os.path.join(out, "SERVO_card.pdf"))

if __name__ == "__main__" and (len(sys.argv) == 1 or "SERVO" in sys.argv[1:]):
    make_servo_card()
