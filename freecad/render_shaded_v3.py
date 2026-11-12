# -*- coding: utf-8 -*-
"""Shaded render with edges (FreeCAD GUI, 'Flat Lines') of output/v3/CNC_v3.FCStd.
Run:  freecad.exe freecad/render_shaded_v3.py     (opens the GUI briefly, saves PNGs, exits)
Out:  output/v3/CNC_v3_shaded_iso.png, CNC_v3_shaded_rear.png  (contain vendor geometry: keep local)
"""
import os
import FreeCAD as App
import FreeCADGui as Gui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "v3")
from PySide import QtCore
LOG = open(os.path.join(OUT, "render_log.txt"), "w")
doc = App.openDocument(os.path.join(OUT, "CNC_v3.FCStd"))
Gui.updateGui()

C = dict(
    plate=(0.36, 0.38, 0.40), alu=(0.80, 0.81, 0.83), rail=(0.66, 0.68, 0.71), block=(0.22, 0.36, 0.60),
    screw=(0.80, 0.80, 0.76), nut=(0.62, 0.55, 0.40), support=(0.16, 0.16, 0.17), coupling=(0.86, 0.22, 0.20),
    motor=(0.13, 0.13, 0.14), amp=(0.26, 0.27, 0.30), table=(0.48, 0.50, 0.53), custom=(0.93, 0.56, 0.22),
    spindle=(0.86, 0.86, 0.89), black=(0.10, 0.10, 0.10), clamp=(0.55, 0.70, 0.86), tool=(0.85, 0.70, 0.25),
)


def colour(n):
    if n.startswith("Datum"):
        return C["plate"]
    if n.startswith(("Gantry_column", "Gantry_beam")):
        return C["alu"]
    if "_rail_" in n and not n.startswith("X_rail_plate"):
        return C["rail"]
    if "_block_" in n:
        return C["block"]
    if n.endswith(("ballscrew", "journal")):
        return C["screw"]
    if n.endswith("ball_nut"):
        return C["nut"]
    if "_support_" in n:
        return C["support"]
    if n.endswith("coupling"):
        return C["coupling"]
    if n.endswith("_motor"):
        return C["motor"]
    if n.startswith("Servo_amp"):
        return C["amp"]
    if n == "Work_table":
        return C["table"]
    if n == "Spindle_body":
        return C["spindle"]
    if n in ("Spindle_fan_cover", "Spindle_plug", "ER11_nut", "Spindle_nose"):
        return C["black"]
    if n == "Spindle_clamp":
        return C["clamp"]
    if n.startswith("Tool"):
        return C["tool"]
    return C["custom"]


for o in doc.Objects:
    if o.TypeId != "Part::Feature":
        continue
    vo = o.ViewObject
    vo.ShapeColor = colour(o.Name)
    vo.LineColor = (0.05, 0.05, 0.05)
    vo.LineWidth = 1.2
    vo.DisplayMode = "Flat Lines"
    vo.Deviation = 0.1
    vo.Visibility = True

def shoot():
    gd = Gui.getDocument(doc.Name)
    Gui.ActiveDocument = gd
    view = gd.ActiveView
    LOG.write("view %s objs %d\n" % (type(view).__name__, len(doc.Objects)))
    try:
        view.setCameraType("Orthographic")
    except Exception as e:
        LOG.write("cam %s\n" % e)
    W, H = 2400, 1800
    view.viewIsometric()
    view.fitAll()
    for _ in range(10):
        Gui.updateGui()
    view.saveImage(os.path.join(OUT, "CNC_v3_shaded_iso.png"), W, H, "White")
    rot = App.Rotation(App.Vector(0, 0, 1), 180).multiply(view.getCameraOrientation())
    view.setCameraOrientation(rot)
    view.fitAll()
    for _ in range(10):
        Gui.updateGui()
    view.saveImage(os.path.join(OUT, "CNC_v3_shaded_rear.png"), W, H, "White")
    LOG.write("saved\n")
    LOG.close()
    os._exit(0)


QtCore.QTimer.singleShot(4000, shoot)