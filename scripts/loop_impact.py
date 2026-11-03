#!/usr/bin/env python3
"""Loop-level effect of the measured transistor-level non-idealities (golden closed-loop model,
model/sim.py: simulate, with the Phase 2 controller):

  dpwm_cal : the same with results/phase3/dpwm_cal.json (calibrated delay line, measured fine steps).
  dpwm : each of the 45 PVT rows of results/phase3/dpwm.json (uncalibrated delay line) replaces
         the ideal fine steps by the measured ones; 8 loads 10..150 mA; limit cycle = more than one
         duty code in the last 1000 periods of a 3000-period run (VIN 3.3 V).
  adc  : 200 random draws of the 15 comparator offsets with the Monte Carlo sigma measured at the
         ADC common mode for 1.8 V out (0.9 V), referred to VOUT (x2 through the divider);
         4 loads; limit cycles, static VOUT error, and the analytic zero-bin check
         (zero-bin width vs the 7.03 mV DPWM step at VIN 3.6 V).
Writes results/phase3/loop_impact.json.
"""
import json
import pathlib
from dataclasses import replace

import numpy as np

import sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model.buck import Buck, Dpwm          # noqa: E402
from model.ctrl_ref import Regs            # noqa: E402
from model.sim import simulate             # noqa: E402
from spicelib import pmap                  # noqa: E402

P3 = ROOT / "results" / "phase3"
B = Buck()
N, OBS = 3000, 1000


def lc_run(args):
    io, fine_table, offsets = args
    dp = Dpwm(fine_table=tuple(fine_table)) if fine_table is not None else Dpwm()
    r = simulate(replace(B, g_load=io / 1.8), dp, Regs(), n=N, adc_offsets=offsets)
    codes = np.unique(r.d[-OBS:])
    return {"n_codes": int(len(codes)), "v_mean": float(r.v[-OBS:].mean()), "v_pp": float(np.ptp(r.v[-OBS:]))}


def main():
    out = {"source": "scripts/loop_impact.py (model/sim.py golden closed loop, inputs from results/phase3)"}
    loads = np.linspace(0.010, 0.150, 8)
    dp = json.loads((P3 / "dpwm.json").read_text()) if (P3 / "dpwm.json").exists() else None
    if dp and "pvt" in dp:
        jobs, keys = [], []
        for row in dp["pvt"]:
            tab = [t - row["ton"][0] for t in row["ton"]]
            for io in loads:
                jobs.append((float(io), tab, None))
                keys.append((row["corner"], row["temp"], row["vdd"], float(io)))
        res = pmap(lc_run, jobs)
        base = pmap(lc_run, [(float(io), None, None) for io in loads])
        n_lc = sum(r["n_codes"] > 1 for r in res)
        out["dpwm_uncal"] = {"cases": len(res), "limit_cycles": int(n_lc),
                             "worst_v_pp": max(r["v_pp"] for r in res),
                             "per_case": [dict(zip(("corner", "temp", "vdd", "io"), k), **r) for k, r in zip(keys, res)],
                             "ideal_dpwm_limit_cycles": int(sum(r["n_codes"] > 1 for r in base))}
        print(f"uncalibrated DPWM: limit cycle in {n_lc} of {len(res)} PVT x load cases "
              f"(ideal DPWM: {out['dpwm_uncal']['ideal_dpwm_limit_cycles']} of {len(base)})")
    dc = json.loads((P3 / "dpwm_cal.json").read_text()) if (P3 / "dpwm_cal.json").exists() else None
    if dc and "pvt" in dc:
        jobs, keys = [], []
        for row in dc["pvt"]:
            tab = [t - row["ton"][0] for t in row["ton"]]      # measured fine delays with the RTL tap mapping
            for io in loads:
                jobs.append((float(io), tab, None))
                keys.append((row["corner"], row["temp"], row["vdd"], float(io)))
        res = pmap(lc_run, jobs)
        n_lc = sum(r["n_codes"] > 1 for r in res)
        out["dpwm_cal"] = {"cases": len(res), "limit_cycles": int(n_lc), "worst_v_pp": max(r["v_pp"] for r in res),
                           "per_case": [dict(zip(("corner", "temp", "vdd", "io"), k), **r) for k, r in zip(keys, res)]}
        print(f"calibrated DPWM: limit cycle in {n_lc} of {len(res)} PVT x load cases")
    cp = json.loads((P3 / "comparator.json").read_text()) if (P3 / "comparator.json").exists() else None
    if cp and "mc_stats" in cp:
        sig_c = cp["mc_stats"]["0.9"]["sigma"]      # ADC common mode at VOUT 1.8 V (VOUT/2)
        sig_v = 2 * sig_c                           # referred to VOUT through the /2 divider
        rng = np.random.default_rng(1)
        draws = rng.normal(0.0, sig_v, size=(200, 15))
        zero_bin = 0.010 + draws[:, 8] - draws[:, 7]
        nonmono = int(np.sum(np.any(np.diff((np.arange(15) - 7.5) * 0.010 + draws, axis=1) <= 0, axis=1)))
        lo = [0.015, 0.05, 0.10, 0.15]
        jobs = [(io, None, draws[k].tolist()) for k in range(200) for io in lo]
        res = pmap(lc_run, jobs)
        n_lc = sum(r["n_codes"] > 1 for r in res)
        verr = np.array([r["v_mean"] - 1.8 for r in res])
        out["adc_offsets"] = {"sigma_comparator": sig_c, "sigma_vout_referred": sig_v, "draws": 200,
                              "cases": len(res), "limit_cycles": int(n_lc),
                              "zero_bin_lt_dpwm_step_fraction": float(np.mean(zero_bin < 0.00703)),
                              "zero_bin_min": float(zero_bin.min()),
                              "nonmonotonic_threshold_draws": nonmono,
                              "vout_error_sigma": float(verr.std()), "vout_error_max": float(np.abs(verr).max())}
        print(f"ADC offsets (sigma {sig_c*1e3:.2f} mV at the comparator, {sig_v*1e3:.2f} mV at VOUT): "
              f"limit cycle in {n_lc} of {len(res)} cases; zero bin < DPWM step in "
              f"{np.mean(zero_bin < 0.00703)*100:.1f} % of draws; VOUT error sigma {verr.std()*1e3:.2f} mV")
    (P3 / "loop_impact.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
