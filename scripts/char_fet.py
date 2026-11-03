#!/usr/bin/env python3
"""Unit power-device characterisation (multiplier must be m=, ngspice ignores the PDK mult= on subckt instances): 1 mm of sky130_fd_pr__{n,p}fet_g5v0d10v5, L = 0.5 um,
10 um fingers, at every corner x temperature x VIN.

Per device:
  ron_mm  : on-resistance x width [ohm*mm] at |VGS| = VIN, |VDS| = 50 mV
  qg_mm   : gate charge per mm [C/mm] for a 0 -> VIN gate swing with VDS = 0
  qoss_mm : drain charge per mm [C/mm] for a 0 -> VIN drain swing, device off (C_oss x V)
  vbd     : body-diode forward drop [V] at 150 mA per mm, device off
Writes results/phase3/fet.json.
"""
from spicelib import PVT, header, pmap, run, save

FINGER_W, L, M = 10.0, 0.5, 100          # 100 x 10 um = 1 mm


def one(args):
    corner, temp, vin = args
    tag = f"fet_{corner}_{temp}_{vin}"
    n = header(corner, temp, title=tag) + f"""
* --- NMOS: Ron (VGS = VIN)
VGN gn 0 {vin}
VDN dn 0 0.05
XN dn gn 0 0 sky130_fd_pr__nfet_g5v0d10v5 W={FINGER_W} L={L} m={M}
* --- PMOS: Ron (VGS = -VIN)
VSP sp 0 {vin}
VGP gp 0 0
VDP dp 0 {vin - 0.05}
XP dp gp sp sp sky130_fd_pr__pfet_g5v0d10v5 W={FINGER_W} L={L} m={M}
* --- NMOS gate charge, VDS = 0
VGQN gqn 0 pwl(0 0 1n 0 2n {vin})
XNQ 0 gqn 0 0 sky130_fd_pr__nfet_g5v0d10v5 W={FINGER_W} L={L} m={M}
* --- PMOS gate charge, VDS = 0 (gate VIN -> 0)
VSQP sqp 0 {vin}
VGQP gqp 0 pwl(0 {vin} 1n {vin} 2n 0)
XPQ sqp gqp sqp sqp sky130_fd_pr__pfet_g5v0d10v5 W={FINGER_W} L={L} m={M}
* --- NMOS output charge (off), drain 0 -> VIN
VDON don 0 pwl(0 0 1n 0 2n {vin})
XNO don 0 0 0 sky130_fd_pr__nfet_g5v0d10v5 W={FINGER_W} L={L} m={M}
* --- PMOS output charge (off), drain VIN -> 0 (VSD 0 -> VIN)
VSOP sop 0 {vin}
VDOP dop 0 pwl(0 {vin} 1n {vin} 2n 0)
XPO dop sop sop sop sky130_fd_pr__pfet_g5v0d10v5 W={FINGER_W} L={L} m={M}
* --- NMOS body diode at 150 mA (device off), current pulled out of the drain
XNB bdn 0 0 0 sky130_fd_pr__nfet_g5v0d10v5 W={FINGER_W} L={L} m={M}
IBN2 bdn 0 0.15
.control
op
let ron_n = 0.05 / i(VDN)
let ron_p = 0.05 / -i(VDP)
print ron_n ron_p
let vbd_n = -v(bdn)
print vbd_n
tran 10p 4n
meas tran qg_n integ i(VGQN) from=0.5n to=3.5n
meas tran qg_p integ i(VGQP) from=0.5n to=3.5n
meas tran qoss_n integ i(VDON) from=0.5n to=3.5n
meas tran qoss_p integ i(VDOP) from=0.5n to=3.5n
quit
.endc
.end
"""
    v = run(n, tag)
    return {"corner": corner, "temp": temp, "vin": vin,
            "n": {"ron_mm": abs(v["ron_n"]), "qg_mm": abs(v["qg_n"]), "qoss_mm": abs(v["qoss_n"]), "vbd": v["vbd_n"]},
            "p": {"ron_mm": abs(v["ron_p"]), "qg_mm": abs(v["qg_p"]), "qoss_mm": abs(v["qoss_p"])}}


if __name__ == "__main__":
    rows = pmap(one, PVT)
    save("fet", {"finger_w_um": FINGER_W, "l_um": L, "width_mm": FINGER_W * M / 1000, "rows": rows,
                 "source": "scripts/char_fet.py (ngspice)"})
    tt = [r for r in rows if r["corner"] == "tt" and r["temp"] == 27 and r["vin"] == 3.3][0]
    print("tt/27C/3.3V:", tt)
    for d in ("n", "p"):
        rs = [r[d]["ron_mm"] for r in rows]
        print(d, "ron_mm min/max", min(rs), max(rs))
