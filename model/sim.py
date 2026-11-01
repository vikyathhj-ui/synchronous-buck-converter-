"""Cycle-accurate closed-loop simulation: fixed-point controller + switched plant.

Per switching period k (timing that the RTL must reproduce):
  1. at t = k*Ts sample VOUT (window ADC) and the inductor valley current (LS still on);
  2. soft start: phase accumulator adds vref_target each period and raises vref_code by one
     each time it passes ss_len, so the ramp takes ss_len periods for any target code;
  3. valley current limit: if iL(valley) > ilim the HS pulse of THIS period is suppressed
     (cycle-by-cycle) and the PID integrator is held;
  4. otherwise period k uses the duty computed in period k-1 (one period compute delay);
  5. PID computes the duty for period k+1 from e[k].
VREF = vref_code * vref_lsb (8-bit code, 10 mV LSB, so 1.8 V = code 180; see DECISIONS D6).
"""
from dataclasses import dataclass, field

import numpy as np

from .buck import SwitchedPlant
from .controller import FixedPid


@dataclass
class Run:
    t: np.ndarray
    v: np.ndarray          # VOUT sampled at the start of each period
    vref: np.ndarray
    e: np.ndarray          # ADC code
    d: np.ndarray          # DPWM code applied in the period
    il_valley: np.ndarray
    il_peak: np.ndarray
    trip: np.ndarray
    vin: np.ndarray
    io: np.ndarray
    dense: list = field(default_factory=list)   # (t, vout, iL) inside periods, if requested


def simulate(buck, dpwm, adc, gains_int, frac, n, vref_target=180, vref_lsb=0.010,
             ss_len=1000, ilim=0.25, io_fn=None, vin_fn=None, dense_from=None,
             dense_to=None, nsub=8, dmin=0, dmax=None):
    io_fn = io_fn or (lambda t: 0.0)
    vin_fn = vin_fn or (lambda t: buck.vin)
    dmax = dpwm.nmax if dmax is None else dmax
    plant = SwitchedPlant(buck)
    pid = FixedPid(*gains_int, frac, dmin, dmax)
    Ts = buck.Ts
    vref_code, ss_acc = 0, 0
    d_next = 0
    rec = {k: np.zeros(n) for k in ("t", "v", "vref", "e", "d", "ilv", "ilp", "trip", "vin", "io")}
    dense = []
    for k in range(n):
        t = k * Ts
        io, vin = io_fn(t), vin_fn(t)
        v = plant.vout(io)
        ilv = plant.x[0]
        if vref_code < vref_target:
            ss_acc += vref_target
            while ss_acc >= ss_len and vref_code < vref_target:
                ss_acc -= ss_len
                vref_code += 1
        elif vref_code > vref_target:
            vref_code = vref_target
        e = adc.code(vref_code * vref_lsb - v)
        trip = ilv > ilim
        d_now = 0 if trip else d_next
        d_next = pid.step(e, hold=trip)
        want = dense_from is not None and dense_from <= t < dense_to
        ipk, dl = plant.period(dpwm.ton(d_now), io, vin, t0=t, nsub=nsub if want else 0)
        dense.extend(dl)
        for key, val in (("t", t), ("v", v), ("vref", vref_code * vref_lsb), ("e", e), ("d", d_now),
                         ("ilv", ilv), ("ilp", ipk), ("trip", trip), ("vin", vin), ("io", io)):
            rec[key][k] = val
    return Run(rec["t"], rec["v"], rec["vref"], rec["e"], rec["d"].astype(int), rec["ilv"],
               rec["ilp"], rec["trip"].astype(bool), rec["vin"], rec["io"], dense)


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
