"""Closed-loop simulation of the golden controller (model/ctrl_ref.py) with the power-stage models.

simulate()          per-period, fast: CCM only (zero-cross is not modelled, so DCM is never entered).
simulate_clocked()  per-clock: exact cycle timing, zero-cross / DCM, the same harness as the cocotb
                    testbench (tb/) but with CtrlRef in place of the RTL.
Both use the timing contract documented in model/ctrl_ref.py.
"""
from dataclasses import dataclass, field

import numpy as np

from .buck import ClockPlant, SwitchedPlant
from .ctrl_ref import FRAC, CtrlRef, Regs, therm_decode, therm_encode

ILIM_LSB = 0.002     # A per ILIM code
VREF_LSB = 0.010     # V per VREF code
ADC_LSB = 0.010


@dataclass
class Run:
    t: np.ndarray
    v: np.ndarray          # VOUT sampled at the start of each period
    vref: np.ndarray       # DAC voltage seen by that sample
    e: np.ndarray          # ADC code
    d: np.ndarray          # DPWM code applied in the period (0 if the HS pulse was suppressed)
    il_valley: np.ndarray  # iL at the valley-comparator sample point (one clock before period end)
    il_peak: np.ndarray
    trip: np.ndarray
    mode: np.ndarray
    vin: np.ndarray
    io: np.ndarray
    dense: list = field(default_factory=list)   # (t, vout, iL) inside periods, if requested


def _regs(regs):
    r = Regs() if regs is None else regs
    r.enable = 1
    return r


def simulate(buck, dpwm, regs=None, n=1000, frac=FRAC, io_fn=None, vin_fn=None,
             dense_from=None, dense_to=None, nsub=8, adc_offsets=None):
    io_fn = io_fn or (lambda t: 0.0)
    vin_fn = vin_fn or (lambda t: buck.vin)
    regs = _regs(regs)
    ctrl = CtrlRef(regs, frac=frac, dpwm_bits=dpwm.bits)
    plant = SwitchedPlant(buck)
    Ts, tclk = buck.Ts, 1.0 / dpwm.fclk
    vref_dac, ilv = 0, 0.0
    rec = {k: np.zeros(n) for k in ("t", "v", "vref", "e", "d", "ilv", "ilp", "trip", "mode", "vin", "io")}
    dense = []
    for k in range(n):
        t = k * Ts
        io, vin = io_fn(t), vin_fn(t)
        trip = ilv > regs.ilim * ILIM_LSB
        v = plant.vout(io)
        e = therm_decode(therm_encode(vref_dac * VREF_LSB - v, ADC_LSB, adc_offsets))
        out = ctrl.period(e, trip, False, dpwm.n_meas() if dpwm.t_elem else None)
        if not out["hs_en"]:
            ton = 0.0
        elif dpwm.t_elem:
            ton = dpwm.ton_cal(out["duty"], out["tap_sel"])
        else:
            ton = dpwm.ton(out["duty"])
        want = dense_from is not None and dense_from <= t < dense_to
        ipk, ilv_new, dl = plant.period(ton, io, vin, t0=t, nsub=nsub if want else 0,
                                        t_pre=tclk, ls=out["ls_en"], tclk=tclk)
        dense.extend(dl)
        for key, val in (("t", t), ("v", v), ("vref", vref_dac * VREF_LSB), ("e", e), ("d", out["duty"]),
                         ("ilv", ilv), ("ilp", ipk), ("trip", trip), ("mode", out["mode"]),
                         ("vin", vin), ("io", io)):
            rec[key][k] = val
        ilv = ilv_new
        vref_dac = out["vref_code"]
    return Run(rec["t"], rec["v"], rec["vref"], rec["e"], rec["d"].astype(int), rec["ilv"], rec["ilp"],
               rec["trip"].astype(bool), rec["mode"].astype(int), rec["vin"], rec["io"], dense)


def simulate_clocked(buck, dpwm, regs=None, n=1000, frac=FRAC, io_fn=None, vin_fn=None, keep_il=False):
    """Per-clock golden closed loop (DCM capable). Returns (Run, extra) where extra holds the
    zero-cross statistics and, with keep_il, the per-clock iL trace."""
    io_fn = io_fn or (lambda t: 0.0)
    vin_fn = vin_fn or (lambda t: buck.vin)
    regs = _regs(regs)
    ctrl = CtrlRef(regs, frac=frac, dpwm_bits=dpwm.bits)
    plant = ClockPlant(buck, dpwm)
    nclk = 1 << dpwm.coarse_bits
    Ts, tclk = buck.Ts, 1.0 / dpwm.fclk
    vref_dac, trip, zc_prev = 0, False, False
    rec = {k: np.zeros(n) for k in ("t", "v", "vref", "e", "d", "ilv", "ilp", "trip", "mode", "vin", "io")}
    il_min, il_trace = [], []
    for k in range(n):
        t = k * Ts
        io, vin = io_fn(t), vin_fn(t)
        v = plant.vout(io)
        e = therm_decode(therm_encode(vref_dac * VREF_LSB - v, ADC_LSB))
        out = ctrl.period(e, trip, zc_prev, dpwm.n_meas() if dpwm.t_elem else None)
        hs = out["hs_en"]
        coarse = out["duty"] >> dpwm.fine_bits if hs else 0
        fine = out["duty"] & ((1 << dpwm.fine_bits) - 1) if hs else 0
        fdel = dpwm.fine_delay(fine, out["tap_sel"])
        ls_cut, zc_seen, ilp, ilv, imin = False, False, 0.0, 0.0, 1e9
        for c in range(nclk):
            ls_en = out["ls_en"] and not ls_cut
            zc = (not plant.hs) and ls_en and plant.il < 0
            cut_next = False
            if c > coarse and zc:
                zc_seen = True
                cut_next = out["dcm"]
            if c == nclk - 1:
                ilv = plant.il
            plant.clock(hs and c == 0, hs and c == coarse, fdel, ls_en, vin, io)
            ilp = max(ilp, plant.il)
            imin = min(imin, plant.il)
            if keep_il:
                il_trace.append((t + (c + 1) * tclk, plant.il, plant.vout(io)))
            if cut_next:
                ls_cut = True
        il_min.append(imin)
        for key, val in (("t", t), ("v", v), ("vref", vref_dac * VREF_LSB), ("e", e), ("d", out["duty"]),
                         ("ilv", ilv), ("ilp", ilp), ("trip", trip), ("mode", out["mode"]),
                         ("vin", vin), ("io", io)):
            rec[key][k] = val
        trip = ilv > regs.ilim * ILIM_LSB
        zc_prev = zc_seen
        vref_dac = out["vref_code"]
    run = Run(rec["t"], rec["v"], rec["vref"], rec["e"], rec["d"].astype(int), rec["ilv"], rec["ilp"],
              rec["trip"].astype(bool), rec["mode"].astype(int), rec["vin"], rec["io"], [])
    return run, {"il_min": np.array(il_min), "il_trace": il_trace}


def open_loop_response(buck, io, f, amp=0.002, settle_periods=1500, cycles=4, min_periods=300):
    """Inject d = D + amp*sin(2 pi f t) (continuous duty, no DPWM quantisation) into the
    switched plant and fit the sampled VOUT response. Returns the complex gain dVout/dd."""
    from .buck import seg
    plant = SwitchedPlant(buck)
    D = buck.duty_dc(io)
    Ts = buck.Ts
    # start at the averaged steady state to shorten settling
    il0 = io + buck.g_load * buck.vout
    plant.x = np.array([il0, buck.vout])
    nmeas = max(min_periods, int(np.ceil(cycles / (f * Ts))))
    A, B = plant.A, plant.B
    ys, ts, ds = [], [], []
    for k in range(settle_periods + nmeas):
        t = k * Ts
        d = D + amp * np.sin(2 * np.pi * f * t)
        if k >= settle_periods:
            ys.append(plant.vout(io))
            ts.append(t)
        ton = d * Ts
        E1, G1 = seg(A, B, ton)
        plant.x = E1 @ plant.x + G1 @ np.array([buck.vin, io])
        E2, G2 = seg(A, B, Ts - ton)
        plant.x = E2 @ plant.x + G2 @ np.array([0.0, io])
    ts, ys = np.array(ts), np.array(ys)
    w = 2 * np.pi * f
    X = np.column_stack([np.sin(w * ts), np.cos(w * ts), np.ones_like(ts)])
    a, b, _ = np.linalg.lstsq(X, ys, rcond=None)[0]
    # y = a sin + b cos = Re{(b - j a) e^{jwt}};  input = amp sin = Re{-j amp e^{jwt}}
    return (b - 1j * a) / (-1j * amp)
