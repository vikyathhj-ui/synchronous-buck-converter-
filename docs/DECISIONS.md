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
