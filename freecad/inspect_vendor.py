# -*- coding: utf-8 -*-
"""Print bounding boxes (global + per solid) of every vendor STEP, to plan placement."""
import os, glob
import Part

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor")
for f in sorted(glob.glob(os.path.join(ROOT, "**", "*.st*p"), recursive=True)):
    s = Part.read(f)
    b = s.BoundBox
    name = os.path.basename(os.path.dirname(os.path.dirname(f)))
    print("== %s  X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]  solids=%d" %
          (name, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, len(s.Solids)))
    for i, so in enumerate(s.Solids):
        c = so.BoundBox
        print("   s%d X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f] vol=%.0f" %
              (i, c.XMin, c.XMax, c.YMin, c.YMax, c.ZMin, c.ZMax, so.Volume))
