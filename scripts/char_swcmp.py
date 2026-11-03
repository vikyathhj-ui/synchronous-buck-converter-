#!/usr/bin/env python3
"""Switch-node comparator (spice/comparator.spice: sw_cmp = pass device + 0.9 V resistive level shift +
cmp_hv) for the zero-cross (threshold 0 V) and valley current limit (threshold -250 mA x 0.23 ohm,
the tt LS on-resistance) functions.
  offset : VSW ramps +/-50 mV around the threshold over 100 decisions (1 mV); offset = flip - threshold,
           referred to VSW (includes resistor-shift mismatch, pass-device drop and comparator offset).
  pvt    : every corner x temperature x VIN; systematic offset and the shifted-node settling time
           (10-90 %) after a 40 mV VSW step (sets the zero-cross detection delay).
  mc     : 50 mismatch samples per function at tt / 27 C / 3.3 V.
Writes results/phase3/swcmp.json. The current-limit accuracy over PVT is dominated by the LS
on-resistance spread (results/phase3/fet.json), added in the summary.
"""
import sys

import numpy as np

from spicelib import CORNERS, HVL, PDK, PVT, header, include, pmap, run, save

HD = PDK / "libs.ref" / "sky130_fd_sc_hd" / "spice" / "sky130_fd_sc_hd.spice"
TCLK, N, VR = 25e-9, 100, 0.05
VSH = 0.9
FUNCS = {"zc": 0.0, "ilim": -0.25 * 0.231}


def one(args):
    func, corner, temp, vin, mc, seed = args
    vth = FUNCS[func]
    tag = f"swc_{func}_{corner}_{temp}_{vin}_{'mc' + str(seed) if mc else 'nom'}"
    T = N * TCLK
    meas = "\n".join(f"meas tran q{k} find v(q) at={k * TCLK + 0.9 * TCLK}" for k in range(N))
    seedline = f"setseed {seed}\nreset\n" if mc else ""
    n = header(corner, temp, mc=mc, title=tag) + include("comparator.spice") + f""".include {HD}
.include {HVL}
VDD vdd 0 1.8
VIN vin 0 {vin}
VLS ls_g 0 {vin}
VSH vsh 0 {VSH}
VTH vth 0 {vth}
VCK clk 0 pulse(0 1.8 0 50p 50p {TCLK / 2 - 50e-12} {TCLK})
VSW sw 0 pwl(0 {vth - VR} {T} {vth + VR} {T + 1e-9} {vth - 0.02} {T + 100e-9} {vth - 0.02} {T + 100.1e-9} {vth + 0.02})
X1 sw ls_g vsh vth clk q vin vdd 0 sw_cmp
.control
{seedline}tran 0.05n {T + 300e-9} 0 0.1n
{meas}
meas tran t10 when v(x1.inp)={(vth - 0.02 + VSH) / 2 + 0.1 * 0.02} rise=1 td={T + 100e-9}
meas tran t90 when v(x1.inp)={(vth - 0.02 + VSH) / 2 + 0.9 * 0.02} rise=1 td={T + 100e-9}
quit
.endc
.end
"""
    v = run(n, tag)
    q = np.array([v[f"q{k}"] for k in range(N)]) > 0.9
    ramp = vth - VR + 2 * VR * np.arange(N) / N
    qq = q[2:]
    fl = np.nonzero(qq[:-1] != qq[1:])[0] + 2
    off = float((ramp[fl[0]] + ramp[fl[0] + 1]) / 2 - vth) if len(fl) == 1 else None
    return {"func": func, "corner": corner, "temp": temp, "vin": vin, "seed": seed, "offset": off,
            "n_flips": int(len(fl)), "settle": v.get("t90", np.nan) - v.get("t10", np.nan)}


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    import json, pathlib
    path = pathlib.Path(__file__).resolve().parents[1] / "results" / "phase3" / "swcmp.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    if what in ("pvt", "all"):
        rows = pmap(one, [(f, c, t, v, False, 0) for f in FUNCS for (c, t, v) in PVT])
        data["pvt"] = rows
        for f in FUNCS:
            r = [x for x in rows if x["func"] == f]
            ok = [x for x in r if x["offset"] is not None]
            print(f"{f}: functional {len(ok)}/{len(r)}; systematic offset "
                  f"{min(x['offset'] for x in ok)*1e3:+.2f}..{max(x['offset'] for x in ok)*1e3:+.2f} mV; "
                  f"settling max {max(x['settle'] for x in r)*1e9:.1f} ns")
    if what in ("mc", "all"):
        rows = pmap(one, [(f, "tt", 27, 3.3, True, s) for f in FUNCS for s in range(1, 51)])
        data["mc"] = rows
        stats = {}
        for f in FUNCS:
            o = np.array([x["offset"] for x in rows if x["func"] == f and x["offset"] is not None])
            stats[f] = {"n": int(len(o)), "mean": float(o.mean()), "sigma": float(o.std(ddof=1))}
            print(f"{f}: MC offset at VSW mean {o.mean()*1e3:+.2f} mV sigma {o.std(ddof=1)*1e3:.2f} mV (n={len(o)})")
        data["mc_stats"] = stats
    data["source"] = "scripts/char_swcmp.py (ngspice)"
    save("swcmp", data)
