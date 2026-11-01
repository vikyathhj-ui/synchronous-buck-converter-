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
plus ESR*dI = 0.57 mV, far below the 18 mV spec. C also sets the load-step undershoot: roughly
dI_step/(2 pi fc C) = 0.135/(2 pi 50e3 10e-6) = 43 mV (analysis), against 49 mV from the switched
model.

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
L = -180 + 50 deg at 50 kHz gives two real equations, solved directly. The result is
kp = 4.45, ki = 0.280, kd = 68.2 (DPWM LSB per ADC LSB), giving fc = 50.2 kHz, PM = 49.9 deg and
GM = 8.6 dB after quantisation to Q2.

### Q6. State the no-limit-cycle conditions and show your design meets them.
(1) The DPWM step at the output must be smaller than the ADC bin: 3.6 V/512 = 7.0 mV < 10 mV at the
worst VIN. (2) There must be integral action with a normalised gain of at most 1:
Ki_n = 0.25*7.03/10 = 0.18. (3) The linear loop must be stable. Evidence: 10 ms of steady state at
3 VIN x 3 loads gave one duty code every time. A 6-bit DPWM (52 mV step) with the same loop limit
cycles at 13 of 15 loads.

### Q7. What does delay-line error do to a hybrid DPWM?
If the taps are off by a factor s, the step across each coarse boundary is (8 - 7s) LSB, so the
DNL is 7(1 - s) LSB. Slow taps (s < 1) leave a gap; fast taps (s > 1) make the DPWM non-monotonic.
In the model, +/-20 % tap error gave a limit cycle at 1 of 15 loads and +/-40 % at 4 of 15. That is
the argument for calibrating the delay line against the clock period.

### Q8. Why did you choose the coefficient word length the way you did?
I swept the fractional bits from 0 to 10 and recomputed fc, PM and the closed-loop poles each time.
With 0 bits, ki rounds to 0: no integrator, and the pole sits at z = 1. Q2 is the smallest word length
with dPM < 1 deg and dfc < 2 %. ki is then 0.25 against 0.28, but the integral zero is far below
crossover, so the margins barely move.

### Q9. Is your loop robust?
Over VIN 3.0–3.6 V and 15–150 mA, PM is 48–52 deg. With L and C at +/-20 % (my assumed tolerance),
PM falls to 33.5 deg at L = 12 uH, C = 8 uF, and to 28 deg when that is combined with VIN 3.6 V.
The reason is that 1/(LC) rises 1.56x, which pushes crossover to 83 kHz. Every case is still stable,
but that corner misses 45 deg; I documented it rather than hide it.
