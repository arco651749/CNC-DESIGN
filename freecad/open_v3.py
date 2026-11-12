# -*- coding: utf-8 -*-
"""Open output/v3/CNC_v3.FCStd in the FreeCAD GUI with colours, shaded + edges ('Flat Lines'), isometric view.
Run:  freecad.exe freecad/open_v3.py   (FreeCAD stays open)
  or in the FreeCAD Python console:  import runpy; runpy.run_path(r'<repo>/freecad/open_v3.py')"""
import os
import FreeCAD as App
import FreeCADGui as Gui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = dict(
    plate=(0.36, 0.38, 0.40), alu=(0.80, 0.81, 0.83), rail=(0.66, 0.68, 0.71), block=(0.22, 0.36, 0.60),
    screw=(0.80, 0.80, 0.76), nut=(0.62, 0.55, 0.40), support=(0.16, 0.16, 0.17), coupling=(0.86, 0.22, 0.20),
    motor=(0.13, 0.13, 0.14), amp=(0.26, 0.27, 0.30), table=(0.48, 0.50, 0.53), custom=(0.93, 0.56, 0.22),
    spindle=(0.86, 0.86, 0.89), black=(0.10, 0.10, 0.10), clamp=(0.55, 0.70, 0.86), tool=(0.85, 0.70, 0.25),
)
RULES = [  # (test, colour) - first match wins
    (lambda n: n.startswith("Datum"), "plate"),
    (lambda n: n.startswith(("Gantry_column", "Gantry_beam")), "alu"),
    (lambda n: "_rail_" in n and not n.startswith("X_rail_plate"), "rail"),
    (lambda n: "_block_" in n, "block"),
    (lambda n: n.endswith(("ballscrew", "journal")), "screw"),
    (lambda n: n.endswith("ball_nut"), "nut"),
    (lambda n: "_support_" in n, "support"),
    (lambda n: n.endswith("coupling"), "coupling"),
    (lambda n: n.endswith("_motor"), "motor"),
    (lambda n: n.startswith("Servo_amp"), "amp"),
    (lambda n: n == "Work_table", "table"),
    (lambda n: n == "Spindle_body", "spindle"),
    (lambda n: n in ("Spindle_fan_cover", "Spindle_plug", "ER11_nut", "Spindle_nose"), "black"),
    (lambda n: n == "Spindle_clamp", "clamp"),
    (lambda n: n.startswith("Tool"), "tool"),
]


def colour(n):
    for test, key in RULES:
        if test(n):
            return C[key]
    return C["custom"]


path = os.path.join(ROOT, "output", "v3", "CNC_v3.FCStd")
doc = next((d for d in App.listDocuments().values() if d.FileName.replace("\\", "/") == path.replace("\\", "/")), None)
doc = doc or App.openDocument(path)
for o in doc.Objects:
    if o.TypeId == "Part::Feature":
        vo = o.ViewObject
        vo.ShapeColor = colour(o.Name)
        vo.LineColor = (0.05, 0.05, 0.05)
        vo.LineWidth = 1.2
        vo.DisplayMode = "Flat Lines"
        vo.Visibility = True
App.setActiveDocument(doc.Name)
v = Gui.getDocument(doc.Name).ActiveView
v.viewIsometric()
v.fitAll()
