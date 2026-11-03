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

## D20 — Simulation infrastructure for Phase 3
- `spice/models/sky130_mini.lib` (scripts/make_minilib.py): the PDK corner sections restricted to the
  devices used, by .include of the installed PDK files. Bit-identical to the full library on a check
  case (ss/125 C/3.0 V) and about 13x faster to load (5.5 s vs 72 s).
- One ngspice thread per process (scripts/spicelib.py writes a local .spiceinit): the container default
  num_threads=8 with 6 parallel jobs oversubscribed the CPU and made runs minutes long.
- Parallel devices use `m=N mult=N`: `m` multiplies the device; the PDK's `mult` only normalises the
  Monte Carlo mismatch sigma (~1/sqrt(l*w*mult)). With `m` alone all copies share one random draw.
- Subcircuit ground ports are `vss`: ngspice treats a node named `gnd` as global ground even inside a
  subcircuit, which silently bypassed a current-sense source.
- `scripts/check_cell_pins.py` checks every standard-cell instance against the PDK pin order; a swapped
  order simulates without error (it happened twice before the check existed).
- Schematics are generated from the SPICE (scripts/gen_xschem.py) and checked by netgen LVS against it
  (scripts/lvs_xschem.sh). A wrong device size makes the check fail; the first version of the
  script missed property errors, which a mutation test caught.

## D21 — Power FET sizing: HS 19.2 mm PMOS, LS 8.8 mm NMOS, 4 segments each (Phase 3)
Chosen by the analytical loss model (scripts/size_power.py) to maximise the mean efficiency over
10/25/50/100/150 mA from the measured unit-device Ron, Qg and Qoss (results/phase3/fet.json). The
optimum is flat (0.75x..1.5x within 0.1 %). Phase 1 assumed Ron = 0.5 ohm; the tt values are inside the
0.25..1 ohm range the robustness check covered.

## D22 — LS driver final pull-down tripled (Phase 3)
The HS turn-on dV/dt couples through the LS Cgd and lifted the LS gate to 0.83 V at fs/125 C/3.6 V
(a dV/dt-induced shoot-through risk). With a 384 um pull-down the worst case over 45 PVT points is
0.42 V (results/phase3/powerstage.json).

## D23 — Adaptive dead time; spec range not met (Phase 3, reported)
The dead-time generator lets a switch turn on only after replica-threshold sensors confirm the other
switch's gate is off, then adds (code + 1) programmed taps. This makes shoot-through prevention
independent of the driver delays at every corner. The cost is a fixed sensing latency: at tt the
dead time is about 6..9 ns at code 0 against the brief's 2 ns minimum (full PVT ranges in
docs/BLOCKS.md). It is reported as a spec deviation.

## D24 — Window ADC: VOUT/3 divider, PMOS-input StrongARM, one shared resistor string (Phase 3)
VOUT 1.0..2.5 V cannot drive 1.8 V comparators directly. Divided by 3 (0.33..0.83 V) it fits a PMOS-
input StrongARM, which also senses the switch node near 0 V for the valley and zero-cross
comparators (through a 5 V pass device gated by the LS gate, so the 1.8 V devices never see VIN).
One 520-unit resistor string at half the DAC LSB gives both VREF/3 and the 15 window thresholds, so
the ADC LSB is a resistor ratio (tracks the poly corner). The ADC LSB at the comparator is 3.33 mV;
comparator offset is quantified with Monte Carlo and not trimmed (user decision).

## D25 — DPWM delay-line calibration (Phase 3, user decision)
Standard-cell delay varies 2.85..3.5x over PVT; the uncalibrated 1.95 ns taps measured 0.64..1.73x
nominal and up to -5 / +2.5 LSB DNL (results/phase3/dpwm.json). Chosen: calibration. A 72-element
replica line is launched every period and sampled one clock later (TDC); the controller averages
16 counts with half-element hysteresis and maps fine code f to tap round(f * N / 8) of a 64-element
main line. Worst-case step error is one element (0.24..0.70 ns), so every DPWM step stays below the
ADC LSB (model test and results/phase3/dpwm_cal.json). RTL: tap_sel[5:0], tdc_launch, tdc_therm[71:0],
CAL register at 0x30; checked bit-exact by the cocotb scoreboard and by the formal properties.

## D26 — Window-ADC comparators on the VIN rail with 5 V devices, VOUT/2 divider (Phase 3)
Supersedes the comparator part of D24. With VOUT 1.0-2.5 V the comparator common mode spans 2.5:1.
A 1.8 V PMOS-input StrongARM could not resolve at CM 0.83 V (VOUT/3 at 2.5 V) at 1.62 V or 1.71 V
supply and -40 C: VDD - CM leaves less gate drive than the cold PMOS threshold, whatever the sizing.
A low-Vt input pair fixed the headroom, but the PDK's LVT Vt-mismatch coefficient is 2.4x the
standard one (13.9 vs 5.9 mV*um): offset sigma ~9 mV. So the 15 comparators (cmp_hv) run from VIN
(3.0-3.6 V) with 5 V devices: headroom of at least 1.75 V at CM 1.25 V (VOUT/2 at 2.5 V), all
corners functional with no measurable systematic offset. The divider becomes VOUT/2 (LSB 5 mV at the
comparator). Mismatch was first dominated by the minimum-size reset switches (charge-injection
imbalance): enlarging them from 1 to 32 um^2 took the offset sigma from ~10 mV to ~2.3 mV. The clock
is level-shifted up and the decision shifted down (HVL cells). The controller samples the ADC two
clocks after the sampling edge (31 ns), RTL updated; cocotb 12/12 and the formal proof still pass.
Note: the PDK's 5 V device models have zero vth0 mismatch but do vary other parameters (toxe, voff,
nfactor) with area scaling; the Monte Carlo results rest on that model.

## D27 — Switch-node comparators: level shift, symmetric threshold path, ideal ILIM DAC (Phase 3)
VSW during LS conduction is about -60..0 mV, where the PMOS-input StrongARM does not resolve.
sw_cmp shifts both inputs up with matched 10 kohm xhigh_po_5p73 dividers to a 0.9 V reference
(CM ~0.45 V) and uses cmp_hv. The threshold must go through an identical path (pass device +
divider): with only the VSW side resistive, kickback moved the threshold by more than 25 mV.
The ILIM threshold voltage comes from an ideal DAC (as the ideal VREF in the brief); the current-
limit accuracy is set by the LS on-resistance spread over PVT (results/phase3/fet.json), not by the
comparator. Zero-cross uses the inverted output.

## D28 — Simulation memory (Phase 3)
Parallel long transients (15-comparator ADC, DPWM) exhausted the 7.6 GB machine because ngspice
keeps every node waveform. scripts/spicelib.py now inserts a `save` line with only the vectors the
measurements use (checked bit-identical on a stored case) and runs 3 jobs in parallel.

## D29 — Window-ADC front end: segmented PVT, Monte Carlo DNL computed (Phase 3, user decision)
Even with only the 15 outputs saved, one 340-decision ADC run grew about 70 MB per minute (the
comparators regenerate every clock, so ngspice takes millions of timepoints): about 3.5 GB and
50 min per run, one at a time, about 23 h for 7 PVT + 20 MC. `.option interp` was tried and
rejected: in a 20-decision A/B check the outputs moved by up to 0.26 V and every measurement after
2.5 us failed ("out of interval").
User decision: simulate the 7 PVT cases in 5 ramp segments (each starts and ends 4 decisions past
its own range; decisions in the overlaps must agree between neighbouring segments), 5 workers
(`SPICE_WORKERS`). Comparator mismatch and its DNL effect are computed instead of simulated
end to end: tt full-front-end thresholds + 15 offsets drawn from the 100 measured cmp_hv
Monte Carlo offsets at CM 0.9 V (x2 to VOUT, mean removed because it is already in the tt run) +
the 15 ladder tap errors of one adcref.json Monte Carlo seed, 10000 trials. This leaves out
mismatch-dependent kickback between neighbouring comparators. The 20-seed full simulation is
still available as `char_adc.py mc`.
`spicelib.run` now deletes the old log before it starts a simulation: a run killed partway had
left a new netlist beside an old log, and SPICE_REUSE would have parsed the stale log (8 DPWM
logs were found in that state and deleted).

## D30 — Window-ADC comparator: static preamp in front of cmp_hv, testbenches on the RTL clocking (Phase 3, user decision)
The first full-front-end run (D29) was functionally wrong at tt: every comparator went to 0 within
a few decisions. Two causes, found with short diagnostic runs:
1. The ADC and comparator testbenches clocked the comparators at 4 MHz / 40 MHz with a 50 % duty
   clock. The RTL (docs/ARCHITECTURE.md, edge 0) fires them once per 1 MHz period with
   `adc_sample` high for one 64 MHz cycle (15.6 ns). Both benches now use that clocking.
2. Kickback. When the cmp_hv tail turns on, its input pair (5 V PMOS, 10 x 2 um x 8) throws charge
   back onto both inputs. With VOUT 12 mV above a threshold (+6 mV at the comparator) the 2 pF /
   109 kohm tap rose about 215 mV and the shared 10 pF VOUT/2 node about 50 mV, 3-6 ns into the
   evaluation: the comparator saw -162 mV and decided wrongly. (The cmp_hv characterisation
   drove both inputs from ideal sources, so it could not show this.)
Options offered: input sampling switches, a static preamp, matched RC on the VOUT/2 side. User
decision: a static preamp per comparator (cmp_adc = adc_pre + cmp_hv). adc_pre is a PMOS pair
(10 x 4 um x 2) with a 10 uA PMOS tail mirrored from one shared adc_pbias diode (ideal 10 uA
reference, like the ideal VREF) and 127 um xhigh_po_1p41 loads. It drives both cmp_hv inputs
through identical loads, so the kick is common mode there, and its small Cgd keeps the kick off the
ADC nodes: in the same test the tap moved about 2 mV, after the decision, and +/-1 mV at the
comparator decided correctly. Cost: 15 x 10 uA + 10 uA from VIN. Gain over corners in
results/phase3/comparator.json (spot check: 5.6-8.8 at tt/ss/ff/sf/fs).
Time step: with 985 ns of quiet time per decision the benches use a 5 ns maximum step. In a
30-decision, 3-comparator ramp the decisions were identical at 0.2, 1, 5 and 10 ns (resolution
0.5 mV of VOUT).
Checked on the way: `m=8 mult=8` gives 8x the current of m=1 (mult only scales the mismatch).
