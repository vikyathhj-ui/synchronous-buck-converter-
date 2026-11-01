#!/usr/bin/env bash
# Phase 0 environment check. Run inside the iic-osic container:
#   docker exec -w /foss/projects/synchronous-buck-converter- iic-osic bash -lc 'scripts/env_check.sh | tee results/env_check.txt'
# Exits non-zero if any required item is missing or a smoke test fails.
set -u
fail=0
row() { printf '%-28s %-8s %s\n' "$1" "$2" "$3"; }
req() { # name, command-for-version
  if command -v "$1" >/dev/null 2>&1; then row "$1" found "$(eval "$2" 2>&1 | head -1)"; else row "$1" MISSING ""; fail=1; fi
}
opt() {
  if command -v "$1" >/dev/null 2>&1; then row "$1" found "(optional)"; else row "$1" absent "(optional)"; fi
}

echo "== Tools =="
req ngspice      "ngspice --version | grep -m1 ngspice"
req verilator    "verilator --version"
req iverilog     "iverilog -V"
req yosys        "yosys -V"
req sby          "echo"
req yosys-smtbmc "echo"
req yices-smt2   "yices-smt2 --version"
opt boolector; opt z3; opt bitwuzla
req python3      "python3 --version"
req librelane    "librelane --version"
opt openlane
req openroad     "openroad -version"
req sta          "sta -version"
req magic        "magic --version"
req netgen       "echo"
req klayout      "klayout -v"
req xschem       "xschem -v | grep -m1 -i xschem"

echo; echo "== Python packages =="
for m in numpy scipy matplotlib control cocotb cocotb_coverage pytest; do
  v=$(python3 -c "import $m; print(getattr($m,'__version__','ok'))" 2>/dev/null)
  if [ -n "$v" ]; then row "$m" found "$v"; else row "$m" MISSING ""; fail=1; fi
done

echo; echo "== PDK =="
row PDK_ROOT "${PDK_ROOT:+found}" "${PDK_ROOT:-unset} PDK=${PDK:-unset} SCL=${STD_CELL_LIBRARY:-unset}"
NG=$PDK_ROOT/$PDK/libs.tech/ngspice
for dev in nfet_g5v0d10v5 pfet_g5v0d10v5; do
  n=$(grep -rlE "sky130_fd_pr__${dev}" "$NG" 2>/dev/null | wc -l)
  [ "$n" -gt 0 ] && row "$dev" found "referenced in $n model files" || { row "$dev" MISSING ""; fail=1; }
done
HVL=$PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hvl/lib
for lib in sky130_fd_sc_hd__tt_025C_1v80.lib; do
  f=$PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd/lib/$lib; [ -f "$f" ] && row "$lib" found "" || { row "$lib" MISSING ""; fail=1; }
done
L=$HVL/sky130_fd_sc_hvl__tt_025C_3v30_lv1v80.lib
if [ -f "$L" ]; then
  row "hvl tt_025C_3v30_lv1v80" found ""
  grep -ohE 'cell *\( *"?sky130_fd_sc_hvl__lsbuf[a-z0-9_]*' "$L" | sed -E 's/.*"//' | sort -u | sed 's/^/    /'
else row "hvl tt_025C_3v30_lv1v80" MISSING ""; fail=1; fi

echo; echo "== Smoke test 1: 5 V devices load in ngspice (tt) =="
W=$(mktemp -d)
cat > "$W/dev.spice" <<SP
* g5v0d10v5 DC op
.lib $NG/sky130.lib.spice tt
VD d 0 3.3
VG g 0 3.3
XN d g 0 0 sky130_fd_pr__nfet_g5v0d10v5 W=10 L=0.5
VDP dp 0 0
VGP gp 0 0
VS s 0 3.3
XP dp gp s s sky130_fd_pr__pfet_g5v0d10v5 W=10 L=0.5
.control
op
print -i(VD) i(VDP)
quit
.endc
.end
SP
if (cd "$W" && ngspice -b dev.spice) > "$W/dev.log" 2>&1 && grep -qE 'i\(vd' "$W/dev.log"; then
  grep -E 'i\(vd' "$W/dev.log" | sed 's/^/    /'; row "5V device op" PASS ""
else tail -20 "$W/dev.log"; row "5V device op" FAIL ""; fail=1; fi

echo; echo "== Smoke test 2: ngspice d_cosim + Verilator (vlnggen) =="
VLNGGEN=$(dirname "$(command -v ngspice)")/../share/ngspice/scripts/vlnggen
[ -f "$VLNGGEN" ] || VLNGGEN=/foss/tools/ngspice/share/ngspice/scripts/vlnggen
cat > "$W/counter.v" <<'V'
module counter (input clk, output reg [3:0] count);
  initial count = 0;
  always @(posedge clk) count <= count + 1;
endmodule
V
cat > "$W/cosim.spice" <<'SP'
* d_cosim smoke test: 4-bit Verilator counter clocked at 10 MHz for 1 us
vclk clk 0 pulse(0 1.8 0 1n 1n 49n 100n)
aadc [clk] [dclk] adcb
.model adcb adc_bridge(in_low=0.9 in_high=0.9)
acnt [dclk] [q0 q1 q2 q3] cnt
.model cnt d_cosim simulation="./counter.so"
adac [q0 q1 q2 q3] [a0 a1 a2 a3] dacb
.model dacb dac_bridge(out_low=0 out_high=1.8)
.control
tran 1n 1.02u
* d_cosim connects vector ports MSB first: q0 = count[3]
let code = (8*a0 + 4*a1 + 2*a2 + a3)/1.8
meas tran c550 find code at=550n
meas tran final_count find code at=1.01u
quit
.endc
.end
SP
if (cd "$W" && ngspice -b "$VLNGGEN" counter.v) > "$W/vlnggen.log" 2>&1 && [ -f "$W/counter.so" ]; then
  row "vlnggen build" PASS "$W/counter.so"
  (cd "$W" && ngspice -b cosim.spice) > "$W/cosim.log" 2>&1
  fc=$(grep -iE '^final_count' "$W/cosim.log" | awk '{print $3}')
  c5=$(grep -iE '^c550' "$W/cosim.log" | awk '{print $3}')
  # rising edges at 1n, 101n, ..., 1001n: 6 before 550n, 11 before 1.01us
  if [ -n "$fc" ] && python3 -c "import sys; sys.exit(0 if abs(float('$fc')-11)<0.01 and abs(float('$c5')-6)<0.01 else 1)"; then
    row "d_cosim run" PASS "count@550n=$c5 (expect 6), count@1.01u=$fc (expect 11)"
  else tail -20 "$W/cosim.log"; row "d_cosim run" FAIL "final_count=${fc:-none}"; fail=1; fi
else tail -20 "$W/vlnggen.log"; row "vlnggen build" FAIL ""; fail=1; fi

echo; echo "work dir: $W"
[ $fail -eq 0 ] && echo "RESULT: ALL OK" || echo "RESULT: SOMETHING MISSING OR FAILED"
exit $fail
