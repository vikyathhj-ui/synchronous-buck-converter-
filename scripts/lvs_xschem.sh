#!/usr/bin/env bash
# Netlist every generated xschem schematic and LVS it against the hand-written SPICE subckt
# (netgen, sky130A setup). Run inside iic-osic from the repo root:  scripts/lvs_xschem.sh
# Writes xschem/netlist/<cell>.spice and results/phase3/lvs_xschem/<cell>.txt; prints a summary.
set -u
ROOT=$(pwd)
mkdir -p xschem/netlist results/phase3/lvs_xschem
cat > xschem/xschemrc <<RC
source $PDK_ROOT/$PDK/libs.tech/xschem/xschemrc
append XSCHEM_LIBRARY_PATH :$ROOT/xschem
RC
REF=results/phase3/lvs_xschem/ref_all.spice
cat spice/powerstage.spice spice/deadtime.spice spice/comparator.spice spice/dpwm_fine.spice \
    spice/dpwm_cal.spice spice/adc_ref.spice > $REF
fail=0
for sch in xschem/*.sch; do
  cell=$(basename "$sch" .sch)
  xschem --rcfile xschem/xschemrc --no_x --quit --tcl "set top_subckt 1; set lvs_netlist 1" --netlist --netlist_path xschem/netlist \
         --netlist_filename "$cell.spice" "$sch" > /dev/null 2>&1
  out=results/phase3/lvs_xschem/$cell.txt
  netgen -batch lvs "xschem/netlist/$cell.spice $cell" "$REF $cell" \
         $PDK_ROOT/$PDK/libs.tech/netgen/${PDK}_setup.tcl "$out" > /dev/null 2>&1
  # pass only on a unique match with no property (W/L/m) errors; netgen tolerance is the sky130A
  # setup's (1 % on W and L)
  if grep -q "Circuits match uniquely" "$out" && ! grep -qiE "do not match|property errors" "$out"; then
    printf '%-14s MATCH\n' "$cell"
  else
    printf '%-14s MISMATCH (see %s)\n' "$cell" "$out"; fail=1
  fi
done
exit $fail
