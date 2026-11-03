#!/usr/bin/env python3
"""Analytical loss model and power-FET sizing (kind = "analysis", inputs from results/phase3/fet.json).

Loss terms per switching period, VIN 3.3 V, VOUT 1.8 V, fsw 1 MHz:
  conduction   Irms^2 (D Rhs + (1-D) Rls + DCR),  Irms^2 = Io^2 + dI^2/12
  gate drive   (Qg_hs + Qg_ls) VIN fsw x (1 + 1/(taper - 1))   (tapered driver adds its own charge)
  output cap   (Qoss_hs + Qoss_ls) VIN fsw                     (HS turn-on charges the switch node)
  overlap      0.5 VIN Io (t_r + t_f) fsw                      (HS hard switching; t_sw from the driver)
  dead time    2 Vbd Io t_dead fsw                             (LS body diode during both dead times)
The widths are chosen to maximise the mean efficiency over the brief's load points.
Writes results/phase3/sizing.json; the transistor-level check is scripts/char_powerstage.py.
"""
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
FET = json.loads((ROOT / "results" / "phase3" / "fet.json").read_text())
TT = [r for r in FET["rows"] if r["corner"] == "tt" and r["temp"] == 27 and r["vin"] == 3.3][0]

VIN, VOUT, FSW, L, DCR = 3.3, 1.8, 1e6, 15e-6, 0.1
LOADS = [0.010, 0.025, 0.050, 0.100, 0.150]
TAPER = 4.0
T_SW = 2e-9          # assumed HS rise + fall total per edge pair, replaced by simulation
T_DEAD = 8e-9        # DT code 3 = 8 ns, each edge


def losses(w_hs, w_ls, io, dev=TT, vin=VIN, t_sw=T_SW, t_dead=T_DEAD, ripple=True, t_bd=None):
    r_hs = dev["p"]["ron_mm"] / w_hs
    r_ls = dev["n"]["ron_mm"] / w_ls
    D = (VOUT + io * (DCR + 0.5 * (r_hs + r_ls))) / vin
    di = (vin - VOUT) * D / (FSW * L) if ripple else 0.0
    irms2 = io ** 2 + di ** 2 / 12
    p = {
        "cond_hs": irms2 * D * r_hs,
        "cond_ls": irms2 * (1 - D) * r_ls,
        "cond_dcr": irms2 * DCR,
        "gate": (dev["p"]["qg_mm"] * w_hs + dev["n"]["qg_mm"] * w_ls) * vin * FSW * (1 + 1 / (TAPER - 1)),
        "coss": (dev["p"]["qoss_mm"] * w_hs + dev["n"]["qoss_mm"] * w_ls) * vin * FSW,
        "overlap": 0.5 * vin * io * t_sw * FSW,
        "deadtime": dev["n"]["vbd"] * io * (2 * t_dead if t_bd is None else t_bd) * FSW,
    }
    pout = VOUT * io
    p["total"] = sum(p.values())
    p["eff"] = pout / (pout + p["total"])
    return p


def mean_eff(w_hs, w_ls):
    return float(np.mean([losses(w_hs, w_ls, io)["eff"] for io in LOADS]))


def main():
    grid_hs = np.arange(4, 81, 1.0)
    grid_ls = np.arange(2, 41, 1.0)
    best = max(((mean_eff(a, b), a, b) for a in grid_hs for b in grid_ls))
    _, w_hs, w_ls = best
    # round each to a multiple of 4 segments x 10 um fingers
    w_hs = float(np.round(w_hs / 0.4) * 0.4)
    w_ls = float(np.round(w_ls / 0.4) * 0.4)
    curve = {f"{io*1e3:.0f}mA": losses(w_hs, w_ls, io) for io in LOADS}
    out = {
        "kind": "analysis", "source": "scripts/size_power.py (inputs: results/phase3/fet.json tt/27C/3.3V)",
        "assumptions": {"taper": TAPER, "t_sw_s": T_SW, "t_dead_s": T_DEAD, "loads_A": LOADS},
        "w_hs_mm": w_hs, "w_ls_mm": w_ls,
        "fingers_hs": int(round(w_hs * 100)), "fingers_ls": int(round(w_ls * 100)),
        "ron_hs_tt": TT["p"]["ron_mm"] / w_hs, "ron_ls_tt": TT["n"]["ron_mm"] / w_ls,
        "mean_eff": mean_eff(w_hs, w_ls), "curve": curve,
        "sensitivity": {f"x{s}": mean_eff(w_hs * s, w_ls * s) for s in (0.5, 0.75, 1.0, 1.5, 2.0)},
    }
    (ROOT / "results" / "phase3" / "sizing.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "curve"}, indent=1))
    for k, v in curve.items():
        print(k, {a: round(b * 1e3, 3) if a != "eff" else round(b, 4) for a, b in v.items()})


if __name__ == "__main__":
    main()
