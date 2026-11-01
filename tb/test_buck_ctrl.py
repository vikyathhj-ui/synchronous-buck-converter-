"""cocotb tests for rtl/buck_ctrl_top.v.

Closed-loop tests use tb/bench.py (RTL + per-clock Python plant + bit-exact golden scoreboard).
Each test writes its metrics to results/phase2/<test>.json; scripts/collect_phase2.py merges them
into results/summary.json["phase2"]. Set QUICK=1 to skip the long runs (used by CI).
"""
import json
import os
import pathlib
import random
from dataclasses import replace

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge

from bench import ADDR, TCLK_NS, Bench, export_coverage
from model.buck import Buck
from model.ctrl_ref import CCM, DCM, FAULT, IDLE, SS, Regs, therm_decode

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "phase2"
OUT.mkdir(parents=True, exist_ok=True)
QUICK = os.environ.get("QUICK", "0") == "1"
VSET = 1.8
B = Buck()


def save(name, metrics, bench=None):
    if bench is not None:
        metrics["scoreboard_periods"] = bench.k
        metrics["scoreboard_mismatches"] = len(bench.mismatches)
    metrics["source"] = f"tb/test_buck_ctrl.py::{name} (cocotb, {cocotb.SIM_NAME})"
    (OUT / f"{name}.json").write_text(json.dumps(metrics, indent=1, default=float) + "\n")
    export_coverage(OUT / "coverage.yml")


def assert_clean(bench):
    assert not bench.mismatches, f"{len(bench.mismatches)} scoreboard mismatches, first: {bench.mismatches[0]}"


def recovery(t, v, t_step, t_end, vset=VSET):
    m = (t >= t_step) & (t < t_end)
    out = np.nonzero(np.abs(v[m] - vset) > 0.01 * vset)[0]
    return float(t[m][out[-1]] - t_step) if len(out) else 0.0


def dense(bench):
    d = np.array(bench.dense)
    return d[:, 0], d[:, 1], d[:, 2]


async def enable(bench, value=1):
    bench.write("ctrl", value)


# ---------------------------------------------------------------------------- register map
async def apb_write(dut, addr, data):
    await FallingEdge(dut.clk)
    dut.paddr.value, dut.pwdata.value, dut.pwrite.value, dut.psel.value = addr, data, 1, 1
    await FallingEdge(dut.clk)
    dut.penable.value = 1
    await FallingEdge(dut.clk)
    dut.psel.value, dut.penable.value, dut.pwrite.value = 0, 0, 0


async def apb_read(dut, addr):
    await FallingEdge(dut.clk)
    dut.paddr.value, dut.pwrite.value, dut.psel.value = addr, 0, 1
    await FallingEdge(dut.clk)
    val = int(dut.prdata.value)
    dut.psel.value = 0
    return val


async def reset_only(dut):
    Clock(dut.clk, TCLK_NS, unit="ns").start()
    for n in ("psel", "penable", "pwrite", "paddr", "pwdata", "adc_therm", "ilim_cmp", "zc_cmp"):
        getattr(dut, n).value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1


@cocotb.test()
async def test_registers(dut):
    """Reset values, read-back, clamping, ID, dead-time and current-limit outputs."""
    await reset_only(dut)
    r = Regs()
    exp = {"ctrl": 0, "vref": r.vref, "kp": r.kp, "ki": r.ki, "kd": r.kd, "dt": (r.dt_lh << 4) | r.dt_hl,
           "ilim": r.ilim, "ss_len": r.ss_len, "dmax": r.dmax, "fault_n": r.fault_n, "id": 0xB0C40001}
    for name, val in exp.items():
        got = await apb_read(dut, ADDR[name])
        assert got == val, f"reset {name}: {got:#x} != {val:#x}"
    cases = [("vref", 50, 100), ("vref", 255, 250), ("vref", 120, 120), ("ss_len", 10, 256),
             ("ss_len", 5000, 5000), ("kp", 0x1FFF, 0xFFF), ("dmax", 0x3FF, 0x1FF), ("ilim", 0x1AB, 0xAB),
             ("dt", 0x75, 0x75), ("ctrl", 0x103, 0x3), ("ctrl", 0x0, 0x0)]
    for name, wr, rd in cases:
        await apb_write(dut, ADDR[name], wr)
        got = await apb_read(dut, ADDR[name])
        assert got == rd, f"{name} write {wr:#x}: read {got:#x}, expected {rd:#x}"
    for code in range(8):
        await apb_write(dut, ADDR["dt"], (code << 4) | code)
        await FallingEdge(dut.clk)
        exp_t = (1 << (code + 1)) - 1
        assert int(dut.dt_hl_therm.value) == exp_t and int(dut.dt_lh_therm.value) == exp_t
    await apb_write(dut, ADDR["ilim"], 77)
    await FallingEdge(dut.clk)
    assert int(dut.ilim_code.value) == 77
    save("test_registers", {"pass": True, "checks": len(exp) + len(cases) + 9})


@cocotb.test()
async def test_therm_decode(dut):
    """Thermometer encoder with random bubbles vs the golden decoder (via STATUS.e)."""
    await reset_only(dut)
    rng = random.Random(1)
    n = 120 if QUICK else 400
    # align to cycle 0
    while not int(dut.adc_sample.value):
        await FallingEdge(dut.clk)
    for i in range(n):
        ones = rng.randint(0, 15)
        w = (1 << ones) - 1
        for _ in range(rng.choice([0, 0, 1, 2])):
            w ^= 1 << rng.randint(0, 14)
        dut.adc_therm.value = w
        await ClockCycles(dut.clk, 2)
        st = await apb_read(dut, ADDR["status"])
        e = ((st >> 4) & 0xF) - (16 if (st >> 7) & 1 else 0)
        assert e == therm_decode(w), f"therm {w:015b}: rtl {e}, ref {therm_decode(w)}"
        while not int(dut.adc_sample.value):
            await FallingEdge(dut.clk)
    save("test_therm_decode", {"pass": True, "patterns": n})


# ---------------------------------------------------------------------------- closed loop
@cocotb.test()
async def test_startup(dut):
    """Soft start into full resistive load: no overshoot > 2 %, no current limit, ends in CCM."""
    b = replace(B, g_load=0.15 / VSET)
    bench = Bench(dut, b, dense_from=0.0, dense_to=1.6e-3)
    await bench.start()
    await enable(bench)
    await bench.run(1600)
    a = bench.arrays()
    t, v, il = dense(bench)
    m = {
        "overshoot_pct": float((v.max() - VSET) / VSET * 100),
        "il_peak": float(il.max()),
        "ilim_trips": int(a["trip"].sum()),
        "t_ccm": float(a["t"][np.argmax(a["mode"] == CCM)]),
        "final_mode": int(a["mode"][-1]),
        "v_final": float(a["v"][-1]),
    }
    save("test_startup", m, bench)
    assert_clean(bench)
    assert m["overshoot_pct"] <= 2.0 and m["ilim_trips"] == 0 and m["final_mode"] == CCM
    np.save(OUT / "startup_dense.npy", np.array(bench.dense)[::4])


@cocotb.test()
async def test_load_step(dut):
    """15 -> 150 -> 15 mA: undershoot <= 90 mV, recovery to +/-1 % within 50 us."""
    b = replace(B, g_load=0.015 / VSET)
    io_fn = lambda t: 0.135 if 2.0e-3 <= t < 2.3e-3 else 0.0
    bench = Bench(dut, b, io_fn=io_fn, dense_from=1.9e-3, dense_to=2.6e-3)
    await bench.start()
    await enable(bench)
    await bench.run(2600)
    t, v, il = dense(bench)
    pre = v[(t >= 1.95e-3) & (t < 2.0e-3)].mean()
    up = (t >= 2.0e-3) & (t < 2.3e-3)
    dn = t >= 2.3e-3
    m = {
        "undershoot": float(pre - v[up].min()),
        "recovery_1pct": recovery(t, v, 2.0e-3, 2.3e-3),
        "down_overshoot": float(v[dn].max() - pre),
        "down_recovery_1pct": recovery(t, v, 2.3e-3, 2.6e-3),
        "ilim_trips": int(bench.arrays()["trip"].sum()),
    }
    save("test_load_step", m, bench)
    np.save(OUT / "load_step_dense.npy", np.array(bench.dense)[::2])
    assert_clean(bench)
    assert m["undershoot"] <= 0.090 and m["recovery_1pct"] <= 50e-6


@cocotb.test()
async def test_line_step(dut):
    """VIN 3.0 -> 3.6 -> 3.0 V with 10 us edges at 150 mA: report the deviation."""
    def vin_fn(t):
        if t < 2.0e-3:
            return 3.0
        if t < 2.01e-3:
            return 3.0 + 0.6 * (t - 2.0e-3) / 10e-6
        if t < 2.5e-3:
            return 3.6
        if t < 2.51e-3:
            return 3.6 - 0.6 * (t - 2.5e-3) / 10e-6
        return 3.0
    b = replace(B, g_load=0.15 / VSET)
    bench = Bench(dut, b, vin_fn=vin_fn, dense_from=1.9e-3, dense_to=3.0e-3)
    await bench.start()
    await enable(bench)
    await bench.run(3000)
    t, v, _ = dense(bench)
    pre = v[(t >= 1.9e-3) & (t < 2.0e-3)].mean()
    m = {"dev_up": float(v[(t >= 2.0e-3) & (t < 2.5e-3)].max() - pre),
         "dev_dn": float(v[t >= 2.5e-3].min() - pre),
         "recovery_up_1pct": recovery(t, v, 2.0e-3, 2.5e-3),
         "recovery_dn_1pct": recovery(t, v, 2.5e-3, 3.0e-3)}
    save("test_line_step", m, bench)
    assert_clean(bench)


@cocotb.test()
async def test_vref_change(dut):
    """VREF 1.8 -> 1.2 -> 2.5 V: VREF ramps at the soft-start rate and VOUT follows."""
    b = replace(B, g_load=0.075 / VSET)
    bench = Bench(dut, b)
    await bench.start()
    await enable(bench)
    await bench.run(1500)
    bench.write("vref", 120)
    await bench.run(1500)
    bench.write("vref", 250)
    await bench.run(1500)
    a = bench.arrays()
    v12 = a["v"][2700:3000]
    v25 = a["v"][4200:4500]
    m = {"v_at_1v2_mean": float(v12.mean()), "v_at_1v2_pp": float(np.ptp(v12)),
         "v_at_2v5_mean": float(v25.mean()), "v_at_2v5_pp": float(np.ptp(v25)),
         "vref_code_end": int(a["vref"][-1]), "duty_at_2v5": int(a["duty"][-1])}
    save("test_vref_change", m, bench)
    assert_clean(bench)
    assert abs(m["v_at_1v2_mean"] - 1.2) < 0.012 and abs(m["v_at_2v5_mean"] - 2.5) < 0.025


@cocotb.test()
async def test_current_limit_fault(dut):
    """Overload: cycle-by-cycle valley limit, FAULT, then fault_clr restarts with soft start."""
    b = replace(B, g_load=0.015 / VSET)
    bench = Bench(dut, b)
    await bench.start()
    await enable(bench)
    await bench.run(1500)
    bench.io_extra = 0.35
    k0 = bench.k
    while bench.rec["mode"][-1] != FAULT and bench.k < k0 + 1000:
        await bench.run(1)
    kf = bench.k
    a = bench.arrays()
    w = slice(k0, kf - 1)
    m = {"periods_to_fault": kf - 1 - k0, "trips_before_fault": int(a["trip"][w].sum()),
         "valley_max_before_fault": float(a["ilv"][w].max()), "peak_max_before_fault": float(a["ilp"][w].max())}
    bench.io_extra = 0.0
    await bench.run(50)
    bench.write("ctrl", 0x101)                 # fault_clr, keep enabled
    await bench.run(1600)
    a = bench.arrays()
    m["restarted_to_ccm"] = bool(a["mode"][-1] == CCM)
    m["modes_after_clear"] = sorted({int(x) for x in a["mode"][kf + 50:]})
    save("test_current_limit_fault", m, bench)
    assert_clean(bench)
    assert kf - 1 - k0 < 1000 and m["restarted_to_ccm"]


@cocotb.test(skip=QUICK)
async def test_limit_cycle(dut):
    """10 ms of steady state at 75 mA after start-up: one duty code (no limit cycle)."""
    b = replace(B, g_load=0.075 / VSET)
    bench = Bench(dut, b)
    await bench.start()
    await enable(bench)
    await bench.run(12000)
    a = bench.arrays()
    codes, cnt = np.unique(a["duty"][2000:], return_counts=True)
    m = {"duty_codes": codes.tolist(), "counts": cnt.tolist(), "adc_codes": sorted(set(a["e"][2000:].tolist())),
         "v_sample_pp": float(np.ptp(a["v"][2000:]))}
    save("test_limit_cycle", m, bench)
    assert_clean(bench)
    assert len(codes) == 1


@cocotb.test()
async def test_dcm(dut):
    """Light load with DCM enabled: CCM -> DCM, LS cut at zero-cross, back to CCM at 100 mA."""
    b = replace(B, g_load=0.005 / VSET)
    io_fn = lambda t: 0.095 if t >= 2.5e-3 else 0.0
    bench = Bench(dut, b, io_fn=io_fn, dense_from=2.3e-3, dense_to=2.31e-3)
    await bench.start()
    await enable(bench, 0x3)
    await bench.run(3000)
    a = bench.arrays()
    dcm = a["mode"] == DCM
    k_dcm = int(np.argmax(dcm)) if dcm.any() else -1
    win = slice(2000, 2500)
    m = {"entered_dcm": bool(dcm.any()), "t_dcm": float(a["t"][k_dcm]) if dcm.any() else None,
         "dcm_il_min": float(a["ilmin"][win].min()), "dcm_cut_cycles": sorted(set(a["cut_cycle"][win].tolist())),
         "dcm_v_mean": float(a["v"][win].mean()), "dcm_v_sample_pp": float(np.ptp(a["v"][win])),
         "dcm_v_min": float(a["vmin"][win].min()), "dcm_v_max": float(a["vmax"][win].max()),
         "mode_changes_in_window": int((np.diff(a["mode"][win]) != 0).sum()),
         "frac_periods_in_dcm": float((a["mode"][win] == DCM).mean()),
         "dcm_duty_codes": sorted(set(a["duty"][win].tolist())),
         "back_to_ccm": bool(a["mode"][-1] == CCM)}
    save("test_dcm", m, bench)
    np.save(OUT / "dcm_dense.npy", np.array(bench.dense))
    assert_clean(bench)
    assert m["entered_dcm"] and m["back_to_ccm"]


@cocotb.test()
async def test_random_registers(dut):
    """Random register writes during closed-loop operation; the scoreboard must stay bit exact."""
    rng = random.Random(7)
    b = replace(B, g_load=0.05 / VSET)
    bench = Bench(dut, b)
    await bench.start()
    await enable(bench)
    await bench.run(1300)
    n = 0
    for _ in range(40 if QUICK else 120):
        name = rng.choice(["vref", "kp", "ki", "kd", "dmax", "ss_len", "ilim", "dt", "fault_n"])
        val = {"vref": rng.randint(90, 255), "kp": rng.randint(40, 130), "ki": rng.randint(1, 6),
               "kd": rng.randint(900, 1300), "dmax": rng.randint(300, 511), "ss_len": rng.randint(200, 1500),
               "ilim": rng.randint(100, 255), "dt": rng.randint(0, 0x77), "fault_n": rng.randint(0, 255)}[name]
        bench.write(name, val)
        n += 1
        await bench.run(rng.randint(5, 40))
    save("test_random_registers", {"writes": n}, bench)
    assert_clean(bench)


@cocotb.test()
async def test_mode_transitions(dut):
    """Every remaining FSM edge: SS/CCM/DCM/FAULT -> IDLE, SS -> FAULT, DCM -> FAULT."""
    b = replace(B, g_load=0.005 / VSET)
    bench = Bench(dut, b)
    await bench.start()
    seen = set()

    async def run_until(pred, limit):
        for _ in range(limit):
            await bench.run(1)
            seen.add(bench.rec["mode"][-1])
            if pred():
                return True
        return False

    def mode():
        return bench.rec["mode"][-1]

    # SS -> IDLE
    await enable(bench)
    assert await run_until(lambda: mode() == SS, 10)
    await bench.run(200)
    bench.write("ctrl", 0)
    assert await run_until(lambda: mode() == IDLE, 10)
    await bench.run(300)
    # SS -> FAULT -> IDLE
    await enable(bench)
    assert await run_until(lambda: mode() == SS, 10)
    await bench.run(100)
    bench.io_extra = 0.40
    assert await run_until(lambda: mode() == FAULT, 400)
    bench.io_extra = 0.0
    await bench.run(20)
    bench.write("ctrl", 0)
    assert await run_until(lambda: mode() == IDLE, 10)
    await bench.run(300)
    # CCM -> IDLE
    await enable(bench)
    assert await run_until(lambda: mode() == CCM, 1300)
    await bench.run(50)
    bench.write("ctrl", 0)
    assert await run_until(lambda: mode() == IDLE, 10)
    await bench.run(300)
    # DCM -> FAULT, then fault_clr and DCM -> IDLE
    await enable(bench, 0x3)
    assert await run_until(lambda: mode() == DCM, 1500)
    await bench.run(50)
    # overload in DCM: must leave DCM (ADC saturates) and then fault from CCM, not collapse
    k_ol = bench.k
    bench.io_extra = 0.40
    assert await run_until(lambda: mode() == FAULT, 400)
    dcm_exit_periods = int(np.argmax(np.array(bench.rec["mode"][k_ol:]) != DCM))
    bench.io_extra = 0.0
    await bench.run(20)
    bench.write("ctrl", 0x103)
    assert await run_until(lambda: mode() == DCM, 1600)
    await bench.run(50)
    bench.write("ctrl", 0)
    assert await run_until(lambda: mode() == IDLE, 10)
    await bench.run(5)
    save("test_mode_transitions", {"modes_seen": sorted(int(x) for x in seen),
                                   "dcm_overload_exit_periods": dcm_exit_periods}, bench)
    assert_clean(bench)
