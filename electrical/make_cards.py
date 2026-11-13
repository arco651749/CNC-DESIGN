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
from matplotlib.patches import Rectangle
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
def short(b): return "%s %s" % (b.ref, b.title.split(" ", 1)[1] if " " in b.title else b.title)
USED = set()
def dests(blk, pin, limit=5):
    others = [(b, p) for (b, p) in nets[pin.net] if not (b is blk and p is pin)]
    if not others: return "（本機內部）"
    for b, _ in others[:limit]: USED.add(b)
    txt = "、".join("%s[%s]" % (b.ref, p.label.replace("−", "-")) for b, p in others[:limit])
    if len(others) > limit: txt += " …共 %d 點" % (len(others))
    return txt

# ---- part definitions ---------------------------------------------------------------------
PARTS = {}
PARTS["BD"] = dict(
    title="RP23CNC V2.02 控制板（grblHAL）  代號 BD",
    image=os.path.join(HERE, "..", "output", "electronics", "RP23CNC_top.png"),
    crop=(120, 20, 1195, 1080),
    image_note="圖：廠商 STEP 3D 模型的俯視渲染（KiCad 匯出），不是照片。端子左右順序以板上絲印為準。",
    zones={  # letter: (x0, y0, x1, y1, name) in original image pixels
        "A": (242, 37, 1072, 112, "上排螺絲端子（22 位）"),
        "B": (242, 988, 1072, 1062, "下排螺絲端子（22 位）"),
        "C": (1093, 175, 1170, 930, "右排螺絲端子（20 位）"),
        "D": (738, 858, 822, 918, "伺服報警輸入排針（2×3，2.54 mm）"),
        "E": (403, 205, 567, 452, "WIZ850io 乙太網路模組座（選配，必須是 W5500）"),
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
    # ---- image with zone overlays
    im = Image.open(P["image"]).convert("RGB")
    x0, y0, x1, y1 = P["crop"]
    ax = fig.add_axes([0.02, 0.42, 0.40, 0.50]); ax.imshow(im.crop(P["crop"])); ax.axis("off")
    for letter, (a, b, c, d, name) in P["zones"].items():
        ax.add_patch(Rectangle((a - x0, b - y0), c - a, d - b, fill=False, ec="#e6007e", lw=2.2))
        ax.text(a - x0 - 4, b - y0 - 4, letter, color="white", fontsize=12, weight="bold", ha="right", va="bottom",
                bbox=dict(boxstyle="circle,pad=0.25", fc="#e6007e", ec="none"))
    fig.text(0.02, 0.405, P["image_note"], fontsize=8, color="#555", va="top")
    # zone legend
    yy = 0.375
    fig.text(0.02, yy, "圖中標示的區域", fontsize=10.5, weight="bold", va="top"); yy -= 0.022
    for letter, (a, b, c, d, name) in P["zones"].items():
        fig.text(0.02, yy, " %s " % letter, fontsize=9, color="white", weight="bold", va="top", bbox=dict(boxstyle="circle,pad=0.2", fc="#e6007e", ec="none"))
        fig.text(0.04, yy, name, fontsize=9, va="top"); yy -= 0.021
    yy -= 0.01
    for i, line in enumerate(P["setup"]):
        wrapped = textwrap.fill(line, 50) if i else line
        fig.text(0.02, yy, wrapped, fontsize=10.5 if i == 0 else 8.4, weight="bold" if i == 0 else None, va="top", linespacing=1.25)
        yy -= 0.0165 * (wrapped.count("\n") + 1) + (0.006 if i else 0.008)
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
    legend = "零件代號：" + "；".join("%s＝%s" % (b.ref, b.title.split(" ", 1)[1] if " " in b.title else b.title)
                                       for b in sorted(USED, key=lambda b: b.ref))
    fig.text(tx, 0.085, textwrap.fill(legend, 100), fontsize=7.8, color="#333", va="top", linespacing=1.3)
    out = os.path.join(HERE, "cards"); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "%s_card.pdf" % ref)); fig.savefig(os.path.join(out, "%s_card.png" % ref), dpi=110)
    plt.close(fig)
    print("wrote", os.path.join(out, "%s_card.pdf" % ref), "rows", len(rows))

if __name__ == "__main__":
    for ref in (sys.argv[1:] or PARTS): make_card(ref)
