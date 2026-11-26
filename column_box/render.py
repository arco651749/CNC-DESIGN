# -*- coding: utf-8 -*-
"""Preview PNGs from mesh.json (painter's algorithm).  python3 column_box/render.py"""
import json, math, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, 'mesh.json')))
HIDE = ('Box_front_cover', 'Box_bottom_cover', 'Box_side_R', 'Louvre_filter')
COL = {'enclosure': (0.78, 0.8, 0.83), 'DIN': (0.55, 0.55, 0.6), 'parts (vendor': (0.25, 0.27, 0.3), 'parts (box': (0.9, 0.55, 0.2), 'reserved': (0.8, 0.8, 0.8), 'fasteners': (0.95, 0.8, 0.1)}
NAMECOL = {'PSU': (0.25, 0.7, 0.3), 'VFD': (1, 0.5, 0.45), 'PC': (0.6, 0.4, 0.95), 'KM1': (0.35, 0.6, 1), 'RCD': (0.9, 0.7, 0.2), 'QF': (0.9, 0.7, 0.2), 'Fan': (0.4, 0.4, 0.45), 'BD': (0.1, 0.5, 0.3)}
def color(m):
    for k, c in NAMECOL.items():
        if m['n'].startswith(k): return c
    for k, c in COL.items():
        if m['g'].startswith(k): return c
    return (0.7, 0.7, 0.7)
def render(az, el, out, title, xlim=None):
    a, e = math.radians(az), math.radians(el)
    # camera direction (from the scene towards the camera)
    d = np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)])
    r = np.cross([0, 0, 1], d); r /= np.linalg.norm(r); u = np.cross(d, r)
    polys, cols, depth = [], [], []
    L_ = np.array([0.4, -0.5, 0.75]); L_ /= np.linalg.norm(L_)
    for m in M:
        if m['n'] in HIDE: continue
        P = np.array(m['p']); T = np.array(m['t'])
        if not len(T): continue
        A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
        N = np.cross(B - A, C - A); n = np.linalg.norm(N, axis=1); n[n == 0] = 1; N = N / n[:, None]
        sh = 0.45 + 0.55 * np.abs(N @ L_)
        base = np.array(color(m))
        cen = (A + B + C) / 3; dep = cen @ d
        xy = np.stack([np.stack([A @ r, A @ u], 1), np.stack([B @ r, B @ u], 1), np.stack([C @ r, C @ u], 1)], 1)
        polys.append(xy); cols.append(np.clip(base[None] * sh[:, None], 0, 1)); depth.append(dep)
    polys = np.concatenate(polys); cols = np.concatenate(cols); depth = np.concatenate(depth)
    o = np.argsort(depth)
    fig, ax = plt.subplots(figsize=(15, 9), dpi=110)
    ax.add_collection(PolyCollection(polys[o], facecolors=cols[o], edgecolors='none', linewidths=0))
    ax.autoscale_view(); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(title, fontsize=14)
    ax.set_xlim(polys[:, :, 0].min() - 10, polys[:, :, 0].max() + 10); ax.set_ylim(polys[:, :, 1].min() - 10, polys[:, :, 1].max() + 10)
    fig.savefig(out, bbox_inches='tight'); plt.close(fig)
render(35, -28, os.path.join(HERE, 'column_box_3d_below.png'), 'Column box 3D - from front-right below (front cover, bottom cover, right wall hidden)')
render(-30, 25, os.path.join(HERE, 'column_box_3d_above.png'), 'Column box 3D - from front-left above (same parts hidden)')
print('ok')
