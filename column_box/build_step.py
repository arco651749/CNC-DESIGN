import os, sys
import FreeCAD as App, Part, Import
from FreeCAD import Vector as V
HERE = os.path.join(os.environ.get('CNC_ROOT', os.getcwd()), 'column_box'); sys.path.insert(0, HERE)
import layout as L
doc = App.newDocument('column_box'); objs = []
x0, x1, y0, y1, z0, z1 = L.ENV
env = Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
for p in L.PARTS:
    o = doc.addObject('Part::Feature', p[1]); o.Shape = Part.makeBox(p[6], p[7], p[8], V(p[3], p[4], p[5])); objs.append(o)
e = doc.addObject('Part::Feature', 'Envelope'); e.Shape = env.cut(Part.makeBox(x1 - x0 - 4, y1 - y0 - 4, z1 - z0 - 4, V(x0 + 2, y0 + 2, z0 + 2))); objs.append(e)
doc.recompute(); Import.export(objs, os.path.join(HERE, 'column_box.step')); print('step ok', len(objs))
