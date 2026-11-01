# Learning notes

## Phase 0
- A plain `docker exec` does not load the tool environment; `bash -lc` is required.
- ngspice `d_cosim` loads a shared library built by `vlnggen` (Verilator). Verilog vector ports appear
  as separate digital nodes, most-significant bit first.
- Digital nodes need `adc_bridge` / `dac_bridge` to connect to analog nodes.

## Phase 1
- The digital loop's plant is the *sampled* model, not the averaged Gvd(s). With trailing-edge PWM and
  sampling at the period start, the duty perturbation acts at D*Ts and propagates for (1-D)*Ts. Above
  about 50 kHz the sampled phase falls well below the averaged phase (bode.png, left).
- A PID designed in the z-domain can be solved directly. Fixing ki = alpha*kp makes C(z0) linear in
  (kp, kd), so the gain and phase conditions give a 2x2 linear system.
- A limit cycle needs a missing output level inside the ADC zero bin. A 6-bit DPWM (52 mV step) limit
  cycles at most loads; the 9-bit hybrid (6.4 mV step) at none, as long as the delay line is accurate.
- Delay-line error turns into DPWM DNL at every coarse boundary: 7*(1 - tap_scale) LSB.
- A large kd on a quantised error gives one-period duty kicks every time the ADC code changes.
- A bug I nearly reported as a result: rescaling the gains for a 6-bit DPWM made ki round to 0 at
  2 fractional bits. That removed the integrator and with it any chance of a limit cycle.
