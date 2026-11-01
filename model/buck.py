"""Buck power-stage models built from one state-space description.

States x = [iL, vC]; inputs u = [v_sw, i_o].
  v_sw : ideal switch-node source (VIN while HS is on, 0 while LS is on).
         Both switches have the same on-resistance `ron`, so it is lumped with
         the inductor DCR into rs = dcr + ron and the A matrix is the same in
         both switch states (assumption A1, see docs/CONTROL.md).
  i_o  : current-source load. An optional resistive load g_load is in parallel.

Three models are derived from it:
  * averaged continuous-time model        -> gvd_s()
  * exact sampled small-signal model      -> sampled(), pz()
    (trailing-edge PWM, output sampled at the start of each period)
  * cycle-accurate switched plant         -> SwitchedPlant
"""
from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm


def seg(A, B, t):
    """Return (e^{At}, integral_0^t e^{As} ds B) using the augmented-matrix exponential."""
    n, m = A.shape[0], B.shape[1]
    M = np.zeros((n + m, n + m))
    M[:n, :n] = A
    M[:n, n:] = B
    E = expm(M * t)
    return E[:n, :n], E[:n, n:]


@dataclass(frozen=True)
class Buck:
    vin: float = 3.3
    vout: float = 1.8
    fsw: float = 1e6
    L: float = 15e-6
    dcr: float = 0.1
    C: float = 10e-6
    esr: float = 10e-3
    ron: float = 0.5      # ASSUMPTION A1: per-switch Ron (HS = LS) until Phase 3 sizing
    g_load: float = 0.0   # resistive load conductance [S]; 0 = current-source load only

    @property
    def Ts(self):
        return 1.0 / self.fsw

    @property
    def rs(self):
        return self.dcr + self.ron

    def matrices(self):
        k = 1.0 / (1.0 + self.esr * self.g_load)
        L, C, esr, G = self.L, self.C, self.esr, self.g_load
        A = np.array([[-(self.rs + k * esr) / L, -k / L],
                      [k / C, -G * k / C]])
        B = np.array([[1.0 / L, k * esr / L],
                      [0.0, -k / C]])
        Cy = np.array([k * esr, k])
        Dy = np.array([0.0, -k * esr])
        return A, B, Cy, Dy

    # ---- closed-form quantities (labelled "analysis" wherever reported) ----
    def duty_dc(self, io):
        """Averaged CCM duty that gives self.vout at load current io."""
        il = io + self.g_load * self.vout
        return (self.vout + self.rs * il) / self.vin

    def f0(self):
        return 1.0 / (2 * np.pi * np.sqrt(self.L * self.C))

    def f_esr(self):
        return 1.0 / (2 * np.pi * self.esr * self.C)

    def ripple_il_pp(self, io=0.15):
        return (self.vin - self.vout) * self.duty_dc(io) * self.Ts / self.L

    # ---- averaged continuous-time control-to-output ----
    def gvd_s(self, f):
        A, B, Cy, _ = self.matrices()
        s = 2j * np.pi * np.atleast_1d(f)
        return np.array([Cy @ np.linalg.solve(si * np.eye(2) - A, B[:, 0]) for si in s]) * self.vin

    # ---- exact sampled small-signal model ----
    def sampled(self, io):
        """x[k+1] = Phi x[k] + Gam d[k] + Gio io[k];  y[k] = Cy x[k] + Dio io[k].

        A duty perturbation moves the HS turn-off edge at D*Ts; to first order it
        injects VIN*Ts*d of volt-seconds there, which then propagates for (1-D)*Ts.
        """
        A, B, Cy, Dy = self.matrices()
        Ts, D = self.Ts, self.duty_dc(io)
        Phi = expm(A * Ts)
        Gam = expm(A * (1 - D) * Ts) @ B[:, 0] * self.vin * Ts
        Gio = seg(A, B[:, 1:2], Ts)[1][:, 0]
        return Phi, Gam, Gio, Cy, Dy[1]

    def pz(self, f, io):
        Phi, Gam, _, Cy, _ = self.sampled(io)
        z = np.exp(2j * np.pi * np.atleast_1d(f) * self.Ts)
        return np.array([Cy @ np.linalg.solve(zi * np.eye(2) - Phi, Gam) for zi in z])


@dataclass(frozen=True)
class Dpwm:
    """Hybrid DPWM: coarse counter at fclk plus a fine delay line.

    tap_scale models delay-line PVT error: actual tap = tap_scale * (Tclk / 2^fine_bits).
    """
    fclk: float = 64e6
    coarse_bits: int = 6
    fine_bits: int = 3
    tap_scale: float = 1.0

    @property
    def bits(self):
        return self.coarse_bits + self.fine_bits

    @property
    def nmax(self):
        return (1 << self.bits) - 1

    def ton(self, code):
        tclk = 1.0 / self.fclk
        c = code >> self.fine_bits
        f = code & ((1 << self.fine_bits) - 1)
        return c * tclk + f * tclk / (1 << self.fine_bits) * self.tap_scale

    def lsb_out(self, vin):
        """Output-referred DPWM LSB [V] (ideal taps)."""
        return vin / (1 << self.bits)


class SwitchedPlant:
    """Cycle-accurate plant: exact piecewise-linear integration of each switch interval."""

    def __init__(self, buck, x0=None):
        self.b = buck
        self.A, self.B, self.Cy, self.Dy = buck.matrices()
        self.x = np.zeros(2) if x0 is None else np.array(x0, float)
        self._cache = {}

    def _seg(self, t):
        key = round(t * 1e15)
        if key not in self._cache:
            self._cache[key] = seg(self.A, self.B, t)
        return self._cache[key]

    def vout(self, io):
        return float(self.Cy @ self.x + self.Dy[1] * io)

    def _advance(self, t, u, nsub, t0, dense):
        if t <= 0:
            return
        if nsub:
            Ed, Gd = self._seg(t / nsub)
            for i in range(nsub):
                self.x = Ed @ self.x + Gd @ u
                dense.append((t0 + (i + 1) * t / nsub, float(self.Cy @ self.x + self.Dy[1] * u[1]), self.x[0]))
        else:
            E, G = self._seg(t)
            self.x = E @ self.x + G @ u

    def period(self, ton, io, vin, t0=0.0, nsub=0):
        """Advance one period (HS on for ton, then LS). Returns (i_peak, dense_list)."""
        Ts = self.b.Ts
        ton = min(max(ton, 0.0), Ts)
        dense = []
        self._advance(ton, np.array([vin, io]), nsub, t0, dense)
        ipk = self.x[0]
        self._advance(Ts - ton, np.array([0.0, io]), nsub, t0 + ton, dense)
        return ipk, dense
