# Architecture

## 1. Block diagram

```
                VIN 3.0-3.6 V
                    |
             +------+------+            L 15 uH, DCR 0.1 ohm
  pwm_set -->| SR latch +  |--HS gate--+
  pwm_rst -->| delay line  |           |         VSW          VOUT
  tap_sel -->| 64 taps     |       [pfet_g5v0d10v5]--+---ooo---+-------+---- load
  tdc_launch>| replica 72  |-> tdc_therm[71:0] (calibration)
             +-------------+           |             |         |       |
  dt_*_therm->  dead-time + level shifters + tapered drivers   C 10 uF   |
  ls_en ----->                         |             |      ESR 10 mohm  |
                                  [nfet_g5v0d10v5]---+         |       |
                                       |             |        GND      |
                                      GND            |                 |
                         zc_cmp <-- zero-cross cmp --+                 |
                       ilim_cmp <-- valley cmp (VDS of LS) <- ilim_code DAC
                                                                       |
   vref_code -> resistor-string DAC -> VREF -> ladder (+/- 7.5 LSB) ->15 StrongARM <-+
                                                         comparators (adc_sample)
                                                              |
                                                        adc_therm[14:0]
                                                              v
   +----------------------- buck_ctrl_top (rtl/, 64 MHz) ------------------------+
   | therm2bin -> PID (Q5, anti-windup) -> duty -> DPWM (6-bit counter + 3 fine)  |
   | soft-start VREF ramp | mode FSM IDLE/SS/CCM/DCM/FAULT | fault score | APB regs |
   +-------------------------------------------------------------------------------+
```

The analog blocks (power stage, drivers, level shifters, dead-time generator, comparators, delay
line, DAC) are Phase 3. This document fixes the interface between them and the controller.

## 2. Controller timing (one switching period = 64 clocks at 64 MHz)

| Cycle | Event |
|---|---|
| 63 (prev.) | `ilim_sample` high: the valley comparator compares LS VDS against the `ilim_code` threshold |
| edge 0 | the mode and duty decided last period take effect; `pwm_set` is high in cycle 0 unless stopped, duty = 0 or `ilim_cmp` tripped (cycle-by-cycle valley limit); `adc_sample` high: the 15 comparators sample VOUT; `ls_en` = running |
| end of 1 | `adc_therm` registered (two clocks after the sampling edge, for the comparator's cold-corner resolve time); `therm2bin` gives e = -8..+7 |
| 2 | PID products kp*e, ki*e, kd*(e - e[-1]) registered |
| 3 | integrator (held on a trip, clamped to [0, DMAX] << 5), PID sum, rounding, clamp -> next duty; VREF ramp (one code at most); fault score (+3 per trip, -1 otherwise); CCM/DCM counters; mode FSM -> next mode. `vref_code` changes here, so the DAC has about 60 clocks to settle |
| coarse | `pwm_rst` high; the HS turns off after the main delay-line tap `tap_sel` = round(fine x N / 8) |
| 40 | `tdc_launch` rises into the 72-element replica line; its taps are sampled at the end of cycle 40 and counted (N) in cycle 41; every 16 periods N updates if it moved by more than half an element (D25) |
| > coarse | LS phase. In DCM a zero-cross (`zc_cmp`) seen in cycle c drops `ls_en` from cycle c + 1 to the end of the period |

ton = coarse x 15.625 ns + tap_sel x t_element (+ a constant mux/latch offset), with duty =
{coarse[5:0], fine[2:0]} and tap_sel = round(fine x N / 8), so the fine step is Tclk / 8 to within one
element at any PVT. DMAX = 496 (default) leaves at least 31 ns of off-time for dead time.

**Delay from sample to applied duty:** the duty computed from the sample at edge 0 of period k is
applied in period k + 1, a 1 us compute delay. This is the z^-1 in `docs/CONTROL.md`.

**Zero-cross granularity:** the comparator is sampled every clock, so iL can stay negative for up
to about 2 clocks (31 ns) before the LS turns off. That is about 4 mA at the 0.12 A/us down-slope at
1.8 V out (analysis); the measured value is in `docs/RESULTS.md` (Phase 2 DCM test).

## 3. Mode FSM

```
          enable=0 (from any state)
   IDLE ----------------------> IDLE
   IDLE --enable--> SS --VREF reached target--> CCM --dcm_en & 8 periods with zero-cross--> DCM
                                                 CCM <--8 periods without zero-cross, ADC = +7, or !dcm_en-- DCM
   SS/CCM --fault score >= FAULT_N--> FAULT --CTRL.fault_clr--> SS (VREF from 0, PID reset)
   (DCM -> FAULT is unreachable: the valley current is 0 in DCM; an overload exits DCM first, D18)
```

Entering SS from IDLE or FAULT resets VREF to 0, the integrator, e[-1] and all counters.

## 4. Interface and register map (APB3, `pready` always 1)

| Addr | Name | Bits | Reset | Notes |
|---|---|---|---|---|
| 0x00 | CTRL | [0] enable, [1] dcm_en, [8] fault_clr (write 1, reads 0) | 0 | |
| 0x04 | VREF | [7:0] target code, 10 mV/code | 180 | clamped to 100..250 (1.0-2.5 V) |
| 0x08 | KP | [11:0] | 86 | Q5 (x 2^-5), DPWM LSB per ADC LSB |
| 0x0C | KI | [11:0] | 3 | Q5 |
| 0x10 | KD | [11:0] | 1131 | Q5 |
| 0x14 | DT | [2:0] HS-off->LS-on, [6:4] LS-off->HS-on | 3, 3 | dead time (code + 1) x 2 ns; output as a thermometer with code + 1 ones (never 0) |
| 0x18 | ILIM | [7:0] | 125 | valley limit, 2 mA/code (250 mA) |
| 0x1C | SS_LEN | [15:0] | 1000 | VREF reaches its target in SS_LEN periods; minimum 256 |
| 0x20 | DMAX | [8:0] | 496 | maximum DPWM code |
| 0x24 | FAULT_N | [7:0] | 64 | fault score threshold, 0 = never |
| 0x28 | STATUS | [2:0] mode, [7:4] e, [15:8] vref_code, [24:16] duty, [25] hs_en | - | read only |
| 0x2C | ID | 0xB0C40001 | - | read only |
| 0x30 | CAL | [10:0] N x 16 (calibrated delay elements per clock) | 640 | read only |

## 5. Golden model

`model/ctrl_ref.py` (CtrlRef) is the bit-exact specification of everything above. The cocotb
bench compares the RTL against it every period (`tb/bench.py`).
