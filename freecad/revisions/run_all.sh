#!/usr/bin/env bash
# Rebuild r2..r6 from output/v3/CNC_v3.FCStd and run the r6 collision sweep.
# Usage (from the repository root):  bash freecad/revisions/run_all.sh [path/to/freecadcmd]
set -e
FC=${1:-freecadcmd}
for f in freecad/revisions/0*.py; do echo "== $f"; "$FC" "$f"; done
echo "collisions: $(cat output/v3/logs/r6_motion.txt)"
