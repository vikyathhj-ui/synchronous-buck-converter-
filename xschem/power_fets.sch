v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=vin}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=sw}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=hs_g}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=ls_g}
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 0 0 0 0 {name=HS0 W=10 L=0.5 nf=1 mult=480 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 30.0 0 0 {name=l0 lab=sw}
C {devices/lab_pin.sym} -20.0 0.0 0 0 {name=l1 lab=hs_g}
C {devices/lab_pin.sym} 20.0 -30.0 0 0 {name=l2 lab=vin}
C {devices/lab_pin.sym} 20.0 0.0 0 0 {name=l3 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 300 0 0 0 {name=HS1 W=10 L=0.5 nf=1 mult=480 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 30.0 0 0 {name=l4 lab=sw}
C {devices/lab_pin.sym} 280.0 0.0 0 0 {name=l5 lab=hs_g}
C {devices/lab_pin.sym} 320.0 -30.0 0 0 {name=l6 lab=vin}
C {devices/lab_pin.sym} 320.0 0.0 0 0 {name=l7 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 600 0 0 0 {name=HS2 W=10 L=0.5 nf=1 mult=480 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 30.0 0 0 {name=l8 lab=sw}
C {devices/lab_pin.sym} 580.0 0.0 0 0 {name=l9 lab=hs_g}
C {devices/lab_pin.sym} 620.0 -30.0 0 0 {name=l10 lab=vin}
C {devices/lab_pin.sym} 620.0 0.0 0 0 {name=l11 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 0 0 0 {name=HS3 W=10 L=0.5 nf=1 mult=480 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 30.0 0 0 {name=l12 lab=sw}
C {devices/lab_pin.sym} 880.0 0.0 0 0 {name=l13 lab=hs_g}
C {devices/lab_pin.sym} 920.0 -30.0 0 0 {name=l14 lab=vin}
C {devices/lab_pin.sym} 920.0 0.0 0 0 {name=l15 lab=vin}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1200 0 0 0 {name=LS0 W=10 L=0.5 nf=1 mult=220 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1220.0 -30.0 0 0 {name=l16 lab=sw}
C {devices/lab_pin.sym} 1180.0 0.0 0 0 {name=l17 lab=ls_g}
C {devices/lab_pin.sym} 1220.0 30.0 0 0 {name=l18 lab=vss}
C {devices/lab_pin.sym} 1220.0 0.0 0 0 {name=l19 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1500 0 0 0 {name=LS1 W=10 L=0.5 nf=1 mult=220 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1520.0 -30.0 0 0 {name=l20 lab=sw}
C {devices/lab_pin.sym} 1480.0 0.0 0 0 {name=l21 lab=ls_g}
C {devices/lab_pin.sym} 1520.0 30.0 0 0 {name=l22 lab=vss}
C {devices/lab_pin.sym} 1520.0 0.0 0 0 {name=l23 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 0 300 0 0 {name=LS2 W=10 L=0.5 nf=1 mult=220 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 270.0 0 0 {name=l24 lab=sw}
C {devices/lab_pin.sym} -20.0 300.0 0 0 {name=l25 lab=ls_g}
C {devices/lab_pin.sym} 20.0 330.0 0 0 {name=l26 lab=vss}
C {devices/lab_pin.sym} 20.0 300.0 0 0 {name=l27 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 300 0 0 {name=LS3 W=10 L=0.5 nf=1 mult=220 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 270.0 0 0 {name=l28 lab=sw}
C {devices/lab_pin.sym} 280.0 300.0 0 0 {name=l29 lab=ls_g}
C {devices/lab_pin.sym} 320.0 330.0 0 0 {name=l30 lab=vss}
C {devices/lab_pin.sym} 320.0 300.0 0 0 {name=l31 lab=vss}
