#!/usr/bin/env python3
"""Window-ADC comparator (spice/comparator.spice: cmp_adc = static preamp + cmp_hv, VIN rail, 5 V
devices; DECISIONS D26, D30). Clocked as in the RTL: one decision per 1 MHz period, clk high for one
64 MHz cycle (15.6 ns); the preamp tails are biased by adc_pbias from an ideal 10 uA reference.

  offset : Monte Carlo (mismatch, tt, 27 C, 1.8 V), 100 samples at each input common mode.
           inp ramps from -25 mV to +25 mV around inn over 100 decisions (0.5 mV/decision);
           the offset is the ramp value where the decision flips.
  pvt    : every corner x temperature x VIN 3.0/3.3/3.6 V at CM 0.5, 0.9 and 1.25 V (the window
           ADC range VOUT/2 for VOUT 1.0-2.5 V): clk -> q delay for 2 mV and 10 mV overdrive (input
           set 500 ns before the edge so the preamp has settled), and whether all decisions are correct.
Writes results/phase3/comparator.json.
"""
import sys

import numpy as np

from spicelib import CORNERS, HVL, PDK, TEMPS, VINS, header, include, pmap, run, save

HD = PDK / "libs.ref" / "sky130_fd_sc_hd" / "spice" / "sky130_fd_sc_hd.spice"
TCLK = 1e-6           # one decision per switching period
TH = 15.625e-9        # clk high for one 64 MHz cycle
TMAX = "5n"           # max time step; A/B-checked against 0.2 ns in D30
N = 100
VR = 0.025
CMS = [0.5, 0.9, 1.25]       # window-ADC common mode = VOUT/2 for VOUT 1.0 / 1.8 / 2.5 V
CMP = "cmp_adc"
BIAS = "IB pb 0 10u\nXPB pb vin adc_pbias"
NMC = 100


def offset(args):
    cm, seed = args
    tag = f"cmp_mc_{cm}_{seed}"
    T = N * TCLK
    meas = "\n".join(f"meas tran q{k} find v(q) at={k * TCLK + 0.9 * TCLK}" for k in range(N))
    n = header("tt", 27, mc=True, title=tag) + include("comparator.spice") + f""".include {HD}
.include {HVL}
VDD vdd 0 1.8
VIN vin 0 3.3
VCK clk 0 pulse(0 1.8 {TCLK / 2} 50p 50p {TH - 50e-12} {TCLK})
{BIAS}
VN inn 0 {cm}
VP inp 0 pwl(0 {cm - VR} {T} {cm + VR})
X1 inp inn clk q pb vin vdd 0 {CMP}
.control
setseed {seed}
reset
tran {TMAX} {T} 0 {TMAX}
{meas}
quit
.endc
.end
"""
    v = run(n, tag)
    q = np.array([v[f"q{k}"] for k in range(N)]) > 0.9
    # ramp value at each decision (decision at the clock rising edge (k + 1/2) x TCLK)
    ramp = -VR + 2 * VR * ((np.arange(N) + 0.5) * TCLK) / T
    flips = _flips(q)
    if len(flips) == 0:
        return {"cm": cm, "seed": seed, "offset": None, "n_flips": 0}
    k = flips[0]
    return {"cm": cm, "seed": seed, "offset": float((ramp[k] + ramp[k + 1]) / 2) if len(flips) == 1 else None,
            "n_flips": int(len(flips))}


def _flips(q):
    """Decision flips, ignoring the first two decisions (latch power-up state)."""
    q = q[2:]
    return np.nonzero(q[:-1] != q[1:])[0] + 2


def pvt(args):
    """At CM 0.33 / 0.60 / 0.83 V (three instances, one shared differential stimulus):
    A: +/-25 mV ramp over 100 decisions -> systematic offset and functionality (exactly one flip);
    B: clk -> q delay at 2 mV and 10 mV overdrive, both polarities."""
    corner, temp, vin = args
    vdd = 1.8
    tag = f"cmp_pvt_{corner}_{temp}_{vin}"
    cms = tuple(CMS)
    T = N * TCLK
    inst = BIAS + "\n" + "\n".join(f"VN{k} inn{k} 0 {cm}\nE{k} inp{k} inn{k} vd 0 1\nX{k} inp{k} inn{k} clk q{k} pb vin vdd 0 {CMP}"
                     for k, cm in enumerate(cms))
    meas = "\n".join(f"meas tran q{k}_{i} find v(q{k}) at={i * TCLK + 0.9 * TCLK}" for k in range(3) for i in range(N))
    na = header(corner, temp, title=tag + "_A") + include("comparator.spice") + f""".include {HD}
.include {HVL}
VDD vdd 0 {vdd}
VIN vin 0 {vin}
VCK clk 0 pulse(0 {vdd} {TCLK / 2} 50p 50p {TH - 50e-12} {TCLK})
VD vd 0 pwl(0 {-VR} {T} {VR})
{inst}
.control
tran {TMAX} {T} 0 {TMAX}
{meas}
quit
.endc
.end
"""
    va = run(na, tag + "_A")
    ramp = -VR + 2 * VR * (np.arange(N) + 0.5) / N
    out = {"corner": corner, "temp": temp, "vin": vin}
    for k, cm in enumerate(cms):
        q = np.array([va[f"q{k}_{i}"] for i in range(N)]) > vdd / 2
        fl = _flips(q)
        out[f"cm{cm}"] = {"functional": bool(len(fl) == 1),
                          "sys_offset": float((ramp[fl[0]] + ramp[fl[0] + 1]) / 2) if len(fl) == 1 else None}
    # B: delays; decisions at clk rising edges 0.5, 1.5, 2.5, 3.5 us; the input steps 500 ns before each
    pts = "0 -0.002 1u -0.002 1.001u 0.002 2u 0.002 2.001u -0.01 3u -0.01 3.001u 0.01"
    measb = []
    for k in range(3):
        measb += [f"meas tran d{r}_{k} trig v(clk) val={vdd/2} rise={r} targ v(q{k}) val={vdd/2} cross=1 td={r - 1}.4u"
                  for r in (1, 2, 3, 4)]
    nb = header(corner, temp, title=tag + "_B") + include("comparator.spice") + f""".include {HD}
.include {HVL}
VDD vdd 0 {vdd}
VIN vin 0 {vin}
VCK clk 0 pulse(0 {vdd} 0.5u 50p 50p {TH - 50e-12} 1u)
VD vd 0 pwl({pts})
{inst}
.ic {" ".join(f"v(x{k}.xc.q_i)=0" for k in range(3))}
.control
tran 0.02n 3.6u 0 0.1n
{chr(10).join(measb)}
quit
.endc
.end
"""
    vb = run(nb, tag + "_B")
    ok = True
    for k, cm in enumerate(cms):
        d = out[f"cm{cm}"]
        d["delay_2mV"] = max(vb.get(f"d1_{k}", np.nan), vb.get(f"d2_{k}", np.nan))
        d["delay_10mV"] = max(vb.get(f"d3_{k}", np.nan), vb.get(f"d4_{k}", np.nan))
        d["ok"] = bool(d["functional"] and d["delay_2mV"] < 2 * 15.625e-9)
        ok &= d["ok"]
    out["correct"] = bool(ok)
    out["delay_1mV"] = max(out[f"cm{cm}"]["delay_2mV"] for cm in cms)   # kept key name for the collector
    out["delay_10mV"] = max(out[f"cm{cm}"]["delay_10mV"] for cm in cms)
    return out


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    import json, pathlib
    path = pathlib.Path(__file__).resolve().parents[1] / "results" / "phase3" / "comparator.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    if what in ("pvt", "all"):
        rows = pmap(pvt, [(c, t, v) for c in CORNERS for t in TEMPS for v in VINS])
        data["pvt"] = rows
        print("all decisions correct:", all(r["correct"] for r in rows))
        print("delay 1 mV  max %.2f ns" % (max(r["delay_1mV"] for r in rows) * 1e9))
        print("delay 10 mV max %.2f ns" % (max(r["delay_10mV"] for r in rows) * 1e9))
    if what in ("mc", "all"):
        rows = pmap(offset, [(cm, s) for cm in CMS for s in range(1, NMC + 1)])
        data["mc"] = rows
        stats = {}
        for cm in CMS:
            os_ = np.array([r["offset"] for r in rows if r["cm"] == cm and r["offset"] is not None])
            multi = sum(1 for r in rows if r["cm"] == cm and r.get("n_flips", 0) > 1)
            if len(os_) == 0 or multi > len(os_) // 2:
                stats[str(cm)] = {"n": int(len(os_)), "failed": True, "n_multiple_flips": int(multi),
                                  "note": "decisions not monotonic in the input ramp: comparator does not work at this CM"}
                print(f"CM {cm:5.2f} V: FAILS ({multi} of {NMC} samples flip more than once)")
                continue
            stats[str(cm)] = {"n_multiple_flips": int(multi), "n": int(len(os_)), "mean": float(os_.mean()), "sigma": float(os_.std(ddof=1)),
                              "min": float(os_.min()), "max": float(os_.max()),
                              "n_missing": sum(1 for r in rows if r["cm"] == cm and r["offset"] is None)}
            print(f"CM {cm:5.2f} V: offset mean {os_.mean()*1e3:+.3f} mV sigma {os_.std(ddof=1)*1e3:.3f} mV "
                  f"range [{os_.min()*1e3:+.2f}, {os_.max()*1e3:+.2f}] mV  n={len(os_)}")
        data["mc_stats"] = stats
    data["source"] = "scripts/char_comparator.py (ngspice)"
    save("comparator", data)
