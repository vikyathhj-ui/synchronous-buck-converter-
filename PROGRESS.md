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
- Open questions for the user (CONTROL.md section 8): L/C tolerance corner PM 28 deg; derivative kicks
  (kd = 68 LSB/LSB); start-up peak iL 221 mA vs the 250 mA limit; valley limit sampled once per
  period; window-ADC common mode (feedback divider).

## Phase 2 — Controller RTL (NEXT, only after the user approves the Phase 1 gate)
- RTL must match `model/controller.py: FixedPid` and the timing in `model/sim.py` (DECISIONS D10).
- Before the first PR: ask the user about creating `main` as the base branch (repo has only rework/buck).
