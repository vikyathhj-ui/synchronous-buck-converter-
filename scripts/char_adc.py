#!/usr/bin/env python3
"""Window ADC front end in closed form: VOUT -> adc_div (VOUT/2, 10 pF) -> 15 x cmp_adc against the 15
threshold taps. Each tap is its Thevenin equivalent from the string (ideal tap voltage, 109 kohm =
the mid-string impedance, 2 pF MIM), so comparator kickback is included; the string's own matching
is in results/phase3/adcref.json (negligible).
VOUT ramps slowly through the 15 thresholds around VREF = 1.8 V (0.5 mV per decision). The
comparators are clocked as in the RTL (docs/ARCHITECTURE.md): one decision per 1 MHz switching
period, adc_sample high for one 64 MHz cycle (15.6 ns). cmp_adc = static preamp + cmp_hv (D30); the
preamp tails share one adc_pbias diode fed by an ideal 10 uA reference. Max time step 5 ns: a
30-decision A/B check gave decisions identical to a 0.2 ns step (D30). Per comparator: flip point vs the ideal VOUT
threshold VREF - (i - 7.5) x 10 mV -> threshold errors, DNL (spacing) and missing codes.
  pvt : the 5 corners at 27 C and 3.3 V, plus ss -40 C / 3.0 V and ff 125 C / 3.6 V
  mcc : Monte Carlo DNL computed from measured data (DECISIONS D29): the tt full-front-end
        thresholds + 15 offsets drawn from the 100 cmp_adc Monte Carlo offsets at CM 0.9 V
        (comparator.json, x2 to VOUT) + the 15 ladder tap errors of one adcref.json Monte Carlo seed
  mc  : 20 simulated mismatch samples at tt / 27 C / 3.3 V (not in "all": ~3.5 GB, 50 min each unsegmented)
The 340-decision ramp is simulated in NSEG segments, each starting W decisions early (comparator
and divider settle) and ending W late; decisions in the overlaps are compared between neighbouring
segments ("overlap_mismatch", must be 0). (A full ramp at the old 0.2 ns step grew past 3 GB.)
Writes results/phase3/adc.json.
"""
import json
import pathlib
import sys

import numpy as np

from spicelib import HVL, PDK, header, include, pmap, run, save

HD = PDK / "libs.ref" / "sky130_fd_sc_hd" / "spice" / "sky130_fd_sc_hd.spice"
TDEC = 1e-6
TH = 15.625e-9                # adc_sample: one 64 MHz cycle
IBIAS = 10e-6
TMAX = "5n"
VREF = 1.8
LSB = 0.010
SPAN = 0.085
STEP = 0.0005
N = int(2 * SPAN / STEP)
NSEG = 5
W = 4


def vout_of(k):
    """Ramp value at the start of decision period k (full-ramp time k x TDEC)."""
    return VREF - SPAN + 2 * SPAN * k / N


def bounds(seg):
    k0, k1 = seg * N // NSEG, (seg + 1) * N // NSEG
    return k0, k1, max(0, k0 - W), min(N, k1 + W)


def seg_run(a):
    """One ramp segment: returns {k: [q0..q14 at decision k]} for k in [ks, ke)."""
    corner, temp, vin, mc, seed, seg = a
    k0, k1, ks, ke = bounds(seg)
    tag = f"adc_{corner}_{temp}_{vin}_{'mc' + str(seed) if mc else 'nom'}_s{seg}of{NSEG}"
    n_loc = ke - ks
    T = n_loc * TDEC
    taps, comps = [], []
    for i in range(15):
        vt = VREF / 2 - (i - 7.5) * LSB / 2          # bit i = 1 when VOUT < VREF - (i - 7.5) LSB
        taps.append(f"VT{i} tv{i} 0 {vt}\nRT{i} tv{i} t{i} 109k\n"
                    f"XCT{i} t{i} 0 sky130_fd_pr__cap_mim_m3_1 w=31 l=31 mf=1")
        comps.append(f"X{i} vdiv t{i} clk q{i} pb vin vdd 0 cmp_adc")
    meas = "\n".join(f"meas tran q{i}_{k} find v(q{i}) at={k * TDEC + 0.9 * TDEC}" for i in range(15) for k in range(n_loc))
    seedline = f"setseed {seed}\nreset\n" if mc else ""
    n = header(corner, temp, mc=mc, title=tag) + include("comparator.spice", "adc_ref.spice") + f""".include {HD}
.include {HVL}
VDD vdd 0 1.8
VIN vin 0 {vin}
VCK clk 0 pulse(0 1.8 {TDEC / 2} 50p 50p {TH - 50e-12} {TDEC})
IB pb 0 {IBIAS}
XPB pb vin adc_pbias
VO vout 0 pwl(0 {vout_of(ks)} {T} {vout_of(ke)})
XDIV vout vdiv 0 adc_div
{chr(10).join(taps)}
{chr(10).join(comps)}
.control
{seedline}tran {TMAX} {T} 0 {TMAX}
{meas}
quit
.endc
.end
"""
    v = run(n, tag, timeout=7200)
    return {ks + k: [v[f"q{i}_{k}"] for i in range(15)] for k in range(n_loc)}


def cases_segments(cases):
    return [c + (seg,) for c in cases for seg in range(NSEG)]


def assemble(case, parts):
    """parts[seg] = seg_run result. Keep each segment's own decisions [k0, k1); count overlap mismatches."""
    q = {}
    mism = 0
    for seg, part in enumerate(parts):
        k0, k1, _, _ = bounds(seg)
        for k in range(k0, k1):
            q[k] = part[k]
        if seg + 1 < NSEG:                      # this segment's tail [k1, k1+W) vs the next one's own samples
            for k in range(k1, min(N, k1 + W)):
                mism += sum((a > 0.9) != (b > 0.9) for a, b in zip(part[k], parts[seg + 1][k]))
    v = {f"q{i}_{k}": q[k][i] for k in range(N) for i in range(15)}
    return v, mism


def sim(corner, temp, vin, mc=False, seed=0, parts=None):
    if parts is None:
        parts = [seg_run((corner, temp, vin, mc, seed, sg)) for sg in range(NSEG)]
    v, mism = assemble((corner, temp, vin, mc, seed), parts)
    T = N * TDEC
    vout_at = VREF - SPAN + 2 * SPAN * (np.arange(N) * TDEC + TDEC / 2) / T   # VOUT at each decision edge
    flips, errs = [], []
    for i in range(15):
        q = np.array([v[f"q{i}_{k}"] for k in range(N)]) > 0.9
        q = q[2:]
        f = np.nonzero(q[:-1] != q[1:])[0] + 2
        ideal = VREF - (i - 7.5) * LSB
        if len(f) == 1:
            x = (vout_at[f[0]] + vout_at[f[0] + 1]) / 2
            flips.append(x)
            errs.append((x - ideal) / LSB)
        else:
            flips.append(None)
            errs.append(None)
    ok = [e for e in errs if e is not None]
    th = [x for x in flips if x is not None]
    # thresholds sorted by VOUT; spacing in LSB (ideal 1)
    spacing = np.diff(sorted(th)) / LSB if len(th) > 1 else np.array([])
    return {"corner": corner, "temp": temp, "vin": vin, "seed": seed, "functional": len(ok) == 15,
            "th_err_lsb": errs, "dnl": (spacing - 1).tolist(),
            "zero_bin_mv": float((flips[7] - flips[8]) * 1e3) if flips[7] and flips[8] else None,
            "missing_codes": int(np.sum(spacing <= 0)) if len(spacing) else None,
            "flips_v": flips, "overlap_mismatch": int(mism)}


PVT = [(c, 27, 3.3) for c in ("tt", "ff", "ss", "sf", "fs")] + [("ss", -40, 3.0), ("ff", 125, 3.6)]


def run_cases(cases):
    """cases: (corner, temp, vin, mc, seed); all segments of all cases go through one worker pool."""
    jobs = cases_segments(cases)
    res = pmap(seg_run, jobs)
    out = []
    for j, c in enumerate(cases):
        out.append(sim(*c, parts=res[j * NSEG:(j + 1) * NSEG]))
    return out


def mc_computed(tt_row, ntrial=10000, rng_seed=1):
    """Monte Carlo DNL from measured pieces: tt nominal flips + random comparator offsets + ladder errors."""
    base = pathlib.Path(__file__).resolve().parents[1] / "results" / "phase3"
    cmp_ = json.loads((base / "comparator.json").read_text())
    off = np.array([r["offset"] for r in cmp_["mc"] if r["cm"] == 0.9 and r["offset"] is not None])
    ref = json.loads((base / "adcref.json").read_text())
    lad = np.array([r["th_err_lsb_180"] for r in ref["rows"] if "th_err_lsb_180" in r and r.get("corner") == "tt"])
    nom = np.array(tt_row["flips_v"])
    rng = np.random.default_rng(rng_seed)
    dnl, miss, terr = [], 0, []
    for _ in range(ntrial):
        o = rng.choice(off, 15, replace=False) - off.mean()     # systematic part is already in the tt flips
        th = nom + 2 * o + lad[rng.integers(len(lad))] * LSB    # inp = VOUT/2 side: x2 to VOUT
        terr.extend((th - (VREF - (np.arange(15) - 7.5) * LSB)) / LSB)
        sp = np.diff(np.sort(th)) / LSB
        dnl.extend(sp - 1)
        miss += int(np.any(sp <= 0))
    dnl, terr = np.array(dnl), np.array(terr)
    return {"method": "computed: tt full-front-end flips + cmp_adc MC offsets (CM 0.9 V, n=%d, x2) + adcref MC "
                      "ladder errors (code 180, n=%d), %d trials, numpy seed %d" % (len(off), len(lad), ntrial, rng_seed),
            "n_offsets": int(len(off)), "offset_sigma_mv": float(off.std() * 1e3), "n_ladder_seeds": int(len(lad)),
            "ntrial": ntrial, "dnl_sigma": float(dnl.std()), "dnl_min": float(dnl.min()), "dnl_max": float(dnl.max()),
            "th_err_sigma_lsb": float(terr.std()), "missing_code_fraction": miss / ntrial}


def mc_one(seed):
    return sim("tt", 27, 3.3, mc=True, seed=seed)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    path = pathlib.Path(__file__).resolve().parents[1] / "results" / "phase3" / "adc.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    if what in ("pvt", "all"):
        rows = run_cases([c + (False, 0) for c in PVT])
        data["pvt"] = rows
        for r in rows:
            print(r["corner"], r["temp"], r["vin"], "functional", r["functional"], "zero bin %s mV" % r["zero_bin_mv"],
                  "DNL", None if not r["dnl"] else (round(min(r["dnl"]), 3), round(max(r["dnl"]), 3)),
                  "overlap mismatches", r["overlap_mismatch"])
    if what in ("mcc", "all"):
        tt = next(r for r in data["pvt"] if (r["corner"], r["temp"], r["vin"]) == ("tt", 27, 3.3))
        data["mc_computed"] = mc_computed(tt)
        print("MC (computed):", data["mc_computed"])
    if what == "mc":
        rows = run_cases([("tt", 27, 3.3, True, sd) for sd in range(1, 21)])
        data["mc"] = rows
        dn = np.array([d for r in rows for d in r["dnl"]])
        zb = np.array([r["zero_bin_mv"] for r in rows if r["zero_bin_mv"] is not None])
        data["mc_stats"] = {"dnl_sigma": float(dn.std()), "dnl_min": float(dn.min()), "dnl_max": float(dn.max()),
                            "zero_bin_mean_mv": float(zb.mean()), "zero_bin_min_mv": float(zb.min()),
                            "missing_code_samples": int(sum(1 for r in rows if r["missing_codes"])),
                            "nonfunctional": int(sum(1 for r in rows if not r["functional"]))}
        print("MC:", data["mc_stats"])
    data["source"] = "scripts/char_adc.py (ngspice)"
    save("adc", data)
