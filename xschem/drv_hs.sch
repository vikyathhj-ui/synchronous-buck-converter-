v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=in}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=out}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=vdd}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 0 0 0 0 {name=P1 W=3 L=0.5 nf=1 mult=1 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 30.0 0 0 {name=l0 lab=h1}
C {devices/lab_pin.sym} -20.0 0.0 0 0 {name=l1 lab=in}
C {devices/lab_pin.sym} 20.0 -30.0 0 0 {name=l2 lab=vdd}
C {devices/lab_pin.sym} 20.0 0.0 0 0 {name=l3 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 0 0 0 {name=N1 W=1 L=0.5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 -30.0 0 0 {name=l4 lab=h1}
C {devices/lab_pin.sym} 280.0 0.0 0 0 {name=l5 lab=in}
C {devices/lab_pin.sym} 320.0 30.0 0 0 {name=l6 lab=vss}
C {devices/lab_pin.sym} 320.0 0.0 0 0 {name=l7 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 600 0 0 0 {name=P2 W=6 L=0.5 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 30.0 0 0 {name=l8 lab=h2}
C {devices/lab_pin.sym} 580.0 0.0 0 0 {name=l9 lab=h1}
C {devices/lab_pin.sym} 620.0 -30.0 0 0 {name=l10 lab=vdd}
C {devices/lab_pin.sym} 620.0 0.0 0 0 {name=l11 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 0 0 0 {name=N2 W=4 L=0.5 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 -30.0 0 0 {name=l12 lab=h2}
C {devices/lab_pin.sym} 880.0 0.0 0 0 {name=l13 lab=h1}
C {devices/lab_pin.sym} 920.0 30.0 0 0 {name=l14 lab=vss}
C {devices/lab_pin.sym} 920.0 0.0 0 0 {name=l15 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1200 0 0 0 {name=P3 W=8 L=0.5 nf=1 mult=6 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1220.0 30.0 0 0 {name=l16 lab=h3}
C {devices/lab_pin.sym} 1180.0 0.0 0 0 {name=l17 lab=h2}
C {devices/lab_pin.sym} 1220.0 -30.0 0 0 {name=l18 lab=vdd}
C {devices/lab_pin.sym} 1220.0 0.0 0 0 {name=l19 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1500 0 0 0 {name=N3 W=8 L=0.5 nf=1 mult=2 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1520.0 -30.0 0 0 {name=l20 lab=h3}
C {devices/lab_pin.sym} 1480.0 0.0 0 0 {name=l21 lab=h2}
C {devices/lab_pin.sym} 1520.0 30.0 0 0 {name=l22 lab=vss}
C {devices/lab_pin.sym} 1520.0 0.0 0 0 {name=l23 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 0 300 0 0 {name=P4 W=8 L=0.5 nf=1 mult=24 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 330.0 0 0 {name=l24 lab=h4}
C {devices/lab_pin.sym} -20.0 300.0 0 0 {name=l25 lab=h3}
C {devices/lab_pin.sym} 20.0 270.0 0 0 {name=l26 lab=vdd}
C {devices/lab_pin.sym} 20.0 300.0 0 0 {name=l27 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 300 0 0 {name=N4 W=8 L=0.5 nf=1 mult=8 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 270.0 0 0 {name=l28 lab=h4}
C {devices/lab_pin.sym} 280.0 300.0 0 0 {name=l29 lab=h3}
C {devices/lab_pin.sym} 320.0 330.0 0 0 {name=l30 lab=vss}
C {devices/lab_pin.sym} 320.0 300.0 0 0 {name=l31 lab=vss}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 600 300 0 0 {name=P5 W=8 L=0.5 nf=1 mult=96 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 330.0 0 0 {name=l32 lab=out}
C {devices/lab_pin.sym} 580.0 300.0 0 0 {name=l33 lab=h4}
C {devices/lab_pin.sym} 620.0 270.0 0 0 {name=l34 lab=vdd}
C {devices/lab_pin.sym} 620.0 300.0 0 0 {name=l35 lab=vdd}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 300 0 0 {name=N5 W=8 L=0.5 nf=1 mult=32 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 270.0 0 0 {name=l36 lab=out}
C {devices/lab_pin.sym} 880.0 300.0 0 0 {name=l37 lab=h4}
C {devices/lab_pin.sym} 920.0 330.0 0 0 {name=l38 lab=vss}
C {devices/lab_pin.sym} 920.0 300.0 0 0 {name=l39 lab=vss}
