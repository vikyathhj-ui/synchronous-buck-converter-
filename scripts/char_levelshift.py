#!/usr/bin/env python3
"""Level shifters (HVL standard cells) at every corner x temperature x VIN (LV supply 1.8 V):
  lsbuflv2hv_1 : 1.8 V -> VIN, drives the gate-driver input (load: first HS driver stage)
  lsbufhv2lv_1 : VIN -> 1.8 V, carries the gate-sense signals into the dead-time logic
Propagation delay (50 % -> 50 %) for rising and falling inputs, and static supply current.
Writes results/phase3/levelshift.json.
"""
from spicelib import HVL, PVT, header, include, pmap, run, save


def one(args):
    corner, temp, vin = args
    tag = f"ls_{corner}_{temp}_{vin}"
    n = header(corner, temp, title=tag) + include("powerstage.spice") + f""".include {HVL}
VLV vlv 0 1.8
VHV vhv 0 {vin}
VA a 0 pulse(0 1.8 2n 100p 100p 20n 40n)
XU a vlv 0 0 vhv vhv x sky130_fd_sc_hvl__lsbuflv2hv_1
XN1 hx x 0 0 sky130_fd_pr__nfet_g5v0d10v5 W=1 L=0.5
XP1 hx x vhv vhv sky130_fd_pr__pfet_g5v0d10v5 W=3 L=0.5
VB b 0 pulse(0 {vin} 2n 100p 100p 20n 40n)
XD b vlv 0 0 vhv vhv y sky130_fd_sc_hvl__lsbufhv2lv_1
XL y 0 0 vlv vlv yl sky130_fd_sc_hvl__inv_1
.control
tran 0.01n 44n 0 0.02n
meas tran up_r trig v(a) val=0.9 rise=1 targ v(x) val={vin/2} rise=1
meas tran up_f trig v(a) val=0.9 fall=1 targ v(x) val={vin/2} fall=1
meas tran dn_r trig v(b) val={vin/2} rise=1 targ v(y) val=0.9 rise=1
meas tran dn_f trig v(b) val={vin/2} fall=1 targ v(y) val=0.9 fall=1
meas tran i_hv_static avg i(VHV) from=15n to=20n
quit
.endc
.end
"""
    v = run(n, tag)
    return {"corner": corner, "temp": temp, "vin": vin, "lv2hv_rise": v["up_r"], "lv2hv_fall": v["up_f"],
            "hv2lv_rise": v["dn_r"], "hv2lv_fall": v["dn_f"], "i_hv_static": -v["i_hv_static"]}


if __name__ == "__main__":
    rows = pmap(one, PVT, workers=2)
    out = {"rows": rows, "source": "scripts/char_levelshift.py (ngspice)"}
    for k in ("lv2hv_rise", "lv2hv_fall", "hv2lv_rise", "hv2lv_fall"):
        xs = [r[k] for r in rows]
        out[k + "_range"] = [min(xs), max(xs)]
        print(f"{k:11s} {min(xs)*1e9:6.3f} .. {max(xs)*1e9:6.3f} ns")
    save("levelshift", out)
