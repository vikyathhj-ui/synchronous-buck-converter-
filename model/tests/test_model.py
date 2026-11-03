"""Model unit tests: python3 -m pytest model/tests -q"""
from dataclasses import replace
from itertools import product

import numpy as np

from model.buck import Buck, Dpwm, SwitchedPlant
from model.controller import Adc, FixedPid, closed_loop_matrix, design, margins
from model.ctrl_ref import CCM, CtrlRef, Regs, therm_decode, therm_encode
from model.sim import open_loop_response, simulate, simulate_clocked

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
        _, _, dense = p.period(D * b.Ts, 0.0, b.vin, nsub=32)
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


G = design(B, 0.15, ADC, DP, 30e3, 60.0, 5.0)
F = 5


def test_design_meets_targets_and_is_stable():
    g = G.quantized(F)
    m = margins(B, 0.15, g, ADC, DP, n=4000)
    assert len(m["crossovers"]) == 1
    assert abs(m["crossovers"][0] / 30e3 - 1) < 0.02
    assert m["pm"][0] >= 59.0
    assert np.abs(np.linalg.eigvals(closed_loop_matrix(B, 0.15, g, ADC, DP)[0])).max() < 1


def test_pm_at_least_45_at_tolerance_corners():
    g = G.quantized(F)
    for vin, L, C, ron, io in product((3.0, 3.6), (12e-6, 18e-6), (8e-6, 12e-6), (0.25, 1.0), (0.015, 0.15)):
        m = margins(replace(B, vin=vin, L=L, C=C, ron=ron), io, g, ADC, DP, n=2500)
        assert len(m["crossovers"]) == 1
        assert min(m["pm"]) >= 45.0, (vin, L, C, ron, io, m["pm"])


def test_fixed_pid_integrator_bounded():
    kp, ki, kd = G.ints(F)
    pid = FixedPid(kp, ki, kd, F, 0, 511)
    for _ in range(5000):
        u = pid.step(7)
        assert 0 <= u <= 511 and pid.acc <= 511 << F
    for _ in range(5000):
        u = pid.step(-8)
        assert 0 <= u <= 511 and pid.acc >= 0


def test_closed_loop_regulates_without_limit_cycle():
    b = replace(B, g_load=0.075 / 1.8)
    kp, ki, kd = G.ints(F)
    r = simulate(b, DP, Regs(kp=kp, ki=ki, kd=kd), n=4000, frac=F)
    assert len(np.unique(r.d[2500:])) == 1
    assert np.all(r.e[2500:] == 0)


def test_therm_roundtrip_and_bubble():
    for i in range(-900, 900):
        err = (i + 0.37) * 1e-4   # avoid exact threshold ties
        assert therm_decode(therm_encode(err)) == ADC.code(err)
    # single bubble inside the thermometer is corrected
    w = therm_encode(0.0)                    # 8 ones: bits 0..7
    assert therm_decode(w ^ (1 << 3)) == 0   # hole at bit 3
    assert therm_decode(w | (1 << 10)) == 0  # isolated one at bit 10


def test_clocked_and_period_sims_agree_in_ccm():
    kp, ki, kd = G.ints(F)
    b = replace(B, g_load=0.075 / 1.8)
    r1 = simulate(b, DP, Regs(kp=kp, ki=ki, kd=kd), n=1600, frac=F)
    r2, _ = simulate_clocked(b, DP, Regs(kp=kp, ki=ki, kd=kd), n=1600, frac=F)
    assert np.array_equal(r1.d, r2.d)
    assert np.max(np.abs(r1.v - r2.v)) < 1e-9
    assert r1.mode[-1] == CCM


def test_calibrated_dpwm_nominal_equals_ideal():
    kp, ki, kd = G.ints(F)
    b = replace(B, g_load=0.075 / 1.8)
    r1 = simulate(b, DP, Regs(kp=kp, ki=ki, kd=kd), n=1500, frac=F)
    r2 = simulate(b, Dpwm(t_elem=1 / 64e6 / 40), Regs(kp=kp, ki=ki, kd=kd), n=1500, frac=F)
    assert np.array_equal(r1.d, r2.d)


def test_calibrated_dpwm_extreme_elements_no_limit_cycle():
    """Element delays at the measured PVT extremes of dlygate4sd3_1 (0.244 ns, 0.698 ns)."""
    kp, ki, kd = G.ints(F)
    for te in (0.244e-9, 0.698e-9):
        dp = Dpwm(t_elem=te)
        d = [dp.fine_delay(f, CtrlRef.tap_of(f, 16 * dp.n_meas())) for f in range(8)]
        steps = [d[f + 1] - d[f] for f in range(7)] + [1 / 64e6 - (d[7] - d[0])]   # incl. coarse boundary
        assert max(steps) * 1e6 * 3.6 < 0.010     # output step (dt * fsw * VIN) below the ADC LSB at 3.6 V
        for io in (0.02, 0.075, 0.14):
            r = simulate(replace(B, g_load=io / 1.8), dp, Regs(kp=kp, ki=ki, kd=kd), n=3000, frac=F)
            assert len(np.unique(r.d[-1000:])) == 1, (te, io)


def test_calibration_hysteresis():
    c = CtrlRef(Regs())
    for k in range(16 * 4):
        c.calibrate(40 + (k % 2))               # 40/41 alternating: mean 40.5 -> sum 648, |648-640| = 8, no update
    assert c.n_cal_q4 == 640
    for _ in range(16):
        c.calibrate(30)
    assert c.n_cal_q4 == 480
