#!/usr/bin/env python3
"""Delay of sky130_fd_sc_hd delay/buffer cells across PVT, to choose the DPWM fine-delay element
and the dead-time tap. Each cell is measured in a chain of 6 identical cells (cells 2..5 timed,
so each sees a realistic input slope and load). The 1.8 V domain is swept 1.62/1.80/1.98 V.
Writes results/phase3/delaycells.json.
"""
from spicelib import CORNERS, PDK, TEMPS, header, pmap, run, save

CELLS = ["buf_1", "clkdlybuf4s15_1", "clkdlybuf4s50_1", "dlygate4sd1_1", "dlygate4sd3_1", "dlymetal6s2s_1"]
VDDS = [1.62, 1.80, 1.98]
HD = PDK / "libs.ref" / "sky130_fd_sc_hd" / "spice" / "sky130_fd_sc_hd.spice"


def one(args):
    cell, corner, temp, vdd = args
    tag = f"dly_{cell}_{corner}_{temp}_{vdd}"
    chain = "\n".join(f"X{i} n{i} 0 0 vdd vdd n{i+1} sky130_fd_sc_hd__{cell}" for i in range(6))
    n = header(corner, temp, title=tag) + f""".include {HD}
VDD vdd 0 {vdd}
VIN n0 0 pulse(0 {vdd} 1n 50p 50p 20n 40n)
{chain}
.control
tran 5p 42n
meas tran tr trig v(n1) val={vdd/2} rise=1 targ v(n5) val={vdd/2} rise=1
meas tran tf trig v(n1) val={vdd/2} fall=1 targ v(n5) val={vdd/2} fall=1
quit
.endc
.end
"""
    v = run(n, tag)
    return {"cell": cell, "corner": corner, "temp": temp, "vdd": vdd,
            "t_rise": v["tr"] / 4, "t_fall": v["tf"] / 4, "t_avg": (v["tr"] + v["tf"]) / 8}


if __name__ == "__main__":
    items = [(c, k, t, v) for c in CELLS for k in CORNERS for t in TEMPS for v in VDDS]
    rows = pmap(one, items)
    summ = {}
    for c in CELLS:
        r = [x for x in rows if x["cell"] == c]
        tt = [x for x in r if x["corner"] == "tt" and x["temp"] == 27 and x["vdd"] == 1.8][0]["t_avg"]
        lo, hi = min(x["t_avg"] for x in r), max(x["t_avg"] for x in r)
        summ[c] = {"tt": tt, "min": lo, "max": hi, "max_over_min": hi / lo}
        print(f"{c:18s} tt {tt*1e9:6.3f} ns  min {lo*1e9:6.3f}  max {hi*1e9:6.3f}  ratio {hi/lo:4.2f}")
    save("delaycells", {"rows": rows, "summary": summ, "source": "scripts/char_delaycells.py (ngspice)"})
