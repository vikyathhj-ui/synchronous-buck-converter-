v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=sw}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=ls_g}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=vs}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 0 0 0 0 {name=PASS W=10 L=0.5 nf=1 mult=10 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 -30.0 0 0 {name=l0 lab=vs}
C {devices/lab_pin.sym} -20.0 0.0 0 0 {name=l1 lab=ls_g}
C {devices/lab_pin.sym} 20.0 30.0 0 0 {name=l2 lab=sw}
C {devices/lab_pin.sym} 20.0 0.0 0 0 {name=l3 lab=vss}
C {devices/res.sym} 300 0 0 0 {name=RPD value=1Meg footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 300 -30 0 0 {name=l4 lab=vs}
C {devices/lab_pin.sym} 300 30 0 0 {name=l5 lab=vss}
