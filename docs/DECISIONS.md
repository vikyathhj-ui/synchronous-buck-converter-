# Decisions

Each entry: decision, reason, evidence.

## D1 — Clone location `~/projects/synchronous-buck-converter-` (Phase 0)
`~/vlsi/CLAUDE.md` puts standalone repos in `~/projects`, mounted at `/foss/projects` in `iic-osic`.

## D2 — SymbiYosys solver: yices (Phase 0)
`yices-smt2` 2.7.0 is installed; boolector, z3 and bitwuzla are not. Evidence: `results/env_check.txt`.

## D3 — Level shifters: use `sky130_fd_sc_hvl__lsbuflv2hv_1` first (Phase 0)
It exists in `sky130_fd_sc_hvl__tt_025C_3v30_lv1v80.lib`, so no custom cross-coupled shifter is needed
unless Phase 3 characterisation shows a problem. Evidence: `results/env_check.txt`.

## D4 — 5 V device ratings not yet verified (Phase 0)
The installed PDK ngspice files contain no SOA limits for `{n,p}fet_g5v0d10v5`. The SkyWater name
convention suggests 5.0 V gate / 10.5 V drain; this is unverified and must be checked against
SkyWater documentation in Phase 3 before sizing. VIN max 3.6 V is well under either value.

## D5 — `d_cosim` port order is MSB first (Phase 0)
A 4-bit Verilator counter under `d_cosim` read 13 with LSB-first mapping and 11 (the correct edge count)
with MSB-first mapping, also 6 at 550 ns. Phase 4 netlists must list bus bits MSB first.
Evidence: smoke test 2 in `scripts/env_check.sh`.

## D6 — VREF DAC: 8-bit code, 10 mV per code (Phase 1)
VREF = code x 10 mV, so 1.8 V = code 180 exactly, and the regulation range 1.0–2.5 V = codes 100–250.
The brief's 1.0–2.5 V range is kept as the allowed register range. The DAC must reach 0 V because the
soft start ramps VREF from 0. A 10 mV DAC step equals the ADC LSB.

## D7 — Soft start by phase accumulator (Phase 1)
Every period the accumulator adds the target code; each time it passes 1000 (the ramp length in
periods), VREF is raised by one code. The ramp therefore takes exactly 1000 periods (1 ms) for any
target, with no divider. Model: `startup_*_vref_ramp_time`.

## D8 — (superseded by D11) PID design point: fc 50 kHz, PM 50 deg, integral zero fc/5 (Phase 1)
The sweep of 45–55 deg gave the same undershoot; recovery grows with PM. 60 deg was not reachable
with a single crossover (conditionally stable design), so it was rejected. Details in docs/CONTROL.md section 4.

## D9 — (superseded by D11) Coefficients in Q2 (Phase 1)
Q2 is the smallest number of fractional bits for which PM moves less than 1 deg and fc less than 2 %
(rule and table in docs/CONTROL.md section 5). Integer gains kp = 18, ki = 1, kd = 273 (x 2^-2).
The output is rounded by (s + 2) >>> 2, and the integrator is clamped to [0, 511] << 2.

## D10 — Controller timing contract for the RTL (Phase 1)
Per period: sample the ADC and the valley comparator at the period start. If the valley current is
over the limit, suppress THIS period's HS pulse and hold the integrator; otherwise apply the duty
computed in the previous period. The PID then computes the next duty. `model/sim.py` is the golden
model, and the Phase 2 RTL must match `FixedPid` bit for bit.

## D11 — Robust PID: fc 30 kHz, PM 60 deg, integral zero fc/5, Q5 (Phase 1, user requirement)
The user does not want the phase margin to drop below spec at any tolerance corner. The new
requirement is PM >= 45 deg in all 162 robustness cases (VIN, L/C +/-20 %, Ron, load). The 50 kHz design
reached 28.3 deg at the L/C -20 % corner. A search found that fc <= 35 kHz is needed; 30 kHz / 60 deg
gives about 48.7 deg in the worst case, while 35 kHz / 60 deg and 30 kHz / 55 deg give only 45.0–45.2 deg.
Integer gains kp = 86, ki = 3, kd = 1131 (x 2^-5). The quantisation rule now also requires each coefficient
within 10 %. Costs: undershoot 66 mV (spec 90), recovery 26 us (spec 50), and a larger line-step
deviation (docs/CONTROL.md section 8, item 6). Enforced by `robust_pm_meets_spec_all` and
model/tests `test_pm_at_least_45_at_tolerance_corners`.
