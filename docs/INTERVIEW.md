# Interview questions

Target: 40+ questions with answers that use this project's numbers (from `results/summary.json`).
Answers are added as each phase produces numbers. Required topics (from `docs/BRIEF.md`):
volt-second balance; choosing L and C; CCM vs DCM; synchronous rectification; dead time vs
shoot-through vs body-diode loss; averaged model and LC double pole; ADC/DPWM delay and phase;
z-domain PID; limit-cycle condition; hybrid DPWM and delay-line PVT; StrongARM operation and offset;
loss breakdown; why 5 V devices; level shifting; valley vs peak current limit.

Numbers below come from `results/summary.json` (phase1), produced by `python3 -m model.phase1`.

### Q1. Derive the buck duty cycle from volt-second balance.
In steady state the inductor's average voltage over a period is zero. During the on-time it sees
VIN - VOUT - rs*IL; during the off-time it sees -VOUT - rs*IL. So D(VIN) = VOUT + rs*IL. With
VIN 3.3 V, VOUT 1.8 V, IL 150 mA and rs = 0.6 ohm (DCR 0.1 + an assumed Ron 0.5), D = 0.5727.

### Q2. How did you choose L and C?
L sets the current ripple: dI = (VIN - VOUT)*D*Ts/L = 57 mA p-p at full load with 15 uH (about 38 %
of 150 mA, in the usual 20–40 % band). C plus ESR sets the voltage ripple: dI/(8 fsw C) = 0.72 mV
plus ESR*dI = 0.57 mV, far below the 18 mV spec. C also sets the load-step undershoot, roughly
dI_step/(2 pi fc C) = 0.135/(2 pi 30e3 10e-6) = 72 mV (analysis) at the 30 kHz crossover, against
66 mV from the switched model.

### Q3. What is the control-to-output transfer function, and where is the double pole?
Gvd(s) = VIN (1 + s ESR C) / (LC s^2 + s(L/R + C(rs+ESR)) + 1 + rs/R) (current-source load: R to
infinity). The LC double pole is at 1/(2 pi sqrt(LC)) = 13.0 kHz; the ESR zero is at 1.59 MHz, so
it does nothing for phase at crossover. Above f0 the plant falls 40 dB/dec with phase heading
to -180 deg.

### Q4. Why does the ADC/compute delay cost phase, and how much?
A delay of T costs 360*f*T degrees at frequency f. Here the duty is computed from the sample at
the start of one period and applied in the next: 1 us is 18 deg at 50 kHz. On top of that, the
trailing-edge modulator responds at D*Ts and the effect is sampled one period later. That is why the
sampled plant's phase at 50 kHz is far below the averaged model's (bode.png).

### Q5. How did you design the PID in the z-domain?
The PID is C(z) = kp + ki/(1 - z^-1) + kd(1 - z^-1). I fixed ki = alpha*kp so the integral zero
sits at fc/5. Then C at z0 = e^{j w_c Ts} is linear in kp and kd. Setting |L| = 1 and angle
L = -180 + PM at fc gives two real equations, solved directly. The final design is fc = 30 kHz,
PM = 60 deg: kp = 2.70, ki = 0.102, kd = 35.4 (DPWM LSB per ADC LSB), giving fc = 30.1 kHz,
PM = 60.2 deg and GM = 14.2 dB after quantisation to Q5.

### Q6. State the no-limit-cycle conditions and show your design meets them.
(1) The DPWM step at the output must be smaller than the ADC bin: 3.6 V/512 = 7.0 mV < 10 mV at the
worst VIN. (2) There must be integral action with a normalised gain of at most 1:
Ki_n = (3/32)*7.03/10 = 0.066. (3) The linear loop must be stable. Evidence: 10 ms of steady state at
3 VIN x 3 loads gave one duty code every time. A 6-bit DPWM (52 mV step) with the same loop limit
cycles at 12 of 15 loads.

### Q7. What does delay-line error do to a hybrid DPWM?
If the taps are off by a factor s, the step across each coarse boundary is (8 - 7s) LSB, so the
DNL is 7(1 - s) LSB. Slow taps (s < 1) leave a gap; fast taps (s > 1) make the DPWM non-monotonic.
In the model, tap errors of -20 % / +20 % gave a limit cycle at 1 / 0 of 15 loads, and
-40 % / +40 % at 3 / 3 of 15. That is the argument for calibrating the delay line against the clock period.

### Q8. Why did you choose the coefficient word length the way you did?
I swept the fractional bits from 0 to 10 and recomputed fc, PM and the closed-loop poles each time.
I picked the smallest word length with dPM < 1 deg, dfc < 2 % and every coefficient within 10 %: Q5,
giving kp = 86, ki = 3, kd = 1131 (x 2^-5). Without the 10 % rule, Q3 passes on margins alone with ki
23 % high. The margins barely notice ki because the integral zero is far below crossover, but the
integral tail and Ki_n do.

### Q9. Is your loop robust?
That was a requirement: PM >= 45 deg at every corner of VIN 3.0–3.6 V, L and C +/-20 % (assumed
tolerance), Ron 0.25–1 ohm and load 15–150 mA, 162 cases in all. My first design (50 kHz, 50 deg)
fell to 28 deg at the L -20 % / C -20 % corner, because the gain above resonance scales with 1/(LC).
Lowering the crossover to 30 kHz with a 60 deg target gives a 48.7 deg worst case. The cost is
undershoot (49 -> 66 mV, spec 90) and a larger line-step deviation (about +/-170 mV for a 0.6 V
VIN step in 10 us).

