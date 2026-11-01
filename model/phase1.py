"""Phase 1: modelling and control design.

Run (inside iic-osic):  python3 -m model.phase1
Writes plots to results/plots/phase1/ and every number to results/summary.json["phase1"].
kind = "analysis" (closed-form hand formula), "model" (computed from the Python models).
"""
import json
import pathlib
from dataclasses import replace
from itertools import product

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .buck import Buck, Dpwm
from .controller import Adc, closed_loop_matrix, design, linear_load_step, loop, margins
from .sim import open_loop_response, simulate

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLOTS = ROOT / "results" / "plots" / "phase1"
SRC = "model/phase1.py"

DESIGN = dict(fc=50e3, pm=50.0, fi_ratio=5.0, io=0.15)
VREF_CODE, VREF_LSB, ILIM = 180, 0.010, 0.25
VSET = VREF_CODE * VREF_LSB

# reference palette (dataviz skill, categorical slots in fixed order) and ink colours
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 1.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "legend.frameon": False,
})

S = {}


def put(key, value, unit, kind="model", note=None):
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    S[key] = {"value": value, "unit": unit, "kind": kind, "source": SRC}
    if note:
        S[key]["note"] = note


def dense_arrays(r):
    d = np.array(r.dense)
    return d[:, 0], d[:, 1], d[:, 2]


def step_metrics(tt, vv, t_step, t_end, vset):
    m = (tt >= t_step) & (tt < t_end)
    pre = (tt >= t_step - 50e-6) & (tt < t_step)
    vpre = vv[pre].mean()
    out = np.nonzero(np.abs(vv[m] - vset) > 0.01 * vset)[0]
    rec = tt[m][out[-1]] - t_step if len(out) else 0.0
    return vpre - vv[m].min(), vv[m].max() - vpre, rec


def main():
    PLOTS.mkdir(parents=True, exist_ok=True)
    b, dp, adc = Buck(), Dpwm(), Adc()

    # ---------------- 1. closed-form analysis ----------------
    put("f0_lc", b.f0(), "Hz", "analysis")
    put("f_esr_zero", b.f_esr(), "Hz", "analysis")
    put("duty_fullload", b.duty_dc(0.15), "-", "analysis", "CCM, rs = dcr + ron (A1)")
    put("il_ripple_pp", b.ripple_il_pp(0.15), "A", "analysis")
    put("vout_ripple_cap_pp", b.ripple_il_pp(0.15) / (8 * b.fsw * b.C), "V", "analysis")
    put("vout_ripple_esr_pp", b.ripple_il_pp(0.15) * b.esr, "V", "analysis")
    for vin in (3.0, 3.3, 3.6):
        put(f"dpwm_lsb_out_vin{vin}", dp.lsb_out(vin), "V", "analysis")
    put("adc_lsb", adc.lsb, "V", "analysis")
    put("dpwm_tap", 1 / dp.fclk / (1 << dp.fine_bits), "s", "analysis")
    put("cond1_dpwm_lsb_lt_adc_lsb_all_vin", bool(dp.lsb_out(3.6) < adc.lsb), "-", "analysis")

    # ---------------- 2. z-domain PID design ----------------
    g = design(b, DESIGN["io"], adc, dp, DESIGN["fc"], DESIGN["pm"], DESIGN["fi_ratio"])
    put("design_target", DESIGN, "-", "model")
    put("gains_float", {"kp": g.kp, "ki": g.ki, "kd": g.kd}, "DPWM LSB / ADC LSB")

    # ---------------- 3. coefficient quantisation ----------------
    m0 = margins(b, DESIGN["io"], g, adc, dp)
    qrows = []
    for F in range(0, 11):
        gq = g.quantized(F)
        mq = margins(b, DESIGN["io"], gq, adc, dp, n=6000)
        eig = np.abs(np.linalg.eigvals(closed_loop_matrix(b, DESIGN["io"], gq, adc, dp)[0])).max()
        fc = mq["crossovers"][-1] if mq["crossovers"] else float("nan")
        pm = min(mq["pm"]) if mq["pm"] else float("nan")
        qrows.append(dict(frac=F, kp=gq.kp, ki=gq.ki, kd=gq.kd, fc=fc, pm=pm,
                          n_cross=len(mq["crossovers"]), max_eig=eig))
    fc0, pm0 = m0["crossovers"][-1], min(m0["pm"])
    ok = [r for r in qrows if r["ki"] > 0 and r["n_cross"] == 1 and abs(r["pm"] - pm0) < 1.0
          and abs(r["fc"] / fc0 - 1) < 0.02]
    F = ok[0]["frac"]
    put("quant_study", qrows, "-", "model")
    put("quant_frac_bits", F, "bits", "model", "smallest F with |dPM|<1 deg, |dfc|<2 %, ki>0, one crossover")
    gq = g.quantized(F)
    gi = g.ints(F)
    put("gains_int", {"kp": gi[0], "ki": gi[1], "kd": gi[2], "frac": F}, "Q(frac) integers")

    mq = margins(b, DESIGN["io"], gq, adc, dp)
    eig = np.abs(np.linalg.eigvals(closed_loop_matrix(b, DESIGN["io"], gq, adc, dp)[0])).max()
    put("fc", mq["crossovers"], "Hz")
    put("pm", mq["pm"], "deg")
    put("gm", mq["gm_db"], "dB")
    put("gm_phase_crossover", mq["phase_crossovers"], "Hz")
    put("cl_max_pole_mag", eig, "-", note="sampled closed loop incl. compute delay; < 1 = stable")
    kin = gq.ki * dp.lsb_out(3.6) / adc.lsb
    put("ki_normalised_worst", kin, "-", "model", "ki * qDPWM_out(3.6 V) / qADC; condition: 0 < Ki_n <= 1")

    # ---------------- 4. robustness grid ----------------
    grid = []
    for vin, L, C, ron, io in product((3.0, 3.3, 3.6), (12e-6, 15e-6, 18e-6), (8e-6, 10e-6, 12e-6),
                                      (0.25, 0.5, 1.0), (0.015, 0.15)):
        bb = replace(b, vin=vin, L=L, C=C, ron=ron)
        mm = margins(bb, io, gq, adc, dp, n=4000)
        ee = np.abs(np.linalg.eigvals(closed_loop_matrix(bb, io, gq, adc, dp)[0])).max()
        grid.append(dict(vin=vin, L=L, C=C, ron=ron, io=io, fc=mm["crossovers"], pm=mm["pm"],
                         gm=mm["gm_db"], max_eig=ee))
    pms = [min(x["pm"]) for x in grid]
    gms = [min(x["gm"]) for x in grid if x["gm"]]
    fcs = [x["fc"][-1] for x in grid]
    worst = grid[int(np.argmin(pms))]
    put("robust_n_cases", len(grid), "-", note="VIN{3.0,3.3,3.6} x L{12,15,18u} x C{8,10,12u} x ron{0.25,0.5,1.0} x io{15m,150m}")
    put("robust_pm_min", min(pms), "deg")
    put("robust_pm_max", max(pms), "deg")
    put("robust_gm_min", min(gms), "dB")
    put("robust_fc_range", [min(fcs), max(fcs)], "Hz")
    put("robust_max_pole_mag", max(x["max_eig"] for x in grid), "-")
    put("robust_all_stable", bool(all(x["max_eig"] < 1 for x in grid)), "-")
    put("robust_worst_case", {k: worst[k] for k in ("vin", "L", "C", "ron", "io")}, "-")
    nomlc = [x for x in grid if x["L"] == b.L and x["C"] == b.C and x["ron"] == b.ron]
    put("pm_range_vin_io_only", [min(min(x["pm"]) for x in nomlc), max(min(x["pm"]) for x in nomlc)], "deg",
        note="nominal L, C, ron; VIN 3.0-3.6 V, io 15/150 mA")
    nomv = [x for x in grid if x["vin"] == b.vin and x["ron"] == b.ron and x["io"] == 0.15]
    put("pm_range_lc_only", [min(min(x["pm"]) for x in nomv), max(min(x["pm"]) for x in nomv)], "deg",
        note="VIN 3.3 V, 150 mA; L 12-18 uH, C 8-12 uF (+/-20 %, assumed tolerance)")

    # ---------------- 5. plant model check: switched-plant injection vs sampled model ----------------
    fval = [2e3, 5e3, 10e3, 13e3, 20e3, 50e3, 100e3, 200e3]
    val = []
    for f in fval:
        h = open_loop_response(b, DESIGN["io"], f)
        p = b.pz(f, DESIGN["io"])[0]
        val.append(dict(f=f, mag_err_db=20 * np.log10(abs(h) / abs(p)),
                        ph_err_deg=float(np.angle(h / p, deg=True)), h=h))
    put("plant_check_max_mag_err", max(abs(v["mag_err_db"]) for v in val), "dB",
        note="switched-plant sine injection vs exact sampled model; checks the derivation, not the physics")
    put("plant_check_max_ph_err", max(abs(v["ph_err_deg"]) for v in val), "deg")

    # ---------------- 6. Bode plot ----------------
    f = np.logspace(2, np.log10(0.4999 * b.fsw), 1500)
    P = b.pz(f, DESIGN["io"])
    Gs = b.gvd_s(f)
    Lf = loop(b, DESIGN["io"], gq, adc, dp, f)
    fig, ax = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
    ax[0, 0].semilogx(f, 20 * np.log10(np.abs(Gs)), color=C2, label="averaged Gvd(s)")
    ax[0, 0].semilogx(f, 20 * np.log10(np.abs(P)), color=C1, label="sampled P(z), exact")
    ax[0, 0].semilogx(fval, [20 * np.log10(abs(v["h"])) for v in val], "o", ms=6, color=C3,
                      mfc=SURF, mew=1.6, label="switched-plant injection")
    ax[1, 0].semilogx(f, np.rad2deg(np.unwrap(np.angle(Gs))), color=C2)
    ax[1, 0].semilogx(f, np.rad2deg(np.unwrap(np.angle(P))), color=C1)
    ax[1, 0].semilogx(fval, [np.rad2deg(np.unwrap(np.angle(P)))[np.argmin(abs(f - v["f"]))] +
                             v["ph_err_deg"] for v in val], "o", ms=6, color=C3, mfc=SURF, mew=1.6)
    ax[0, 0].set_title("Plant: control (duty) to VOUT, VIN 3.3 V, 150 mA")
    ax[0, 0].set_ylabel("magnitude [dB V/duty]")
    ax[1, 0].set_ylabel("phase [deg]")
    ax[0, 0].legend(loc="lower left")
    ax[0, 1].semilogx(f, 20 * np.log10(np.abs(Lf)), color=C1)
    ax[1, 1].semilogx(f, np.rad2deg(np.unwrap(np.angle(Lf))), color=C1)
    ax[0, 1].axhline(0, color=INK2, lw=0.8)
    ax[1, 1].axhline(-180, color=INK2, lw=0.8)
    fcx, pmx = mq["crossovers"][-1], mq["pm"][-1]
    ax[0, 1].axvline(fcx, color=INK2, lw=0.8, ls="--")
    ax[1, 1].axvline(fcx, color=INK2, lw=0.8, ls="--")
    ax[1, 1].annotate(f"fc = {fcx/1e3:.1f} kHz\nPM = {pmx:.1f} deg", (fcx, -180 + pmx),
                      xytext=(8, 10), textcoords="offset points")
    if mq["phase_crossovers"]:
        fg = mq["phase_crossovers"][-1]
        ax[0, 1].annotate(f"GM = {mq['gm_db'][-1]:.1f} dB at {fg/1e3:.0f} kHz",
                          (fg, -mq["gm_db"][-1]), xytext=(-150, -20), textcoords="offset points")
    ax[0, 1].set_title(f"Loop gain L(z) with quantised PID (Q{F}), incl. compute delay")
    for a in ax[1]:
        a.set_xlabel("frequency [Hz]")
    fig.tight_layout()
    fig.savefig(PLOTS / "bode.png", dpi=150)
    plt.close(fig)

    gi_args = (gi, F)

    # ---------------- 7. load step 15 -> 150 mA ----------------
    g15 = 0.015 / VSET          # 15 mA resistive base load
    bl = replace(b, g_load=g15)
    io_fn = lambda t: 0.135 if 3.0e-3 <= t < 3.3e-3 else 0.0
    r = simulate(bl, dp, adc, *gi_args, n=3600, vref_target=VREF_CODE, ilim=ILIM, io_fn=io_fn,
                 dense_from=2.9e-3, dense_to=3.6e-3, nsub=16)
    tt, vv, ii = dense_arrays(r)
    us, _, rec_up = step_metrics(tt, vv, 3.0e-3, 3.3e-3, VSET)
    _, os_dn, rec_dn = step_metrics(tt, vv, 3.3e-3, 3.6e-3, VSET)
    put("loadstep_undershoot", us, "V", note="switched plant, step at a period boundary (faster than 100 ns)")
    put("loadstep_recovery_1pct", rec_up, "s")
    put("loadstep_down_overshoot", os_dn, "V")
    put("loadstep_down_recovery_1pct", rec_dn, "s")
    put("loadstep_ilim_trips", int(r.trip.sum()), "-")
    tl, yl = linear_load_step(b, DESIGN["io"], gq, adc, dp, 0.135, n_before=100, n_after=300)
    put("loadstep_undershoot_linear", -yl.min(), "V", note="linear sampled model, no quantisation, current-source load")
    k0 = int(round(3.0e-3 / b.Ts))
    put("loadstep_undershoot_switched_sampled", r.v[k0 - 50:k0].mean() - r.v[k0:k0 + 300].min(), "V",
        note="same run as loadstep_undershoot, sampled instants only (compare with linear)")
    fig, ax = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
    ax[0].plot((tt - 3e-3) * 1e6, vv * 1e3, color=C1, lw=1.2, label="switched plant + fixed-point PID")
    ax[0].plot((tl - tl[100]) * 1e6, (VSET + yl) * 1e3, color=C2, lw=1.6, ls="--", label="linear sampled model")
    for s_ in (1, -1):
        ax[0].axhline((VSET * (1 + 0.01 * s_)) * 1e3, color=INK2, lw=0.8, ls=":")
    ax[0].axhline((VSET - 0.090) * 1e3, color="#d03b3b", lw=0.8, ls="-.")
    ax[0].text(-95, (VSET - 0.087) * 1e3, "spec limit: 90 mV undershoot", color=INK2)
    ax[0].text(-95, (VSET + 0.021) * 1e3, "+/-1 % band", color=INK2)
    ax[0].set_ylabel("VOUT [mV]")
    ax[0].set_title(f"Load step 15 -> 150 mA -> 15 mA: undershoot {us*1e3:.1f} mV, "
                    f"recovery {rec_up*1e6:.1f} us (model)")
    ax[0].legend(loc="center right")
    ax[1].plot((tt - 3e-3) * 1e6, ii * 1e3, color=C1, lw=1.0)
    ax[1].set_ylabel("iL [mA]")
    ax[1].set_xlabel("time from step [us]")
    fig.tight_layout()
    fig.savefig(PLOTS / "load_step.png", dpi=150)
    plt.close(fig)

    # ---------------- 8. start-up ----------------
    starts = {}
    for name, gload in (("noload", 0.0), ("fullload", 0.15 / VSET)):
        bs = replace(b, g_load=gload)
        rs_ = simulate(bs, dp, adc, *gi_args, n=2500, vref_target=VREF_CODE, ilim=ILIM,
                       dense_from=0.0, dense_to=2.5e-3, nsub=4)
        ts, vs, is_ = dense_arrays(rs_)
        ramp_end = rs_.t[np.argmax(rs_.vref >= VSET - 1e-9)]
        put(f"startup_{name}_overshoot_pct", (vs.max() - VSET) / VSET * 100, "%")
        put(f"startup_{name}_il_peak", is_.max(), "A")
        put(f"startup_{name}_ilim_trips", int(rs_.trip.sum()), "-")
        put(f"startup_{name}_vref_ramp_time", ramp_end, "s")
        starts[name] = (ts, vs, is_, rs_)
    fig, ax = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
    for (name, (ts, vs, is_, rs_)), col in zip(starts.items(), (C1, C2)):
        ax[0].plot(ts * 1e3, vs, color=col, lw=1.2, label=name.replace("load", " load"))
        ax[1].plot(ts * 1e3, is_ * 1e3, color=col, lw=0.8, label=name.replace("load", " load"))
    ax[0].plot(starts["noload"][3].t * 1e3, starts["noload"][3].vref, color=INK2, lw=0.8, ls="--", label="VREF (soft start)")
    ax[1].axhline(ILIM * 1e3, color="#d03b3b", lw=0.8, ls="-.")
    ax[1].text(0.05, ILIM * 1e3 - 18, "valley current limit 250 mA", color=INK2)
    ax[0].set_ylabel("VOUT [V]")
    ax[1].set_ylabel("iL [mA]")
    ax[1].set_xlabel("time [ms]")
    ax[0].set_title("Start-up with 1 ms soft-start ramp (model)")
    ax[0].legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(PLOTS / "startup.png", dpi=150)
    plt.close(fig)

    # ---------------- 9. line step 3.0 <-> 3.6 V in 10 us, full load ----------------
    def vin_fn(t):
        if t < 3.0e-3:
            return 3.0
        if t < 3.01e-3:
            return 3.0 + 0.6 * (t - 3.0e-3) / 10e-6
        if t < 3.5e-3:
            return 3.6
        if t < 3.51e-3:
            return 3.6 - 0.6 * (t - 3.5e-3) / 10e-6
        return 3.0
    bf = replace(b, g_load=0.15 / VSET)
    r = simulate(bf, dp, adc, *gi_args, n=4000, vref_target=VREF_CODE, ilim=ILIM, vin_fn=vin_fn,
                 dense_from=2.9e-3, dense_to=4.0e-3, nsub=8)
    tt, vv, _ = dense_arrays(r)
    m_up = (tt >= 3.0e-3) & (tt < 3.5e-3)
    m_dn = tt >= 3.5e-3
    vpre = vv[(tt >= 2.9e-3) & (tt < 3.0e-3)].mean()
    put("linestep_up_dev_max", vv[m_up].max() - vpre, "V", note="3.0 -> 3.6 V in 10 us, 150 mA")
    put("linestep_dn_dev_min", vv[m_dn].min() - vpre, "V", note="3.6 -> 3.0 V in 10 us, 150 mA")
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot((tt - 3e-3) * 1e6, vv * 1e3, color=C1, lw=1.0)
    ax.set_xlabel("time from VIN rise [us]")
    ax.set_ylabel("VOUT [mV]")
    ax.set_title("Line step 3.0 -> 3.6 -> 3.0 V (10 us edges), 150 mA (model)")
    fig.tight_layout()
    fig.savefig(PLOTS / "line_step.png", dpi=150)
    plt.close(fig)

    # ---------------- 10. ripple at full load ----------------
    r = simulate(bf, dp, adc, *gi_args, n=3000, vref_target=VREF_CODE, ilim=ILIM,
                 dense_from=2.95e-3, dense_to=3.0e-3, nsub=64)
    _, vv, ii = dense_arrays(r)
    put("ripple_vout_pp_fullload", vv.max() - vv.min(), "V", note="VIN 3.3 V, 150 mA resistive, steady state")
    put("ripple_il_pp_fullload", ii.max() - ii.min(), "A")

    # ---------------- 11. limit-cycle check: 10 ms steady state ----------------
    lc = []
    hist_nom = None
    for vin, io in product((3.0, 3.3, 3.6), (0.015, 0.075, 0.15)):
        bb = replace(b, vin=vin, g_load=io / VSET)
        rr = simulate(bb, dp, adc, *gi_args, n=12000, vref_target=VREF_CODE, ilim=ILIM)
        ss = slice(2000, 12000)
        codes, cnt = np.unique(rr.d[ss], return_counts=True)
        ecodes = np.unique(rr.e[ss])
        lc.append(dict(vin=vin, io=io, n_duty_codes=len(codes), duty_codes=codes.tolist(),
                       adc_codes=ecodes.tolist(), v_sample_pp=float(np.ptp(rr.v[ss]))))
        if vin == 3.3 and io == 0.075:
            hist_nom = (codes, cnt)
    put("limitcycle_runs", lc, "-", note="10 ms after a 2 ms start-up, resistive load")
    put("limitcycle_free_all", bool(all(x["n_duty_codes"] == 1 for x in lc)), "-")

    # counter-example: 6-bit DPWM (counter only), DPWM LSB at output > ADC LSB.
    # Same loop design in the 6-bit code units; gains are 8x smaller, so 8 fractional bits are
    # used to keep ki non-zero (with F=2 it rounds to 0 and the loop has no integrator).
    dp6 = Dpwm(coarse_bits=6, fine_bits=0)
    F6 = 8
    g6 = design(b, DESIGN["io"], adc, dp6, DESIGN["fc"], DESIGN["pm"], DESIGN["fi_ratio"])
    n_lc6, c6, n6 = 0, None, None
    for io in np.linspace(0.010, 0.150, 15):
        bb = replace(b, g_load=io / VSET)
        rr = simulate(bb, dp6, adc, g6.ints(F6), F6, n=12000, vref_target=VREF_CODE, ilim=ILIM)
        cc, nn = np.unique(rr.d[2000:], return_counts=True)
        n_lc6 += len(cc) > 1
        if len(cc) > 1 and c6 is None:
            c6, n6, io6, pp6 = cc, nn, io, float(np.ptp(rr.v[2000:]))
    put("counterexample_6bit_dpwm_lsb_out", dp6.lsb_out(3.3), "V", "analysis")
    put("counterexample_6bit_gains_int", dict(zip(("kp", "ki", "kd"), g6.ints(F6)), frac=F6), "Q(frac)")
    put("counterexample_6bit_loads_with_limit_cycle", int(n_lc6), "of 15 loads 10..150 mA")
    if c6 is not None:
        put("counterexample_6bit_example", {"io": io6, "duty_codes": c6.tolist(), "v_sample_pp": pp6}, "-")
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    ax[0].bar(hist_nom[0], hist_nom[1], width=0.8, color=C1)
    ax[0].set_title("9-bit hybrid DPWM, 75 mA: duty codes over 10 ms")
    if c6 is not None:
        ax[1].bar(c6, n6, width=0.8, color=C2)
        ax[1].set_title(f"6-bit DPWM (LSB 52 mV > ADC 10 mV), {io6*1e3:.0f} mA")
    else:
        ax[1].set_title("6-bit DPWM: no limit cycle found")
    ax[0].set_xlim(hist_nom[0][0] - 6, hist_nom[0][-1] + 6)
    for a in ax:
        a.set_xlabel("DPWM code")
        a.set_ylabel("periods")
        a.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    fig.tight_layout()
    fig.savefig(PLOTS / "limit_cycle_hist.png", dpi=150)
    plt.close(fig)

    # ---------------- 12. delay-line tap error sweep ----------------
    scales = [0.6, 0.8, 1.0, 1.2, 1.4]
    loads = np.linspace(0.010, 0.150, 15)
    tap = []
    for s_ in scales:
        dps = replace(dp, tap_scale=s_)
        tons = np.array([dps.ton(c) for c in range(dp.nmax + 1)])
        steps = np.diff(tons) / (1 / dp.fclk / (1 << dp.fine_bits))
        n_lc = 0
        pp = []
        for io in loads:
            bb = replace(b, g_load=io / VSET)
            rr = simulate(bb, dps, adc, *gi_args, n=5000, vref_target=VREF_CODE, ilim=ILIM)
            n_lc += len(np.unique(rr.d[2500:])) > 1
            pp.append(float(np.ptp(rr.v[2500:])))
        tap.append(dict(tap_scale=s_, dnl_max=float(steps.max() - 1), dnl_min=float(steps.min() - 1),
                        loads_with_limit_cycle=int(n_lc), n_loads=len(loads), v_sample_pp_max=max(pp)))
    put("tapsweep", tap, "-", note="DNL from ideal-tap model; limit cycle = >1 duty code in 2.5 ms steady state")
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    ax[0].plot(scales, [x["dnl_max"] for x in tap], "o-", color=C1, ms=6, label="max DNL")
    ax[0].plot(scales, [x["dnl_min"] for x in tap], "o-", color=C2, ms=6, label="min DNL")
    ax[0].set_xlabel("delay-line tap / ideal tap")
    ax[0].set_ylabel("DPWM DNL [LSB]")
    ax[0].legend()
    ax[1].bar(scales, [x["loads_with_limit_cycle"] for x in tap], width=0.12, color=C1)
    ax[1].set_xlabel("delay-line tap / ideal tap")
    ax[1].set_ylabel(f"loads with limit cycle (of {len(loads)})")
    fig.suptitle("Effect of uncalibrated delay-line error (model)")
    fig.tight_layout()
    fig.savefig(PLOTS / "tap_sweep.png", dpi=150)
    plt.close(fig)

    # ---------------- 13. overload: valley current limit ----------------
    io_ol = lambda t: 0.35 if 3.0e-3 <= t < 3.2e-3 else 0.0
    rr = simulate(bl, dp, adc, *gi_args, n=3500, vref_target=VREF_CODE, ilim=ILIM, io_fn=io_ol)
    w = slice(int(3.0e-3 / b.Ts), int(3.2e-3 / b.Ts))
    put("overload_valley_max", float(rr.il_valley[w].max()), "A", note="0.365 A load for 200 us, ILIM 0.25 A")
    put("overload_peak_max", float(rr.il_peak[w].max()), "A")
    put("overload_trips", int(rr.trip[w].sum()), "-")
    put("overload_vout_min", float(rr.v[w].min()), "V")

    # ---------------- write ----------------
    path = ROOT / "results" / "summary.json"
    summary = json.loads(path.read_text()) if path.exists() else {}
    summary["phase1"] = S
    path.write_text(json.dumps(summary, indent=1, default=float) + "\n")
    print(json.dumps({k: v["value"] for k, v in S.items()
                      if k not in ("quant_study", "limitcycle_runs", "tapsweep")}, indent=1, default=float))


if __name__ == "__main__":
    main()
