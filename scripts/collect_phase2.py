#!/usr/bin/env python3
"""Merge the Phase 2 results into results/summary.json["phase2"] and draw the RTL plots.

Inputs (all produced by tools, nothing typed by hand):
  results/phase2/<test>.json      cocotb closed-loop metrics (tb/test_buck_ctrl.py)
  results/phase2/coverage.yml     cocotb-coverage functional coverage
  results/phase2/lint.txt         Verilator -Wall lint log (make lint)
  formal/buck_ctrl/status         SymbiYosys result (make formal)
  tb/results.xml                  cocotb JUnit results
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
P2 = ROOT / "results" / "phase2"
PLOTS = ROOT / "results" / "plots" / "phase2"
C1, C2, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                     "legend.frameon": False})


def rel(p):
    return str(p.relative_to(ROOT))


def main():
    S = {}
    for f in sorted(P2.glob("test_*.json")):
        d = json.loads(f.read_text())
        src = d.pop("source")
        S[f.stem] = {"value": d, "kind": "rtl-sim", "source": src, "file": rel(f)}

    junit = ROOT / "tb" / "results.xml"
    if junit.exists():
        cases = ET.parse(junit).getroot().iter("testcase")
        res = {}
        for c in cases:
            st = "fail" if c.find("failure") is not None or c.find("error") is not None else \
                 "skip" if c.find("skipped") is not None else "pass"
            res[c.get("name")] = st
        S["cocotb_results"] = {"value": res, "kind": "rtl-sim", "source": rel(junit)}

    cov = P2 / "coverage.yml"
    if cov.exists():
        y = yaml.safe_load(cov.read_text())
        pts = {k: round(v["cover_percentage"], 1) for k, v in y.items() if k.count(".") == 1}
        S["functional_coverage_pct"] = {"value": pts, "kind": "rtl-sim", "source": rel(cov)}

    lint = P2 / "lint.txt"
    if lint.exists():
        txt = lint.read_text()
        S["lint"] = {"value": {"warnings": len(re.findall(r"%Warning", txt)), "errors": len(re.findall(r"%Error", txt))},
                     "kind": "lint", "source": rel(lint)}

    status = ROOT / "formal" / "buck_ctrl" / "status"
    if status.exists():
        S["formal"] = {"value": status.read_text().split()[0], "kind": "formal",
                       "source": "formal/buck_ctrl.sby (status file)"}

    path = ROOT / "results" / "summary.json"
    summary = json.loads(path.read_text()) if path.exists() else {}
    summary["phase2"] = S
    path.write_text(json.dumps(summary, indent=1, default=float) + "\n")

    PLOTS.mkdir(parents=True, exist_ok=True)
    ls = P2 / "load_step_dense.npy"
    if ls.exists():
        d = np.load(ls)
        t = (d[:, 0] - 2.0e-3) * 1e6
        fig, ax = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
        ax[0].plot(t, d[:, 1] * 1e3, color=C1, lw=1.0)
        for s_ in (1.01, 0.99):
            ax[0].axhline(1800 * s_, color=INK2, lw=0.8, ls=":")
        ax[0].axhline(1800 - 90, color="#d03b3b", lw=0.8, ls="-.")
        ax[0].text(-95, 1713, "spec limit: 90 mV undershoot", color=INK2)
        ax[0].set_ylabel("VOUT [mV]")
        m = S["test_load_step"]["value"]
        ax[0].set_title(f"RTL in closed loop (cocotb): 15 -> 150 -> 15 mA, undershoot "
                        f"{m['undershoot']*1e3:.1f} mV, recovery {m['recovery_1pct']*1e6:.1f} us")
        ax[1].plot(t, d[:, 2] * 1e3, color=C1, lw=0.8)
        ax[1].set_ylabel("iL [mA]")
        ax[1].set_xlabel("time from step [us]")
        fig.tight_layout()
        fig.savefig(PLOTS / "rtl_load_step.png", dpi=150)
        plt.close(fig)
    dc = P2 / "dcm_dense.npy"
    if dc.exists():
        d = np.load(dc)
        t = (d[:, 0] - d[0, 0]) * 1e6
        fig, ax = plt.subplots(figsize=(8, 3.2))
        ax.plot(t, d[:, 2] * 1e3, color=C1, lw=1.0)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xlabel("time [us]")
        ax.set_ylabel("iL [mA]")
        ax.set_title("RTL in DCM at 5 mA (cocotb): LS turned off after the zero-cross is detected")
        fig.tight_layout()
        fig.savefig(PLOTS / "rtl_dcm_il.png", dpi=150)
        plt.close(fig)
    print(json.dumps({k: v["value"] for k, v in S.items()}, indent=1, default=float))


if __name__ == "__main__":
    main()
