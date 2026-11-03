# Transistor-level blocks (Phase 3)

Every number in the tables is generated from `results/summary.json["phase3"]` (scripts/collect_phase3.py
reads the per-block JSON written by each `scripts/char_*.py`, which parses ngspice output) by
`scripts/update_docs.py`. "pending" means the characterisation has not finished.

**Conditions.** PVT = 5 corners (tt ff ss sf fs) x -40 / 27 / 125 C x VIN 3.0 / 3.3 / 3.6 V. Blocks on
the 1.8 V digital supply are swept at 1.62 / 1.80 / 1.98 V instead of VIN. Monte Carlo uses the PDK
mismatch models (`mc_mm_switch=1`, parallel devices with `m=N mult=N`, DECISIONS D20).
Model library: `spice/models/sky130_mini.lib` (identical results to the full PDK library, D20).

**Schematics.** `xschem/*.sch` are generated from the SPICE netlists (`scripts/gen_xschem.py`) and
checked against them with netgen (`scripts/lvs_xschem.sh`); a wrong device size or connection makes
the check fail.

<!-- AUTO:p3_lvs -->
| Cell | xschem vs SPICE (netgen) |
|---|---|
| adc_div | match |
| adc_string | match |
| cmp_hv | match |
| cmp_sa | match |
| deadtime_gen | match |
| dpwm_cal | match |
| dpwm_fine | match |
| drv_hs | match |
| drv_ls | match |
| dt_prog | match |
| dt_stage | match |
| dt_tap | match |
| gate_sense | match |
| power_fets | match |
| sw_cmp | match |
| sw_sense | match |
| tdc_line | match |
<!-- /AUTO:p3_lvs -->

## 1. Power FETs (`spice/powerstage.spice: power_fets`)

HS `pfet_g5v0d10v5` and LS `nfet_g5v0d10v5`, L = 0.5 um, 10 um fingers, 4 equal segments each
(segment control for light load is a stretch goal; the segments share one gate today).
Device limits (SkyWater documentation): |VDS| <= 11 V, |VGS| <= 5.5 V; this design applies at most 3.6 V.

Sizing (`scripts/size_power.py`, analysis): the loss model below with the measured per-mm Ron, Qg and
Qoss, widths chosen for the best mean efficiency over 10/25/50/100/150 mA.

```
P = Irms^2 (D Rhs + (1-D) Rls + DCR) + (Qg_hs + Qg_ls) VIN fsw (1 + 1/(taper-1))
  + (Qoss_hs + Qoss_ls) VIN fsw + 0.5 VIN Io t_sw fsw + Vbd Io t_bd fsw
```

<!-- AUTO:p3_power -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| NMOS g5v0d10v5 Ron x W, tt / PVT range | 2.033 | ohm*mm | results/phase3/fet.json (scripts/char_fet.py) |
|   over 45 PVT points | 1.34 .. 3.53 | ohm*mm | results/phase3/fet.json (scripts/char_fet.py) |
| PMOS g5v0d10v5 Ron x W, tt | 6.456 | ohm*mm | results/phase3/fet.json (scripts/char_fet.py) |
|   over 45 PVT points | 4.19 .. 10.60 | ohm*mm | results/phase3/fet.json (scripts/char_fet.py) |
| Gate charge per mm (n / p), tt | 5.28 / 4.42 | pC/mm | results/phase3/fet.json (scripts/char_fet.py) |
| LS body-diode drop at 150 mA/mm, tt | 0.759 | V | results/phase3/fet.json (scripts/char_fet.py) |
| HS / LS width (loss-model optimum) | 19.2 / 8.8 | mm | results/phase3/sizing.json (scripts/size_power.py) |
| HS / LS Ron at tt | 0.336 / 0.231 | ohm | results/phase3/sizing.json (scripts/size_power.py) |
| Model mean efficiency 10..150 mA (power stage only) | 96.33 | % | results/phase3/sizing.json (scripts/size_power.py) |
<!-- /AUTO:p3_power -->

**Model vs simulation** (`scripts/char_powerstage.py losses`): the power stage switching a constant
inductor current (steady state in one period), FET loss measured as the average of VDS x ID through
0 V sense sources, gate drive as the driver plus level-shifter supply power. The model uses the
body-diode time measured in the same run. Plot: `results/plots/phase3/loss_model_vs_sim.png`.

<!-- AUTO:p3_losses -->
| Load [mA] | FET loss sim [mW] | FET loss model [mW] | Gate drive sim [mW] | Gate drive model [mW] | Body diode [ns/period] |
|---|---|---|---|---|---|
| 10 | 0.326 | 0.361 | 0.543 | 0.577 | 26.7 |
| 25 | 0.757 | 0.909 | 0.542 | 0.577 | 29.0 |
| 50 | 1.775 | 2.119 | 0.542 | 0.577 | 29.9 |
| 100 | 4.910 | 5.634 | 0.541 | 0.577 | 30.4 |
| 150 | 9.510 | 10.602 | 0.540 | 0.577 | 30.6 |
<!-- /AUTO:p3_losses -->

The model is 10-17 % above the simulated FET loss: it uses the body-diode drop measured at
150 mA/mm, while the real LS carries the current at a lower density. With the ideal 10 ns logic
gaps used here the body diode conducts about 30 ns per period; at 150 mA that is about a third of
the FET loss, which is why the dead time matters for efficiency (section 3).

## 2. Gate drivers and level shifters (`drv_hs`, `drv_ls`, HVL `lsbuflv2hv_1` / `lsbufhv2lv_1`)

Tapered inverter chains on the VIN domain (5 V devices): HS 5 stages (final 256 / 768 um), LS 4 stages.
The LS final pull-down was tripled to 384 um after the HS turn-on dV/dt lifted the LS gate to 0.83 V at
fs / 125 C / 3.6 V (a dV/dt-induced shoot-through risk, D22). Level shifting uses the PDK HVL cells.

<!-- AUTO:p3_driver -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| HS_ON -> HS gate (50 %) | 1.50 .. 3.80 | ns | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| HS off delay | 1.06 .. 2.37 | ns | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| LS_ON -> LS gate | 1.34 .. 3.36 | ns | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| LS off delay | 0.86 .. 1.87 | ns | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| HS gate fall / rise (10-90 %) | 0.81 .. 1.92 / 0.61 .. 1.59 | ns | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| LS gate rise / fall | 0.59 .. 1.33 / 0.27 .. 0.55 | ns | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| Max LS gate bump during HS turn-on (dV/dt) | 0.424 | V | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| Max HS Vsg disturbance while off | 2.2 | mV | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| Max switch-node dV/dt | 21.9 | V/ns | results/phase3/powerstage.json (scripts/char_powerstage.py) |
| Level shifter lv->hv rise / fall | 0.59 .. 1.71 / 0.27 .. 0.52 | ns | results/phase3/levelshift.json (scripts/char_levelshift.py) |
| Level shifter hv->lv rise / fall | 0.22 .. 0.67 / 0.28 .. 0.71 | ns | results/phase3/levelshift.json (scripts/char_levelshift.py) |
<!-- /AUTO:p3_driver -->

## 3. Dead-time generator (`spice/deadtime.spice`)

Adaptive break-before-make: a switch may start to turn on only after a replica-threshold sensor on the
other power gate (`gate_sense`, same device type, so its threshold tracks PVT) confirms it is off; then
(code + 1) programmed taps of ~2 ns are added (`dt_prog`, thermometer select from the RTL). Measured
at the power gates with 0.5 V thresholds (below the device thresholds), for +150 mA and -30 mA inductor
current (the switch node commutates the other way at light load). Plot: `deadtime_pvt.png`.

<!-- AUTO:p3_deadtime -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| Code 0: HS off -> LS on, over PVT | pending | ns | - |
| Code 0: LS off -> HS on, over PVT | pending | ns | - |
| Code 3: HS off -> LS on, over PVT | pending | ns | - |
| Code 3: LS off -> HS on, over PVT | pending | ns | - |
| Code 7: HS off -> LS on, over PVT | pending | ns | - |
| Code 7: LS off -> HS on, over PVT | pending | ns | - |
| Smallest dead time, all runs | pending | ns | - |
| Shoot-through free (dead time > 0 everywhere) | pending | - | - |
<!-- /AUTO:p3_deadtime -->

**Spec deviation (reported, D23).** The brief asks for 2-16 ns programmable. The sensing path adds a
fixed latency, so the shortest dead time is several ns longer than 2 ns. It is the price of making
shoot-through prevention independent of the driver delays at every corner.

## 4. DPWM fine stage and delay-line calibration (`spice/dpwm_fine.spice`, `spice/dpwm_cal.spice`)

Uncalibrated (baseline): 7 taps of 5 x `dlygate4sd3_1`. Standard-cell delay varies 2.85-3.5x over PVT
(`results/phase3/delaycells.json`), so the taps miss the 1.953 ns LSB badly. Calibrated (the design,
D25): a 64-element main line with a 64:1 mux and a 72-element replica line; the controller counts how
many replica elements an edge passes in one clock period (N), averages 16 counts with half-element
hysteresis, and selects tap round(f x N / 8). Plot: `dpwm_dnl_inl_pvt.png` (calibrated vs uncalibrated).

<!-- AUTO:p3_dpwm -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| Uncalibrated: tap / ideal over PVT | 0.639 .. 1.731 | - | results/phase3/dpwm.json (scripts/char_dpwm.py) |
| Uncalibrated: DNL over PVT | -5.12 .. +2.51 | LSB | results/phase3/dpwm.json (scripts/char_dpwm.py) |
| Calibrated: N (elements per clock) over PVT | pending | - | - |
| Calibrated: DNL over PVT | pending | LSB | - |
| Calibrated: INL over PVT | pending | LSB | - |
| Calibrated: largest output step at VIN 3.6 V (PVT) | pending | mV | - |
| Calibrated: DNL sigma, Monte Carlo | pending | LSB | - |
| Calibrated: largest output step at VIN 3.6 V (MC) | pending | mV | - |
| Main vs replica element delay, worst relative difference | pending | % | - |
<!-- /AUTO:p3_dpwm -->

## 5. Window-ADC comparators (`spice/comparator.spice: cmp_hv`)

PMOS-input StrongARM on the VIN rail with 5 V devices (D26), isolation inverters, HV->LV shifters and a
1.8 V NAND SR latch; the controller reads the result two clocks after the sampling edge. Common mode
VOUT/2 = 0.5-1.25 V. A 1.8 V version (`cmp_sa`) is kept as the record: it cannot reach the upper common
mode at cold, low-supply corners, and a low-Vt input pair has 2.4x the mismatch. Plot:
`comparator_offset_hist.png`.

<!-- AUTO:p3_comparator -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| All corners functional at CM 0.5 / 0.9 / 1.25 V, 2 mV overdrive < 31 ns | False | - | results/phase3/comparator.json (scripts/char_comparator.py) |
| Worst clk -> q delay, 2 mV overdrive | 105.31 | ns | results/phase3/comparator.json (scripts/char_comparator.py) |

| Common mode [V] | Offset mean [mV] | Offset sigma [mV] | Range [mV] | Samples |
|---|---|---|---|---|
| 0.33 | +0.04 | 3.48 | -7.25 .. +7.75 | 100 |
| 0.6 | +0.19 | 1.88 | -3.75 .. +4.75 | 100 |
| 0.83 | - | - | fails | 0 |
| -0.1 | - | - | fails | 5 |

<!-- /AUTO:p3_comparator -->

## 6. Switch-node comparators: valley current limit and zero-cross (`sw_cmp`)

VSW is sensed through a 5 V pass device gated by the LS gate (the 1.8 V side never sees VIN) and both
inputs are shifted to ~0.45 V by matched 10 kohm dividers to 0.9 V; the threshold uses an identical
path so the comparator's kickback cancels (D27). The ILIM threshold voltage is an ideal DAC; its
current accuracy is limited by the LS Ron spread over PVT, quantified below.

<!-- AUTO:p3_swcmp -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| Zero-cross: functional over PVT | pending | - | - |
| Zero-cross: systematic offset over PVT (at VSW) | pending | mV | - |
| Zero-cross: shift-network settling (10-90 %) | pending | ns | - |
| Valley limit: functional over PVT | pending | - | - |
| Valley limit: systematic offset over PVT (at VSW) | pending | mV | - |
| Valley limit: shift-network settling (10-90 %) | pending | ns | - |
| Offset sigma at VSW, MC (zc / ilim) | pending | mV | - |
| 250 mA setting: actual valley threshold over the LS Ron PVT spread | pending | mA | - |
<!-- /AUTO:p3_swcmp -->

## 7. Window-ADC reference and front end (`spice/adc_ref.spice`)

One 520-unit `high_po_1p41` string (2.5 mV per unit, 1.3 V top from an ideal reference) gives VREF/2
and the 15 window thresholds at half codes, so the ADC LSB is a resistor ratio. VOUT/2 comes from six
5.7 kohm `xhigh_po_1p41` units with a 10 pF MIM cap; each threshold tap has a 2 pF MIM cap (kickback).
The full front end (divider + 15 comparators + tap impedances) is simulated with a slow VOUT ramp
(`scripts/char_adc.py`).

<!-- AUTO:p3_adc -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| Threshold error sigma from the string (code 100 / 180 / 250) | 0.084 / 0.078 / 0.038 | LSB | results/phase3/adcref.json (scripts/char_adcref.py) |
| Threshold spacing sigma from the string | 0.0107 / 0.0107 / 0.0109 | LSB | results/phase3/adcref.json (scripts/char_adcref.py) |
| Divider ratio sigma | 0.276 | % | results/phase3/adcref.json (scripts/char_adcref.py) |
| Full front end MC (DNL sigma, min, max; zero bin mean / min; samples with missing codes) | pending | - | - |
<!-- /AUTO:p3_adc -->

## 8. Effect on the loop

The measured non-idealities put back into the Phase 1/2 closed-loop golden model
(`scripts/loop_impact.py`): limit cycles are counted at 8 loads per PVT point.

<!-- AUTO:p3_impact -->
| Quantity | Value | Unit | Source |
|---|---|---|---|
| Uncalibrated DPWM: PVT x load cases with a limit cycle | pending | - | - |
| Calibrated DPWM: PVT x load cases with a limit cycle | pending | - | - |
| Comparator offsets: cases with a limit cycle; VOUT error sigma | pending | - | - |
| Comparator offsets: draws with zero bin < DPWM step (7.03 mV) | pending | - | - |
<!-- /AUTO:p3_impact -->

## 9. Not covered here

- Noise: no transient-noise simulation of the comparators (thermal noise adds to the offsets above).
- The VREF and ILIM references are ideal sources (brief: no bandgap). The 0.9 V shift reference too.
- Layout parasitics: Phase 5 (post-layout Ron and switching loss for the power stage).
- Full mixed-signal closed loop with these blocks: Phase 4.
