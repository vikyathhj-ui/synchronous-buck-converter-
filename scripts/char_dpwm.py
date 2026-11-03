#!/usr/bin/env python3
"""DPWM fine stage (spice/dpwm_fine.spice), uncalibrated.

One simulation per condition runs 8 switching periods with fine_sel = 0..7 (coarse = 2), and
measures the HS pulse width ton(k). From it:
  step_k   = ton(k) - ton(k-1), k = 1..7, and the coarse-boundary step Tclk - (ton(7) - ton(0))
  DNL_k    = step_k / LSB - 1, LSB = Tclk/8 = 1.953 ns;  INL_k = (ton(k) - ton(0)) / LSB - k
  tap_scale = mean tap / ideal tap (input to the loop-level check)
  pvt : every corner x temperature x VDD 1.62/1.80/1.98
  mc  : 100 mismatch samples at tt / 27 C / 1.8 V
Writes results/phase3/dpwm.json.
"""
import sys

import numpy as np

from spicelib import CORNERS, PDK, TEMPS, header, include, pmap, run, save

HD = PDK / "libs.ref" / "sky130_fd_sc_hd" / "spice" / "sky130_fd_sc_hd.spice"
TCLK = 1 / 64e6
LSB = TCLK / 8
TP = 100e-9      # one test period


def sim(corner, temp, vdd, mc=False, seed=0):
    tag = f"dpwm_{corner}_{temp}_{vdd}_{'mc' + str(seed) if mc else 'nom'}"
    srcs = []
    for b in range(3):
        pts = []
        for k in range(8):
            lvl = vdd * ((k >> b) & 1)
            pts += [f"{k * TP + 1e-9}", f"{lvl}", f"{(k + 1) * TP}", f"{lvl}"]
        srcs.append(f"VS{b} s{b} 0 pwl(0 0 " + " ".join(pts) + ")")
    meas = "\n".join(
        f"meas tran ton{k} trig v(hs_pwm) val={vdd/2} rise=1 td={k * TP + 5e-9} "
        f"targ v(hs_pwm) val={vdd/2} fall=1 td={k * TP + 5e-9}" for k in range(8))
    seedline = f"setseed {seed}\nreset\n" if mc else ""
    n = header(corner, temp, mc=mc, title=tag) + include("deadtime.spice", "dpwm_fine.spice") + f""".include {HD}
VDD vdd 0 {vdd}
VSET pwm_set 0 pulse(0 {vdd} 10n 50p 50p {TCLK - 100e-12} {TP})
VRST pwm_rst 0 pulse(0 {vdd} {10e-9 + 2 * TCLK} 50p 50p {TCLK - 100e-12} {TP})
{chr(10).join(srcs)}
X1 pwm_set pwm_rst s0 s1 s2 hs_pwm vdd 0 dpwm_fine
.control
{seedline}tran 0.02n {8 * TP} 0 0.05n
{meas}
quit
.endc
.end
"""
    v = run(n, tag)
    ton = np.array([v[f"ton{k}"] for k in range(8)])
    steps = np.append(np.diff(ton), TCLK - (ton[7] - ton[0]))
    return {"corner": corner, "temp": temp, "vdd": vdd, "seed": seed, "ton": ton.tolist(),
            "dnl": (steps / LSB - 1).tolist(), "inl": ((ton - ton[0]) / LSB - np.arange(8)).tolist(),
            "tap_scale": float(np.mean(np.diff(ton)) / LSB)}


def pvt_one(a):
    return sim(*a)


def mc_one(seed):
    return sim("tt", 27, 1.8, mc=True, seed=seed)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    import json, pathlib
    path = pathlib.Path(__file__).resolve().parents[1] / "results" / "phase3" / "dpwm.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    if what in ("pvt", "all"):
        rows = pmap(pvt_one, [(c, t, v) for c in CORNERS for t in TEMPS for v in (1.62, 1.8, 1.98)])
        data["pvt"] = rows
        ts = [r["tap_scale"] for r in rows]
        dn = [d for r in rows for d in r["dnl"]]
        print(f"tap_scale min {min(ts):.3f} max {max(ts):.3f}; DNL min {min(dn):+.2f} max {max(dn):+.2f} LSB")
    if what in ("mc", "all"):
        rows = pmap(mc_one, range(1, 101))
        data["mc"] = rows
        dn = np.array([r["dnl"][:7] for r in rows])
        print(f"MC tt: within-line DNL sigma {dn.std():.3f} LSB, max |DNL| {np.abs(dn).max():.3f} LSB")
    data["source"] = "scripts/char_dpwm.py (ngspice)"
    save("dpwm", data)
