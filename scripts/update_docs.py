#!/usr/bin/env python3
"""Fill the auto-generated blocks in docs/*.md from results/summary.json.

A block is delimited by  <!-- AUTO:name -->  and  <!-- /AUTO:name -->.
Run: python3 scripts/update_docs.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "results" / "summary.json").read_text())


def v(key, phase="phase1"):
    return S[phase][key]["value"]


def k(key, phase="phase1"):
    return S[phase][key]["kind"]


def row(label, value, unit, kind):
    return f"| {label} | {value} | {unit} | {kind} |"


def tbl(rows):
    return "\n".join(["| Quantity | Value | Unit | Kind |", "|---|---|---|---|"] + rows)


def p1_analysis():
    return tbl([
        row("LC resonance f0", f"{v('f0_lc')/1e3:.2f}", "kHz", k("f0_lc")),
        row("ESR zero", f"{v('f_esr_zero')/1e6:.2f}", "MHz", k("f_esr_zero")),
        row("Duty at 150 mA (rs = DCR + Ron)", f"{v('duty_fullload'):.4f}", "-", k("duty_fullload")),
        row("Inductor ripple p-p, 150 mA", f"{v('il_ripple_pp')*1e3:.1f}", "mA", k("il_ripple_pp")),
        row("VOUT ripple p-p, capacitive term", f"{v('vout_ripple_cap_pp')*1e3:.3f}", "mV", k("vout_ripple_cap_pp")),
        row("VOUT ripple p-p, ESR term", f"{v('vout_ripple_esr_pp')*1e3:.3f}", "mV", k("vout_ripple_esr_pp")),
        row("DPWM tap", f"{v('dpwm_tap')*1e9:.3f}", "ns", k("dpwm_tap")),
        row("DPWM LSB at VOUT, VIN 3.0 / 3.3 / 3.6 V",
            " / ".join(f"{v(f'dpwm_lsb_out_vin{x}')*1e3:.2f}" for x in (3.0, 3.3, 3.6)), "mV", "analysis"),
        row("ADC LSB", f"{v('adc_lsb')*1e3:.0f}", "mV", k("adc_lsb")),
        row("Condition 1 (DPWM LSB < ADC LSB at all VIN)", v("cond1_dpwm_lsb_lt_adc_lsb_all_vin"), "-", "analysis"),
    ])


def p1_design():
    gf, gi = v("gains_float"), v("gains_int")
    F = gi["frac"]
    gm = v("gm")
    return tbl([
        row("Design target", f"fc {v('design_target')['fc']/1e3:.0f} kHz, PM {v('design_target')['pm']:.0f} deg, "
            f"integral zero fc/{v('design_target')['fi_ratio']:.0f}", "-", "model"),
        row("kp, ki, kd (float)", f"{gf['kp']:.4f}, {gf['ki']:.4f}, {gf['kd']:.3f}", "DPWM LSB / ADC LSB", "model"),
        row(f"kp, ki, kd (Q{F} integers)", f"{gi['kp']}, {gi['ki']}, {gi['kd']}", f"x 2^-{F}", "model"),
        row("Crossover fc", ", ".join(f"{x/1e3:.1f}" for x in v("fc")), "kHz", "model"),
        row("Phase margin", ", ".join(f"{x:.1f}" for x in v("pm")), "deg", "model"),
        row("Gain margin", ", ".join(f"{x:.1f}" for x in gm) + " at " +
            ", ".join(f"{x/1e3:.0f} kHz" for x in v("gm_phase_crossover")), "dB", "model"),
        row("Max closed-loop pole magnitude", f"{v('cl_max_pole_mag'):.4f}", "-", "model"),
        row("Normalised integral gain Ki_n (worst VIN)", f"{v('ki_normalised_worst'):.3f}", "-", "model"),
        row("Plant model check, max error", f"{v('plant_check_max_mag_err'):.1e} dB, "
            f"{v('plant_check_max_ph_err'):.1e} deg", "-", "model"),
    ])


def p1_quant():
    lines = ["| frac bits | kp | ki | kd | fc [kHz] | PM [deg] | crossovers | max pole |", "|---|---|---|---|---|---|---|---|"]
    for r in v("quant_study"):
        lines.append(f"| {r['frac']} | {r['kp']:.4f} | {r['ki']:.4f} | {r['kd']:.4f} | {r['fc']/1e3:.2f} | "
                     f"{r['pm']:.2f} | {r['n_cross']} | {r['max_eig']:.4f} |")
    lines.append("")
    lines.append(f"Chosen: **Q{v('quant_frac_bits')}** ({S['phase1']['quant_frac_bits']['note']}).")
    return "\n".join(lines)


def p1_robust():
    w = v("robust_worst_case")
    return tbl([
        row("Cases", v("robust_n_cases"), "-", "model"),
        row("PM range, VIN and load only (nominal L, C, Ron)", "{:.1f} .. {:.1f}".format(*v("pm_range_vin_io_only")), "deg", "model"),
        row("PM range, L and C +/-20 % only", "{:.1f} .. {:.1f}".format(*v("pm_range_lc_only")), "deg", "model"),
        row("PM range, all cases", f"{v('robust_pm_min'):.1f} .. {v('robust_pm_max'):.1f}", "deg", "model"),
        row("GM minimum, all cases", f"{v('robust_gm_min'):.1f}", "dB", "model"),
        row("fc range, all cases", "{:.1f} .. {:.1f}".format(*(x / 1e3 for x in v("robust_fc_range"))), "kHz", "model"),
        row("All closed loops stable", v("robust_all_stable"), "-", "model"),
        row("Single crossover in every case", v("robust_single_crossover_all"), "-", "model"),
        row(f"PM >= {v('pm_spec_all_cases'):.0f} deg in every case (requirement)", v("robust_pm_meets_spec_all"), "-", "model"),
        row("Worst case", f"VIN {w['vin']} V, L {w['L']*1e6:.0f} uH, C {w['C']*1e6:.0f} uF, "
            f"Ron {w['ron']} ohm, io {w['io']*1e3:.0f} mA", "-", "model"),
    ])


def p1_time():
    return tbl([
        row("Load step 15->150 mA: undershoot (switched)", f"{v('loadstep_undershoot')*1e3:.1f}", "mV", "model"),
        row("  same, sampled instants only", f"{v('loadstep_undershoot_switched_sampled')*1e3:.1f}", "mV", "model"),
        row("  same, linear sampled model", f"{v('loadstep_undershoot_linear')*1e3:.1f}", "mV", "model"),
        row("  recovery to +/-1 %", f"{v('loadstep_recovery_1pct')*1e6:.1f}", "us", "model"),
        row("Load step 150->15 mA: overshoot", f"{v('loadstep_down_overshoot')*1e3:.1f}", "mV", "model"),
        row("  recovery to +/-1 %", f"{v('loadstep_down_recovery_1pct')*1e6:.1f}", "us", "model"),
        row("Start-up overshoot, no load / full load",
            f"{v('startup_noload_overshoot_pct'):.2f} / {v('startup_fullload_overshoot_pct'):.2f}", "%", "model"),
        row("Start-up peak iL, no load / full load",
            f"{v('startup_noload_il_peak')*1e3:.0f} / {v('startup_fullload_il_peak')*1e3:.0f}", "mA", "model"),
        row("Start-up current-limit trips", f"{v('startup_noload_ilim_trips')} / {v('startup_fullload_ilim_trips')}", "-", "model"),
        row("Soft-start VREF ramp time", f"{v('startup_noload_vref_ramp_time')*1e3:.3f}", "ms", "model"),
        row("Line step 3.0->3.6 V: max deviation", f"{v('linestep_up_dev_max')*1e3:+.1f}", "mV", "model"),
        row("Line step 3.6->3.0 V: max deviation", f"{v('linestep_dn_dev_min')*1e3:+.1f}", "mV", "model"),
        row("VOUT ripple p-p, 150 mA", f"{v('ripple_vout_pp_fullload')*1e3:.2f}", "mV", "model"),
        row("iL ripple p-p, 150 mA", f"{v('ripple_il_pp_fullload')*1e3:.1f}", "mA", "model"),
        row("Overload 365 mA: max valley / peak iL (before FAULT)",
            f"{v('overload_valley_max')*1e3:.0f} / {v('overload_peak_max')*1e3:.0f}", "mA", "model"),
        row("Overload: trips / periods before FAULT, min VOUT",
            f"{v('overload_trips')} / {v('overload_periods_before_fault')}, {v('overload_vout_min'):.3f} V", "-", "model"),
        row("Overload: FAULT after", f"{v('overload_fault_after')*1e6:.0f}" if v("overload_fault") else "no fault", "us", "model"),
    ])


def p1_limit():
    lines = ["| VIN [V] | load [mA] | duty codes in 10 ms | ADC codes | sampled VOUT p-p [mV] |", "|---|---|---|---|---|"]
    for r in v("limitcycle_runs"):
        lines.append(f"| {r['vin']} | {r['io']*1e3:.0f} | {r['duty_codes']} | {r['adc_codes']} | {r['v_sample_pp']*1e3:.3f} |")
    lines.append("")
    lines.append(f"Limit-cycle free in all 9 runs: **{v('limitcycle_free_all')}**. "
                 f"Counter-example, 6-bit DPWM (LSB {v('counterexample_6bit_dpwm_lsb_out')*1e3:.1f} mV at VOUT): "
                 f"limit cycle at **{v('counterexample_6bit_loads_with_limit_cycle')} of 15** loads.")
    if "counterexample_6bit_example" in S["phase1"]:
        ex = v("counterexample_6bit_example")
        lines.append(f"Example at {ex['io']*1e3:.0f} mA: duty codes {ex['duty_codes']}, sampled VOUT p-p {ex['v_sample_pp']*1e3:.1f} mV.")
    lines.append("")
    lines.append("| tap / ideal | DNL max [LSB] | DNL min [LSB] | loads with limit cycle | max sampled p-p [mV] |")
    lines.append("|---|---|---|---|---|")
    for r in v("tapsweep"):
        lines.append(f"| {r['tap_scale']} | {r['dnl_max']:+.2f} | {r['dnl_min']:+.2f} | "
                     f"{r['loads_with_limit_cycle']} of {r['n_loads']} | {r['v_sample_pp_max']*1e3:.2f} |")
    return "\n".join(lines)


def p2(key):
    return S["phase2"][key]["value"]


def p2_tests():
    lines = ["| Test | Result | Periods checked | Scoreboard mismatches | Key metrics |", "|---|---|---|---|---|"]
    res = p2("cocotb_results") if "cocotb_results" in S.get("phase2", {}) else {}
    for name, st in res.items():
        m = S["phase2"].get(name, {}).get("value", {})
        keys = [k for k in m if k not in ("scoreboard_periods", "scoreboard_mismatches", "pass")]
        def fmt(x):
            if isinstance(x, float):
                return f"{x:.4g}"
            return str(x)
        lines.append(f"| {name} | {st} | {m.get('scoreboard_periods', '-')} | {m.get('scoreboard_mismatches', '-')} | "
                     + "; ".join(f"{k} = {fmt(m[k])}" for k in keys[:6]) + " |")
    return "\n".join(lines)


def p2_checks():
    rows = []
    if "lint" in S.get("phase2", {}):
        l = p2("lint")
        rows.append(row("Verilator -Wall lint", f"{l['warnings']} warnings, {l['errors']} errors", "-", "lint"))
    if "formal" in S.get("phase2", {}):
        rows.append(row("SymbiYosys k-induction (formal/buck_ctrl.sby)", p2("formal"), "-", "formal"))
    if "functional_coverage_pct" in S.get("phase2", {}):
        for k, v in p2("functional_coverage_pct").items():
            rows.append(row(f"coverage {k}", f"{v:.1f}", "%", "rtl-sim"))
    return tbl(rows)


# ------------------------------------------------------------------ phase 3
def _p3(key):
    e = S.get("phase3", {}).get(key)
    return None if e is None else e["value"]


def _ns(x):
    return f"{x * 1e9:.2f}"


def _rng(x, f, unit_scale=1.0, fmt="{:.2f}"):
    return (fmt + " .. " + fmt).format(x[0] * unit_scale, x[1] * unit_scale)


def _table(rows):
    lines = ["| Quantity | Value | Unit | Source |", "|---|---|---|---|"]
    for label, key, f, unit in rows:
        v = _p3(key)
        src = S.get("phase3", {}).get(key, {}).get("source") or "-"
        lines.append(f"| {label} | {'pending' if v is None else f(v)} | {unit} | {src} |")
    return "\n".join(lines)


def p3_power():
    r2 = lambda x: _rng(x, None)
    return _table([
        ("NMOS g5v0d10v5 Ron x W, tt / PVT range", "fet_ron_mm_n_tt", lambda v: f"{v:.3f}", "ohm*mm"),
        ("  over 45 PVT points", "fet_ron_mm_n_range", r2, "ohm*mm"),
        ("PMOS g5v0d10v5 Ron x W, tt", "fet_ron_mm_p_tt", lambda v: f"{v:.3f}", "ohm*mm"),
        ("  over 45 PVT points", "fet_ron_mm_p_range", r2, "ohm*mm"),
        ("Gate charge per mm (n / p), tt", "fet_qg_mm_tt", lambda v: f"{v['n']*1e12:.2f} / {v['p']*1e12:.2f}", "pC/mm"),
        ("LS body-diode drop at 150 mA/mm, tt", "fet_body_diode_vf_tt", lambda v: f"{v:.3f}", "V"),
        ("HS / LS width (loss-model optimum)", "power_w_hs", lambda v: f"{v:.1f} / {_p3('power_w_ls'):.1f}", "mm"),
        ("HS / LS Ron at tt", "power_ron_hs_tt", lambda v: f"{v:.3f} / {_p3('power_ron_ls_tt'):.3f}", "ohm"),
        ("Model mean efficiency 10..150 mA (power stage only)", "sizing_mean_eff_model", lambda v: f"{v*100:.2f}", "%"),
    ])


def p3_driver():
    rn = lambda v: f"{v[0]*1e9:.2f} .. {v[1]*1e9:.2f}"
    return _table([
        ("HS_ON -> HS gate (50 %)", "drv_hs_on_dly_range", rn, "ns"),
        ("HS off delay", "drv_hs_off_dly_range", rn, "ns"),
        ("LS_ON -> LS gate", "drv_ls_on_dly_range", rn, "ns"),
        ("LS off delay", "drv_ls_off_dly_range", rn, "ns"),
        ("HS gate fall / rise (10-90 %)", "drv_hs_fall_range", lambda v: f"{rn(v)} / {rn(_p3('drv_hs_rise_range'))}", "ns"),
        ("LS gate rise / fall", "drv_ls_rise_range", lambda v: f"{rn(v)} / {rn(_p3('drv_ls_fall_range'))}", "ns"),
        ("Max LS gate bump during HS turn-on (dV/dt)", "ls_gate_dvdt_bump_max", lambda v: f"{v:.3f}", "V"),
        ("Max HS Vsg disturbance while off", "hs_gate_disturb_max", lambda v: f"{v*1e3:.1f}", "mV"),
        ("Max switch-node dV/dt", "sw_dvdt_max", lambda v: f"{v/1e9:.1f}", "V/ns"),
        ("Level shifter lv->hv rise / fall", "levelshift_lv2hv_rise_range", lambda v: f"{rn(v)} / {rn(_p3('levelshift_lv2hv_fall_range'))}", "ns"),
        ("Level shifter hv->lv rise / fall", "levelshift_hv2lv_rise_range", lambda v: f"{rn(v)} / {rn(_p3('levelshift_hv2lv_fall_range'))}", "ns"),
    ])


def p3_losses():
    v = _p3("loss_compare")
    if v is None:
        return "pending"
    lines = ["| Load [mA] | FET loss sim [mW] | FET loss model [mW] | Gate drive sim [mW] | Gate drive model [mW] | Body diode [ns/period] |",
             "|---|---|---|---|---|---|"]
    for r in v:
        lines.append(f"| {r['io']*1e3:.0f} | {r['fet_sim']*1e3:.3f} | {r['fet_model']*1e3:.3f} | {r['gate_sim']*1e3:.3f} | "
                     f"{r['gate_model']*1e3:.3f} | {r['t_bd']*1e9:.1f} |")
    return "\n".join(lines)


def p3_deadtime():
    rn = lambda v: f"{v[0]*1e9:.2f} .. {v[1]*1e9:.2f}"
    rows = []
    for c in (0, 3, 7):
        rows.append((f"Code {c}: HS off -> LS on, over PVT", f"deadtime_code{c}_hl_range", rn, "ns"))
        rows.append((f"Code {c}: LS off -> HS on, over PVT", f"deadtime_code{c}_lh_range", rn, "ns"))
    rows += [("Smallest dead time, all runs", "deadtime_min_all", lambda v: f"{v*1e9:.2f}", "ns"),
             ("Shoot-through free (dead time > 0 everywhere)", "shoot_through_free", str, "-")]
    return _table(rows)


def p3_dpwm():
    return _table([
        ("Uncalibrated: tap / ideal over PVT", "dpwm_uncal_tap_scale_range", lambda v: f"{v[0]:.3f} .. {v[1]:.3f}", "-"),
        ("Uncalibrated: DNL over PVT", "dpwm_uncal_dnl_range", lambda v: f"{v[0]:+.2f} .. {v[1]:+.2f}", "LSB"),
        ("Calibrated: N (elements per clock) over PVT", "dpwm_cal_n_range", lambda v: f"{v[0]} .. {v[1]}", "-"),
        ("Calibrated: DNL over PVT", "dpwm_cal_dnl_range", lambda v: f"{v[0]:+.3f} .. {v[1]:+.3f}", "LSB"),
        ("Calibrated: INL over PVT", "dpwm_cal_inl_range", lambda v: f"{v[0]:+.3f} .. {v[1]:+.3f}", "LSB"),
        ("Calibrated: largest output step at VIN 3.6 V (PVT)", "dpwm_cal_max_step_mv_vin36", lambda v: f"{v:.2f}", "mV"),
        ("Calibrated: DNL sigma, Monte Carlo", "dpwm_cal_mc_dnl_sigma", lambda v: f"{v:.3f}", "LSB"),
        ("Calibrated: largest output step at VIN 3.6 V (MC)", "dpwm_cal_mc_max_step_mv_vin36", lambda v: f"{v:.2f}", "mV"),
        ("Main vs replica element delay, worst relative difference", "dpwm_cal_main_vs_replica", lambda v: f"{v*100:.2f}", "%"),
    ])


def p3_comparator():
    st = _p3("cmp_offset_stats")
    rows = [("All corners functional at CM 0.5 / 0.9 / 1.25 V, 2 mV overdrive < 31 ns", "cmp_all_decisions_correct", str, "-"),
            ("Worst clk -> q delay, 2 mV overdrive", "cmp_delay_1mV_max", lambda v: f"{v*1e9:.2f}", "ns")]
    t = _table(rows)
    if st:
        t += "\n\n| Common mode [V] | Offset mean [mV] | Offset sigma [mV] | Range [mV] | Samples |\n|---|---|---|---|---|\n"
        for cm, x in st.items():
            if x.get("failed"):
                t += f"| {cm} | - | - | fails | {x['n']} |\n"
            else:
                t += f"| {cm} | {x['mean']*1e3:+.2f} | {x['sigma']*1e3:.2f} | {x['min']*1e3:+.2f} .. {x['max']*1e3:+.2f} | {x['n']} |\n"
    return t


def p3_swcmp():
    rows = []
    for f, name in (("zc", "Zero-cross"), ("ilim", "Valley limit")):
        rows.append((f"{name}: functional over PVT", f"swcmp_{f}_functional", str, "-"))
        rows.append((f"{name}: systematic offset over PVT (at VSW)", f"swcmp_{f}_sys_offset_range", lambda v: f"{v[0]*1e3:+.2f} .. {v[1]*1e3:+.2f}", "mV"))
        rows.append((f"{name}: shift-network settling (10-90 %)", f"swcmp_{f}_settle_max", lambda v: f"{v*1e9:.2f}", "ns"))
    rows.append(("Offset sigma at VSW, MC (zc / ilim)", "swcmp_mc_stats", lambda v: f"{v['zc']['sigma']*1e3:.2f} / {v['ilim']['sigma']*1e3:.2f}", "mV"))
    rows.append(("250 mA setting: actual valley threshold over the LS Ron PVT spread", "ilim_threshold_current_range", lambda v: f"{v[0]*1e3:.0f} .. {v[1]*1e3:.0f}", "mA"))
    return _table(rows)


def p3_adc():
    rows = [("Threshold error sigma from the string (code 100 / 180 / 250)", "adcref_threshold_sigma_lsb",
             lambda v: " / ".join(f"{x:.3f}" for x in v.values()), "LSB"),
            ("Threshold spacing sigma from the string", "adcref_spacing_sigma_lsb", lambda v: " / ".join(f"{x:.4f}" for x in v.values()), "LSB"),
            ("Divider ratio sigma", "divider_ratio_sigma_rel", lambda v: f"{v*100:.3f}", "%"),
            ("Full front end MC (DNL sigma, min, max; zero bin mean / min; samples with missing codes)", "adc_mc_stats",
             lambda v: f"{v['dnl_sigma']:.3f}, {v['dnl_min']:+.2f}, {v['dnl_max']:+.2f} LSB; {v['zero_bin_mean_mv']:.2f} / {v['zero_bin_min_mv']:.2f} mV; {v['missing_code_samples']}", "-")]
    t = _table(rows)
    pv = _p3("adc_pvt")
    if pv:
        t += "\n\n| Corner | T [C] | VIN [V] | Functional | Zero bin [mV] | DNL range [LSB] | Missing codes |\n|---|---|---|---|---|---|---|\n"
        for r in pv:
            d = r["dnl_range"]
            zb = "-" if r["zero_bin_mv"] is None else f"{r['zero_bin_mv']:.2f}"
            dr = "-" if d is None else f"{d[0]:+.2f} .. {d[1]:+.2f}"
            t += f"| {r['corner']} | {r['temp']} | {r['vin']} | {r['functional']} | {zb} | {dr} | {r['missing_codes']} |\n"
    return t


def p3_impact():
    rows = [("Uncalibrated DPWM: PVT x load cases with a limit cycle", "loop_impact_dpwm_uncal",
             lambda v: f"{v['limit_cycles']} of {v['cases']} (ideal DPWM: {v['ideal_dpwm_limit_cycles']})", "-"),
            ("Calibrated DPWM: PVT x load cases with a limit cycle", "loop_impact_dpwm_cal",
             lambda v: f"{v['limit_cycles']} of {v['cases']}", "-"),
            ("Comparator offsets: cases with a limit cycle; VOUT error sigma", "loop_impact_adc_offsets",
             lambda v: f"{v['limit_cycles']} of {v['cases']}; {v['vout_error_sigma']*1e3:.2f} mV", "-"),
            ("Comparator offsets: draws with zero bin < DPWM step (7.03 mV)", "loop_impact_adc_offsets",
             lambda v: f"{v['zero_bin_lt_dpwm_step_fraction']*100:.1f} %", "-")]
    return _table(rows)


def p3_lvs():
    v = _p3("xschem_vs_spice_lvs")
    if v is None:
        return "pending"
    return "| Cell | xschem vs SPICE (netgen) |\n|---|---|\n" + "\n".join(f"| {k} | {'match' if x else 'MISMATCH'} |" for k, x in v.items())


BLOCKS = {"p1_analysis": p1_analysis, "p1_design": p1_design, "p1_quant": p1_quant,
          "p1_robust": p1_robust, "p1_time": p1_time, "p1_limit": p1_limit,
          "p2_tests": p2_tests, "p2_checks": p2_checks,
          "p3_power": p3_power, "p3_driver": p3_driver, "p3_losses": p3_losses, "p3_deadtime": p3_deadtime,
          "p3_dpwm": p3_dpwm, "p3_comparator": p3_comparator, "p3_swcmp": p3_swcmp, "p3_adc": p3_adc,
          "p3_impact": p3_impact, "p3_lvs": p3_lvs}


def main():
    for md in (ROOT / "docs").glob("*.md"):
        text = md.read_text()
        new = text
        for name, fn in BLOCKS.items():
            pat = re.compile(rf"(<!-- AUTO:{name} -->\n).*?(<!-- /AUTO:{name} -->)", re.S)
            new = pat.sub(lambda m: m.group(1) + fn() + "\n" + m.group(2), new)
        if new != text:
            md.write_text(new)
            print("updated", md.relative_to(ROOT))


if __name__ == "__main__":
    main()
