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

## D12 — Hardware-realisable timing contract (Phase 2)
Three changes to the Phase 1 model, so that the RTL can implement it exactly:
(a) VREF is updated during period k and first seen by the sample at the start of period k+1, because
the DAC needs time to settle; (b) the valley comparator samples one clock (15.6 ns) before the period
ends, so its result can gate that period's HS turn-on; (c) the applied duty is re-clamped to DMAX at
the period boundary. Phase 1 was re-run: the load-step undershoot moved by less than 0.1 mV.
The contract is in `model/ctrl_ref.py` and `docs/ARCHITECTURE.md`.

## D13 — DMAX default 496 (Phase 2)
At code 511 the HS would turn off 2 ns before the next period, too short for any dead time (2–16 ns).
496 leaves 2 clocks (31 ns). It is a register, so it can be changed.

## D14 — Fault by a leaky trip score, not consecutive trips (Phase 2)
A counter of consecutive current-limited periods never reached its threshold in a hard overload,
because each suppressed HS pulse lets the valley current fall below the limit, so trips alternate.
The score is +3 per tripped period and -1 per clean one, with FAULT at FAULT_N = 64; any sustained
trip rate above 25 % faults. The model shows FAULT after 99 us at 365 mA, and the RTL test after the
number of periods in `results/phase2/test_current_limit_fault.json`. FAULT is latched until
CTRL.fault_clr, which restarts with a soft start.

## D15 — Dead-time selections as thermometer codes (Phase 2)
DT codes 0..7 mean (code + 1) x 2 ns = 2..16 ns. The controller outputs (code + 1) ones per field, so
the selection can never be zero taps. This is the formal property "dead time never zero".

## D16 — DCM entry/exit after 8 periods; zero-cross qualified after the coarse HS cycle (Phase 2)
Zero-cross is only believed in cycles after the HS turn-off cycle (VSW is high while the HS is on).
CCM -> DCM needs 8 consecutive periods with a zero-cross; DCM -> CCM needs 8 without one. No
pulse skipping or PFM yet: they are stretch goals, not implemented.

## D17 — Verification approach (Phase 2)
The RTL is checked against the golden model bit for bit, every period, in closed loop with a
per-clock Python plant (cocotb + Icarus). The safety properties are proved unboundedly with
SymbiYosys k-induction (yices); two deliberate RTL mutations each made the proof fail, which
shows the properties are not vacuous. Icarus is used rather than Verilator because the run time is
dominated by the Python plant.

## D18 — Leave DCM at once when the ADC saturates high (Phase 2, bug found in verification)
Found while trying to cover the DCM -> FAULT transition. With a heavy load in DCM, the duty rises only
through the integrator (the ADC is saturated at +7). The current still returns to zero every period,
so the "8 periods without zero-cross" exit never fired, and VOUT fell about 40 mV per period with the
converter stuck in DCM. Fix in both model and RTL: DCM -> CCM immediately when e = +7.
Also, DCM -> FAULT is unreachable by construction: in DCM the valley current is 0, so the limit
cannot trip; an overload leaves DCM first and faults from CCM. It is removed from the
transition coverage bins.

## D19 — DCM does not regulate with the CCM-designed PID (Phase 2, open, user to decide)
With DCM enabled at 5 mA, VOUT swings by about 180 mV p-p (1.75–1.93 V) in the RTL test window
(`results/phase2/test_dcm.json`: dcm_v_min, dcm_v_max); in a longer exploratory model run the mode
also switched between DCM and CCM repeatedly. The PID was
designed for the CCM plant; the DCM plant has a different gain and pole, and after D18 every large
dip also forces a DCM -> CCM -> DCM cycle. In forced CCM at the same load the loop holds one duty
code. So DCM is implemented and verified against the model, but is not usable for regulation. DCM is a stretch goal and is off by default (CTRL.dcm_en = 0, forced
CCM); every spec is met in CCM. Options for later: separate DCM gains, or pulse skipping/PFM.
