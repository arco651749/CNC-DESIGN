"""v14 motion model (owner 2026-11-28): the whole machine as a FreeCAD Assembly with slider joints for Y / X / Z and a Simulation,
built from the v14 model (CNC_v14_base.FCStd = machine + base). Open it in FreeCAD (Assembly workbench), drag the parts or play the
simulation. The joints are the single definition of the motion; later checks can drive them (assembly.updateForFrame).
Run (needs the GUI for the view providers; headless works with a virtual display):
    CNC_ROOT=$PWD xvfb-run -a /opt/freecad/bin/freecad freecad/v14/27_assembly_v14.py
Out: output/v14/CNC_v14_assembly.FCStd (local only, like every FCStd; contains vendor models: internal use, do not publish)."""
import os, re
import FreeCAD as App, FreeCADGui as Gui, Part
import JointObject, UtilsAssembly, CommandCreateSimulation as CS
ROOT = os.environ.get('CNC_ROOT', os.getcwd())
V = App.Vector
src = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))
def cls(o):                                                    # same motion classes as the checks 02 / 07 / 23
    n = o.Label
    if 'Motion' in o.PropertiesList and o.Motion: return o.Motion
    if n.startswith(('Y_rail', 'Work_table', 'Y_ballscrew', 'Y_support', 'Y_coupling', 'Y_motor')): return 'y'
    if n.startswith(('Z_block', 'Z_spacer', 'Z_slide', 'Z_ball_nut', 'Z_nut_housing', 'Spindle', 'ER11', 'Tool')): return 'z'
    if n.startswith(('X_block', 'X_carriage', 'X_ball_nut', 'X_nut_bracket', 'X_saddle', 'Z_')): return 'x'
    return ''
def colour(n, k):                                              # as the conduit page: cable system dark, motors black, axes coloured
    if n.startswith(('Conduit_', 'X_branch_box', 'Table_cable', 'Feeder_entry')):
        return (0.07, 0.07, 0.08) if re.search(r'(fitting|connector|gland)', n) else (0.22, 0.24, 0.27)
    if n.startswith(('X_motor', 'Y_motor', 'Z_motor')) and 'plate' not in n and 'block' not in n: return (0.2, 0.22, 0.25)
    return {'y': (0.78, 0.62, 0.42), 'x': (0.5, 0.64, 0.8), 'z': (0.62, 0.72, 0.84)}.get(k, (0.68, 0.71, 0.75))
doc = App.newDocument('CNC_v14_assembly')
asm = doc.addObject('Assembly::AssemblyObject', 'Assembly'); asm.Label = 'CNC_v14'
jg = asm.newObject('Assembly::JointGroup', 'Joints')
GROUPS = {'': 'Frame', 'y': 'Table_Y', 'x': 'Carriage_X', 'z': 'Head_Z'}
PARTS = {}
for k, name in GROUPS.items():
    p = asm.newObject('App::Part', name); p.Label = name; PARTS[k] = p
n_ = {k: 0 for k in GROUPS}
for o in src.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull() or not o.Shape.Solids: continue
    if o.Label.startswith(('Electrical_panel', 'Servo_amp', 'Controller', 'Board_standoff', 'Panel_standoff', 'Keepout')): continue
    k = cls(o)
    if k not in PARTS: k = ''
    f = doc.addObject('Part::Feature', re.sub(r'\W', '_', o.Label)); f.Label = o.Label; f.Shape = o.Shape.copy()
    PARTS[k].addObject(f); n_[k] += 1
    f.ViewObject.ShapeColor = colour(o.Label, k)
    if o.Label.startswith(('Box_top', 'Guard_')): f.ViewObject.Transparency = 60
# datum cubes: one per part at the same place, so every slider joint starts at offset 0 (home); the joint axis is the face normal
D = V(0, 0, -400)                                              # under the machine, out of the way
DAT = {}
for k, p in PARTS.items():
    c = doc.addObject('Part::Box', 'Datum_' + p.Name); c.Length = c.Width = c.Height = 10; c.Placement.Base = D
    c.ViewObject.Visibility = False; p.addObject(c); DAT[k] = c
ground = jg.newObject('App::FeaturePython', 'GroundedJoint')
JointObject.GroundedJoint(ground, PARTS[''])
JointObject.ViewProviderGroundedJoint(ground.ViewObject)
# Part::Box faces: Face2 +x, Face4 +y, Face6 +z
FACE = {'x': ('Face2', 'Vertex7'), 'y': ('Face4', 'Vertex7'), 'z': ('Face6', 'Vertex7')}   # Vertex7 = (L, W, H) lies on all three
TRAVEL = {'y': (-250.0, 150.0), 'x': (-182.5, 182.5), 'z': (-50.0, 50.0)}
JOINTS = {}
for k, parent in (('y', ''), ('x', ''), ('z', 'x')):
    j = jg.newObject('App::FeaturePython', 'Slider_' + k.upper())
    JointObject.Joint(j, JointObject.JointTypes.index('Slider'))
    JointObject.ViewProviderJoint(j.ViewObject)
    fa, ve = FACE[k]
    a, b = PARTS[parent], PARTS[k]
    refs = [[a, [DAT[parent].Name + '.' + fa, DAT[parent].Name + '.' + ve]],   # reference = [component, [sub paths inside it]]
            [b, [DAT[k].Name + '.' + fa, DAT[k].Name + '.' + ve]]]          # ([assembly, ['Part.Child.Face']] is ignored by the solver)
    j.Proxy.setJointConnectors(j, refs)
    j.EnableLengthMin = j.EnableLengthMax = True
    j.LengthMin, j.LengthMax = TRAVEL[k]
    j.Label = {'y': 'Y 工作台', 'x': 'X 滑座', 'z': 'Z 工具頭'}[k]
    JOINTS[k] = j
doc.recompute(); asm.solve()
# simulation: Y, X and Z through their full travel (sine, periods 8 / 12 / 6 s, all start at home)
sg = UtilsAssembly.getSimulationGroup(asm)
sim = sg.newObject('App::FeaturePython', 'Simulation'); CS.Simulation(sim); CS.ViewProviderSimulation(sim.ViewObject)
sim.bTimeEnd = 24.0; sim.cTimeStepOutput = 0.05
for k, f in (('y', '-50 + 200*sin(2*pi*time/8)'), ('x', '182.5*sin(2*pi*time/12)'), ('z', '50*sin(2*pi*time/6)')):
    m = asm.newObject('App::FeaturePython', 'Motion_' + k.upper()); CS.Motion(m, 'Linear', JOINTS[k], f); CS.ViewProviderMotion(m.ViewObject)
    sim.Group = sim.Group + [m]
doc.recompute()
out = os.path.join(ROOT, 'output', 'v14', 'CNC_v14_assembly.FCStd')
doc.saveAs(out)
log = ['v14 assembly: parts %s, joints %s' % ({GROUPS[k]: v for k, v in n_.items()}, [j.Label for j in JOINTS.values()])]
try:                                                           # self-check: play the simulation and read where the parts went
    rc = asm.generateSimulation(sim); nf = asm.numberOfFrames(); log.append('simulation rc %s, frames %d' % (rc, nf))
    import math
    for i in (40, 80, 120, 200, 300):
        asm.updateForFrame(i); t = i * sim.cTimeStepOutput.Value
        log.append('frame %3d  table y %7.1f  carriage x %7.1f  head x %7.1f z %6.1f   (formula Y %7.1f X %7.1f Z %6.1f)' % (
            i, PARTS['y'].Placement.Base.y, PARTS['x'].Placement.Base.x, PARTS['z'].Placement.Base.x, PARTS['z'].Placement.Base.z,
            -50 + 200 * math.sin(2 * math.pi * t / 8), 182.5 * math.sin(2 * math.pi * t / 12), 50 * math.sin(2 * math.pi * t / 6)))
except Exception as e:
    log.append('simulation not generated here: %s' % e)
open(os.path.join(ROOT, 'output', 'v14', 'logs', 'v14_assembly.txt'), 'w', encoding='utf-8').write('\n'.join(log) + '\n')
Gui.getMainWindow().close()
