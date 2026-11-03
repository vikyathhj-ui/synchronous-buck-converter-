"""Small helper for the Phase 3 characterisation scripts (run inside iic-osic).

Every number reported by a char_*.py script is parsed from ngspice output by this module; the
netlists are written to results/phase3/work/ (git-ignored) so any run can be reproduced by hand.
"""
import json
import os
import pathlib
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / "results" / "phase3" / "work"
OUT = ROOT / "results" / "phase3"
PDK = pathlib.Path(os.environ.get("PDK_ROOT", "/foss/pdks")) / os.environ.get("PDK", "sky130A")
LIB_FULL = PDK / "libs.tech" / "ngspice" / "sky130.lib.spice"
LIB = ROOT / "spice" / "models" / "sky130_mini.lib"   # scripts/make_minilib.py
HVL = PDK / "libs.ref" / "sky130_fd_sc_hvl" / "spice" / "sky130_fd_sc_hvl.spice"
SPICE_DIR = ROOT / "spice"

CORNERS = ["tt", "ff", "ss", "sf", "fs"]
TEMPS = [-40, 27, 125]
VINS = [3.0, 3.3, 3.6]
PVT = [(c, t, v) for c in CORNERS for t in TEMPS for v in VINS]

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def header(corner="tt", temp=27, mc=False, title="netlist", full=False):
    lines = [f"* {title}", f".lib {LIB_FULL if full else LIB} {corner}"]
    if mc:
        lines.append(".param mc_mm_switch=1")
    lines.append(f".temp {temp}")
    lines.append(".option savecurrents=0 klu")
    return "\n".join(lines) + "\n"


def include(*names):
    return "".join(f".include {SPICE_DIR / n}\n" for n in names)


SPICEINIT = """* written by scripts/spicelib.py: one thread per ngspice, because the scripts run several
* ngspice processes in parallel (the container default num_threads=8 oversubscribes the CPU)
set ngbehavior=hsa
set skywaterpdk
set ng_nomodcheck
set num_threads=1
option noinit
option klu
"""


def with_save(netlist):
    """Insert a `save` line before the first analysis in the .control block listing only the
    vectors the measurements use (v(...) and i(...)); by default ngspice keeps every node of a
    long transient in memory, which ran the machine out of memory with parallel jobs."""
    if ".control" not in netlist:
        return netlist
    head, ctl = netlist.split(".control", 1)
    vecs = sorted(set(re.findall(r"\b([vi]\([^()=]+\))", ctl)))
    if not vecs:
        return netlist
    lines = ctl.split("\n")
    for k, line in enumerate(lines):
        if re.match(r"\s*(tran|op|dc|ac)\b", line):
            lines.insert(k, "save " + " ".join(vecs))
            break
    return head + ".control" + "\n".join(lines)


def _includes_newer(netlist, log):
    """True if a repo netlist included by `netlist` changed after `log` was written: a reused log
    must have been simulated with the current subcircuits. (The model library is not checked: its
    only change added LVT models, which the reused runs do not use; DECISIONS D28.)"""
    t = log.stat().st_mtime
    for inc in re.findall(r"^\.include\s+(\S+)", netlist, re.M):
        pth = pathlib.Path(inc)
        if SPICE_DIR in pth.parents and pth.exists() and pth.stat().st_mtime > t:
            return True
    return False


def run(netlist, tag, timeout=1800):
    """Run ngspice -b on `netlist`; return dict of every 'name = value' line in the output."""
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / ".spiceinit").write_text(SPICEINIT)
    f = WORK / f"{tag}.spice"
    log = WORK / f"{tag}.log"
    full = with_save(netlist)
    # SPICE_REUSE=1: parse an existing log if its netlist is unchanged (recovers results after a
    # crash in the post-processing without re-simulating; logs from before the save-line change count)
    if (os.environ.get("SPICE_REUSE") == "1" and log.exists() and f.exists()
            and f.read_text() in (netlist, full) and not _includes_newer(netlist, log)):
        out = log.read_text()
    else:
        log.unlink(missing_ok=True)  # a killed run must not leave an old log beside the new netlist
        f.write_text(full)
        p = subprocess.run(["ngspice", "-b", str(f)], cwd=WORK, capture_output=True, text=True, timeout=timeout)
        out = p.stdout + p.stderr
        log.write_text(out)
    vals = {}
    for m in re.finditer(rf"^\s*([A-Za-z_][\w\[\]().#]*)\s*=\s*({_NUM})", out, re.M):
        vals[m.group(1).lower()] = float(m.group(2))
    if "error" in out.lower() and not vals:
        raise RuntimeError(f"ngspice failed for {tag}: see {WORK / (tag + '.log')}")
    return vals


def pmap(fn, items, workers=3):
    # SPICE_WORKERS overrides the default for light runs (~150 MB each); keep 3 for char_adc.py
    workers = int(os.environ.get("SPICE_WORKERS", workers))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))


def save(block, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{block}.json").write_text(json.dumps(data, indent=1, default=float) + "\n")
