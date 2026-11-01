"""Digital controller: window ADC, z-domain PID design, loop analysis, fixed-point golden PID.

Units used by the controller (and by the RTL in Phase 2):
  e  : ADC code, signed 4-bit (-8..+7), e = q((VREF - VOUT) / adc_lsb)
  u  : DPWM code (0..2^bits - 1), duty = u / 2^bits
  kp, ki, kd : DPWM LSB per ADC LSB

PID (parallel form, computed once per switching period):
  I[k] = clamp(I[k-1] + ki*e[k])                  (anti-windup clamp to the duty range)
  u    = kp*e[k] + I[k] + kd*(e[k] - e[k-1])
  C(z) = kp + ki / (1 - z^-1) + kd * (1 - z^-1)
The duty computed from the sample at the start of period k is applied in period k+1,
so the loop has an extra z^-1 for the ADC conversion and computation.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Adc:
    """Mid-tread window ADC; thresholds at (i - 7.5)*lsb, i = 0..14 (15 comparators)."""
    lsb: float = 0.010
    cmin: int = -8
    cmax: int = 7

    def code(self, err):
        return int(min(max(np.floor(err / self.lsb + 0.5), self.cmin), self.cmax))


@dataclass(frozen=True)
class Gains:
    kp: float
    ki: float
    kd: float

    def cz(self, z):
        zi = 1.0 / z
        return self.kp + self.ki / (1 - zi) + self.kd * (1 - zi)

    def quantized(self, frac):
        s = 1 << frac
        return Gains(round(self.kp * s) / s, round(self.ki * s) / s, round(self.kd * s) / s)

    def ints(self, frac):
        s = 1 << frac
        return round(self.kp * s), round(self.ki * s), round(self.kd * s)


def kc(adc, dpwm):
    """Gain from (controller code units) to (duty per volt of error)."""
    return 1.0 / (adc.lsb * (1 << dpwm.bits))


def loop(buck, io, gains, adc, dpwm, f):
    """Loop gain L(e^{jwTs}) = z^-1 * C(z) * kc * P(z)."""
    z = np.exp(2j * np.pi * np.atleast_1d(f) * buck.Ts)
    return gains.cz(z) * kc(adc, dpwm) * buck.pz(f, io) / z


def design(buck, io, adc, dpwm, fc, pm_deg, fi_ratio):
    """Place crossover at fc with phase margin pm_deg; integral zero near fc/fi_ratio.

    With ki = alpha*kp (alpha = 2*pi*(fc/fi_ratio)*Ts), C(z0) is linear in (kp, kd), so the
    two conditions |L(z0)| = 1 and angle L(z0) = -180 + PM give a 2x2 real linear system.
    """
    Ts = buck.Ts
    z0 = np.exp(2j * np.pi * fc * Ts)
    G = kc(adc, dpwm) * buck.pz(fc, io)[0] / z0
    target = np.exp(1j * np.deg2rad(-180 + pm_deg)) / G
    alpha = 2 * np.pi * (fc / fi_ratio) * Ts
    w1 = 1 + alpha / (1 - 1 / z0)
    w2 = 1 - 1 / z0
    M = np.array([[w1.real, w2.real], [w1.imag, w2.imag]])
    kp, kd = np.linalg.solve(M, [target.real, target.imag])
    return Gains(kp, alpha * kp, kd)


def margins(buck, io, gains, adc, dpwm, fmin=10.0, n=20000):
    """Crossover frequencies, phase margins and gain margins from a dense grid up to Nyquist."""
    f = np.logspace(np.log10(fmin), np.log10(0.4999 * buck.fsw), n)
    Lf = loop(buck, io, gains, adc, dpwm, f)
    mag = np.abs(Lf)
    ph = np.unwrap(np.angle(Lf))
    out = {"crossovers": [], "pm": [], "phase_crossovers": [], "gm_db": []}
    lm = np.log(mag)
    for i in np.nonzero(np.sign(lm[:-1]) != np.sign(lm[1:]))[0]:
        t = lm[i] / (lm[i] - lm[i + 1])
        fx = f[i] * (f[i + 1] / f[i]) ** t
        p = ph[i] + t * (ph[i + 1] - ph[i])
        out["crossovers"].append(float(fx))
        out["pm"].append(float(np.rad2deg(p) % 360 - 180))
    # phase crossovers at -180 + 360 n
    pr = (np.rad2deg(ph) + 180) / 360
    k = np.floor(pr)
    for i in np.nonzero(k[:-1] != k[1:])[0]:
        out["phase_crossovers"].append(float(f[i]))
        out["gm_db"].append(float(-20 * np.log10(mag[i])))
    return out


def closed_loop_matrix(buck, io, gains, adc, dpwm):
    """Linear closed loop, state s = [dx(2), d_k, I_{k-1}, e_{k-1}] in perturbation coordinates."""
    Phi, Gam, Gio, Cy, Dio = buck.sampled(io)
    Kv = 1.0 / adc.lsb
    N = float(1 << dpwm.bits)
    E = -Kv * Cy                       # e_k = E @ dx_k
    kp, ki, kd = gains.kp, gains.ki, gains.kd
    M = np.zeros((5, 5))
    M[0:2, 0:2] = Phi
    M[0:2, 2] = Gam
    M[2, 0:2] = (kp + ki + kd) * E / N
    M[2, 3] = 1.0 / N
    M[2, 4] = -kd / N
    M[3, 0:2] = ki * E
    M[3, 3] = 1.0
    M[4, 0:2] = E
    return M, Phi, Gam, Gio, Cy, Dio


def linear_load_step(buck, io, gains, adc, dpwm, dio, n_before=50, n_after=400):
    """Sampled-instant output deviation for a load-current step dio (no quantisation)."""
    M, Phi, Gam, Gio, Cy, Dio = closed_loop_matrix(buck, io, gains, adc, dpwm)
    Bd = np.zeros(5)
    Bd[0:2] = Gio
    # feedthrough of io into e_k through ESR
    Kv = 1.0 / adc.lsb
    N = float(1 << dpwm.bits)
    efeed = -Kv * Dio
    Bd[2] = (gains.kp + gains.ki + gains.kd) * efeed / N
    Bd[3] = gains.ki * efeed
    Bd[4] = efeed
    s = np.zeros(5)
    t, y = [], []
    for k in range(n_before + n_after):
        d = dio if k >= n_before else 0.0
        y.append(float(Cy @ s[0:2] + Dio * d))
        t.append(k * buck.Ts)
        s = M @ s + Bd * d
    return np.array(t), np.array(y)


class FixedPid:
    """Bit-exact integer PID: the golden model for the Phase 2 RTL.

    kp_i, ki_i, kd_i are integers in Q(frac). The integrator acc is in Q(frac) and is
    clamped to [umin, umax] << frac (anti-windup). Output rounding: (s + 2^(frac-1)) >> frac
    (arithmetic shift, i.e. floor, as Verilog >>> on a signed value).
    """

    def __init__(self, kp_i, ki_i, kd_i, frac, umin, umax, acc0=0):
        self.kp, self.ki, self.kd, self.F = kp_i, ki_i, kd_i, frac
        self.umin, self.umax = umin, umax
        self.acc = acc0
        self.e1 = 0

    def step(self, e, hold=False):
        F = self.F
        if not hold:
            self.acc = min(max(self.acc + self.ki * e, self.umin << F), self.umax << F)
        s = self.kp * e + self.acc + self.kd * (e - self.e1)
        self.e1 = e
        u = (s + (1 << (F - 1))) >> F if F > 0 else s
        return min(max(u, self.umin), self.umax)
