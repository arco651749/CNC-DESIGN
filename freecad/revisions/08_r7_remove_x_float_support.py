# -*- coding: utf-8 -*-
"""r6 -> r7: remove the X floating support C-TEF12 (X screw becomes fixed-free like Y and Z).
Critical speed (fixed-free, root ~12.5, L~450): ~2100 rpm, x0.8 = ~1680 rpm > 1200 rpm needed at 100 mm/s.
Run from the repository root:  freecadcmd freecad/revisions/08_r7_remove_x_float_support.py"""
import os
import FreeCAD as App
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
doc = App.openDocument(ROOT + '/output/v3/CNC_v3_r6.FCStd')
doc.removeObject(doc.getObjectsByLabel('X_support_float')[0].Name)
xs = doc.getObjectsByLabel('X_ballscrew')[0]
if 'Spec' in xs.PropertiesList: xs.Spec = 'C-KBS1505-517.5, fixed-free (C-TEK12 at the motor end only)'
doc.recompute(); doc.saveAs(ROOT + '/output/v3/CNC_v3_r7.FCStd')
