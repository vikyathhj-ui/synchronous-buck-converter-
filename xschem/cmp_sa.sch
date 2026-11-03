v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=inp}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=inn}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=clk}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=q}
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=vdd}
C {devices/iopin.sym} -600 200 0 0 {name=p5 lab=vss}
C {sky130_stdcells/clkinv_1.sym} 0 0 0 0 {name=XINV VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} -40.0 0.0 0 0 {name=l0 lab=clk}
C {devices/lab_pin.sym} 40.0 0.0 0 0 {name=l1 lab=clkb}
C {sky130_fd_pr/pfet_01v8.sym} 300 0 0 0 {name=T W=8 L=0.5 nf=1 mult=8 model=pfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 30.0 0 0 {name=l2 lab=tail}
C {devices/lab_pin.sym} 280.0 0.0 0 0 {name=l3 lab=clkb}
C {devices/lab_pin.sym} 320.0 -30.0 0 0 {name=l4 lab=vdd}
C {devices/lab_pin.sym} 320.0 0.0 0 0 {name=l5 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 600 0 0 0 {name=P1 W=8 L=1 nf=1 mult=8 model=pfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 30.0 0 0 {name=l6 lab=x1}
C {devices/lab_pin.sym} 580.0 0.0 0 0 {name=l7 lab=inp}
C {devices/lab_pin.sym} 620.0 -30.0 0 0 {name=l8 lab=tail}
C {devices/lab_pin.sym} 620.0 0.0 0 0 {name=l9 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 900 0 0 0 {name=P2 W=8 L=1 nf=1 mult=8 model=pfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 30.0 0 0 {name=l10 lab=x2}
C {devices/lab_pin.sym} 880.0 0.0 0 0 {name=l11 lab=inn}
C {devices/lab_pin.sym} 920.0 -30.0 0 0 {name=l12 lab=tail}
C {devices/lab_pin.sym} 920.0 0.0 0 0 {name=l13 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 1200 0 0 0 {name=P3 W=4 L=0.5 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 1220.0 30.0 0 0 {name=l14 lab=outn}
C {devices/lab_pin.sym} 1180.0 0.0 0 0 {name=l15 lab=outp}
C {devices/lab_pin.sym} 1220.0 -30.0 0 0 {name=l16 lab=x1}
C {devices/lab_pin.sym} 1220.0 0.0 0 0 {name=l17 lab=vdd}
C {sky130_fd_pr/pfet_01v8.sym} 1500 0 0 0 {name=P4 W=4 L=0.5 nf=1 mult=1 model=pfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 1520.0 30.0 0 0 {name=l18 lab=outp}
C {devices/lab_pin.sym} 1480.0 0.0 0 0 {name=l19 lab=outn}
C {devices/lab_pin.sym} 1520.0 -30.0 0 0 {name=l20 lab=x2}
C {devices/lab_pin.sym} 1520.0 0.0 0 0 {name=l21 lab=vdd}
C {sky130_fd_pr/nfet_01v8.sym} 0 300 0 0 {name=N3 W=2 L=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 270.0 0 0 {name=l22 lab=outn}
C {devices/lab_pin.sym} -20.0 300.0 0 0 {name=l23 lab=outp}
C {devices/lab_pin.sym} 20.0 330.0 0 0 {name=l24 lab=vss}
C {devices/lab_pin.sym} 20.0 300.0 0 0 {name=l25 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 300 300 0 0 {name=N4 W=2 L=0.5 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 270.0 0 0 {name=l26 lab=outp}
C {devices/lab_pin.sym} 280.0 300.0 0 0 {name=l27 lab=outn}
C {devices/lab_pin.sym} 320.0 330.0 0 0 {name=l28 lab=vss}
C {devices/lab_pin.sym} 320.0 300.0 0 0 {name=l29 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 600 300 0 0 {name=R1 W=2 L=0.15 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 270.0 0 0 {name=l30 lab=x1}
C {devices/lab_pin.sym} 580.0 300.0 0 0 {name=l31 lab=clkb}
C {devices/lab_pin.sym} 620.0 330.0 0 0 {name=l32 lab=vss}
C {devices/lab_pin.sym} 620.0 300.0 0 0 {name=l33 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 900 300 0 0 {name=R2 W=2 L=0.15 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 270.0 0 0 {name=l34 lab=x2}
C {devices/lab_pin.sym} 880.0 300.0 0 0 {name=l35 lab=clkb}
C {devices/lab_pin.sym} 920.0 330.0 0 0 {name=l36 lab=vss}
C {devices/lab_pin.sym} 920.0 300.0 0 0 {name=l37 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 1200 300 0 0 {name=R3 W=2 L=0.15 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 1220.0 270.0 0 0 {name=l38 lab=outn}
C {devices/lab_pin.sym} 1180.0 300.0 0 0 {name=l39 lab=clkb}
C {devices/lab_pin.sym} 1220.0 330.0 0 0 {name=l40 lab=vss}
C {devices/lab_pin.sym} 1220.0 300.0 0 0 {name=l41 lab=vss}
C {sky130_fd_pr/nfet_01v8.sym} 1500 300 0 0 {name=R4 W=2 L=0.15 nf=1 mult=1 model=nfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 1520.0 270.0 0 0 {name=l42 lab=outp}
C {devices/lab_pin.sym} 1480.0 300.0 0 0 {name=l43 lab=clkb}
C {devices/lab_pin.sym} 1520.0 330.0 0 0 {name=l44 lab=vss}
C {devices/lab_pin.sym} 1520.0 300.0 0 0 {name=l45 lab=vss}
C {sky130_stdcells/inv_1.sym} 0 600 0 0 {name=XIP VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} -40.0 600.0 0 0 {name=l46 lab=outp}
C {devices/lab_pin.sym} 40.0 600.0 0 0 {name=l47 lab=outp_b}
C {sky130_stdcells/inv_1.sym} 300 600 0 0 {name=XIN VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 260.0 600.0 0 0 {name=l48 lab=outn}
C {devices/lab_pin.sym} 340.0 600.0 0 0 {name=l49 lab=outn_b}
C {sky130_stdcells/nand2_1.sym} 600 600 0 0 {name=XL1 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 540.0 580.0 0 0 {name=l50 lab=outn_b}
C {devices/lab_pin.sym} 540.0 620.0 0 0 {name=l51 lab=qb}
C {devices/lab_pin.sym} 660.0 600.0 0 0 {name=l52 lab=q_i}
C {sky130_stdcells/nand2_1.sym} 900 600 0 0 {name=XL2 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 840.0 580.0 0 0 {name=l53 lab=outp_b}
C {devices/lab_pin.sym} 840.0 620.0 0 0 {name=l54 lab=q_i}
C {devices/lab_pin.sym} 960.0 600.0 0 0 {name=l55 lab=qb}
C {sky130_stdcells/buf_1.sym} 1200 600 0 0 {name=XB VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 1160.0 600.0 0 0 {name=l56 lab=q_i}
C {devices/lab_pin.sym} 1240.0 600.0 0 0 {name=l57 lab=q}
