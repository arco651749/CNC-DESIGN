# CNC-DESIGN – rules for Claude

## Design rules (from the owner)

- **Pneumatic parts are modelled with their fittings.** Every air cylinder, slide or valve is placed together with its push-in
  fittings (real size, e.g. SMC KQ2H04-M5 straight / KQ2L04-M5 elbow for M5 ports) and a short tube stub, on the ports the catalog
  shows. Fittings and tubes are part of the collision checks. Choose the cylinder orientation so the port side has room for them
  (owner, v13: the probe slide had to be mirrored because its fittings did not fit).
- **Vendor parts at catalog size.** Bought parts are modelled from the vendor drawing / STEP (dimension page saved in `vendor/`),
  never from a guessed envelope; the BOM row (`freecad/v13/13_bom_v13.py`, PURCHASE) gets supplier, part number and link.
- **Read the whole check report.** After every collision sweep, review the "DESIGN CONTACTS AT HOME" section as well as the
  travel-end collisions; a new contact at home is a design error until explained.

## Working rules

- Language with the owner: Traditional Chinese.
- Push to the session branch after each change; merge to `main` only when the owner says 「併到main」.
- Build chain (v13): `01_v13_toolhead.py` -> `06_base_coolant_v13.py` -> checks `02` / `07` / `12` -> pages `03` / `04` / `05` / `08`
  -> DXF `09` / `10` -> BOM `13`. Run FreeCAD scripts with `CNC_ROOT=$PWD /opt/freecad/bin/freecadcmd <script>`.
