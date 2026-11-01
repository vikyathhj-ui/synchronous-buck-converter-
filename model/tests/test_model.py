"""Model unit tests: python3 -m pytest model/tests -q"""
from dataclasses import replace

import numpy as np

from model.buck import Buck, Dpwm, SwitchedPlant
from model.controller import Adc, FixedPid, closed_loop_matrix, design, margins
from model.sim import open_loop_response, simulate

B, DP, ADC = Buck(), Dpwm(), Adc()


def test_open_loop_dc_matches_averaged():
    """Switched plant at the averaged duty settles to VOUT within the ripple."""
    b = replace(B, g_load=0.15 / 1.8)
    p = SwitchedPlant(b)
    D = b.duty_dc(0.0)
    for _ in range(3000):
        p.period(D * b.Ts, 0.0, b.vin)
    vs = []
    for _ in range(10):
        _, dense = p.period(D * b.Ts, 0.0, b.vin, nsub=32)
        vs += [x[1] for x in dense]
    assert abs(np.mean(vs) - b.vout) < 2e-3


def test_sampled_model_matches_switched_injection():
    for f in (5e3, 50e3):
        h = open_loop_response(B, 0.15, f, settle_periods=800)
        p = B.pz(f, 0.15)[0]
        assert abs(20 * np.log10(abs(h) / abs(p))) < 0.05
        assert abs(np.angle(h / p, deg=True)) < 0.5


def test_resolution_condition_all_vin():
    for vin in (3.0, 3.3, 3.6):
        assert DP.lsb_out(vin) < ADC.lsb


def test_dpwm_ideal_is_monotonic_and_covers_period():
    tons = np.array([DP.ton(c) for c in range(DP.nmax + 1)])
    assert np.all(np.diff(tons) > 0)
    assert abs(tons[-1] + DP.ton(1) - B.Ts) < 1e-15


def test_adc_mid_tread_and_saturation():
    assert ADC.code(0.0) == 0 and ADC.code(0.0049) == 0 and ADC.code(0.0051) == 1
    assert ADC.code(1.0) == 7 and ADC.code(-1.0) == -8


def test_design_meets_targets_and_is_stable():
    g = design(B, 0.15, ADC, DP, 50e3, 50.0, 5.0).quantized(2)
    m = margins(B, 0.15, g, ADC, DP, n=4000)
    assert len(m["crossovers"]) == 1
    assert abs(m["crossovers"][0] / 50e3 - 1) < 0.02
    assert m["pm"][0] >= 45.0
    assert np.abs(np.linalg.eigvals(closed_loop_matrix(B, 0.15, g, ADC, DP)[0])).max() < 1


def test_fixed_pid_integrator_bounded():
    pid = FixedPid(18, 1, 273, 2, 0, 511)
    for _ in range(5000):
        u = pid.step(7)
        assert 0 <= u <= 511 and pid.acc <= 511 << 2
    for _ in range(5000):
        u = pid.step(-8)
        assert 0 <= u <= 511 and pid.acc >= 0


def test_closed_loop_regulates_without_limit_cycle():
    g = design(B, 0.15, ADC, DP, 50e3, 50.0, 5.0)
    b = replace(B, g_load=0.075 / 1.8)
    r = simulate(b, DP, ADC, g.ints(2), 2, n=4000)
    assert len(np.unique(r.d[2500:])) == 1
    assert np.all(r.e[2500:] == 0)
