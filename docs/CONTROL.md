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
| 3.0 | 150 | [323] | [0.0] | 0.000 |
| 3.3 | 15 | [281] | [0.0] | 0.000 |
| 3.3 | 75 | [286] | [0.0] | 0.000 |
| 3.3 | 150 | [293] | [0.0] | 0.000 |
| 3.6 | 15 | [257] | [0.0] | 0.000 |
| 3.6 | 75 | [262] | [0.0] | 0.000 |
| 3.6 | 150 | [269] | [0.0] | 0.000 |

Limit-cycle free in all 9 runs: **True**. Counter-example, 6-bit DPWM (LSB 51.6 mV at VOUT): limit cycle at **13 of 15** loads.
Example at 20 mA: duty codes [26, 27, 35, 36, 44, 45], sampled VOUT p-p 14.1 mV.

| tap / ideal | DNL max [LSB] | DNL min [LSB] | loads with limit cycle | max sampled p-p [mV] |
|---|---|---|---|---|
| 0.6 | +2.80 | -0.40 | 4 of 15 | 12.63 |
| 0.8 | +1.40 | -0.20 | 1 of 15 | 11.13 |
| 1.0 | +0.00 | -0.00 | 0 of 15 | 0.00 |
| 1.2 | +0.20 | -1.40 | 1 of 15 | 10.17 |
| 1.4 | +0.40 | -2.80 | 4 of 15 | 10.43 |
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
iteration. Design point: VIN 3.3 V, 150 mA, current-source load (the least damping), fc = 50 kHz
(fsw/20), PM = 50 deg.

Why 50 deg and fc/5: a 45 to 55 deg sweep in the switched simulation gave the same undershoot
(about 49 mV) with recovery growing as PM rises; 60 deg could not be met with one crossover (the loop
crossed 0 dB three times around the LC resonance, i.e. a conditionally stable design), so it was
rejected. 50 deg leaves margin above the 45 deg spec for VIN and load variation.

<!-- AUTO:p1_design -->
| Quantity | Value | Unit | Kind |
|---|---|---|---|
| Design target | fc 50 kHz, PM 50 deg, integral zero fc/5 | - | model |
| kp, ki, kd (float) | 4.4515, 0.2797, 68.240 | DPWM LSB / ADC LSB | model |
| kp, ki, kd (Q2 integers) | 18, 1, 273 | x 2^-2 | model |
| Crossover fc | 50.2 | kHz | model |
| Phase margin | 49.9 | deg | model |
| Gain margin | 8.6 at 125 kHz | dB | model |
| Max closed-loop pole magnitude | 0.9575 | - | model |
| Normalised integral gain Ki_n (worst VIN) | 0.176 | - | model |
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
| 0 | 4.0000 | 0.0000 | 68.0000 | 51.08 | 51.47 | 1 | 1.0000 |
| 1 | 4.5000 | 0.5000 | 68.0000 | 48.55 | 49.70 | 1 | 0.9623 |
| 2 | 4.5000 | 0.2500 | 68.2500 | 50.21 | 49.88 | 1 | 0.9575 |
| 3 | 4.5000 | 0.2500 | 68.2500 | 50.21 | 49.88 | 1 | 0.9575 |
| 4 | 4.4375 | 0.2500 | 68.2500 | 50.17 | 50.06 | 1 | 0.9581 |
| 5 | 4.4375 | 0.2812 | 68.2500 | 49.99 | 50.04 | 1 | 0.9587 |
| 6 | 4.4531 | 0.2812 | 68.2344 | 49.99 | 50.00 | 1 | 0.9586 |
| 7 | 4.4531 | 0.2812 | 68.2422 | 49.99 | 49.99 | 1 | 0.9586 |
| 8 | 4.4531 | 0.2812 | 68.2383 | 49.99 | 49.99 | 1 | 0.9586 |
| 9 | 4.4512 | 0.2793 | 68.2402 | 50.00 | 50.00 | 1 | 0.9586 |
| 10 | 4.4512 | 0.2793 | 68.2402 | 50.00 | 50.00 | 1 | 0.9586 |

Chosen: **Q2** (smallest F with |dPM|<1 deg, |dfc|<2 %, ki>0, one crossover).
<!-- /AUTO:p1_quant -->

Note that at the chosen F, ki is 0.25 against 0.280 (-11 %). The margins hardly move because the
integral zero is well below crossover. It only slows the final integral tail, which the time-domain
runs below include, because they use the quantised integers.

## 6. Robustness

The quantised gains are evaluated over VIN 3.0/3.3/3.6 V, L 12/15/18 uH, C 8/10/12 uF,
Ron 0.25/0.5/1.0 ohm and load 15/150 mA (162 cases).

<!-- AUTO:p1_robust -->
| Quantity | Value | Unit | Kind |
|---|---|---|---|
| Cases | 162 | - | model |
| PM range, VIN and load only (nominal L, C, Ron) | 48.2 .. 51.9 | deg | model |
| PM range, L and C +/-20 % only | 33.5 .. 56.7 | deg | model |
| PM range, all cases | 28.3 .. 66.5 | deg | model |
| GM minimum, all cases | 4.0 | dB | model |
| fc range, all cases | 31.5 .. 83.2 | kHz | model |
| All closed loops stable | True | - | model |
| Worst case | VIN 3.6 V, L 12 uH, C 8 uF, Ron 0.25 ohm, io 150 mA | - | model |
<!-- /AUTO:p1_robust -->

**Reading this.** VIN and load alone keep PM near the design value. The large spread comes from L and
C tolerance: with both at -20 % the gain above resonance (proportional to 1/(LC)) rises by
1/0.64 = 1.56x, so crossover moves up toward the delay-dominated region and PM drops. VIN feedforward
would not fix this, because it is an LC-tolerance effect. Every case stays stable, but the corner
falls below the 45 deg spec, so section 8 raises it as an open question.

## 7. Predicted time-domain response

Switched plant plus the bit-exact fixed-point controller (`model/sim.py`, `model/controller.py: FixedPid`)
with ADC saturation, DPWM quantisation, soft start and the valley current limit. The load step uses a
15 mA resistive base load plus a 135 mA current step; start-up, the line step and the ripple use
resistive loads.

<!-- AUTO:p1_time -->
| Quantity | Value | Unit | Kind |
|---|---|---|---|
| Load step 15->150 mA: undershoot (switched) | 49.2 | mV | model |
|   same, sampled instants only | 48.8 | mV | model |
|   same, linear sampled model | 46.7 | mV | model |
|   recovery to +/-1 % | 15.4 | us | model |
| Load step 150->15 mA: overshoot | 46.7 | mV | model |
|   recovery to +/-1 % | 17.0 | us | model |
| Start-up overshoot, no load / full load | 0.33 / 0.33 | % | model |
| Start-up peak iL, no load / full load | 73 / 221 | mA | model |
| Start-up current-limit trips | 0 / 0 | - | model |
| Soft-start VREF ramp time | 0.999 | ms | model |
| Line step 3.0->3.6 V: max deviation | +59.2 | mV | model |
| Line step 3.6->3.0 V: max deviation | -63.5 | mV | model |
| VOUT ripple p-p, 150 mA | 0.78 | mV | model |
| iL ripple p-p, 150 mA | 53.9 | mA | model |
| Overload 365 mA: max valley / peak iL | 413 / 417 | mA | model |
| Overload: trips in 200 periods, min VOUT | 119, 0.239 V | - | model |
<!-- /AUTO:p1_time -->

Plots: `load_step.png`, `startup.png`, `line_step.png`, `limit_cycle_hist.png` and `tap_sweep.png` in
`results/plots/phase1/`.

## 8. Observations and open questions

1. **Derivative kick from quantised error.** kd is about 68 DPWM LSB per ADC LSB, so a single ADC code
   change moves the duty by about 68 LSB for one period. This is visible as iL spikes in the recovery
   phase of the load step and during soft start (where VREF steps every ~5.6 us). The loop settles to a
   single code, but the spikes are real current stress. Phase 2 options: filter the D term, or a finer
   soft-start step. (Derivative-on-measurement is not directly available, because the window ADC
   measures the error, not VOUT.)
2. **Start-up current margin.** At full load the start-up peak iL is close to the 250 mA limit (see
   the table). A slower ramp or option 1 above would widen this margin.
3. **Valley limit is sampled once per period.** The check happens at the period start, so with a
   heavy overload the valley current can exceed the threshold by up to one on-time ramp before the
   next HS pulse is suppressed. Phase 2/3 must decide whether the comparator also gates the HS
   turn-on continuously (a true valley limit).
4. **Window ADC common mode.** With VREF up to 2.5 V and comparators on 1.8 V, the comparator inputs
   cannot sit at VOUT directly. A feedback divider (e.g. VOUT/2 with a 5 mV ladder LSB, which is
   still 10 mV at VOUT) is the likely Phase 3 answer. Near 0 V during soft start, the lower ladder taps
   would be negative; the ADC simply saturates there.
5. **Robustness to L/C tolerance** (section 6): the PM falls below 45 deg only at the
   L -20 % / C -20 % corner. It is your call whether +/-20 % is the right tolerance, and whether to
   lower fc for margin there.
