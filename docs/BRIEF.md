# P5 — `digital-buck-sky130`

**Title:** Digitally Controlled Synchronous Buck Converter in SKY130, with a hybrid DPWM, digital PID control, a window ADC, and current-limit and zero-cross protection.

Reworks the empty `synchronous-buck-converter-` repo (rename suggested). Target roles are power management IC design and mixed-signal design (TI, Infineon, NXP, ADI). Power management is TI's core analog business.

This is your mixed-signal flagship while the ERFC OTA is on hold. It uses analog and digital design together, and its analog blocks are comparators, drivers and power switches, **not OTAs**.

## Part A — Design specification (read this yourself)

### A1. Why this stands out
Most student buck converters are MATLAB/Simulink or LTspice models built from discrete parts. Open-source *integrated* converter work is rare; the closest found is a 2024 three-level flying-capacitor buck built with open-source PDKs ([UCU](https://investigadores.ucu.edu.uy/en/publications/open-source-multilevel-converter-power-ic-design-and-test/)).

This project covers the full IC version:
- transistor-level power stage and gate drivers in SKY130 5 V devices;
- an RTL digital controller taken through LibreLane;
- a compensator designed in the z-domain from an averaged model;
- limit-cycle-free resolution planning (DPWM vs ADC);
- **closed-loop mixed-signal co-simulation** (ngspice `d_cosim` + Verilator, available since ngspice 42).

TI interviewers can probe every block of it.

### A2. Electrical specification

| Parameter | Value |
|---|---|
| VIN | 3.3 V nominal (3.0–3.6 V) |
| VOUT | 1.8 V default; programmable 1.0–2.5 V via an 8-bit reference code |
| IOUT | 0–150 mA |
| fsw | 1 MHz (PWM, CCM) |
| Controller clock | 64 MHz |
| Power devices | `pfet_g5v0d10v5` high side, `nfet_g5v0d10v5` low side (check names and SOA in the installed PDK) |
| Off-chip L | 15 µH, DCR 0.1 Ω (ripple ≈ 55 mA p-p at 1.8 V out, about 36% of full load) |
| Off-chip C | 10 µF, ESR 10 mΩ |
| Output ripple | ≤ 1% of VOUT (18 mV p-p) |
| Load step 15 → 150 mA in 100 ns | undershoot ≤ 90 mV (5%); recovery to ±1% within 50 µs |
| Line step 3.0 ↔ 3.6 V in 10 µs | report the deviation |
| Line/load regulation | report |
| Efficiency | target ≥ 85% peak; report the full curve over 10–150 mA |
| Soft start | 1 ms ramp, overshoot ≤ 2%, no inrush above the current limit |
| Current limit | cycle-by-cycle valley limit, threshold programmable (default 250 mA) |
| Dead time | programmable 2–16 ns (3-bit); **no shoot-through at any PVT corner** |
| Light load (stretch) | zero-cross detection gives DCM; pulse-skipping/PFM below about 15 mA |

**Resolution plan.** This is the classic limit-cycle condition and must be documented:
- **DPWM:** 9 bits = a 6-bit counter at 64 MHz plus a 3-bit delay line, about 1.95 ns per tap. That gives 3.3 V / 512 ≈ 6.4 mV per LSB at the output.
- **Window ADC:** 10 mV LSB, 4-bit signed (±8 LSB), saturating outside the window.
- **Condition:** the DPWM LSB must be smaller than the ADC LSB, and the integral gain must satisfy the no-limit-cycle condition. Show both in `docs/CONTROL.md`.

**Out of scope, stated plainly:**
- **Reference:** VREF comes from an ideal source plus a resistor-string DAC; a bandgap is not designed.
- **Off-chip parts:** L and C are ideal models with DCR and ESR.
- **No full-chip analog-plus-digital integration layout** unless time permits; see A6.

### A3. Architecture
- **Power stage:** segmented power FETs (4 segments, so efficiency can be optimised at light load with fewer segments: a stretch goal); tapered gate drivers on the VIN domain; level shifters from 1.8 V to 3.3 V (check for `sky130_fd_sc_hvl__lsbuflv2hv*` in the installed liberty, otherwise use a custom cross-coupled shifter).
- **Dead-time generator:** non-overlap logic with a programmable delay, verified at every PVT corner.
- **Window ADC:** a resistor-string reference ladder around VREF, plus 15 StrongARM dynamic comparators clocked once per switching period, plus a thermometer-to-binary encoder with bubble correction. Report comparator offset with Monte Carlo and its effect on ADC DNL.
- **Hybrid DPWM:** the counter compare gives the coarse duty; a 3-bit delay line (current-starved or a plain inverter chain) gives the fine duty. Report DPWM DNL/INL at every PVT corner. Delay-line PVT variation is a known weakness: either add calibration (e.g. measure the delay line against the clock period and select taps) or quantify the error and its effect on the loop. Document the choice.
- **Digital controller (RTL):**
  - discrete PID with fixed-point coefficients;
  - anti-windup;
  - soft-start reference ramp;
  - current-limit handling (truncate the duty);
  - mode FSM (startup / CCM / DCM / fault);
  - an APB or simple register interface for VREF code, PID coefficients, dead time and current limit.
- **Protection comparators:**
  - **Valley current limit:** clocked comparator sensing VSW during low-side conduction (VDS of the LS device).
  - **Zero-cross detection:** comparator on VSW for DCM. Its timing granularity is limited by the clock; quantify this.

### A4. Design and verification flow
1. **Python modelling (`model/`):**
   - averaged small-signal model, control-to-output transfer function, LC resonance (≈13 kHz with these values);
   - z-domain PID design for crossover ≈ 50 kHz (≤ fsw/20) and phase margin ≥ 45°, including one switching period of ADC/compute delay and the DPWM delay;
   - coefficient quantisation study;
   - a **switched (cycle-accurate) plant model** for closed-loop simulation;
   - predicted load-step and start-up response.
2. **Controller RTL, verified with cocotb in closed loop against the Python switched plant:**
   - start-up;
   - load steps;
   - line steps;
   - VREF changes;
   - current-limit events;
   - limit-cycle checks: run 10 ms of steady state, then look at the duty-code histogram.

   Plus lint, coverage, and SymbiYosys properties: duty is always within limits, dead-time fields are never zero, the FSM stays legal, and anti-windup bounds the integrator.
3. **Transistor-level blocks in ngspice with the sky130 PDK:**
   - power stage + drivers: Ron, gate charge, switching loss, shoot-through check;
   - dead-time generator;
   - comparators (offset with Monte Carlo, delay);
   - delay line (PVT);
   - level shifters.

   Every block is characterised at all 5 corners × 3 temperatures × VIN 3.0/3.3/3.6.
4. **Closed-loop mixed-signal co-simulation:** the controller RTL runs through Verilator under ngspice `d_cosim` (ngspice ≥ 42; check the installed version), with the transistor-level power stage, comparators, delay line and ideal L/C/load. Show start-up, steady state and one load step at TT, and key corners if runtime allows. If `d_cosim` is unavailable, fall back to a synthesised gate-level controller netlist in ngspice for short windows, and document that.
5. **Efficiency:** measured from co-simulation (or transistor power stage + RTL duty) at 10, 25, 50, 100 and 150 mA, with a loss breakdown (conduction, switching, gate drive, controller from OpenSTA power).

### A5. Deliverables
- `docs/SPEC.md`, `docs/ARCHITECTURE.md` (block diagram, timing per switching cycle), `docs/CONTROL.md` (derivations, Bode plots, limit-cycle analysis, quantisation), `docs/BLOCKS.md` (per-block characterisation), `docs/RESULTS.md`.
- `docs/DECISIONS.md`, `docs/LEARNING.md`, `docs/INTERVIEW.md`.
- **Plots:** efficiency curve, load transient, line transient, start-up, Bode (model), DPWM DNL/INL across PVT, comparator offset histogram, loss breakdown.
- `results/summary.json` as the only source of numbers; `make all`; CI for lint, controller sim and model tests.

### A6. Physical design
- **Required:** the digital controller through LibreLane on sky130 (area, timing at all corners, power).
- **Required:** power FET array plus drivers in Magic, using parametric unit-finger generators via Magic Tcl, with DRC/LVS/PEX. Re-simulate Ron and switching loss post-layout.
- **Stretch:** comparators and delay-line layout; top-level integration.

### A7. Done when
- The loop is stable across PVT in co-simulation, with load-step and ripple specs met (or each miss explained).
- There is no shoot-through at any corner.
- The efficiency curve is complete.
- The controller is LibreLane-clean and the power stage DRC/LVS-clean.
- You can derive the control-to-output transfer function and explain the limit-cycle condition on a whiteboard.

---

## Part B — Prompt for Claude Code

**How to use this:** paste this **entire file** (Part A and Part B) into Claude Code as one message, inside a clone of `synchronous-buck-converter-`.

---

You are working in my GitHub repo `synchronous-buck-converter-` (owner `vikyathhj-ui`, currently empty). Build `digital-buck-sky130`: a digitally controlled synchronous buck converter in SKY130, with a transistor-level power stage, an RTL controller and closed-loop mixed-signal co-simulation. Part A of this message is the binding specification. I am a final-year ECE student applying for power-management and mixed-signal IC roles (TI and similar); correctness and honesty matter more than speed.

### Non-negotiable rules
1. **Never fabricate or hand-type a result.** Every number comes from a script parsing an ngspice/Verilator/LibreLane/Magic/Netgen output, stored in `results/summary.json` with its source path. Hand analysis is labelled "analysis" and compared with simulation.
2. **Never tune results to targets by hiding conditions.** Report misses with the physical reason, propose trade-offs, and **ask me** before relaxing any spec.
3. **Git:**
   - Branch `rework/buck`.
   - Conventional Commits after each gate, with what/why/verification (command + result) in the body. Keep the default `Co-Authored-By: Claude` trailer.
   - Push after each commit; open a PR at each phase end with `gh pr create`. **Never merge**, never force-push, never rewrite history.
4. **Ask me before:** renaming the repo, changing visibility, installing system packages, or acting outside this repo.
5. Never commit PDK files, `*.raw` or large logs.
6. Keep `PROGRESS.md` current so a new session can continue from "Read CLAUDE.md and PROGRESS.md and continue".
7. Keep `docs/DECISIONS.md`, `docs/LEARNING.md` and `docs/INTERVIEW.md` (40+ questions with answers using this project's numbers). The questions must cover:
   - the buck volt-second balance;
   - choosing L and C;
   - CCM vs DCM;
   - why synchronous rectification;
   - dead time vs shoot-through vs body-diode loss;
   - the averaged model and the LC double pole;
   - why the ADC/DPWM delay costs phase;
   - z-domain PID;
   - the limit-cycle condition;
   - hybrid DPWM trade-offs and delay-line PVT;
   - StrongARM comparator operation and offset;
   - the loss breakdown;
   - why 5 V devices;
   - level shifting;
   - valley vs peak current limit.

### Phase 0 — Setup (one commit)
- **Environment check:** `ngspice` (version ≥ 42 needed for `d_cosim`; check that `vlnggen` or the documented Verilator glue works by building the shipped example), `verilator`, `iverilog`, `yosys`, `sby` + a solver, `python3` with numpy/scipy/matplotlib/control/cocotb/cocotb-coverage, `librelane`/`openlane`, `openroad`, `sta`, `magic`, `netgen`, `klayout`, the sky130A PDK (`PDK_ROOT`), and the `sky130_fd_sc_hd` and `sky130_fd_sc_hvl` liberty files.
  - Search the PDK for `g5v0d10v5` models and `lsbuflv2hv` cells and report them.
  - Print a found/missing table. If anything is missing, stop and give me install commands; no sudo.
- **Save the brief and set up the repo:** save this message verbatim as `docs/BRIEF.md`. Create `CLAUDE.md` ("binding spec is docs/BRIEF.md"), `PROGRESS.md`, `.gitattributes` (`* text=auto eol=lf`), `.gitignore`, and `LICENSE` (Apache-2.0).
- **Layout:**
  ```
  model/  rtl/  tb/  formal/  xschem/  spice/  cosim/  layout/  flow/  scripts/  results/  docs/  .github/workflows/
  ```

### Phase 1 — Modelling and control design
- Python averaged model, z-domain PID design, quantisation study, switched plant model, and the resolution plan check, written up in `docs/CONTROL.md` with plots.

Gate: **stop and show me** the Bode plot, phase margin and predicted load step before RTL.

### Phase 2 — Controller RTL and closed-loop verification
- RTL: PID, anti-windup, soft start, DPWM counter + fine-select logic, mode FSM, current-limit handling, registers.
- cocotb closed loop against the Python switched plant (all scenarios in A4.2), coverage, and SymbiYosys properties.
- CI.

Gate: all pass. Commit, then open a PR.

### Phase 3 — Transistor-level blocks
- Xschem schematics plus testbenches: power stage + drivers, dead-time generator, StrongARM comparator, window-ADC ladder, delay line, level shifters.
- Characterise each across PVT (and Monte Carlo for the comparators and delay line) with `scripts/char_*.py`.
- Size the power FETs for the efficiency target and justify it with a loss model compared against simulation.

Gate: `docs/BLOCKS.md` complete. Commit.

### Phase 4 — Mixed-signal closed loop
- `cosim/`: Verilator-compiled controller under ngspice `d_cosim` with the transistor blocks. Runs: start-up, steady state, load step, line step at TT, then key corners as runtime allows (run in the background).
- Efficiency at 5 load points with a loss breakdown.
- If `d_cosim` fails, use the gate-level fallback and document it.

Gate: `docs/RESULTS.md` with plots. Commit, then open a PR.

### Phase 5 — Physical
- LibreLane on the controller: area, timing at all corners, power from a VCD of a closed-loop run.
- Magic parametric power FET plus driver layout with DRC (Magic + KLayout), LVS (Netgen) and PEX; post-layout Ron and switching-loss re-simulation.

Gate: clean. Commit.

### Phase 6 — Docs and close
- **README:**
  - pitch;
  - block diagram;
  - key results table auto-generated from `summary.json`;
  - efficiency and load-transient plots;
  - "Reproduce";
  - "Limitations": no silicon; ideal VREF; ideal off-chip L/C; which blocks have layout;
  - "AI assistance": "Developed with Claude Code; all results reproduced by Vikyath J with `make all`."
- `results/resume_bullets.md`: 3 bullets using only `summary.json` numbers.
- Open the final PR. Then ask me whether to rename the repo to `digital-buck-sky130`.

Start with Phase 0, in plan mode, and show me the plan before editing files.
