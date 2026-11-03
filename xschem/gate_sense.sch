v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=vin}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=hs_g}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=ls_g}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=hs_on_s}
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=ls_on_s}
C {devices/iopin.sym} -600 200 0 0 {name=p5 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 0 0 0 0 {name=PS W=10 L=0.5 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 30.0 0 0 {name=l0 lab=hs_on_s}
C {devices/lab_pin.sym} -20.0 0.0 0 0 {name=l1 lab=hs_g}
C {devices/lab_pin.sym} 20.0 -30.0 0 0 {name=l2 lab=vin}
C {devices/lab_pin.sym} 20.0 0.0 0 0 {name=l3 lab=vin}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 0 0 0 {name=PD W=0.42 L=8 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 -30.0 0 0 {name=l4 lab=hs_on_s}
C {devices/lab_pin.sym} 280.0 0.0 0 0 {name=l5 lab=vin}
C {devices/lab_pin.sym} 320.0 30.0 0 0 {name=l6 lab=vss}
C {devices/lab_pin.sym} 320.0 0.0 0 0 {name=l7 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 600 0 0 0 {name=NS W=4 L=0.5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 -30.0 0 0 {name=l8 lab=lsb}
C {devices/lab_pin.sym} 580.0 0.0 0 0 {name=l9 lab=ls_g}
C {devices/lab_pin.sym} 620.0 30.0 0 0 {name=l10 lab=vss}
C {devices/lab_pin.sym} 620.0 0.0 0 0 {name=l11 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 0 0 0 {name=NU W=0.42 L=8 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 30.0 0 0 {name=l12 lab=lsb}
C {devices/lab_pin.sym} 880.0 0.0 0 0 {name=l13 lab=vss}
C {devices/lab_pin.sym} 920.0 -30.0 0 0 {name=l14 lab=vin}
C {devices/lab_pin.sym} 920.0 0.0 0 0 {name=l15 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1200 0 0 0 {name=NI W=2 L=0.5 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1220.0 30.0 0 0 {name=l16 lab=ls_on_s}
C {devices/lab_pin.sym} 1180.0 0.0 0 0 {name=l17 lab=lsb}
C {devices/lab_pin.sym} 1220.0 -30.0 0 0 {name=l18 lab=vin}
C {devices/lab_pin.sym} 1220.0 0.0 0 0 {name=l19 lab=vin}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1500 0 0 0 {name=NJ W=1 L=0.5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1520.0 -30.0 0 0 {name=l20 lab=ls_on_s}
C {devices/lab_pin.sym} 1480.0 0.0 0 0 {name=l21 lab=lsb}
C {devices/lab_pin.sym} 1520.0 30.0 0 0 {name=l22 lab=vss}
C {devices/lab_pin.sym} 1520.0 0.0 0 0 {name=l23 lab=vss}
