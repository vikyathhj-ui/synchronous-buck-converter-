#!/usr/bin/env python3
"""Dead-time generator + level shifters + drivers + power FETs, closed through the gate sensors.

For every corner x temperature x VIN, DT code 0, 3, 7 (both edges), and inductor current +150 mA
and -30 mA (light-load valley, where the switch node commutates the other way):
  dt_hl : HS confirmed off (hs_g > VIN - 0.5 V) -> LS starts (ls_g > 0.5 V)    [ns]
  dt_lh : LS confirmed off (ls_g < 0.5 V)       -> HS starts (hs_g < VIN - 0.5 V)
          A negative value would be an overlap (shoot-through window).
  t_bd  : body-diode conduction per period (VSW < -0.3 V or VSW > VIN + 0.3 V)  [ns]
The 0.5 V gate thresholds are below the device thresholds (|Vt| about 0.7-1 V), so a positive dead
time here means neither switch conducts by more than subthreshold leakage at that instant.
Writes results/phase3/deadtime.json.
"""
from spicelib import HVL, PDK, PVT, header, include, pmap, run, save

HD = PDK / "libs.ref" / "sky130_fd_sc_hd" / "spice" / "sky130_fd_sc_hd.spice"
TS = 1e-6
CODES = [0, 3, 7]
CURRENTS = [0.15, -0.03]


def therm(code):
    return [1 if i <= code else 0 for i in range(8)]


def one(args):
    corner, temp, vin, code, io = args
    tag = f"dt_{corner}_{temp}_{vin}_{code}_{io}"
    t = therm(code)
    tsrc = "\n".join(f"VTH{i} hl{i} 0 {1.8 * t[i]}\nVTL{i} lh{i} 0 {1.8 * t[i]}" for i in range(8))
    d = 0.55
    t_rise2 = 1e-6               # PWM rises at the start of period 2
    t_fall2 = 1e-6 + d * TS      # PWM falls
    n = header(corner, temp, title=tag) + include("powerstage.spice", "deadtime.spice") + f""".include {HD}
.include {HVL}
VPWR vin 0 {vin}
VLV  vdd 0 1.8
VPWM pwm 0 pulse(0 1.8 0 50p 50p {d * TS} {TS})
VLSE ls_en 0 1.8
{tsrc}
XDT pwm ls_en hs_on_s ls_on_s hs_on ls_on hl0 hl1 hl2 hl3 hl4 hl5 hl6 hl7 lh0 lh1 lh2 lh3 lh4 lh5 lh6 lh7 vdd vin 0 deadtime_gen
XLSH hs_on vdd 0 0 vin vin hs_on_hv sky130_fd_sc_hvl__lsbuflv2hv_1
XLSL ls_on vdd 0 0 vin vin ls_on_hv sky130_fd_sc_hvl__lsbuflv2hv_1
XDH hs_on_hv hs_g vin 0 drv_hs
XDL ls_on_hv ls_g vin 0 drv_ls
XPF vin sw hs_g ls_g 0 power_fets
XGS vin hs_g ls_g hs_on_s ls_on_s 0 gate_sense
IL sw 0 {io}
.control
tran 0.05n 2.0u 0 0.1n
meas tran t_hs_off when v(hs_g)={vin - 0.5} rise=1 td={t_fall2}
meas tran t_ls_on  when v(ls_g)=0.5 rise=1 td={t_fall2}
meas tran t_ls_off when v(ls_g)=0.5 fall=1 td={t_rise2 - 0.2e-6}
meas tran t_hs_on  when v(hs_g)={vin - 0.5} fall=1 td={t_rise2 - 0.2e-6}
let bd = (v(sw) < -0.3) + (v(sw) > {vin + 0.3})
meas tran t_bd integ bd from={t_rise2 - 0.05e-6} to={t_rise2 + 0.95e-6}
meas tran hs_on_cmd_dly trig v(pwm) val=0.9 rise=1 td={t_rise2 - 1e-9} targ v(hs_on) val=0.9 rise=1 td={t_rise2 - 1e-9}
quit
.endc
.end
"""
    v = run(n, tag)
    return {"corner": corner, "temp": temp, "vin": vin, "code": code, "io": io,
            "dt_hl": v["t_ls_on"] - v["t_hs_off"], "dt_lh": v["t_hs_on"] - v["t_ls_off"],
            "t_bd": v["t_bd"], "pwm_to_hs_on": v["hs_on_cmd_dly"]}


if __name__ == "__main__":
    items = [(c, t, v, k, i) for (c, t, v) in PVT for k in CODES for i in CURRENTS]
    rows = pmap(one, items)
    out = {"rows": rows, "source": "scripts/char_deadtime.py (ngspice)"}
    for code in CODES:
        r = [x for x in rows if x["code"] == code]
        for k in ("dt_hl", "dt_lh"):
            xs = [x[k] for x in r]
            out[f"code{code}_{k}_min"] = min(xs)
            out[f"code{code}_{k}_max"] = max(xs)
            print(f"code {code} {k}: min {min(xs)*1e9:6.2f} ns  max {max(xs)*1e9:6.2f} ns")
        tt = [x for x in r if x["corner"] == "tt" and x["temp"] == 27 and x["vin"] == 3.3 and x["io"] == 0.15][0]
        out[f"code{code}_tt"] = tt
        print(f"code {code} tt: dt_hl {tt['dt_hl']*1e9:.2f} ns dt_lh {tt['dt_lh']*1e9:.2f} ns body diode {tt['t_bd']*1e9:.2f} ns")
    out["min_dead_time_all"] = min(min(x["dt_hl"], x["dt_lh"]) for x in rows)
    out["shoot_through_free"] = out["min_dead_time_all"] > 0
    print("min dead time over all runs:", out["min_dead_time_all"] * 1e9, "ns; shoot-through free:", out["shoot_through_free"])
    save("deadtime", out)
