# v14 CNC sandbox (MuJoCo)

一個給 AI 規劃量測動作的沙盒：把工件放上工作台，交一份動作清單（移動、探針伸縮、探測、拍照），沙盒逐步執行並回報
碰撞、超出行程、探針觸發座標、相機影像與對焦。它不模擬切削；精確的設計干涉檢查仍以 `freecad/v14/02 / 07 / 12` 為準。

A sandbox for an AI to plan measuring moves on a workpiece and have them checked before the real machine runs them.
建置過程、設計理由與踩過的坑：`docs/mujoco_sandbox_build.md`。

## Build

```bash
CNC_ROOT=$PWD /opt/freecad/bin/freecadcmd freecad/v14/26_export_mujoco_v14.py   # meshes + manifest from the v14 model
python3 sandbox/build_mjcf.py                                                    # output/v14/mujoco/cnc_v14.xml
MUJOCO_GL=egl python3 sandbox/demo_plan.py                                       # demo: output/v14/mujoco/runs/demo_ok, demo_crash
```

The meshes (`output/v14/mujoco/meshes/`) are not in git because they contain vendor models for internal use only: run step 1 first.

Needs `pip install mujoco pillow numpy` (MuJoCo 3.2+; tested 4.0.1). Headless rendering: `MUJOCO_GL=egl`.

## Model

| body | joint | range (mm) | moves |
|---|---|---|---|
| table | Y (slide +Y) | -250..150 | work table, prism station |
| carriage | X (slide +X) | -182.5..182.5 | X carriage / Z axis plates |
| head | Z (slide +Z, on the carriage) | -50..50 | spindle, camera, probe slide body |
| probe | P (slide -Z, on the head) | 0..60 | SMC MXH10-60Z table, probe; ball D2 on a 26 stylus |
| cover | C (slide +Y, on the table) | 0..30 | prism cover |

- Collisions: tool-head parts (spindle, clamp, ER11 nut, tool, camera, air ring, nozzles, probe body, slide, conduit head bracket) against
  obstacles (table top as an exact box, prism station, workpieces). Mesh colliders use their convex hulls (a few mm conservative on
  concave parts); the probe ball / stylus and box workpieces are exact.
- Probe: ball or stylus contact = trigger (located by bisection to 1 um). Any other head part touching an obstacle = crash.
- Camera: Moritex MML04-HR120D (0.4x telecentric) + Basler daA2448-70uc, orthographic, field 16.8 x 14.0 mm, image x = +X, up = +Y;
  focus plane = lens front - 120 (DOF 5.3). With Z +50 the camera focuses at most 30 above the table top.

## Coordinates

- **axes** `X, Y, Z` (mm, home 0) = machine axis positions.
- **table points** = machine coordinates at Y = 0 (table top z 110, T-slots at x 0 / ±65 / ±130). Workpieces are placed in this frame.
- Helpers: `camera_over(x, y, z_surface)`, `probe_at(x, y, z)` (probe extended), `tool_at(x, y, z)` give axis targets; `where()` gives the
  current axes and the table points of the tool tip, probe ball centre and camera focus point.

## Plan steps

```python
from cnc_sandbox import CNCSandbox
sb = CNCSandbox()
sb.add_box('block', (120, 80, 25), centre=(20, 10), yaw=5)       # or sb.add_mesh('part', 'part.stl', pos=(x, y, 110), yaw=0)
plan = [
  {'op': 'move', 'Z': 45},                                       # straight move in axis space, checked every 0.5 mm
  {'op': 'move', **sb.camera_over(-39.8, -35.3, 135)}, {'op': 'capture', 'name': 'corner'},
  {'op': 'probe', 'state': 'down'},                              # MXH slide out (60), ball 25 below the tool tip
  {'op': 'move', **sb.probe_at(-50, 10, 125)},
  {'op': 'probe_move', 'X': sb.probe_at(-35, 10, 125)['X'], 'feed': 200},   # G38.2-like: stops at the trigger
  {'op': 'probe', 'state': 'up'},
]
report = sb.run(plan)        # {'ok', 'estimated_time_s', 'steps': [...], 'final': ...}
```

Step results: `ok` (+ `warning` when a head part passes within 0.5 mm of an obstacle), `triggered` (axes, ball centre and contact point in
table coordinates), `no_trigger`, `crash` (the two parts, where, last safe axes), `out_of_travel`, `error`. Captures return the image
path, mm per pixel, and per visible surface its share of the field and focus error.

## Limits of this version

- Kinematic only (no axis dynamics; time estimate = path length / feed, rapid 5000 mm/min assumed).
- No cutting, no coolant, no conduits; the prism tool-setting optics are not simulated.
- Machine-structure parts are visual only (the AI's moves cannot reach them within travel).
- Vendor models inside the meshes are for internal use only: do not publish the sandbox outside the project.
