# Progress

## Phase 0 — Setup (DONE)
- Cloned to `~/projects/synchronous-buck-converter-`, branch `rework/buck` (repo was empty).
- `scripts/env_check.sh` → `results/env_check.txt`: `RESULT: ALL OK` (all tools, Python packages, PDK,
  5 V device DC op, vlnggen + d_cosim counter). cocotb-coverage 2.0 was installed by the user with
  `pip install --user --break-system-packages cocotb-coverage` in the container (lost on `docker rm`).
- `docs/BRIEF.md` (verbatim brief), `CLAUDE.md`, `LICENSE`, folder skeleton, `docs/DECISIONS.md` (D1–D5),
  `docs/LEARNING.md`, `docs/INTERVIEW.md` (topics only so far).

## Phase 1 — Modelling and control design (DONE, waiting at gate for user review)
- `model/buck.py` (averaged, exact sampled, switched plant), `model/controller.py` (ADC, z-domain PID
  design, margins, bit-exact `FixedPid`), `model/sim.py` (closed-loop golden model), `model/phase1.py`
  (all numbers -> `results/summary.json["phase1"]`, plots -> `results/plots/phase1/`).
- `docs/CONTROL.md`: tables auto-filled by `scripts/update_docs.py`. `make all` = model + tests + docs.
- User required PM >= 45 deg at every robustness corner -> redesigned to fc 30 kHz / PM 60 deg, Q5
  (DECISIONS D11); worst case 48.7 deg over 162 cases.
- Open items (CONTROL.md section 8): derivative kicks (kd = 35); valley limit sampled once per period;
  window-ADC common mode (feedback divider); line step about +/-170 mV (VIN feedforward would need a VIN sensor).

## Phase 2 — Controller RTL and closed-loop verification (DONE, PR #1 open into main, user merges)
- `rtl/buck_ctrl_top.v`, `rtl/therm2bin.v`; golden model `model/ctrl_ref.py`; per-clock golden sim
  `model/sim.py: simulate_clocked`; timing contract in `docs/ARCHITECTURE.md` (DECISIONS D12–D19).
- cocotb bench `tb/` (bit-exact scoreboard every period, per-clock Python plant): 11/11 pass, 0
  mismatches; functional coverage 100 %; Verilator lint clean; SymbiYosys k-induction PASS.
- Results: `results/phase2/*.json` -> `summary.json["phase2"]` (scripts/collect_phase2.py);
  `docs/VERIFICATION.md`. CI: `.github/workflows/ci.yml` (lint, model tests, formal, cocotb QUICK).
- Open: DCM does not regulate with the CCM PID (D19, off by default); slow large-signal recovery when
  the window ADC saturates (line step). Ask the user whether to work on either.
- `main` created at 5a9c47a and set as default (user approved). PR #1 = Phases 1-2. After the user merges, fast-forward rework/buck to origin/main if needed.

## Phase 3 — Transistor-level blocks (IN PROGRESS; WIP commit 2026-11-03, results below are on disk)
Done (results in results/phase3/*.json, DECISIONS D20-D30):
- Infrastructure: spice/models/sky130_mini.lib, scripts/spicelib.py (1 thread per ngspice, `save`
  lines, SPICE_REUSE=1 log reuse, SPICE_WORKERS override, old log deleted before a re-run - D29),
  check_cell_pins.py, gen_xschem.py + lvs_xschem.sh (17/17 matched before the cmp_adc change).
- Unit FETs, sizing (HS 19.2 mm, LS 8.8 mm), power stage + drivers, level shifters, delay cells,
  dead time (min 3.97 ns, shoot-through free), sw_cmp (45/45 functional, MC sigma 3.80/3.96 mV),
  ADC string + VOUT/2 divider (adcref.json, re-run 2026-11-03), DPWM calibration (dpwm_cal.json:
  PVT DNL -0.875..+0.665 LSB; MC DNL sigma 0.084 LSB).
- RTL: delay-line calibration + ADC sampled 2 clocks after the edge; cocotb 12/12, lint 0, formal PASS.
- 2026-11-03 finding (D30): the full ADC front end failed - comparator kickback through the unequal
  tap / divider networks, and the benches clocked faster than the RTL. User chose a static preamp:
  new cmp_adc = adc_pre + cmp_hv (+ adc_pbias) in spice/comparator.spice; char_adc.py and
  char_comparator.py now use the RTL clocking (1 MHz, 15.6 ns pulse) and a 5 ns max step.
  comparator.json is STILL the old cmp_hv data until char_comparator.py is re-run.
- char_adc.py: ramp split into 5 segments (D29); MC DNL computed from cmp_adc MC offsets + ladder
  MC ("mcc", user decision D29).

ADC PVT with cmp_adc ran 2026-11-03 (results/phase3/adc.json "pvt", 64 min at 5 workers):
tt 27 C and ff 125 C / 3.6 V correct (threshold error 0 within the +/-0.025 LSB ramp resolution,
0 missing codes). ff/ss/sf/fs 27 C and ss -40 C: every real flip is at the ideal position, plus
scattered single wrong decisions 25-50+ mV from any threshold, and some overlap mismatches
(history dependent). A single cmp_adc decides cleanly at every corner (no SR-latch race: loser
output max 0.65 V, latch inputs stay > 1.7 V).
PAUSED HERE (user, 2026-11-07). Cause found: NOT the step size (ff 27 seg 0: 8 / 5 / 5 wrong at
5 / 2 / 1 ns, at different places). Waveform dump (results/phase3/work/_probe.py) showed the
cmp_hv output SR latch flipping inside one 0.55 ns step when the winning output is released at
reset, with trapezoidal ringing before it: a numerical artifact. With `.option method=gear`:
ff 27 seg 0 0 wrong (was 8), fs 27 seg 0 0 wrong (was 42), same 40-decision window 0 (was 1).
Next: add method=gear to the char_adc.py and char_comparator.py netlists (write D31; consider
whether char_swcmp / DPWM latches need the same check), then re-run char_adc.py pvt (~65 min).

Remaining (cd scripts; export SPICE_REUSE=1 SPICE_WORKERS=5):
  python3 char_adc.py pvt             # again, after the step-size question is settled
  python3 char_comparator.py all      # cmp_adc: 45 PVT + 300 MC (old logs are cmp_hv, will re-run)
  python3 char_adc.py mcc             # needs the new comparator.json
  python3 loop_impact.py; python3 collect_phase3.py; python3 update_docs.py
Then: add adc_pre / cmp_adc / adc_pbias to gen_xschem.py + LVS, update the window-ADC schematic,
check every number in docs/BLOCKS.md (still from the old cmp_hv results), update INTERVIEW/LEARNING,
commit Phase 3 (no PR at Phase 3 per the brief), then Phase 4.
Watch memory: run one char script at a time; `free -m` (RAM + 2 GB swap).

## Phase 4 — Mixed-signal closed loop (NOT STARTED)
