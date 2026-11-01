# digital-buck-sky130 (repo `synchronous-buck-converter-`)

**Binding spec is `docs/BRIEF.md`.** Read it, then `PROGRESS.md`, before doing anything.

- Tools run in container `iic-osic`: `docker exec -w /foss/projects/synchronous-buck-converter- iic-osic bash -lc '...'`
  (the `-l` is required). git/gh run on the host (no gh in the container).
- Branch `rework/buck`. Conventional Commits, push after each commit, PRs at phase ends; never merge,
  force-push or rewrite history. Ask before rename, visibility change, installs, or acting outside the repo.
- Every number comes from a script parsing tool output into `results/summary.json`. No hand-typed results.
- `d_cosim` connects Verilog vector ports MSB first (verified in `scripts/env_check.sh`).
