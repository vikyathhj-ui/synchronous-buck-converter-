#!/usr/bin/env python3
"""Generate xschem schematics (.sch) and symbols (.sym) from the SPICE subcircuits in spice/.

Each instance is placed on a grid with its PDK symbol (sky130_fd_pr devices, sky130_stdcells) or
the generated symbol of another subcircuit; every pin gets a net label (lab_pin) at the pin
position, and every subcircuit port an iopin. No wires are drawn; connectivity is by net name.
The schematics are checked by scripts/lvs_xschem.sh: xschem netlists them and netgen compares
the result with the hand-written SPICE (LVS netlist vs netlist).
Run inside iic-osic: python3 scripts/gen_xschem.py
"""
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPICE = ROOT / "spice"
OUT = ROOT / "xschem"
PDK = pathlib.Path(os.environ.get("PDK_ROOT", "/foss/pdks")) / os.environ.get("PDK", "sky130A")
XLIB = PDK / "libs.tech" / "xschem"
SHARE = pathlib.Path("/foss/tools/xschem/share/xschem/xschem_library")
FILES = ["powerstage.spice", "deadtime.spice", "comparator.spice", "dpwm_fine.spice", "dpwm_cal.spice",
         "adc_ref.spice"]
HEADER = "v {xschem version=3.4.7RC file_version=1.2}\nG {}\nK {}\nV {}\nS {}\nE {}\n"
POWER = ("VGND", "VNB", "VPB", "VPWR", "LVPWR")


def logical_lines(text):
    out = []
    for line in text.splitlines():
        line = line.split(";")[0].rstrip()
        if not line or line.startswith("*"):
            continue
        if line.startswith("+") and out:
            out[-1] += " " + line[1:]
        else:
            out.append(line)
    return out


def parse_subckts():
    subs = {}
    for f in FILES:
        cur = None
        for line in logical_lines((SPICE / f).read_text()):
            tok = line.split()
            if tok[0].lower() == ".subckt":
                ports = [t for t in tok[2:] if "=" not in t]
                params = dict(t.split("=", 1) for t in tok[2:] if "=" in t)
                cur = {"name": tok[1], "ports": ports, "params": params, "inst": [], "file": f}
                subs[tok[1]] = cur
            elif tok[0].lower() == ".ends":
                cur = None
            elif cur is not None:
                cur["inst"].append(tok)
    return subs


def sym_pins(path):
    """Pin name -> (x, y) centre, in symbol order."""
    pins = []
    for m in re.finditer(r"^B 5 (\S+) (\S+) (\S+) (\S+) \{([^}]*)\}", path.read_text(), re.M):
        x1, y1, x2, y2 = map(float, m.group(1, 2, 3, 4))
        name = re.search(r"name=(\S+)", m.group(5)).group(1)
        pins.append((name, ((x1 + x2) / 2, (y1 + y2) / 2)))
    return pins


def write_sym(sub):
    name, ports, params = sub["name"], sub["ports"], sub["params"]
    h = 20 * len(ports) + 20
    lines = [HEADER.replace("K {}", "K {type=subcircuit\nformat=\"@name @pinlist @symname"
                            + "".join(f" {k}=@{k}" for k in params) + "\"\ntemplate=\"name=x1"
                            + "".join(f" {k}={v}" for k, v in params.items()) + "\"}")]
    lines.append(f"L 4 -60 -10 60 -10 {{}}\nL 4 -60 {h - 10} 60 {h - 10} {{}}")
    lines.append(f"L 4 -60 -10 -60 {h - 10} {{}}\nL 4 60 -10 60 {h - 10} {{}}")
    for i, p in enumerate(ports):
        y = 20 * i + 10
        lines.append(f"B 5 -62.5 {y - 2.5} -57.5 {y + 2.5} {{name={p} dir=inout}}")
        lines.append(f"L 4 -80 {y} -60 {y} {{}}")
        lines.append(f"T {{{p}}} -55 {y - 6} 0 0 0.15 0.15 {{}}")
    lines.append(f"T {{@symname}} -55 {h - 5} 0 0 0.2 0.2 {{}}\nT {{@name}} -55 -25 0 0 0.2 0.2 {{}}")
    (OUT / f"{name}.sym").write_text("\n".join(lines) + "\n")
    # pins of the generated symbol, shifted so the box edge is the pin
    return [(p, (-60.0, 20.0 * i + 10)) for i, p in enumerate(ports)]


def write_prim_sym(model, pins):
    h = 20 * len(pins) + 20
    lines = [HEADER.replace("K {}", "K {type=primitive\nformat=\"@name @pinlist " + model + "\"\ntemplate=\"name=x1\"}")]
    lines.append(f"L 4 -60 -10 60 -10 {{}}\nL 4 -60 {h - 10} 60 {h - 10} {{}}")
    lines.append(f"L 4 -60 -10 -60 {h - 10} {{}}\nL 4 60 -10 60 {h - 10} {{}}")
    for i, p in enumerate(pins):
        y = 20 * i + 10
        lines.append(f"B 5 -62.5 {y - 2.5} -57.5 {y + 2.5} {{name={p} dir=inout}}")
        lines.append(f"T {{{p}}} -55 {y - 6} 0 0 0.15 0.15 {{}}")
    lines.append(f"T {{{model.split('__')[1]}}} -55 {h - 5} 0 0 0.2 0.2 {{}}\nT {{@name}} -55 -25 0 0 0.2 0.2 {{}}")
    (OUT / f"{model}.sym").write_text("\n".join(lines) + "\n")
    return [(p, (-60.0, 20.0 * i + 10)) for i, p in enumerate(pins)]


def main():
    OUT.mkdir(exist_ok=True)
    subs = parse_subckts()
    gen_pins = {name: write_sym(s) for name, s in subs.items()}
    lab_pin = "devices/lab_pin.sym"
    for name, sub in subs.items():
        out = [HEADER]
        for i, p in enumerate(sub["ports"]):
            out.append(f"C {{devices/iopin.sym}} -600 {i * 40} 0 0 {{name=p{i} lab={p}}}")
        n_lab = 0
        for k, tok in enumerate(sub["inst"]):
            iname = tok[0]
            X, Y = 300 * (k % 6), 300 * (k // 6)
            model = next((t for t in tok[1:] if "=" not in t and (t.startswith("sky130_") or t in subs)), None)
            if model is None and iname[0].upper() == "R":
                a, b, val = tok[1], tok[2], tok[3]
                out.append(f"C {{devices/res.sym}} {X} {Y} 0 0 {{name={iname} value={val} footprint=1206 device=resistor m=1}}")
                for net, (px, py) in ((a, (0, -30)), (b, (0, 30))):
                    out.append(f"C {{{lab_pin}}} {X + px} {Y + py} 0 0 {{name=l{n_lab} lab={net}}}"); n_lab += 1
                continue
            nets = tok[1:tok.index(model)]
            props = dict(t.split("=", 1) for t in tok[tok.index(model) + 1:] if "=" in t)
            if model.startswith("sky130_fd_pr__res_") or model.startswith("sky130_fd_pr__cap_mim"):
                dev = model.replace("sky130_fd_pr__", "")
                nm = iname[1:] if iname[0].upper() == "X" else iname
                pins = dict(sym_pins(XLIB / "sky130_fd_pr" / f"{dev}.sym"))
                if dev.startswith("res_"):
                    attr = f"name={nm} L={props['l']} mult={props.get('mult', '1')} model={dev} spiceprefix=X"
                    order = ["P", "M", "B"]
                else:
                    attr = f"name={nm} W={props['w']} L={props['l']} MF={props.get('mf', '1')} model={dev} spiceprefix=X"
                    order = ["c0", "c1"]
                out.append(f"C {{sky130_fd_pr/{dev}.sym}} {X} {Y} 0 0 {{{attr}}}")
                for pname, net in zip(order, nets):
                    px, py = pins[pname]
                    out.append(f"C {{{lab_pin}}} {X + px} {Y + py} 0 0 {{name=l{n_lab} lab={net}}}"); n_lab += 1
            elif model.startswith("sky130_fd_pr__"):
                dev = model.replace("sky130_fd_pr__", "")
                pins = sym_pins(XLIB / "sky130_fd_pr" / f"{dev}.sym")
                m = props.get("m", "1")
                nm = iname[1:] if iname[0].upper() == "X" else iname
                attr = (f"name={nm} W={props['W']} L={props['L']} nf=1 mult={m} model={dev} spiceprefix=X")
                out.append(f"C {{sky130_fd_pr/{dev}.sym}} {X} {Y} 0 0 {{{attr}}}")
                order = {"D": 0, "G": 1, "S": 2, "B": 3}
                for pname, (px, py) in pins:
                    net = nets[order[pname]]
                    out.append(f"C {{{lab_pin}}} {X + px} {Y + py} 0 0 {{name=l{n_lab} lab={net}}}"); n_lab += 1
            elif model.startswith("sky130_fd_sc_"):
                lib, cell = model.split("__")
                libdir = "sky130_stdcells"
                symf = XLIB / libdir / f"{cell}.sym"
                cellpins = re.search(r"^\.subckt\s+" + re.escape(model) + r"\s+(.+)$",
                                     (PDK / "libs.ref" / lib / "spice" / f"{lib}.spice").read_text(), re.M).group(1).split()
                netmap = dict(zip(cellpins, nets))
                if not symf.exists():
                    # no PDK symbol (e.g. HVL level shifters): generated primitive with all pins
                    gp = write_prim_sym(model, cellpins)
                    out.append(f"C {{{model}.sym}} {X} {Y} 0 0 {{name={iname}}}")
                    for pname, (px, py) in gp:
                        out.append(f"C {{{lab_pin}}} {X + px} {Y + py} 0 0 {{name=l{n_lab} lab={netmap[pname]}}}"); n_lab += 1
                    continue
                pwr = " ".join(f"{p}={netmap[p]}" for p in cellpins if p in POWER)
                prefix = f"{lib}__"
                out.append(f"C {{{libdir}/{cell}.sym}} {X} {Y} 0 0 {{name={iname} {pwr} prefix={prefix}}}")
                for pname, (px, py) in sym_pins(symf):
                    out.append(f"C {{{lab_pin}}} {X + px} {Y + py} 0 0 {{name=l{n_lab} lab={netmap[pname]}}}"); n_lab += 1
            else:
                pins = gen_pins[model]
                pp = " ".join(f"{k}={v}" for k, v in props.items())
                out.append(f"C {{{model}.sym}} {X} {Y} 0 0 {{name={iname} {pp}}}")
                for (pname, (px, py)), net in zip(pins, nets):
                    out.append(f"C {{{lab_pin}}} {X + px} {Y + py} 0 0 {{name=l{n_lab} lab={net}}}"); n_lab += 1
        (OUT / f"{name}.sch").write_text("\n".join(out) + "\n")
        print("wrote", f"xschem/{name}.sch", len(sub["inst"]), "instances")


if __name__ == "__main__":
    main()
