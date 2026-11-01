# Progress

## Phase 0 — Setup (DONE)
- Cloned to `~/projects/synchronous-buck-converter-`, branch `rework/buck` (repo was empty).
- `scripts/env_check.sh` → `results/env_check.txt`: `RESULT: ALL OK` (all tools, Python packages, PDK,
  5 V device DC op, vlnggen + d_cosim counter). cocotb-coverage 2.0 was installed by the user with
  `pip install --user --break-system-packages cocotb-coverage` in the container (lost on `docker rm`).
- `docs/BRIEF.md` (verbatim brief), `CLAUDE.md`, `LICENSE`, folder skeleton, `docs/DECISIONS.md` (D1–D5),
  `docs/LEARNING.md`, `docs/INTERVIEW.md` (topics only so far).

## Phase 1 — Modelling and control design (NEXT)
- `model/`: averaged model, z-domain PID, quantisation study, switched plant, resolution-plan check.
- Write up in `docs/CONTROL.md` with plots.
- Gate: STOP and show the user the Bode plot, phase margin and predicted load step before any RTL.
