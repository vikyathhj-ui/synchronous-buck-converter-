# Control design (Phase 1)

All numbers in the tables below are generated from `results/summary.json` by
`scripts/update_docs.py`; `summary.json` is written by `python3 -m model.phase1`.
"analysis" = closed-form formula, "model" = computed by the Python models in `model/`.
No transistor-level result exists yet: the power stage is ideal switches plus an assumed Ron.

## 1. Assumptions

| ID | Assumption | Replaced by |
|---|---|---|
| A1 | HS and LS on-resistance are equal, Ron = 0.5 ohm each, so the series resistance rs = DCR + Ron is the same in both switch states | Phase 3 power-stage sizing and ngspice Ron |
| A2 | Ideal switches: no dead time, no body-diode conduction, no gate-drive or switching loss, no driver delay | Phase 3/4 transistor-level blocks |
| A3 | Ideal ADC: no comparator offset or noise; thresholds exactly at (i - 7.5) x 10 mV | Phase 3 comparator Monte Carlo |
| A4 | Ideal DPWM taps unless `tap_scale` is swept | Phase 3 delay-line PVT |
| A5 | Off-chip L and C at nominal; +/-20 % used only for the robustness sweep (the brief gives no tolerance) | your choice of tolerance |
| A6 | Load steps applied as ideal steps at a period boundary (faster than the 100 ns spec edge, so conservative) | - |

## 2. Power-stage models

States x = [iL, vC], inputs u = [v_sw, i_o], resistive load conductance G (may be 0),
k = 1 / (1 + ESR G):

```
L diL/dt = v_sw - (rs + k ESR) iL - k vC + k ESR i_o
C dvC/dt = k iL - G k vC - k i_o
VOUT     = k ESR iL + k vC - k ESR i_o
```

**Volt-second balance (CCM):** D VIN = VOUT + rs IL, so D = (VOUT + rs IL) / VIN.

**Averaged control-to-output** (v_sw = d VIN): Gvd(s) = Cy (sI - A)^-1 B_vsw VIN. This is a
second-order low-pass with the LC double pole at f0 = 1 / (2 pi sqrt(LC)), damped by rs and the load,
and the ESR zero at 1 / (2 pi ESR C).

**Exact sampled small-signal model** (what the digital loop actually sees). VOUT is sampled at the
start of each period; the HS turns on there and off at D Ts (trailing-edge modulation). A duty
perturbation d moves the turn-off edge, injecting VIN Ts d volt-seconds at t = D Ts, which then
evolves for (1 - D) Ts:

```
x[k+1] = Phi x[k] + Gam d[k],   Phi = e^{A Ts},   Gam = e^{A (1-D) Ts} B_vsw VIN Ts
P(z)   = Cy (zI - Phi)^-1 Gam
```

The controller computes d[k+1] from the sample at k (one full period of ADC + compute delay),
so the loop gain is

```
L(z) = z^-1 * C(z) * P(z) / (q_ADC * 2^N_DPWM)
```

The z^-1, plus the extra phase P(z) has relative to Gvd(s) (about (1 - D) Ts of
modulator delay), is the reason the digital loop has less phase than the averaged model at the
same crossover. At 50 kHz the 1 us compute delay alone costs 360 x 50e3 x 1e-6 = 18 deg (analysis).

**Model check.** The switched plant (exact piecewise-linear integration of each switch interval,
`model/buck.py: SwitchedPlant`) was driven with a small sinusoidal duty and its sampled response
fitted (`model/sim.py: open_loop_response`). It matches P(z) to within the error shown in the design
table. This shows that the sampled-model derivation is right. It does **not** show that the plant
matches silicon; that comes from the transistor-level co-simulation in Phase 4.

<!-- AUTO:p1_analysis -->
| Quantity | Value | Unit | Kind |
|---|---|---|---|
| LC resonance f0 | 12.99 | kHz | analysis |
| ESR zero | 1.59 | MHz | analysis |
| Duty at 150 mA (rs = DCR + Ron) | 0.5727 | - | analysis |
| Inductor ripple p-p, 150 mA | 57.3 | mA | analysis |
| VOUT ripple p-p, capacitive term | 0.716 | mV | analysis |
| VOUT ripple p-p, ESR term | 0.573 | mV | analysis |
| DPWM tap | 1.953 | ns | analysis |
| DPWM LSB at VOUT, VIN 3.0 / 3.3 / 3.6 V | 5.86 / 6.45 / 7.03 | mV | analysis |
| ADC LSB | 10 | mV | analysis |
| Condition 1 (DPWM LSB < ADC LSB at all VIN) | True | - | analysis |
<!-- /AUTO:p1_analysis -->

## 3. Resolution plan and the limit-cycle conditions

A digitally controlled converter limit-cycles when no DPWM level puts VOUT inside the ADC zero bin
(Peterchev and Sanders, IEEE Trans. Power Electron., 2003). The conditions used here:

1. **DPWM finer than ADC (output-referred):** q_DPWM,out = VIN / 2^9 < q_ADC = 10 mV, at every VIN.
   The worst case is VIN = 3.6 V. The window ADC is mid-tread (a zero bin of +/-5 mV), so some DPWM
   level always lands inside it.
2. **Integral action with a bounded step:** the integrator must be present (ki > 0, otherwise there is
   a static error rather than a limit cycle) and, normalised as
   Ki_n = ki * q_DPWM,out / q_ADC (how many ADC bins the integrator moves VOUT per sample for a
   one-bin error), 0 < Ki_n <= 1. This normalisation is my statement of the condition; it is checked
   by simulation below, not taken as proof.
3. **Stable linear loop** (all closed-loop poles inside the unit circle).

Check: 10 ms of steady state per case after start-up, then the histogram of the applied duty codes
(`results/plots/phase1/limit_cycle_hist.png`). The counter-example uses a 6-bit counter-only DPWM
(LSB 52 mV > 10 mV) with the same loop design.

<!-- AUTO:p1_limit -->
| VIN [V] | load [mA] | duty codes in 10 ms | ADC codes | sampled VOUT p-p [mV] |
|---|---|---|---|---|
| 3.0 | 15 | [309] | [0.0] | 0.000 |
| 3.0 | 75 | [315] | [0.0] | 0.000 |
| 3.0 | 150 | [322] | [0.0] | 0.000 |
| 3.3 | 15 | [281] | [0.0] | 0.000 |
| 3.3 | 75 | [286] | [0.0] | 0.000 |
| 3.3 | 150 | [293] | [0.0] | 0.000 |
| 3.6 | 15 | [257] | [0.0] | 0.000 |
| 3.6 | 75 | [262] | [0.0] | 0.000 |
| 3.6 | 150 | [269] | [0.0] | 0.000 |

Limit-cycle free in all 9 runs: **True**. Counter-example, 6-bit DPWM (LSB 51.6 mV at VOUT): limit cycle at **12 of 15** loads.
Example at 20 mA: duty codes [31, 35, 36, 40], sampled VOUT p-p 15.3 mV.

| tap / ideal | DNL max [LSB] | DNL min [LSB] | loads with limit cycle | max sampled p-p [mV] |
|---|---|---|---|---|
| 0.6 | +2.80 | -0.40 | 3 of 15 | 13.53 |
| 0.8 | +1.40 | -0.20 | 1 of 15 | 11.78 |
| 1.0 | +0.00 | -0.00 | 0 of 15 | 0.00 |
| 1.2 | +0.20 | -1.40 | 0 of 15 | 0.00 |
| 1.4 | +0.40 | -2.80 | 3 of 15 | 11.18 |
<!-- /AUTO:p1_limit -->

**Delay-line error.** The tap sweep scales every fine tap by `tap_scale` (an uncalibrated delay line
across PVT). The coarse-boundary step then becomes (8 - 7 x tap_scale) LSB, so the DNL is
7 (1 - tap_scale) LSB: a missing-code gap if tap_scale < 1, or a non-monotonic step if tap_scale > 1.
Both cause limit cycles at some loads, as the table shows. This is the quantified input to the Phase 3
decision between calibrating the delay line (measuring taps against the clock period) and accepting
the error.

## 4. PID design (z-domain)

Parallel PID once per period, in controller units (e in ADC LSB, u in DPWM LSB):

```
I[k] = clamp(I[k-1] + ki e[k], 0, 511)          anti-windup
u[k] = kp e[k] + I[k] + kd (e[k] - e[k-1])      applied in period k+1
C(z) = kp + ki / (1 - z^-1) + kd (1 - z^-1)
```

**Method** (`model/controller.py: design`). With ki = alpha kp (alpha = 2 pi (fc/5) Ts, which puts the
integral zero near fc/5), C(z0) at z0 = e^{j 2 pi fc Ts} is linear in (kp, kd). The conditions
|L(z0)| = 1 and angle L(z0) = -180 + PM are then two real equations in two unknowns, with no
iteration. Design point: VIN 3.3 V, 150 mA, current-source load (the least damping), **fc = 30 kHz,
PM = 60 deg**, integral zero at fc/5.

**Requirement that sets the design: PM >= 45 deg in every robustness case of section 6**, not just at
nominal (user decision, DECISIONS D11). History:
- The first design was fc = 50 kHz (fsw/20), PM = 50 deg. It gave 49.9 deg at nominal but 28.3 deg
  at the L -20 % / C -20 % / VIN 3.6 V corner, and was rejected for that reason.
- A search over fc 30–45 kHz, PM targets 50/55/60 deg and integral zeros at fc/5 and fc/8 found that only fc <= 35 kHz
  keeps the worst corner >= 45 deg. 35 kHz / 60 deg and 30 kHz / 55 deg hit 45.0–45.2 deg, which leaves
  no margin. 30 kHz / 60 deg gives about 48.7 deg worst case and was chosen.
- Cost: the load-step undershoot rises from 49 mV to 66 mV (still inside the 90 mV spec), recovery
  slows from 15 to 26 us (spec 50 us), and the line-step deviation grows (section 8, item 6). Gain:
  kd halves (68 -> 35), so the derivative kicks halve, and GM rises to 14 dB.

<!-- AUTO:p1_design -->
| Quantity | Value | Unit | Kind |
|---|---|---|---|
| Design target | fc 30 kHz, PM 60 deg, integral zero fc/5 | - | model |
| kp, ki, kd (float) | 2.6953, 0.1016, 35.350 | DPWM LSB / ADC LSB | model |
| kp, ki, kd (Q5 integers) | 86, 3, 1131 | x 2^-5 | model |
| Crossover fc | 30.1 | kHz | model |
| Phase margin | 60.2 | deg | model |
| Gain margin | 14.2 at 124 kHz | dB | model |
| Max closed-loop pole magnitude | 0.9697 | - | model |
| Normalised integral gain Ki_n (worst VIN) | 0.066 | - | model |
| Plant model check, max error | 4.1e-08 dB, 1.7e-06 deg | - | model |
<!-- /AUTO:p1_design -->

Bode plot: `results/plots/phase1/bode.png`.

## 5. Coefficient quantisation

Each coefficient is round(K x 2^F) / 2^F. For each F the loop margins and closed-loop poles are
recomputed. The selection rule is the smallest F with |dPM| < 1 deg, |dfc / fc| < 2 %, ki > 0 and a
single crossover.

<!-- AUTO:p1_quant -->
| frac bits | kp | ki | kd | fc [kHz] | PM [deg] | crossovers | max pole |
|---|---|---|---|---|---|---|---|
| 0 | 3.0000 | 0.0000 | 35.0000 | 31.51 | 59.07 | 1 | 1.0000 |
| 1 | 2.5000 | 0.0000 | 35.5000 | 31.14 | 62.92 | 1 | 1.0000 |
| 2 | 2.7500 | 0.0000 | 35.2500 | 31.32 | 60.98 | 1 | 1.0000 |
| 3 | 2.7500 | 0.1250 | 35.3750 | 29.78 | 59.15 | 1 | 0.9528 |
| 4 | 2.6875 | 0.1250 | 35.3750 | 29.68 | 59.66 | 1 | 0.9503 |
| 5 | 2.6875 | 0.0938 | 35.3438 | 30.09 | 60.19 | 1 | 0.9697 |
| 6 | 2.6875 | 0.1094 | 35.3438 | 29.88 | 59.93 | 1 | 0.9613 |
| 7 | 2.6953 | 0.1016 | 35.3516 | 30.00 | 60.00 | 1 | 0.9659 |
| 8 | 2.6953 | 0.1016 | 35.3516 | 30.00 | 60.00 | 1 | 0.9659 |
| 9 | 2.6953 | 0.1016 | 35.3496 | 30.00 | 60.00 | 1 | 0.9659 |
| 10 | 2.6953 | 0.1016 | 35.3506 | 30.00 | 60.00 | 1 | 0.9659 |

Chosen: **Q5** (smallest F with |dPM|<1 deg, |dfc|<2 %, one crossover, every coefficient within 10 %).
<!-- /AUTO:p1_quant -->

The rule also requires every coefficient to be within 10 % of its design value. Without it, Q3 would
pass on margins alone with ki rounded to 0.125 against 0.102 (+23 %). Margins hardly see ki because the
integral zero is well below crossover, but ki sets the integral tail and Ki_n. The time-domain runs
below use the quantised integers.

## 6. Robustness

The quantised gains are evaluated over VIN 3.0/3.3/3.6 V, L 12/15/18 uH, C 8/10/12 uF,
Ron 0.25/0.5/1.0 ohm and load 15/150 mA (162 cases).

<!-- AUTO:p1_robust -->
| Quantity | Value | Unit | Kind |
|---|---|---|---|
| Cases | 162 | - | model |
| PM range, VIN and load only (nominal L, C, Ron) | 59.6 .. 61.1 | deg | model |
| PM range, L and C +/-20 % only | 54.6 .. 63.5 | deg | model |
| PM range, all cases | 48.7 .. 82.0 | deg | model |
| GM minimum, all cases | 9.6 | dB | model |
| fc range, all cases | 19.2 .. 47.9 | kHz | model |
| All closed loops stable | True | - | model |
| Single crossover in every case | True | - | model |
| PM >= 45 deg in every case (requirement) | True | - | model |
| Worst case | VIN 3.6 V, L 12 uH, C 8 uF, Ron 0.25 ohm, io 150 mA | - | model |
<!-- /AUTO:p1_robust -->

**Reading this.** VIN and load alone barely move PM. The spread comes from L and C tolerance: with
both at -20 % the gain above resonance (proportional to 1/(LC)) rises by 1/0.64 = 1.56x, so crossover
moves up toward the delay-dominated region and PM drops; with both at +20 % crossover moves down.
VIN feedforward would not fix this, because it is an LC-tolerance effect. The design is chosen so the
worst corner still meets 45 deg (`robust_pm_meets_spec_all`). Tolerance of +/-20 % on L and C is an
assumption (A5).

## 7. Predicted time-domain response

Switched plant plus the bit-exact fixed-point controller (`model/sim.py`, `model/controller.py: FixedPid`)
with ADC saturation, DPWM quantisation, soft start and the valley current limit. The load step uses a
15 mA resistive base load plus a 135 mA current step; start-up, the line step and the ripple use
resistive loads.

<!-- AUTO:p1_time -->
| Quantity | Value | Unit | Kind |
|---|---|---|---|
| Load step 15->150 mA: undershoot (switched) | 65.7 | mV | model |
|   same, sampled instants only | 65.3 | mV | model |
|   same, linear sampled model | 64.8 | mV | model |
|   recovery to +/-1 % | 25.6 | us | model |
| Load step 150->15 mA: overshoot | 65.8 | mV | model |
|   recovery to +/-1 % | 24.9 | us | model |
| Start-up overshoot, no load / full load | -0.01 / -0.00 | % | model |
| Start-up peak iL, no load / full load | 55 / 205 | mA | model |
| Start-up current-limit trips | 0 / 0 | - | model |
| Soft-start VREF ramp time | 0.999 | ms | model |
| Line step 3.0->3.6 V: max deviation | +174.1 | mV | model |
| Line step 3.6->3.0 V: max deviation | -169.0 | mV | model |
| VOUT ripple p-p, 150 mA | 0.78 | mV | model |
| iL ripple p-p, 150 mA | 53.9 | mA | model |
| Overload 365 mA: max valley / peak iL | 373 / 382 | mA | model |
| Overload: trips in 200 periods, min VOUT | 116, 0.049 V | - | model |
<!-- /AUTO:p1_time -->

Plots: `load_step.png`, `startup.png`, `line_step.png`, `limit_cycle_hist.png` and `tap_sweep.png` in
`results/plots/phase1/`.

## 8. Observations and open questions

1. **Derivative kick from quantised error.** kd is about 35 DPWM LSB per ADC LSB (68 in the rejected
   50 kHz design), so a single ADC code change moves the duty by about 35 LSB for one period. This
   shows as iL spikes in the load-step recovery and during soft start (where VREF steps every
   ~5.6 us). The loop settles to a single code, but the spikes are real current stress. Phase 2 options:
   filter the D term, or a finer soft-start step. (Derivative-on-measurement is not directly
   available, because the window ADC measures the error, not VOUT.)
2. **Start-up current margin.** At full load the start-up peak iL is below the 250 mA limit, by the
   margin shown in the table.
3. **Valley limit is sampled once per period.** The check happens at the period start, so with a
   heavy overload the valley current can exceed the threshold by up to one on-time ramp before the
   next HS pulse is suppressed (see the overload rows). Phase 2/3 must decide whether the comparator
   also gates the HS turn-on continuously (a true valley limit).
4. **Window ADC common mode.** With VREF up to 2.5 V and comparators on 1.8 V, the comparator inputs
   cannot sit at VOUT directly. A feedback divider (e.g. VOUT/2 with a 5 mV ladder LSB, which is
   still 10 mV at VOUT) is the likely Phase 3 answer. Near 0 V during soft start, the lower ladder taps
   would be negative; the ADC simply saturates there.
5. **Robustness** (section 6): met in every case, by design.
6. **Line step is the price of the robust design.** A 0.6 V VIN step in 10 us moves VOUT by the amount
   in the table, well outside the ADC window (+70/-80 mV), so the loop works with a saturated error
   for a few tens of us. The brief only asks for this to be reported. The usual fix is VIN
   feedforward (scale the duty by VIN_nom/VIN), but it needs a VIN measurement that the architecture
   does not have. That is an architecture change for the user to decide, not done here.
