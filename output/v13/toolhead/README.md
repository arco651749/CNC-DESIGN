# v13 tool-head module – decisions (frozen)

| # | Question | Decision |
|---|----------|----------|
| 1 | X travel | X lengthened 155 → ±227.5, so spindle, camera and probe all cover the 300×300 work area |
| 2 | Spacing (camera D / probe P) | **C: camera 70 mm left, probe 85 mm right** of the spindle, all centres on y −20. Spindle at x −7.5 so camera (−77.5) and probe (+77.5) are symmetric on the Z slide. Lens front 40 above the tool tip (4 above the spindle nose); light path 40 + 70 = 110 = WD |
| 3 | Mounting | One integrated module. The module plate replaces Spindle_mount_plate and keeps the RBPB8 pivot + shims + differential screws for spindle tram only; camera and probe offsets are calibrated after tramming (re-check them after every tram change) |
| 4 | X screw | Fixed-supported: C-TEK12 (motor end) + C-TEF12 at x −268.5, C-KBS1505-616 |
| 5 | Probe drive | Air slide (bore 10, stroke 60) with 2 auto switches; retracted switch = spindle enable / feed hold interlock; spring-return valve retracts on power loss |
| 6 | Spindle plug | Spindle turned 90°, plug faces forward (−Y) |
| 7 | Camera focus range | Spec limit: the camera sees work tops 0..50 mm above the table (focus plane = lens front − 110, Z +50 max) |
| 8 | Module stiffness / repeatability | Shim bolts spread to z 305 / 490 (185 apart, Z slide 30 longer at the bottom); spindle clamp located by 2 dowels D6 |
| 9 | Optics protection | Pneumatic flip cover over the prism (open only for tool setting); lens air ring (no window, WD unchanged) |
| 10 | Probe signal | grblHAL probe input, NC wiring; not the MR-J4 MSD latch (point-table mode cannot take the pulse train) |

Prism: reflects +X, on the table T-slot x −130 at the rear-left corner (fold point x −195, y 200, z 140), outside the work area.
Tool measured at X −117.5, table −220, Z −40.

Table T-slots: DIN 650 14 at x 0 / ±65 / ±130 (moved from ±80 / ±160, clear of the Y rail M12 taps).

Sketches: `concept.png` (layout), `spacing_options.png` (question 2). Screenshots: `toolset_lightpath.png`, `camera_fov.png`, `x_screw_support.png`.
