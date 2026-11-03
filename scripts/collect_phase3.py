#!/usr/bin/env python3
"""Merge the Phase 3 block results (results/phase3/*.json, all parsed from ngspice/netgen output)
into results/summary.json["phase3"] and draw the block plots in results/plots/phase3/.
Missing inputs are skipped, so this can run while characterisation is still in progress.
"""
import json
import pathlib
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
P3 = ROOT / "results" / "phase3"
PLOTS = ROOT / "results" / "plots" / "phase3"
C1, C2, C3, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#1baf7a", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "legend.frameon": False})
S = {}


def load(name):
    p = P3 / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def put(key, value, unit, kind="sim", src=None, note=None):
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    S[key] = {"value": value, "unit": unit, "kind": kind, "source": src}
    if note:
        S[key]["note"] = note


def rng(rows, f):
    xs = [f(r) for r in rows]
    return [min(xs), max(xs)]


def main():
    PLOTS.mkdir(parents=True, exist_ok=True)
    src = "results/phase3/{}.json (scripts/char_{}.py)"

    fet = load("fet")
    if fet:
        tt = [r for r in fet["rows"] if r["corner"] == "tt" and r["temp"] == 27 and r["vin"] == 3.3][0]
        s = src.format("fet", "fet")
        put("fet_ron_mm_n_tt", tt["n"]["ron_mm"], "ohm*mm", src=s)
        put("fet_ron_mm_p_tt", tt["p"]["ron_mm"], "ohm*mm", src=s)
        put("fet_ron_mm_n_range", rng(fet["rows"], lambda r: r["n"]["ron_mm"]), "ohm*mm", src=s, note="45 PVT points")
        put("fet_ron_mm_p_range", rng(fet["rows"], lambda r: r["p"]["ron_mm"]), "ohm*mm", src=s)
        put("fet_qg_mm_tt", {"n": tt["n"]["qg_mm"], "p": tt["p"]["qg_mm"]}, "C/mm", src=s)
        put("fet_qoss_mm_tt", {"n": tt["n"]["qoss_mm"], "p": tt["p"]["qoss_mm"]}, "C/mm", src=s)
        put("fet_body_diode_vf_tt", tt["n"]["vbd"], "V", src=s, note="150 mA per mm")

    sz = load("sizing")
    if sz:
        s = "results/phase3/sizing.json (scripts/size_power.py)"
        put("power_w_hs", sz["w_hs_mm"], "mm", "analysis", s)
        put("power_w_ls", sz["w_ls_mm"], "mm", "analysis", s)
        put("power_ron_hs_tt", sz["ron_hs_tt"], "ohm", "analysis", s)
        put("power_ron_ls_tt", sz["ron_ls_tt"], "ohm", "analysis", s)
        put("sizing_mean_eff_model", sz["mean_eff"], "-", "analysis", s, "loss model only; no controller/comparator power")
        put("sizing_sensitivity", sz["sensitivity"], "-", "analysis", s)

    ps = load("powerstage")
    if ps and "delays" in ps:
        s = src.format("powerstage", "powerstage")
        d = ps["delays"]
        for k in ("hs_on_dly", "hs_off_dly", "ls_on_dly", "ls_off_dly", "hs_fall", "hs_rise", "ls_rise", "ls_fall"):
            put(f"drv_{k}_range", rng(d, lambda r: r[k]), "s", src=s)
        put("ls_gate_dvdt_bump_max", max(r["ls_g_bump"] for r in d), "V", src=s, note="LS gate while HS turns on")
        put("hs_gate_disturb_max", max(r["hs_vsg_bump"] for r in d), "V", src=s, note="HS Vsg while off")
        put("sw_dvdt_max", max(r["sw_dvdt_max"] for r in d), "V/s", src=s)
    if ps and "losses" in ps:
        s = src.format("powerstage", "powerstage")
        put("loss_compare", [{"io": r["io"], "fet_sim": r["sim"]["p_fet"], "fet_model": r["model"]["p_fet"],
                              "gate_sim": r["sim"]["p_drv"] + r["sim"]["p_shift"], "gate_model": r["model"]["p_gate"],
                              "t_bd": r["sim"]["t_bd_per_period"]} for r in ps["losses"]], "W", src=s,
            note="constant inductor current, tt/27C/3.3V, ideal 1.8 V commands with 10 ns logic dead time")
        lc = ps["losses"]
        io = np.array([r["io"] for r in lc]) * 1e3
        fig, ax = plt.subplots(figsize=(7, 3.4))
        w = 3.0
        ax.bar(io - w / 2, [r["sim"]["p_fet"] * 1e3 for r in lc], width=w, color=C1, label="FET loss, ngspice")
        ax.bar(io + w / 2, [r["model"]["p_fet"] * 1e3 for r in lc], width=w, color=C2, label="FET loss, model")
        ax.plot(io, [(r["sim"]["p_drv"] + r["sim"]["p_shift"]) * 1e3 for r in lc], "o-", color=C3, ms=6,
                label="gate drive, ngspice")
        ax.set_xlabel("load current [mA]")
        ax.set_ylabel("loss [mW]")
        ax.set_title("Power stage losses: simulation vs analytical model (tt, 27 C, 3.3 V)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(PLOTS / "loss_model_vs_sim.png", dpi=150)
        plt.close(fig)

    dt = load("deadtime")
    if dt:
        s = src.format("deadtime", "deadtime")
        for code in (0, 3, 7):
            put(f"deadtime_code{code}_hl_range", [dt[f"code{code}_dt_hl_min"], dt[f"code{code}_dt_hl_max"]], "s", src=s)
            put(f"deadtime_code{code}_lh_range", [dt[f"code{code}_dt_lh_min"], dt[f"code{code}_dt_lh_max"]], "s", src=s)
            put(f"deadtime_code{code}_tt", {k: dt[f"code{code}_tt"][k] for k in ("dt_hl", "dt_lh", "t_bd")}, "s", src=s)
        put("deadtime_min_all", dt["min_dead_time_all"], "s", src=s, note="45 PVT x codes 0/3/7 x +150/-30 mA")
        put("shoot_through_free", dt["shoot_through_free"], "-", src=s)
        fig, ax = plt.subplots(figsize=(7, 3.4))
        for code, col in zip((0, 3, 7), (C1, C2, C3)):
            r = [x for x in dt["rows"] if x["code"] == code]
            ax.plot(np.arange(len(r)), [x["dt_hl"] * 1e9 for x in r], ".", color=col, ms=6, label=f"code {code}, HS off -> LS on")
            ax.plot(np.arange(len(r)), [x["dt_lh"] * 1e9 for x in r], "x", color=col, ms=5)
        ax.axhline(0, color="#d03b3b", lw=0.8)
        ax.set_xlabel("PVT x current case")
        ax.set_ylabel("dead time at the gates [ns]")
        ax.set_title("Dead time across PVT (dots HS->LS, crosses LS->HS); 0 = shoot-through limit")
        ax.legend(loc="upper left")
        fig.tight_layout()
        fig.savefig(PLOTS / "deadtime_pvt.png", dpi=150)
        plt.close(fig)

    dc = load("delaycells")
    if dc:
        put("delaycells", dc["summary"], "s", src=src.format("delaycells", "delaycells"))

    dp = load("dpwm")
    if dp and "pvt" in dp:
        s = src.format("dpwm", "dpwm")
        rows = dp["pvt"]
        put("dpwm_uncal_tap_scale_range", rng(rows, lambda r: r["tap_scale"]), "-", src=s)
        put("dpwm_uncal_dnl_range", [min(min(r["dnl"]) for r in rows), max(max(r["dnl"]) for r in rows)], "LSB", src=s)
        put("dpwm_uncal_inl_range", [min(min(r["inl"]) for r in rows), max(max(r["inl"]) for r in rows)], "LSB", src=s)
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
        for r in rows:
            col = {"tt": C1, "ff": C2, "ss": C3}.get(r["corner"], INK2)
            ax[0].plot(range(1, 9), r["dnl"], "-", color=col, lw=0.8, alpha=0.7)
            ax[1].plot(range(8), r["inl"], "-", color=col, lw=0.8, alpha=0.7)
        ax[0].set_xlabel("step (8 = coarse boundary)")
        ax[0].set_ylabel("DNL [LSB]")
        ax[1].set_xlabel("fine code")
        ax[1].set_ylabel("INL [LSB]")
        fig.suptitle("Uncalibrated DPWM fine stage over 45 PVT points (tt blue, ff orange, ss green, sf/fs grey)")
        fig.tight_layout()
        fig.savefig(PLOTS / "dpwm_dnl_inl_pvt.png", dpi=150)
        plt.close(fig)
    if dp and "mc" in dp:
        dn = np.array([r["dnl"][:7] for r in dp["mc"]])
        put("dpwm_mc_dnl_sigma", float(dn.std()), "LSB", src=src.format("dpwm", "dpwm"), note="100 MC, tt")

    cp = load("comparator")
    if cp and "pvt" in cp:
        s = src.format("comparator", "comparator")
        put("cmp_all_decisions_correct", all(r["correct"] for r in cp["pvt"]), "-", src=s, note="1 mV and 10 mV, 45 PVT")
        put("cmp_delay_1mV_max", max(r["delay_1mV"] for r in cp["pvt"]), "s", src=s)
    if cp and "mc_stats" in cp:
        s = src.format("comparator", "comparator")
        put("cmp_offset_stats", cp["mc_stats"], "V", src=s, note="100 MC per input common mode, tt 27 C")
        fig, ax = plt.subplots(figsize=(7, 3.4))
        cols = [C1, C2, C3, INK2]
        for (cm, st), col in zip(cp["mc_stats"].items(), cols):
            if st.get("failed"):
                continue
            os_ = [r["offset"] * 1e3 for r in cp["mc"] if str(r["cm"]) == cm and r["offset"] is not None]
            ax.hist(os_, bins=20, histtype="step", lw=1.6, color=col,
                    label=f"CM {cm} V: sigma {st['sigma']*1e3:.2f} mV")
        ax.axvspan(-2.5, 2.5, color=GRID, alpha=0.6, label="+/- half ADC LSB at the comparator (5 mV LSB)")
        ax.set_xlabel("input-referred offset [mV]")
        ax.set_ylabel("samples")
        ax.set_title("Window-ADC comparator (cmp_adc: preamp + cmp_hv) offset, Monte Carlo, tt 27 C, VIN 3.3 V")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(PLOTS / "comparator_offset_hist.png", dpi=150)
        plt.close(fig)

    dcal = load("dpwm_cal")
    if dcal and "pvt" in dcal:
        s_ = src.format("dpwm_cal", "dpwm_cal")
        rows = dcal["pvt"]
        put("dpwm_cal_n_range", rng(rows, lambda r: r["n"]), "elements/Tclk", src=s_)
        put("dpwm_cal_dnl_range", [min(min(r["dnl"]) for r in rows), max(max(r["dnl"]) for r in rows)], "LSB", src=s_)
        put("dpwm_cal_inl_range", [min(min(r["inl"]) for r in rows), max(max(r["inl"]) for r in rows)], "LSB", src=s_)
        put("dpwm_cal_max_step_mv_vin36", max(r["max_step_mv_vin36"] for r in rows), "mV", src=s_,
            note="largest DPWM step at VOUT (VIN 3.6 V); must stay below the 10 mV ADC LSB")
        put("dpwm_cal_main_vs_replica", max(abs(r["t_main"] / r["t_rep"] - 1) for r in rows), "-", src=s_,
            note="largest relative element-delay difference, main vs replica line")
        unc = load("dpwm")
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
        if unc and "pvt" in unc:
            for r in unc["pvt"]:
                ax[0].plot(range(1, 9), r["dnl"], "-", color=GRID, lw=0.8)
                ax[1].plot(range(8), r["inl"], "-", color=GRID, lw=0.8)
        for r in rows:
            ax[0].plot(range(1, 9), r["dnl"], "-", color=C1, lw=0.8, alpha=0.7)
            ax[1].plot(range(8), r["inl"], "-", color=C1, lw=0.8, alpha=0.7)
        ax[0].set_xlabel("step (8 = coarse boundary)")
        ax[0].set_ylabel("DNL [LSB]")
        ax[1].set_xlabel("fine code")
        ax[1].set_ylabel("INL [LSB]")
        fig.suptitle("DPWM fine stage over 45 PVT points: calibrated (blue) vs uncalibrated (grey)")
        fig.tight_layout()
        fig.savefig(PLOTS / "dpwm_dnl_inl_pvt.png", dpi=150)
        plt.close(fig)
    if dcal and "mc" in dcal:
        dn = np.array([r["dnl"] for r in dcal["mc"]])
        put("dpwm_cal_mc_dnl_sigma", float(dn.std()), "LSB", src=src.format("dpwm_cal", "dpwm_cal"), note="50 MC, tt")
        put("dpwm_cal_mc_max_step_mv_vin36", max(r["max_step_mv_vin36"] for r in dcal["mc"]), "mV",
            src=src.format("dpwm_cal", "dpwm_cal"))

    sw = load("swcmp")
    if sw and "pvt" in sw:
        s_ = src.format("swcmp", "swcmp")
        for f in ("zc", "ilim"):
            r = [x for x in sw["pvt"] if x["func"] == f]
            ok = [x for x in r if x["offset"] is not None]
            put(f"swcmp_{f}_functional", f"{len(ok)}/{len(r)}", "-", src=s_)
            if ok:
                put(f"swcmp_{f}_sys_offset_range", rng(ok, lambda x: x["offset"]), "V", src=s_, note="referred to VSW")
            put(f"swcmp_{f}_settle_max", max(x["settle"] for x in r), "s", src=s_)
    if sw and "mc_stats" in sw:
        put("swcmp_mc_stats", sw["mc_stats"], "V", src=src.format("swcmp", "swcmp"), note="referred to VSW, 50 MC each")
        if fet:
            ron = rng(fet["rows"], lambda r: r["n"]["ron_mm"])
            put("ilim_threshold_current_range", [0.25 * 2.032 / ron[1], 0.25 * 2.032 / ron[0]], "A", "analysis",
                "results/phase3/fet.json", "250 mA setting with the threshold fixed at 250 mA x Ron(tt): the LS Ron spread over PVT")

    adc = load("adc")
    if adc and "pvt" in adc:
        s_ = src.format("adc", "adc")
        put("adc_pvt", [{k: r[k] for k in ("corner", "temp", "vin", "functional", "zero_bin_mv", "missing_codes")}
                        | {"dnl_range": [min(r["dnl"]), max(r["dnl"])] if r["dnl"] else None} for r in adc["pvt"]], "-", src=s_)
    if adc and "mc_stats" in adc:
        put("adc_mc_stats", adc["mc_stats"], "LSB / mV", src=src.format("adc", "adc"), note="20 MC, full front end incl. kickback")

    ls = load("levelshift")
    if ls:
        s_ = src.format("levelshift", "levelshift")
        for k in ("lv2hv_rise", "lv2hv_fall", "hv2lv_rise", "hv2lv_fall"):
            put(f"levelshift_{k}_range", ls[k + "_range"], "s", src=s_)

    li = P3 / "loop_impact.json"
    if li.exists():
        d = json.loads(li.read_text())
        for k in ("dpwm_uncal", "dpwm_cal", "adc_offsets"):
            if k in d:
                put(f"loop_impact_{k}", {a: b for a, b in d[k].items() if a != "per_case"}, "-", "model",
                    "results/phase3/loop_impact.json (scripts/loop_impact.py)")

    ar = load("adcref")
    if ar:
        s = src.format("adcref", "adcref")
        put("adcref_threshold_sigma_lsb", {c: ar[f"code{c}"]["th_err_sigma_lsb"] for c in (100, 180, 250)}, "LSB", src=s)
        put("adcref_spacing_sigma_lsb", {c: ar[f"code{c}"]["spacing_err_sigma_lsb"] for c in (100, 180, 250)}, "LSB", src=s)
        put("divider_ratio_sigma_rel", ar["div_ratio_sigma_rel"], "-", src=s)

    lvs = sorted((P3 / "lvs_xschem").glob("*.txt"))
    if lvs:
        res = {}
        for f in lvs:
            t = f.read_text()
            res[f.stem] = bool("Circuits match uniquely" in t and not re.search("do not match|property errors", t, re.I))
        put("xschem_vs_spice_lvs", res, "-", "lvs", "results/phase3/lvs_xschem/*.txt (scripts/lvs_xschem.sh, netgen)")

    path = ROOT / "results" / "summary.json"
    summary = json.loads(path.read_text()) if path.exists() else {}
    summary["phase3"] = S
    path.write_text(json.dumps(summary, indent=1, default=float) + "\n")
    print(f"phase3: {len(S)} entries")


if __name__ == "__main__":
    main()
