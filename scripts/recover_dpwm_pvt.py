#!/usr/bin/env python3
"""Rebuild results/phase3/dpwm.json["pvt"] from the ngspice logs of scripts/char_dpwm.py (used once,
after the uncalibrated-DPWM Monte Carlo was stopped: calibration made it unnecessary). Same parsing
and formulas as char_dpwm.sim()."""
import re
import numpy as np
from char_dpwm import LSB, TCLK
from spicelib import CORNERS, OUT, TEMPS, WORK, save

rows = []
for c in CORNERS:
    for t in TEMPS:
        for v in (1.62, 1.8, 1.98):
            log = (WORK / f"dpwm_{c}_{t}_{v}_nom.log").read_text()
            ton = np.array([float(re.search(rf"^ton{k}\s*=\s*(\S+)", log, re.M).group(1)) for k in range(8)])
            # In some runs the SR latch powered up in an undefined state, so the first test period
            # (fine = 0) measured a fall before the rise (negative ton0). Codes 1..7 are valid; ton0 is
            # then estimated as ton1 minus the mean step of codes 1..7 and the row is flagged.
            ton0_invalid = bool(ton[0] < 0)
            if ton0_invalid:
                ton[0] = ton[1] - np.mean(np.diff(ton[1:]))
            steps = np.append(np.diff(ton), TCLK - (ton[7] - ton[0]))
            rows.append({"corner": c, "temp": t, "vdd": v, "seed": 0, "ton": ton.tolist(), "ton0_invalid": ton0_invalid,
                         "dnl": (steps / LSB - 1).tolist(), "inl": ((ton - ton[0]) / LSB - np.arange(8)).tolist(),
                         "tap_scale": float(np.mean(np.diff(ton[1:])) / LSB)})
ts = [r["tap_scale"] for r in rows]
dn = [d for r in rows for d in r["dnl"]]
print(f"recovered {len(rows)} PVT rows ({sum(r['ton0_invalid'] for r in rows)} with ton0 estimated); tap_scale {min(ts):.3f}..{max(ts):.3f}; DNL {min(dn):+.2f}..{max(dn):+.2f} LSB")
save("dpwm", {"pvt": rows, "source": "scripts/char_dpwm.py (ngspice; pvt rows rebuilt from its logs by "
              "scripts/recover_dpwm_pvt.py; uncalibrated Monte Carlo not run)"})
