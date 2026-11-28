"""Concept sketch (owner 2026-11-28): open sheet-metal guide on the X carriage, conduits visible.
Run: python3 docs/sketches/x_carriage_open_route.py -> docs/sketches/x_carriage_open_route.png"""
import math, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'; plt.rcParams['axes.unicode_minus'] = False
def boxf(ax, x0, x1, y0, y1, z0, z1, c, a=0.25):
    v = np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]])
    f = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]
    ax.add_collection3d(Poly3DCollection([v[i] for i in f], facecolors=c, edgecolors='k', linewidths=0.3, alpha=a))
def arc(c, r, a0, a1, plane, n=20):
    out = []
    for k in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * k / n); u, w = r * math.cos(t), r * math.sin(t)
        out.append((c[0] + u, c[1], c[2] + w) if plane == 'xz' else (c[0], c[1] + u, c[2] + w))
    return out
def run(x, dz, end_y, top):            # PA-29 (x 110) / PA-17 (x 70): horizontal end -> up -> forward over the saddle -> down
    R = 60
    p = [(x + 60 + 40, 230, 522 + dz)] + arc((x, 230, 522 + dz + R), R, -90, -180, 'xz')[::-1][::-1]
    p = [(x + R + 40, 230, 522 + dz)] + [(x + R * math.cos(math.radians(t)), 230, 522 + dz + R + R * math.sin(math.radians(t))) for t in np.linspace(-90, -180, 20)]
    p += [(x, 230, top - R)] + [(x, 230 - R + R * math.cos(math.radians(t)), top - R + R * math.sin(math.radians(t))) for t in np.linspace(0, 90, 20)]
    p += [(x, end_y + R, top)] + [(x, end_y + R + R * math.cos(math.radians(t)), top - R + R * math.sin(math.radians(t))) for t in np.linspace(90, 180, 20)]
    p += [(x, end_y, top - R - 20)]
    return np.array(p)
fig = plt.figure(figsize=(12, 7.5)); ax = fig.add_subplot(111, projection='3d')
boxf(ax, -142, 142, 122, 134, 500, 706, '#8fb3d9')                  # saddle (upper part)
boxf(ax, -30, 30, 49, 120, 671, 836, '#333333', 0.6)                # Z motor
boxf(ax, -60, 60, 44, 134, 663, 701, '#8fb3d9')                     # Z motor plate
boxf(ax, -90, 90, 34, 62, 470, 572, '#c9d6e3', 0.15)                # Z slide (top at Z +50)
boxf(ax, -200, 300, 120, 300, 474, 494, '#bbbbbb', 0.12)            # box top plate (part)
# side plate (sheet metal, x 127..130) following the conduit, flanges to the saddle faces, foot tab under the loop end
side = [(130, 255, 500), (130, 255, 800), (130, 20, 800), (130, 20, 700), (130, 122, 700), (130, 122, 560), (130, 137, 560), (130, 137, 500)]
ax.add_collection3d(Poly3DCollection([side], facecolors='#d9a441', edgecolors='k', linewidths=0.6, alpha=0.55))
boxf(ax, 127, 190, 205, 255, 500, 503, '#d9a441', 0.7)              # foot tab carrying the loop-end clamps
a = run(110, 0, 40, 770); b = run(75, 32, 95, 805)
ax.plot(*a.T, color='k', lw=9, solid_capstyle='round'); ax.plot(*b.T, color='#444', lw=6, solid_capstyle='round')
ax.plot([110, 110], [40, 40], [690, 520], color='k', lw=9)          # Z run continues down to the tool head (hanging U)
for p, t in (((175, 230, 522), '固定座 1（滾動環活動端）'), ((110, 230, 640), '固定座 2'), ((110, 150, 770), '固定座 3'), ((110, 40, 690), '固定座 4（Z 段上端）'),
             ((75, 95, 735), 'PA-17 → Z 馬達（PAQ-1716 + 小支架）')):
    ax.scatter(*p, color='#c0392b', s=40); ax.text(p[0] + 8, p[1], p[2] + 8, t, fontsize=9)
ax.text(140, 260, 805, '側板（SPHC t3 雷射切割，沿浪管外形）', fontsize=9, color='#7a5200')
ax.text(-30, 85, 845, 'Z 馬達', fontsize=9); ax.text(-140, 128, 520, 'X 滑座', fontsize=9)
ax.text(200, 230, 540, '← 頂板滾動環 PA-29 + PA-17（兩條並行）', fontsize=9)
ax.set_xlim(-150, 250); ax.set_ylim(0, 300); ax.set_zlim(480, 860); ax.set_box_aspect((400, 300, 380))
ax.view_init(22, -60); ax.set_xlabel('x'); ax.set_ylabel('y'); ax.set_zlabel('z')
ax.set_title('X 滑座：外露浪管 + 鈑金側板（概念簡圖）\n黑：PA-29（主軸、相機、探針、氣管）  灰：PA-17（Z 馬達）  紅點：浪管固定座', fontsize=11)
plt.tight_layout(); plt.savefig(__file__.replace('.py', '.png'), dpi=130)
