# v13 tool-head module – decisions (frozen)

| # | Question | Decision |
|---|----------|----------|
| 1 | X travel | X lengthened 155 → ±227.5, so spindle, camera and probe all cover the 300×300 work area |
| 2 | Spacing (camera D / probe P) | **C: camera 70 mm left, probe 85 mm right** of the spindle, all centres on y −20. Spindle at x −7.5 so camera (−77.5) and probe (+77.5) are symmetric on the Z slide. Lens front 40 above the tool tip (4 above the spindle nose); light path 40 + 70 = 110 = WD |
| 3 | Mounting | One integrated module. The module plate replaces Spindle_mount_plate and keeps the RBPB8 pivot + shims + differential screws for spindle tram only; camera and probe offsets are calibrated after tramming (re-check them after every tram change) |
| 4 | X screw | Fixed-supported: C-TEK12 (motor end) + C-TEF12 at x −268.5, C-KBS1505-616 |
| 5 | Probe drive | Air slide (bore 10, stroke 60) with 2 auto switches; retracted switch = spindle enable / feed hold interlock; spring-return valve retracts on power loss |
| 6 | Spindle plug | Spindle turned 90°, plug faces forward (−Y) |
| 7 | Camera focus range | Spec limit: the camera sees work tops 0..25 mm above the table (focus plane = lens front − 110, Z +50 max; was 0..50 before item 11) |
| 8 | Module stiffness / repeatability | Shim bolts spread to z 305 / 490 (185 apart, Z slide 30 longer at the bottom); spindle clamp located by 2 dowels D6 |
| 9 | Optics protection | Sliding cover over the prism (lid + skirts on both X sides, compact cylinder, slides 30 toward +Y only for tool setting); lens air ring (no window, WD unchanged) |
| 10 | Probe | XUNKUANER touch probe (Amazon ASIN B0FWXWX7CT, DC 5-24 V, NPN NO) to the grblHAL probe input; not the MR-J4 MSD latch (point-table mode cannot take the pulse train). Ball retracted level with the spindle body bottom (tip +41), extended 19 below the tip. BOM: `output/v13/CNC_v13_BOM.csv` |
| 11 | Z height | Whole Z assembly 25 lower on the saddle: tool tip (stick-out 22) reaches −5..95 above the table, i.e. Z −50 goes 5 below the table top (set the Z soft limit / use a sacrificial plate). Gantry clearance for work + fixture passing under the Z plate: 87 (was 112). Prism station lowered (fold 15 above the table, station top 29.5) so the spindle body, lens and air ring clear it at Z −50; only the tool / nozzle tips can reach into it, like any fixture. Tool-setting pose Z −30 |

Prism: reflects +X, on the table T-slot x −130 at the rear-left corner (fold point x −195, y 206, z 125 = 15 above the table), outside the work area.
Tool measured at X −117.5, table −226, Z −30 (stick-out 22).

Table T-slots: DIN 650 14 at x 0 / ±65 / ±130 (moved from ±80 / ±160, clear of the Y rail M12 taps).

Sketches: `concept.png` (layout), `spacing_options.png` (question 2). Screenshots: `toolset_lightpath.png`, `camera_fov.png`, `x_screw_support.png`.
