# -*- coding: utf-8 -*-
"""Basler dart R daA2448-70uc (CS-Mount) as a STEP, built from Basler's official dimension drawing
(docs.baslerweb.com/daa2448-70uc, images/drawing-dart-classic-usb-cs-mount-dimensions.svg; copies in vendor/basler/daA2448-70uc/).
Basler's own STEP sits behind www.baslerweb.com, which refuses automated downloads; replace this file with it when available.
Camera frame: optical axis +Z, z = 0 at the front face of the CS-mount ring (lens flange), camera body toward -Z.
  CS-mount ring    D28.3 x 5.5          z -5.5 .. 0     lens thread 1"-32 UN (D25.4)
  housing          29 x 29, corners R1   z -14.4 .. -5.5  front face: 4 x M2 (D2.2, max 3.2 deep) on 22.4 x 22.4
  board            28.3 x 27            z -17.4 .. -14.4 (incl. parts), 4 x D2.08 on 22.4
  I/O connector    top, out to z -19.4;  USB 3.0 Micro-B on +X, 1.4 past the board edge
  sensor plane     z -12.5 (CS-mount flange focal distance), Sony IMX548 1/1.8", 6.71 x 5.61 mm
Run:  freecadcmd freecad/v12/11_camera_daA2448_model.py   Out: vendor/basler/daA2448-70uc/daA2448-70uc_CS_from_drawing.step"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V
ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
OUT = os.path.join(ROOT, 'vendor', 'basler', 'daA2448-70uc', 'daA2448-70uc_CS_from_drawing.step')
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def zcyl(r, z0, z1, x=0, y=0): return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))
house = box(-14.5, 14.5, -14.5, 14.5, -14.4, -5.5)
house = house.makeFillet(1.0, [e for e in house.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[-1].Point.z) > 1])
ring = zcyl(14.15, -5.5, 0).cut(zcyl(12.7, -5.5, 0))              # CS-mount ring, 1"-32 thread bore D25.4
body = house.fuse(ring).cut(zcyl(11.0, -11.5, -5.5))               # light path to the sensor window
for sx in (-1, 1):
    for sy in (-1, 1):
        body = body.cut(zcyl(1.1, -5.5 - 3.2, -5.5, 11.2 * sx, 11.2 * sy))   # 4 x M2, max 3.2 deep
sensor = box(-3.355, 3.355, -2.805, 2.805, -12.6, -12.5)          # IMX548 active area (for reference)
board = box(-14.15, 14.15, -13.5, 13.5, -15.6, -14.4)              # PCB + low parts
for sx in (-1, 1):
    for sy in (-1, 1): board = board.cut(zcyl(1.04, -15.6, -14.4, 11.2 * sx, 11.2 * sy))
parts = box(-12, 8, -10, 10, -17.4, -15.6)                         # tallest parts on the back
io = box(-4, 4, 9, 13, -19.4, -15.6)                               # I/O connector (top)
usb = box(6.5, 15.55, -4.0, 4.0, -17.4, -14.6)                     # USB 3.0 Micro-B, opening toward +X
cam = Part.makeCompound([body, sensor, board, parts, io, usb])
cam.exportStep(OUT)
b = cam.BoundBox
print('STEP', OUT, 'bbox', [round(x, 2) for x in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
