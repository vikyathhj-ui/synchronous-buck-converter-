#!/usr/bin/env python3
"""Check every standard-cell instance in spice/*.spice against the PDK .subckt pin list:
power pins (VGND/VNB/VPB/VPWR/LVPWR) must connect to supply nets. Catches swapped pin orders,
which simulate without any error message. Exit code 1 on any problem.
"""
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDK = pathlib.Path(os.environ.get("PDK_ROOT", "/foss/pdks")) / os.environ.get("PDK", "sky130A")
LIBS = [PDK / "libs.ref" / l / "spice" / f"{l}.spice" for l in ("sky130_fd_sc_hd", "sky130_fd_sc_hvl")]
SUPPLY = re.compile(r"^(0|gnd|vss|vdd|vin|vdrv|vlv|vsh|vinp|vpwr|lvpwr)$", re.I)
GROUND = re.compile(r"^(0|gnd|vss)$", re.I)

pins = {}
for lib in LIBS:
    for m in re.finditer(r"^\.subckt\s+(\S+)\s+(.+)$", lib.read_text(), re.M):
        pins[m.group(1)] = m.group(2).split()

bad = 0
checked = 0
for f in sorted((ROOT / "spice").glob("*.spice")):
    for ln, line in enumerate(f.read_text().splitlines(), 1):
        tok = line.split()
        if not tok or not tok[0].upper().startswith("X"):
            continue
        cell = next((t for t in tok[1:] if t.startswith("sky130_fd_sc_")), None)
        if cell is None:
            continue
        nets = tok[1:tok.index(cell)]
        exp = pins.get(cell)
        checked += 1
        if exp is None or len(exp) != len(nets):
            print(f"{f.name}:{ln}: {cell}: {len(nets)} nets, expected {exp}")
            bad += 1
            continue
        for p, n in zip(exp, nets):
            if p in ("VGND", "VNB") and not GROUND.match(n):
                print(f"{f.name}:{ln}: {cell} pin {p} on net '{n}' (expected ground)"); bad += 1
            elif p in ("VPB", "VPWR", "LVPWR") and not SUPPLY.match(n):
                print(f"{f.name}:{ln}: {cell} pin {p} on net '{n}' (expected supply)"); bad += 1
            elif p not in ("VGND", "VNB", "VPB", "VPWR", "LVPWR") and SUPPLY.match(n) and not GROUND.match(n):
                print(f"{f.name}:{ln}: {cell} signal pin {p} on supply net '{n}'"); bad += 1
print(f"checked {checked} standard-cell instances, {bad} problems")
sys.exit(1 if bad else 0)
