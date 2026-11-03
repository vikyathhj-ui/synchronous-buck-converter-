#!/usr/bin/env python3
"""Power stage + drivers + level shifters (spice/powerstage.spice, HVL lsbuflv2hv_1).

  delays : every corner x temperature x VIN, switching a 150 mA inductor current:
           propagation from the 1.8 V command (HS_ON / LS_ON, 50 %) to the power-gate 50 % point,
           and the power-gate 10-90 % edge times. Ideal 1.8 V commands with 10 ns logic dead time.
  losses : tt / 27 C / 3.3 V, 10..150 mA, switching a constant inductor current (steady state in
           one period): FET loss = average VDS*ID through 0 V sense sources, gate drive = driver +
           level-shifter supply power; compared with the analytical model (scripts/size_power.py)
           at the same rms current and the measured body-diode time. Efficiency with the real L/C
           and the closed loop is Phase 4.
Writes results/phase3/powerstage.json.
"""
import sys

from size_power import losses as model_losses
from spicelib import HVL, PVT, header, include, pmap, run, save

TS = 1e-6
DT_LOGIC = 10e-9


def stage(vin, lv=1.8):
    return f"""{include('powerstage.spice')}.include {HVL}
VPWR vinp 0 {vin}
VDRV vdrv 0 {vin}
VLV  vlv  0 {lv}
VSH  vsh  0 {vin}
XLSH hs_on vlv 0 0 vsh vsh hs_on_hv sky130_fd_sc_hvl__lsbuflv2hv_1
XLSL ls_on vlv 0 0 vsh vsh ls_on_hv sky130_fd_sc_hvl__lsbuflv2hv_1
XDH hs_on_hv hs_g vdrv 0 drv_hs
XDL ls_on_hv ls_g vdrv 0 drv_ls
VIHS vinp vin_hs 0
VILS ls_src 0 0
XPF vin_hs sw hs_g ls_g ls_src power_fets
"""


def commands(d, n_per):
    """HS_ON high for d*TS - DT, LS_ON high in the rest minus dead time on both sides."""
    ton = d * TS
    hs = f"VHS hs_on 0 pulse(0 1.8 {DT_LOGIC} 50p 50p {ton - 50e-12} {TS})"
    ls = f"VLS ls_on 0 pulse(0 1.8 {ton + 2 * DT_LOGIC} 50p 50p {TS - ton - 3 * DT_LOGIC} {TS})"
    return hs + "\n" + ls + "\n"


def delays(args):
    corner, temp, vin = args
    tag = f"ps_dly_{corner}_{temp}_{vin}"
    d = 0.55
    t_hs_on = 1e-6 + DT_LOGIC                      # HS_ON rises (period 2)
    t_hs_off = 1e-6 + d * TS + DT_LOGIC            # HS_ON falls
    t_ls_on = 1e-6 + d * TS + 2 * DT_LOGIC         # LS_ON rises
    t_ls_off = 2e-6 - DT_LOGIC                     # LS_ON falls
    w = 30e-9
    n = header(corner, temp, title=tag) + stage(vin) + commands(d, 2) + f"""
IL sw 0 0.15
.control
tran 0.05n 2.05u 0 0.1n
meas tran hs_on_dly trig v(hs_on) val=0.9 rise=1 td={t_hs_on - 1e-9} targ v(hs_g) val={vin/2} fall=1 td={t_hs_on - 1e-9}
meas tran hs_off_dly trig v(hs_on) val=0.9 fall=1 td={t_hs_off - 1e-9} targ v(hs_g) val={vin/2} rise=1 td={t_hs_off - 1e-9}
meas tran ls_on_dly trig v(ls_on) val=0.9 rise=1 td={t_ls_on - 1e-9} targ v(ls_g) val={vin/2} rise=1 td={t_ls_on - 1e-9}
meas tran ls_off_dly trig v(ls_on) val=0.9 fall=1 td={t_ls_off - 1e-9} targ v(ls_g) val={vin/2} fall=1 td={t_ls_off - 1e-9}
meas tran hs_fall trig v(hs_g) val={0.9*vin} fall=1 td={t_hs_on - 1e-9} targ v(hs_g) val={0.1*vin} fall=1 td={t_hs_on - 1e-9}
meas tran hs_rise trig v(hs_g) val={0.1*vin} rise=1 td={t_hs_off - 1e-9} targ v(hs_g) val={0.9*vin} rise=1 td={t_hs_off - 1e-9}
meas tran ls_rise trig v(ls_g) val={0.1*vin} rise=1 td={t_ls_on} targ v(ls_g) val={0.9*vin} rise=1 td={t_ls_on}
meas tran ls_fall trig v(ls_g) val={0.9*vin} fall=1 td={t_ls_off - 1e-9} targ v(ls_g) val={0.1*vin} fall=1 td={t_ls_off - 1e-9}
* dv/dt-induced gate disturbance while the device must stay off
meas tran ls_g_bump max v(ls_g) from={t_hs_on} to={t_hs_on + w}
let vsg_hs = {vin} - v(hs_g)
let dsw = deriv(v(sw))
meas tran hs_vsg_bump max vsg_hs from={t_hs_off + 6e-9} to={t_ls_on + 20e-9}
meas tran sw_dvdt_max max dsw from={t_hs_on} to={t_hs_on + w}
quit
.endc
.end
"""
    v = run(n, tag)
    keys = ["hs_on_dly", "hs_off_dly", "ls_on_dly", "ls_off_dly", "hs_fall", "hs_rise", "ls_rise", "ls_fall",
            "ls_g_bump", "hs_vsg_bump", "sw_dvdt_max"]
    return {"corner": corner, "temp": temp, "vin": vin, **{k: v[k] for k in keys}}


def loss_run(io, corner="tt", temp=27, vin=3.3, periods=6, avg=3):
    """Switching into a constant inductor current (ripple-free): reaches steady state in one period,
    so each loss term is measured directly. The model is evaluated at the same rms current and
    with the body-diode time measured here."""
    tag = f"ps_loss_{corner}_{temp}_{vin}_{io}"
    d = 1.8 / vin
    t0, t1 = (periods - avg) * TS, periods * TS
    n = header(corner, temp, title=tag) + stage(vin) + commands(d, periods) + f"""
IL sw 0 {io}
.control
tran 0.05n {t1} 0 0.1n
let php = (v(vin_hs)-v(sw))*i(VIHS)
let pls = v(sw)*i(VILS)
let pdrv = -{vin}*i(VDRV)
let psh = -{vin}*i(VSH) - 1.8*i(VLV)
let bd = (v(sw) < -0.3) + (v(sw) > {vin + 0.3})
meas tran p_hs avg php from={t0} to={t1}
meas tran p_ls avg pls from={t0} to={t1}
meas tran p_drv avg pdrv from={t0} to={t1}
meas tran p_shift avg psh from={t0} to={t1}
meas tran t_bd integ bd from={t0} to={t1}
quit
.endc
.end
"""
    v = run(n, tag)
    sim = {k: v[k] for k in ("p_hs", "p_ls", "p_drv", "p_shift")}
    sim["t_bd_per_period"] = v["t_bd"] / avg
    sim["p_fet"] = sim["p_hs"] + sim["p_ls"]
    m = model_losses(19.2, 8.8, io, ripple=False, t_bd=sim["t_bd_per_period"])
    mod = {"cond_hs": m["cond_hs"], "cond_ls": m["cond_ls"], "coss": m["coss"], "overlap": m["overlap"],
           "deadtime": m["deadtime"], "p_gate": m["gate"]}
    mod["p_fet"] = mod["cond_hs"] + mod["cond_ls"] + mod["coss"] + mod["overlap"] + mod["deadtime"]
    return {"io": io, "duty": d, "sim": sim, "model": mod}


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    data = {}
    if what in ("delays", "all"):
        rows = pmap(delays, PVT)
        data["delays"] = rows
        for k in ("hs_on_dly", "hs_off_dly", "ls_on_dly", "ls_off_dly", "hs_fall", "hs_rise", "ls_rise", "ls_fall"):
            xs = [r[k] for r in rows]
            print(f"{k:11s} min {min(xs)*1e9:6.2f} ns  max {max(xs)*1e9:6.2f} ns")
        for k in ("ls_g_bump", "hs_vsg_bump"):
            xs = [r[k] for r in rows]
            print(f"{k:11s} min {min(xs):6.3f} V   max {max(xs):6.3f} V")
        xs = [r["sw_dvdt_max"] for r in rows]
        print(f"sw dV/dt max {max(xs)/1e9:6.2f} V/ns")
    if what in ("losses", "all"):
        rows = pmap(loss_run, [0.010, 0.025, 0.050, 0.100, 0.150], workers=3)
        data["losses"] = rows
        for r in rows:
            s, m = r["sim"], r["model"]
            print(f"{r['io']*1e3:4.0f} mA  FET sim {s['p_fet']*1e3:6.3f} (hs {s['p_hs']*1e3:.3f} ls {s['p_ls']*1e3:.3f}) "
                  f"model {m['p_fet']*1e3:6.3f} mW | gate drive sim {(s['p_drv']+s['p_shift'])*1e3:6.3f} "
                  f"model {m['p_gate']*1e3:6.3f} mW | body diode {s['t_bd_per_period']*1e9:.1f} ns/period")
    import json, pathlib
    path = pathlib.Path(__file__).resolve().parents[1] / "results" / "phase3" / "powerstage.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(data)
    old["source"] = "scripts/char_powerstage.py (ngspice)"
    save("powerstage", old)
