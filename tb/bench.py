"""Closed-loop cocotb bench: RTL controller + per-clock Python plant + golden-model scoreboard.

Every clock (at the falling edge, when the RTL outputs for that cycle are stable):
  * the plant (model/buck.py: ClockPlant) is advanced by one clock with the RTL's pwm_set,
    pwm_rst, tap_sel (x t_elem) and ls_en;
  * the comparators are driven from the plant state at that cycle's rising edge:
    window ADC (cycle 0), valley current limit (cycle 63), zero-cross (every cycle).
Every period the scoreboard runs model/ctrl_ref.py: CtrlRef with the same ADC code, trip,
zero-cross history and TDC count and checks, bit for bit: mode, HS enable, LS enable, coarse duty,
delay-line tap, VREF code.
Delay line: element delay t_elem (default Tclk/40, which gives the ideal 1.953 ns fine step); the
replica-line TDC is driven with N = floor(Tclk / t_elem) ones; the HS turns off tap_sel * t_elem
after the pwm_rst edge. set_t_elem() changes it during a run (temperature drift).
"""
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge
from cocotb_coverage.coverage import CoverPoint, coverage_db

from model.buck import ClockPlant, Dpwm
from model.ctrl_ref import CtrlRef, Regs, therm_decode, therm_encode
from model.sim import ADC_LSB, ILIM_LSB, VREF_LSB

TCLK_NS = 15.625
ADDR = dict(ctrl=0x00, vref=0x04, kp=0x08, ki=0x0C, kd=0x10, dt=0x14, ilim=0x18, ss_len=0x1C, cal=0x30,
            dmax=0x20, fault_n=0x24, status=0x28, id=0x2C)
# DCM -> FAULT is unreachable: the valley current is 0 in DCM, so the limit cannot trip (DECISIONS D18)
TRANSITIONS = [(0, 1), (1, 2), (2, 3), (3, 2), (1, 4), (2, 4), (4, 1), (1, 0), (2, 0), (3, 0), (4, 0)]


@CoverPoint("ctrl.mode", xf=lambda s: s["mode"], bins=[0, 1, 2, 3, 4])
@CoverPoint("ctrl.transition", xf=lambda s: (s["prev_mode"], s["mode"]), bins=TRANSITIONS)
@CoverPoint("ctrl.adc_code", xf=lambda s: s["e"], bins=list(range(-8, 8)))
@CoverPoint("ctrl.fine_sel", xf=lambda s: s["fine"], bins=list(range(8)))
@CoverPoint("ctrl.coarse", xf=lambda s: s["coarse"], bins=["0", "1-15", "16-31", "32-47", "48-62"],
            rel=lambda v, b: v is not None and (str(v) == b if "-" not in b else
                                                  int(b.split("-")[0]) <= v <= int(b.split("-")[1])))
@CoverPoint("ctrl.trip", xf=lambda s: s["trip"], bins=[False, True])
@CoverPoint("ctrl.zc_seen", xf=lambda s: s["zc"], bins=[False, True])
@CoverPoint("ctrl.dcm_cut", xf=lambda s: s["cut"], bins=[False, True])
def sample_coverage(s):
    pass


class Bench:
    def __init__(self, dut, buck, dpwm=None, io_fn=None, vin_fn=None, dense_from=None, dense_to=None,
                 t_elem=None):
        self.dut = dut
        self.b = buck
        self.dpwm = dpwm or Dpwm(t_elem=t_elem if t_elem is not None else TCLK_NS * 1e-9 / 40)
        self.plant = ClockPlant(buck, self.dpwm)
        self.ref = CtrlRef(Regs())
        self.io_fn = io_fn or (lambda t: 0.0)
        self.vin_fn = vin_fn or (lambda t: buck.vin)
        self.io_extra = 0.0             # added by tests (e.g. remove an overload after a fault)
        self.dense_from, self.dense_to = dense_from, dense_to
        self.k = 0
        self.trip = False
        self.zc_prev = False
        self.vref_dac = 0
        self.prev_mode = 0
        self.writes = []
        self.mismatches = []
        self.n_prev = self.dpwm.n_meas()
        self.rec = {k: [] for k in ("t", "v", "e", "duty", "mode", "trip", "vref", "ilv", "ilp", "ilmin",
                                    "vmin", "vmax", "zc", "cut_cycle")}
        self.dense = []
        self._drv = {}

    # ------------------------------------------------------------------ helpers
    def _set(self, name, value):
        if self._drv.get(name) != value:
            getattr(self.dut, name).value = value
            self._drv[name] = value

    async def start(self):
        d = self.dut
        Clock(d.clk, TCLK_NS, unit="ns").start()
        for n in ("psel", "penable", "pwrite", "paddr", "pwdata", "adc_therm", "ilim_cmp", "zc_cmp"):
            self._set(n, 0)
        self._set("tdc_therm", (1 << self.dpwm.n_meas()) - 1)
        d.rst_n.value = 0
        await ClockCycles(d.clk, 5)
        await FallingEdge(d.clk)
        d.rst_n.value = 1
        # align to cycle 0 of a period
        while True:
            await FallingEdge(d.clk)
            if int(d.adc_sample.value):
                break

    def set_t_elem(self, t_elem):
        """Change the delay-element delay (both lines); the TDC sees it from the next cycle 40."""
        from dataclasses import replace as _r
        self.dpwm = _r(self.dpwm, t_elem=t_elem)

    def write(self, name, value):
        """Queue an APB write; it is issued in cycles 8..10 of the next period and mirrored into
        the golden model after that period's update (the RTL consumes it in the period after)."""
        self.writes.append((name, value))

    def _apply_model_write(self, name, value):
        r = self.ref.regs
        if name == "ctrl":
            r.write("enable", value & 1)
            r.write("dcm_en", (value >> 1) & 1)
            if value & 0x100:
                self.ref.fault_clr = True
        elif name == "dt":
            r.write("dt_hl", value & 7)
            r.write("dt_lh", (value >> 4) & 7)
        else:
            r.write(name, value)

    # ------------------------------------------------------------------ main loop
    async def run(self, n_periods):
        for _ in range(n_periods):
            await self._period()

    async def _period(self):
        d, p, ref = self.dut, self.plant, self.ref
        Ts = self.b.Ts
        t0 = self.k * Ts
        io = self.io_fn(t0) + self.io_extra
        vin = self.vin_fn(t0)

        # cycle 0: ADC samples VOUT at this period's first edge
        v = p.vout(io)
        therm = therm_encode(self.vref_dac * VREF_LSB - v, ADC_LSB)
        self._set("adc_therm", therm)
        e = therm_decode(therm)
        out = ref.period(e, self.trip, self.zc_prev, self.n_prev)

        mode_rtl = int(d.mode.value)
        set_rtl = int(d.pwm_set.value)
        exp_coarse = out["duty"] >> 3 if out["hs_en"] else None
        exp_fine = out["duty"] & 7 if out["hs_en"] else None
        exp_tap = out["tap_sel"] if out["hs_en"] else None
        coarse_eff = exp_coarse if out["hs_en"] else 0
        errs = []
        if mode_rtl != out["mode"]:
            errs.append(f"mode rtl={mode_rtl} ref={out['mode']}")
        if set_rtl != int(out["hs_en"]):
            errs.append(f"pwm_set rtl={set_rtl} ref={int(out['hs_en'])}")

        write = self.writes.pop(0) if self.writes else None
        coarse_obs, fine_obs = None, None
        zc_seen, cut_cycle = False, None
        ilv, ilp, ilmin = 0.0, -1e9, 1e9
        vmin, vmax = 1e9, -1e9
        vref_rtl = None
        want_dense = self.dense_from is not None and self.dense_from <= t0 < self.dense_to

        for c in range(64):
            prst = int(d.pwm_rst.value)
            lsen = int(d.ls_en.value)
            if c == 0 and lsen != int(out["ls_en"]):
                errs.append(f"ls_en rtl={lsen} ref={int(out['ls_en'])}")
            fdel = 0.0
            if prst:
                tap = int(d.tap_sel.value)
                fdel = tap * self.dpwm.t_elem
                if coarse_obs is None:
                    coarse_obs, fine_obs = c, tap
            if out["dcm"] and cut_cycle is None and c > 0 and not lsen:
                cut_cycle = c
            # zero-cross comparator: VSW > 0 while the LS conducts means iL < 0
            zc = (not p.hs) and bool(lsen) and p.il < 0
            self._set("zc_cmp", int(zc))
            if zc and c > coarse_eff:
                zc_seen = True
            if c == 63:
                ilv = p.il
                self._set("ilim_cmp", int(ilv > int(d.ilim_code.value) * ILIM_LSB))
            if write is not None:
                name, value = write
                if c == 8:
                    self._set("paddr", ADDR[name])
                    self._set("pwdata", value)
                    self._set("pwrite", 1)
                    self._set("psel", 1)
                elif c == 9:
                    self._set("penable", 1)
                elif c == 10:
                    self._set("psel", 0)
                    self._set("penable", 0)
                    self._set("pwrite", 0)
            if c == 12:
                vref_rtl = int(d.vref_code.value)
            if c == 40:
                n_now = self.dpwm.n_meas()
                self._set("tdc_therm", (1 << n_now) - 1)
            p.clock(set_rtl if c == 0 else 0, prst, fdel, lsen, vin, io)
            vc = p.vout(io)
            vmin, vmax = min(vmin, vc), max(vmax, vc)
            ilp, ilmin = max(ilp, p.il), min(ilmin, p.il)
            if want_dense:
                self.dense.append((t0 + (c + 1) * TCLK_NS * 1e-9, vc, p.il))
            await FallingEdge(d.clk)

        if out["hs_en"]:
            if (coarse_obs, fine_obs) != (exp_coarse, exp_tap):
                errs.append(f"duty/tap rtl=({coarse_obs},{fine_obs}) ref=({exp_coarse},{exp_tap})")
        elif coarse_obs is not None:
            errs.append(f"pwm_rst while HS disabled (cycle {coarse_obs})")
        if vref_rtl != out["vref_code"]:
            errs.append(f"vref rtl={vref_rtl} ref={out['vref_code']}")
        if errs:
            self.mismatches.append((self.k, errs))
            if len(self.mismatches) <= 5:
                self.dut._log.error(f"period {self.k}: " + "; ".join(errs))

        if write is not None:
            self._apply_model_write(*write)
        self.trip = ilv > self.ref.regs.ilim * ILIM_LSB
        self.n_prev = n_now
        self.zc_prev = zc_seen
        self.vref_dac = vref_rtl

        sample_coverage({"mode": out["mode"], "prev_mode": self.prev_mode, "e": e,
                         "fine": exp_fine if exp_fine is not None else -1, "coarse": exp_coarse,
                         "trip": bool(self.trip), "zc": zc_seen, "cut": cut_cycle is not None})
        self.prev_mode = out["mode"]
        for key, val in (("t", t0), ("v", v), ("e", e), ("duty", out["duty"]), ("mode", out["mode"]),
                         ("trip", self.trip), ("vref", vref_rtl), ("ilv", ilv), ("ilp", ilp),
                         ("ilmin", ilmin), ("vmin", vmin), ("vmax", vmax), ("zc", zc_seen),
                         ("cut_cycle", cut_cycle if cut_cycle is not None else -1)):
            self.rec[key].append(val)
        self.k += 1

    def arrays(self):
        return {k: np.array(v) for k, v in self.rec.items()}


def export_coverage(path):
    coverage_db.export_to_yaml(filename=str(path))
    return {k: coverage_db[k].cover_percentage for k in coverage_db if k.count(".") == 1}
