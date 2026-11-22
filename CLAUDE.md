# CNC-DESIGN – rules for Claude

## Design principles (agreed with the owner, v13)

A. Function geometry first
1. **Solve the functional geometry before placing parts.** Work out the dimension relations that fix positions (optics, reach,
   strokes) and let them drive the layout. e.g. telecentric tool setting: down leg + across leg = WD, so the camera height is set by
   the camera-to-spindle distance D; raising the prism does not help.
2. **Define the height chain up front.** Tool-tip reach, camera focus plane, clearance under the gantry, tool-setting height and
   probe strokes all hang on Z; write them down as one table and re-check all of them when any one changes.
3. **After changing a parameter, chase every dependent part.** e.g. X +155 -> nut-bracket slot, screw length / critical speed
   (C-TEF12 added), rail holes, base; Z -25 -> Z motor plate vs saddle, spindle vs prism station, camera range.

B. Bought parts and pneumatics
4. **Bought parts at catalog size, and check availability.** Model from the vendor drawing / STEP (dimension page saved in
   `vendor/`), never a guessed envelope; check discontinuation notices before choosing (MXH-Z -> MXH2). The BOM row
   (`freecad/v13/13_bom_v13.py`, PURCHASE) gets supplier, part number and link.
5. **Identify catalog views by cross-checking dimensions,** not by their position on the page (MXH2 head-end ports vs rod-end plate).
6. **Pneumatic parts are modelled with their fittings.** Every cylinder / slide / valve gets its real push-in fittings (e.g. SMC
   KQ2H04-M5 straight, KQ2L04-M5 elbow for M5 ports) and a tube stub on the catalog ports, with port holes cut; they take part in the
   collision checks. Choose the orientation so the port side has room (the probe slide had to be mirrored).

C. Assembly, adjustment, fastening
7. **Adjusters stay reachable from the front with everything fitted** (face screws, shim bolts moved when camera / probe were added).
8. **Modules are assembled and calibrated on the bench, then fitted as one unit** (camera / probe brackets bolted from the
   module-plate back).
9. **Check every fastener:** thread depth > engagement length, enough wall in front of blind holes (else tap through), counterbore
   depth vs head, drill / tap tool fully in material (HOLE_CHECK).

D. Stiffness and load paths
10. **Short load paths, no cantilevers.** Mount on the face the force goes into (probe on the rod-end plate, not on an arm), spread
    supports apart (module shim bolts 35 -> 185), support long screws at both ends.

E. Safety and control
11. **Moving devices report their state and fail safe.** e.g. probe "retracted" switch gates spindle enable / feed, spring-return valve
    retracts on power loss; mind NO vs NC (broken-wire detection).
12. **Confirm what the controller / drive can actually do before designing around it** (MR-J4 MSD latch works only in point-table
    mode, which cannot take the interpolating pulse train).

F. Interference and protection
13. **Fixed items on the table are obstacles:** keep them below the spindle body at the lowest Z; tool / nozzle tips reaching into
    them are reported separately as fixture contacts.
14. **Moving guards are checked in their open state too** (the flip cover hit the lens when open -> sliding cover).
15. **Read the whole check report.** After every sweep review "DESIGN CONTACTS AT HOME" as well as the travel-end collisions; a new
    contact at home is a design error until explained.

## Working rules

- Language with the owner: Traditional Chinese.
- Push to the session branch after each change; merge to `main` only when the owner says 「併到main」.
- Build chain (v13): `01_v13_toolhead.py` -> `06_base_coolant_v13.py` -> checks `02` / `07` / `12` -> pages `03` / `04` / `05` / `08`
  -> DXF `09` / `10` -> BOM `13`. Run FreeCAD scripts with `CNC_ROOT=$PWD /opt/freecad/bin/freecadcmd <script>`.
