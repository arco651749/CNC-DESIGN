"""Tiny KiCad 7 schematic generator: block symbols, wires, labels, junctions + sanity checks."""
import uuid, math, unicodedata, os
FONT = os.environ.get("WIRING_FONT", "WenQuanYi Zen Hei")
U, R = 2.54, 5.08
NS = uuid.UUID("6f1d0000-0000-4000-8000-000000000001")
_c = [0]
def uid():
    _c[0] += 1
    return str(uuid.uuid5(NS, str(_c[0])))
def q(s): return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
def f(v): return ("%.4f" % v).rstrip("0").rstrip(".")
def tw(s): return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)
def eff(size=1.27, bold=False, just=None, hide=False):
    s = "(effects (font (face %s) (size %s %s)%s)" % (q(FONT), f(size), f(size), " bold" if bold else "")
    if just: s += " (justify %s)" % just
    if hide: s += " hide"
    return s + ")"

class Pin:
    def __init__(s, blk, pid, side, x, y, label):
        s.blk, s.pid, s.side, s.x, s.y, s.label = blk, pid, side, round(x, 4), round(y, 4), label
    def __repr__(s): return "%s.%s" % (s.blk.ref, s.pid)

class Block:
    def __init__(s, ref, title, cx, top, left=(), right=(), topp=(), bottom=(), w=None, minh=15.24, tmode=None):
        s.ref, s.title, s.cx, s.top = ref, title, cx, top
        s.tmode = tmode
        s.spec = dict(left=[], right=[], top=[], bottom=[])
        def norm(it): return (it[0], it[1], it[2] if len(it) > 2 else it[0])
        for k, v in (("left", left), ("right", right), ("top", topp), ("bottom", bottom)):
            s.spec[k] = [norm(i) for i in v]
        lm = max([tw(i[2]) for i in s.spec["left"]] or [0]); rm = max([tw(i[2]) for i in s.spec["right"]] or [0])
        tm = max([tw(i[2]) for i in s.spec["top"]] or [0]); bm = max([tw(i[2]) for i in s.spec["bottom"]] or [0])
        if w is None:
            w = max(10.16, math.ceil(((lm + rm) * 1.35 + 5) / R) * R)
        s.w = w
        rows = [i[1] for i in s.spec["left"] + s.spec["right"]] or [0]
        h = (max(rows) + 1) * R
        if s.spec["top"] or s.spec["bottom"]:
            h = max(h, math.ceil(((tm + bm) * 1.35 + 4) / R) * R)
        s.h = max(h, minh)
        s.cy = top + s.h / 2
        s.pins = {}
        def add(side, pid, x, y, label):
            assert pid not in s.pins, (ref, pid)
            s.pins[pid] = Pin(s, pid, side, x, y, label)
        for pid, r, lab in s.spec["left"]: add("left", pid, cx - w / 2 - R, top + r * R, lab)
        for pid, r, lab in s.spec["right"]: add("right", pid, cx + w / 2 + R, top + r * R, lab)
        for pid, o, lab in s.spec["top"]: add("top", pid, cx + o, top - R, lab)
        for pid, o, lab in s.spec["bottom"]: add("bottom", pid, cx + o, top + s.h + R, lab)
    def __getitem__(s, k): return s.pins[k]
    @property
    def bbox(s): return (s.cx - s.w / 2, s.top, s.cx + s.w / 2, s.top + s.h)
    def lib(s):
        w, h = s.w, s.h
        o = ['(symbol %s (pin_numbers hide) (pin_names (offset 1.016)) (in_bom no) (on_board no)' % q("BLK:" + s.ref)]
        for k, v in (("Reference", s.ref), ("Value", s.title), ("Footprint", ""), ("Datasheet", "")):
            o.append('  (property %s %s (at 0 0 0) (effects (font (size 1.27 1.27)) hide))' % (q(k), q(v)))
        o.append('  (symbol %s (rectangle (start %s %s) (end %s %s) (stroke (width 0.3) (type default)) (fill (type background))))' % (
            q(s.ref + "_0_1"), f(-w / 2), f(h / 2), f(w / 2), f(-h / 2)))
        o.append('  (symbol %s' % q(s.ref + "_1_1"))
        n = 0
        for p in s.pins.values():
            n += 1
            lx, ly = p.x - s.cx, s.cy - p.y
            ang = {"left": 0, "right": 180, "top": 270, "bottom": 90}[p.side]
            o.append('    (pin passive line (at %s %s %d) (length %s) (name %s %s) (number %s %s))' % (
                f(lx), f(ly), ang, f(R), q(p.label), eff(1.27), q(str(n)), eff(1.0)))
        o.append('  )')
        o.append(')')
        return "\n".join(o)
    def inst(s, root):
        has_top = bool(s.spec["top"]) if s.tmode is None else (s.tmode == "inside")
        if has_top:
            tx, ty = s.cx - s.w / 2 + 0.8, s.top + 2.0
        else:
            tx, ty = s.cx - s.w / 2, s.top - 1.2
        rd = s.ref if s.ref[-1].isdigit() else s.ref + "1"
        o = ['(symbol (lib_id %s) (at %s %s 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid %s)' % (q("BLK:" + s.ref), f(s.cx), f(s.cy), uid())]
        o.append('  (property "Reference" %s (at %s %s 0) %s)' % (q(rd), f(tx), f(ty), eff(1.4, True, "left bottom", hide=True)))
        o.append('  (property "Value" %s (at %s %s 0) %s)' % (q(s.title), f(tx), f(ty), eff(1.5, True, "left bottom")))
        o.append('  (property "Footprint" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))' % (f(s.cx), f(s.cy)))
        o.append('  (property "Datasheet" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))' % (f(s.cx), f(s.cy)))
        for i in range(len(s.pins)): o.append('  (pin %s (uuid %s))' % (q(str(i + 1)), uid()))
        o.append('  (instances (project "CNC_wiring" (path "/%s" (reference %s) (unit 1))))' % (root, q(rd)))
        o.append(')')
        return "\n".join(o)

class Sheet:
    def __init__(s, paper="A1"):
        s.paper = paper; s.blocks = []; s.wires = []; s.labels = []; s.texts = []; s.frames = []; s.junctions = []
        s.root = str(uuid.uuid5(NS, "root"))
    def add(s, b): s.blocks.append(b); return b
    def seg(s, net, color, width, x1, y1, x2, y2):
        x1, y1, x2, y2 = [round(v, 4) for v in (x1, y1, x2, y2)]
        if (x1, y1) == (x2, y2): return
        s.wires.append(dict(net=net, color=color, width=width, p=(x1, y1, x2, y2)))
    def poly(s, net, color, width, pts):
        for a, b in zip(pts, pts[1:]): s.seg(net, color, width, a[0], a[1], b[0], b[1])
    def conn(s, net, color, pins, lane=None, width=0.254, label=None):
        pins = list(pins)
        if len(pins) == 2:
            a, b = pins
            if a.y == b.y and a.side in ("left", "right") and b.side in ("left", "right"):
                s.seg(net, color, width, a.x, a.y, b.x, b.y); s.pin_net(net, pins); return
            if a.x == b.x and a.side in ("top", "bottom") and b.side in ("top", "bottom"):
                s.seg(net, color, width, a.x, a.y, b.x, b.y); s.pin_net(net, pins); return
        if all(p.side in ("left", "right") for p in pins):
            ys = [p.y for p in pins]
            for p in pins: s.seg(net, color, width, p.x, p.y, lane, p.y)
            s.seg(net, color, width, lane, min(ys), lane, max(ys))
        elif all(p.side in ("top", "bottom") for p in pins):
            xs = [p.x for p in pins]
            for p in pins: s.seg(net, color, width, p.x, p.y, p.x, lane)
            s.seg(net, color, width, min(xs), lane, max(xs), lane)
        else:
            raise ValueError("mixed sides " + str(pins))
        s.pin_net(net, pins)
        if label: s.label(net, label, lane if pins[0].side in ("left", "right") else min(p.x for p in pins), min(p.y for p in pins) if pins[0].side in ("left", "right") else lane, 0)
    def L(s, net, color, pa, pb, width=0.254):
        """L-shaped route: pa top/bottom pin -> pb left/right pin."""
        s.seg(net, color, width, pa.x, pa.y, pa.x, pb.y); s.seg(net, color, width, pa.x, pb.y, pb.x, pb.y); s.pin_net(net, [pa, pb])
    def pin_net(s, net, pins):
        for p in pins:
            if getattr(p, "net", None) not in (None, net): raise ValueError("pin %s on two nets %s %s" % (p, p.net, net))
            p.net = net
    def stub(s, pin, label, color, length=R, width=0.254, justify_override=None):
        dx, dy, ang = {"left": (-1, 0, 180), "right": (1, 0, 0), "top": (0, -1, 90), "bottom": (0, 1, 270)}[pin.side]
        ex, ey = pin.x + dx * length, pin.y + dy * length
        s.seg(label, color, width, pin.x, pin.y, ex, ey)
        s.label(label, label, ex, ey, ang)
        s.pin_net(label, [pin])
    def label(s, net, text, x, y, ang):
        s.labels.append(dict(net=net, text=text, p=(round(x, 4), round(y, 4)), ang=ang))
    def text(s, t, x, y, size=1.6, bold=False, color=None):
        s.texts.append(dict(t=t, p=(x, y), size=size, bold=bold))
    def frame(s, x1, y1, x2, y2, name=None):
        s.frames.append((x1, y1, x2, y2, name))
    # ---------- checks ----------
    def split_wires(s):
        """Split a wire wherever another same-net wire ends on its interior, so every T becomes endpoint-to-endpoint."""
        bynet = {}
        for w in s.wires: bynet.setdefault(w["net"], []).append(w)
        out = []
        for net, ws in bynet.items():
            ends = set()
            for w in ws:
                a, b, c, d = w["p"]; ends.add((a, b)); ends.add((c, d))
            for w in ws:
                a, b, c, d = w["p"]
                cuts = [P for P in ends if P not in ((a, b), (c, d)) and on_seg(P, w["p"])]
                if not cuts: out.append(w); continue
                if a == c: cuts.sort(key=lambda P: P[1], reverse=(d < b))
                else: cuts.sort(key=lambda P: P[0], reverse=(c < a))
                pts = [(a, b)] + cuts + [(c, d)]
                for P, Q in zip(pts, pts[1:]):
                    out.append(dict(net=net, color=w["color"], width=w["width"], p=(P[0], P[1], Q[0], Q[1])))
        s.wires = out
    def junctions_auto(s):
        pts = {}
        bynet = {}
        for w in s.wires: bynet.setdefault(w["net"], []).append(w["p"])
        J = set()
        for net, segs in bynet.items():
            cand = set()
            for (a, b, c, d) in segs: cand.add((a, b)); cand.add((c, d))
            for P in cand:
                ends = interior = 0
                for (a, b, c, d) in segs:
                    if (a, b) == P or (c, d) == P: ends += 1
                    elif on_seg(P, (a, b, c, d)): interior += 1
                if (interior >= 1 and ends >= 1) or ends >= 3: J.add(P)
        s.junctions = sorted(J)
    def verify(s):
        errs = []
        W = s.wires
        for i in range(len(W)):
            for j in range(i + 1, len(W)):
                a, b = W[i], W[j]
                if a["net"] == b["net"]: continue
                r = seg_conflict(a["p"], b["p"])
                if r: errs.append("%s <-> %s : %s %s %s" % (a["net"], b["net"], r, a["p"], b["p"]))
        pinpts = {}
        for b in s.blocks:
            for p in b.pins.values(): pinpts[(p.x, p.y)] = p
        for (px, py), p in pinpts.items():
            for w in W:
                if on_seg((px, py), w["p"]) and w["net"] != getattr(p, "net", None):
                    errs.append("pin %s touched by wire of net %s" % (p, w["net"]))
        for l in s.labels:
            hit = [w["net"] for w in W if on_seg(l["p"], w["p"])]
            if l["net"] not in hit: errs.append("label %s at %s not on its net wire (hit %s)" % (l["text"], l["p"], hit))
            elif set(hit) != {l["net"]}: errs.append("label %s touches other nets %s" % (l["text"], hit))
        for w in W:
            x1, y1, x2, y2 = w["p"]
            for b in s.blocks:
                bx1, by1, bx2, by2 = b.bbox
                bx1 += .3; by1 += .3; bx2 -= .3; by2 -= .3
                if x1 == x2 and bx1 < x1 < bx2 and not (max(y1, y2) <= by1 or min(y1, y2) >= by2): errs.append("wire %s passes through block %s" % (w["net"], b.ref))
                if y1 == y2 and by1 < y1 < by2 and not (max(x1, x2) <= bx1 or min(x1, x2) >= bx2): errs.append("wire %s passes through block %s" % (w["net"], b.ref))
        return errs
    # ---------- output ----------
    def write(s, path, title, comments=()):
        s.split_wires()
        s.junctions_auto()
        o = ['(kicad_sch (version 20230121) (generator eeschema)', '  (uuid %s)' % s.root, '  (paper %s)' % q(s.paper)]
        o.append('  (title_block (title %s) (date "2026-11-13") (rev "A") (company "CNC-DESIGN")%s)' % (q(title), "".join(' (comment %d %s)' % (i + 1, q(c)) for i, c in enumerate(comments))))
        o.append('  (lib_symbols')
        for b in s.blocks: o.append(b.lib())
        o.append('  )')
        for (x1, y1, x2, y2, name) in s.frames:
            o.append('  (polyline (pts (xy %s %s) (xy %s %s) (xy %s %s) (xy %s %s) (xy %s %s)) (stroke (width 0.2) (type dash) (color 120 120 120 1)) (uuid %s))' % (
                f(x1), f(y1), f(x2), f(y1), f(x2), f(y2), f(x1), f(y2), f(x1), f(y1), uid()))
            if name: o.append('  (text %s (at %s %s 0) %s (uuid %s))' % (q(name), f(x1 + 2), f(y1 + 4.2), eff(2.4, True, "left bottom"), uid()))
        for w in s.wires:
            r, g, b = w["color"]
            x1, y1, x2, y2 = w["p"]
            o.append('  (wire (pts (xy %s %s) (xy %s %s)) (stroke (width %s) (type default) (color %d %d %d 1)) (uuid %s))' % (f(x1), f(y1), f(x2), f(y2), f(w["width"]), r, g, b, uid()))
        for (x, y) in s.junctions:
            o.append('  (junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid %s))' % (f(x), f(y), uid()))
        for l in s.labels:
            just = {0: "left bottom", 90: "left bottom", 180: "right bottom", 270: "right bottom"}[l["ang"]]
            o.append('  (label %s (at %s %s %d) %s (uuid %s))' % (q(l["text"]), f(l["p"][0]), f(l["p"][1]), l["ang"], eff(1.27, False, just), uid()))
        for t in s.texts:
            o.append('  (text %s (at %s %s 0) %s (uuid %s))' % (q(t["t"]), f(t["p"][0]), f(t["p"][1]), eff(t["size"], t["bold"], "left top"), uid()))
        for b in s.blocks: o.append(b.inst(s.root))
        o.append('  (sheet_instances (path "/" (page "1")))')
        o.append(')')
        open(path, "w", encoding="utf-8").write("\n".join(o) + "\n")

def on_seg(P, S):
    x, y = P; a, b, c, d = S
    if a == c: return abs(x - a) < 1e-6 and min(b, d) - 1e-6 <= y <= max(b, d) + 1e-6
    if b == d: return abs(y - b) < 1e-6 and min(a, c) - 1e-6 <= x <= max(a, c) + 1e-6
    return False
def seg_conflict(A, B):
    for P in ((A[0], A[1]), (A[2], A[3])):
        if on_seg(P, B): return "endpoint-on-wire"
    for P in ((B[0], B[1]), (B[2], B[3])):
        if on_seg(P, A): return "endpoint-on-wire"
    # collinear overlap
    if A[0] == A[2] and B[0] == B[2] and A[0] == B[0]:
        if min(max(A[1], A[3]), max(B[1], B[3])) - max(min(A[1], A[3]), min(B[1], B[3])) > 1e-6: return "overlap"
    if A[1] == A[3] and B[1] == B[3] and A[1] == B[1]:
        if min(max(A[0], A[2]), max(B[0], B[2])) - max(min(A[0], A[2]), min(B[0], B[2])) > 1e-6: return "overlap"
    return None
