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

## Phase 2 — Controller RTL (NEXT, only after the user approves the Phase 1 gate)
- RTL must match `model/controller.py: FixedPid` and the timing in `model/sim.py` (DECISIONS D10).
- Before the first PR: ask the user about creating `main` as the base branch (repo has only rework/buck).
