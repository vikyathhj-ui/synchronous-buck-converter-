"""Golden reference model of the digital controller (rtl/buck_ctrl_top.v must match it bit for bit).

Clock 64 MHz, one switching period = 64 clocks, cycle index cnt = 0..63.

Timing contract for period k (cycle numbers are cnt values in period k):
  cycle 63 of k-1  ilim_sample: valley comparator samples iL (LS still on).
  edge 0           mode_cur, duty_cur become the values decided in period k-1.
                   pwm_set is high in cycle 0 if the converter is running, duty_cur != 0 and the
                   valley comparator did not trip (cycle-by-cycle limit).
                   adc_sample is high in cycle 0: the window ADC samples VOUT at this edge.
  cycle coarse     pwm_rst is high; the analog delay line ends the HS pulse fine_sel taps later.
                   ton = coarse*Tclk + fine*Tclk/8. coarse = 0 with fine > 0 gives a fine-only pulse.
  cycles 1..3      ADC result is registered, the PID computes the next duty, VREF ramps one code,
                   the mode FSM decides the next mode. vref_code changes at the end of cycle 3, so
                   the DAC has the rest of the period to settle before the next sample.
  fault score      +3 for every current-limited period, -1 for every clean one (floor 0, saturates
                   at 255); FAULT when it reaches fault_n. A sustained trip rate above 25 % faults;
                   isolated trips do not. (A consecutive-trip counter never fired in a hard overload,
                   because each suppressed pulse lets the valley fall below the limit.)
  cycles > coarse  LS phase. In DCM a zero-cross (zc_cmp = 1) seen in such a cycle turns LS off
                   from the next cycle until the end of the period. The zc seen in a period is also
                   counted for the CCM <-> DCM decision taken in the next period.

All state updates that the RTL does in cycles 1..3 happen here in one call of period().
"""
from dataclasses import dataclass, field

IDLE, SS, CCM, DCM, FAULT = 0, 1, 2, 3, 4
RUN = (SS, CCM, DCM)
MODE_NAMES = {IDLE: "IDLE", SS: "SS", CCM: "CCM", DCM: "DCM", FAULT: "FAULT"}

FRAC = 5            # PID coefficient fractional bits (DECISIONS D11)
N_ZC = 8            # consecutive periods with / without zero-cross to enter / leave DCM
ADC_MAX = 7         # ADC code at positive saturation (VOUT >= 65 mV below VREF)
VREF_MIN, VREF_MAX = 100, 250   # allowed VREF register range (1.0 .. 2.5 V)
SS_LEN_MIN = 256    # at most one VREF code per period
CNT_SAT = 255       # 8-bit saturating counters
TRIP_UP, TRIP_DN = 3, 1   # fault score: +3 per current-limited period, -1 per clean period


@dataclass
class Regs:
    enable: int = 0
    dcm_en: int = 0
    vref: int = 180
    kp: int = 86
    ki: int = 3
    kd: int = 1131
    dt_hl: int = 3       # dead time HS off -> LS on = (code + 1) * 2 ns
    dt_lh: int = 3       # dead time LS off -> HS on
    ilim: int = 125      # valley current limit = code * 2 mA
    ss_len: int = 1000   # VREF ramp: target code reached in ss_len periods
    dmax: int = 496      # maximum DPWM code (leaves >= 16 taps of off-time for dead time)
    fault_n: int = 64    # FAULT when the trip score reaches this (0 = never)

    def write(self, name, value):
        """Register write with the same clamping as the RTL."""
        if name == "vref":
            value = min(max(value & 0xFF, VREF_MIN), VREF_MAX)
        elif name == "ss_len":
            value = max(value & 0xFFFF, SS_LEN_MIN)
        elif name == "dmax":
            value = value & 0x1FF
        elif name in ("kp", "ki", "kd"):
            value = value & 0xFFF
        elif name in ("dt_hl", "dt_lh"):
            value = value & 0x7
        elif name in ("ilim", "fault_n"):
            value = value & 0xFF
        elif name in ("enable", "dcm_en"):
            value = value & 1
        setattr(self, name, value)


def therm_decode(therm):
    """15-bit thermometer -> signed ADC code with 3-input majority bubble correction.

    therm bit i = 1 when (VREF - VOUT) >= (i - 7.5) * LSB. Out-of-range neighbours: bit -1 = 1, bit 15 = 0.
    """
    bits = [(therm >> i) & 1 for i in range(15)]
    ext = [1] + bits + [0]
    corr = [1 if ext[i] + ext[i + 1] + ext[i + 2] >= 2 else 0 for i in range(15)]
    return sum(corr) - 8


def therm_encode(err, lsb=0.010):
    """Ideal comparators: thermometer word for an error voltage (VREF - VOUT)."""
    w = 0
    for i in range(15):
        if err >= (i - 7.5) * lsb:
            w |= 1 << i
    return w


@dataclass
class CtrlRef:
    regs: Regs = field(default_factory=Regs)
    frac: int = FRAC
    dpwm_bits: int = 9

    def __post_init__(self):
        self.mode = IDLE
        self.vref_code = 0
        self.ss_acc = 0
        self.acc = 0
        self.e1 = 0
        self.duty_cur = 0
        self.trip_run = 0
        self.zc_run = 0
        self.nzc_run = 0
        self.fault_clr = False

    # ---- PID (identical integer arithmetic to rtl/pid.v) ----
    def _pid(self, e, hold):
        r, F = self.regs, self.frac
        hi = r.dmax << F
        if not hold:
            self.acc = min(max(self.acc + r.ki * e, 0), hi)
        s = r.kp * e + self.acc + r.kd * (e - self.e1)
        self.e1 = e
        u = (s + (1 << (F - 1))) >> F if F > 0 else s
        return min(max(u, 0), r.dmax)

    def _reset_loop(self):
        self.acc = 0
        self.e1 = 0
        self.vref_code = 0
        self.ss_acc = 0
        self.trip_run = 0
        self.zc_run = 0
        self.nzc_run = 0

    def period(self, e, trip, zc_prev):
        """Advance one switching period.

        e       : ADC code sampled at edge 0 of this period (therm_decode of the comparators)
        trip    : valley comparator sampled in cycle 63 of the previous period
        zc_prev : a qualified zero-cross was seen during the previous period
        Returns the controls that are in force during THIS period plus the VREF code that the DAC
        takes at the end of cycle 3 (and that the next sample will see).
        """
        r = self.regs
        mode = self.mode
        running = mode in RUN
        duty = min(self.duty_cur, r.dmax)     # re-clamped at the period boundary (DMAX may change)
        hs_en = running and duty != 0 and not trip
        out = {"mode": mode, "hs_en": hs_en, "duty": duty if hs_en else 0,
               "ls_en": running, "dcm": mode == DCM}

        d_next = 0
        if running:
            self.trip_run = min(self.trip_run + TRIP_UP, CNT_SAT) if trip else max(self.trip_run - TRIP_DN, 0)
            if mode == CCM:
                self.zc_run = min(self.zc_run + 1, CNT_SAT) if zc_prev else 0
            if mode == DCM:
                self.nzc_run = min(self.nzc_run + 1, CNT_SAT) if not zc_prev else 0
            d_next = self._pid(e, trip)
            # VREF ramp toward the target, at most one code per period
            if self.vref_code != r.vref:
                self.ss_acc += r.vref
                if self.ss_acc >= r.ss_len:
                    self.ss_acc -= r.ss_len
                    self.vref_code += 1 if self.vref_code < r.vref else -1
            else:
                self.ss_acc = 0

        # mode FSM
        nxt = mode
        if not r.enable:
            nxt = IDLE
        elif mode == IDLE:
            nxt = SS
        elif mode == FAULT:
            if self.fault_clr:
                nxt = SS
        elif r.fault_n and self.trip_run >= r.fault_n:
            nxt = FAULT
        elif mode == SS:
            if self.vref_code == r.vref:
                nxt = CCM
        elif mode == CCM:
            if r.dcm_en and self.zc_run >= N_ZC:
                nxt = DCM
        elif mode == DCM:
            # leave DCM after N_ZC periods without zero-cross, or at once when VOUT is so low that the
            # ADC saturates (+7): otherwise a heavy load keeps the duty small, the current still
            # returns to zero each period, and the converter stays in DCM while VOUT collapses
            if not r.dcm_en or self.nzc_run >= N_ZC or e >= ADC_MAX:
                nxt = CCM
        self.fault_clr = False

        if nxt != mode:
            if nxt in (IDLE, FAULT) or (nxt == SS and mode in (IDLE, FAULT)):
                self._reset_loop()
                d_next = 0
            if nxt == DCM:
                self.nzc_run = 0
            if nxt == CCM:
                self.zc_run = 0
        if nxt not in RUN:
            d_next = 0
        self.mode = nxt
        self.duty_cur = d_next
        out["vref_code"] = self.vref_code
        return out
