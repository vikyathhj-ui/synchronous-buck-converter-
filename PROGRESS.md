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

## Phase 2 — Controller RTL and closed-loop verification (DONE, PR pending user answer on `main`)
- `rtl/buck_ctrl_top.v`, `rtl/therm2bin.v`; golden model `model/ctrl_ref.py`; per-clock golden sim
  `model/sim.py: simulate_clocked`; timing contract in `docs/ARCHITECTURE.md` (DECISIONS D12–D19).
- cocotb bench `tb/` (bit-exact scoreboard every period, per-clock Python plant): 11/11 pass, 0
  mismatches; functional coverage 100 %; Verilator lint clean; SymbiYosys k-induction PASS.
- Results: `results/phase2/*.json` -> `summary.json["phase2"]` (scripts/collect_phase2.py);
  `docs/VERIFICATION.md`. CI: `.github/workflows/ci.yml` (lint, model tests, formal, cocotb QUICK).
- Open: DCM does not regulate with the CCM PID (D19, off by default); slow large-signal recovery when
  the window ADC saturates (line step). Ask the user whether to work on either.
- Before opening the Phase 2 PR: ask the user to approve creating `main` as the base branch.

## Phase 3 — Transistor-level blocks (NEXT)
