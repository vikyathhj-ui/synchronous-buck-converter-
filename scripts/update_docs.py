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
        row("Overload 365 mA: max valley / peak iL",
            f"{v('overload_valley_max')*1e3:.0f} / {v('overload_peak_max')*1e3:.0f}", "mA", "model"),
        row("Overload: trips in 200 periods, min VOUT",
            f"{v('overload_trips')}, {v('overload_vout_min'):.3f} V", "-", "model"),
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


BLOCKS = {"p1_analysis": p1_analysis, "p1_design": p1_design, "p1_quant": p1_quant,
          "p1_robust": p1_robust, "p1_time": p1_time, "p1_limit": p1_limit}


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
