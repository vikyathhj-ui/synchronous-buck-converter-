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
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=vin}
C {devices/iopin.sym} -600 200 0 0 {name=p5 lab=vdd}
C {devices/iopin.sym} -600 240 0 0 {name=p6 lab=vss}
C {sky130_fd_sc_hvl__lsbuflv2hv_1.sym} 0 0 0 0 {name=XCS}
C {devices/lab_pin.sym} -60.0 10.0 0 0 {name=l0 lab=clk}
C {devices/lab_pin.sym} -60.0 30.0 0 0 {name=l1 lab=vdd}
C {devices/lab_pin.sym} -60.0 50.0 0 0 {name=l2 lab=vss}
C {devices/lab_pin.sym} -60.0 70.0 0 0 {name=l3 lab=vss}
C {devices/lab_pin.sym} -60.0 90.0 0 0 {name=l4 lab=vin}
C {devices/lab_pin.sym} -60.0 110.0 0 0 {name=l5 lab=vin}
C {devices/lab_pin.sym} -60.0 130.0 0 0 {name=l6 lab=clk_h}
C {sky130_stdcells/inv_1.sym} 300 0 0 0 {name=XCI VGND=vss VNB=vss VPB=vin VPWR=vin prefix=sky130_fd_sc_hvl__}
C {devices/lab_pin.sym} 260.0 0.0 0 0 {name=l7 lab=clk_h}
C {devices/lab_pin.sym} 340.0 0.0 0 0 {name=l8 lab=clkb}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 600 0 0 0 {name=T W=10 L=0.5 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 30.0 0 0 {name=l9 lab=tail}
C {devices/lab_pin.sym} 580.0 0.0 0 0 {name=l10 lab=clkb}
C {devices/lab_pin.sym} 620.0 -30.0 0 0 {name=l11 lab=vin}
C {devices/lab_pin.sym} 620.0 0.0 0 0 {name=l12 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 900 0 0 0 {name=P1 W=10 L=2 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 30.0 0 0 {name=l13 lab=x1}
C {devices/lab_pin.sym} 880.0 0.0 0 0 {name=l14 lab=inp}
C {devices/lab_pin.sym} 920.0 -30.0 0 0 {name=l15 lab=tail}
C {devices/lab_pin.sym} 920.0 0.0 0 0 {name=l16 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1200 0 0 0 {name=P2 W=10 L=2 nf=1 mult=8 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1220.0 30.0 0 0 {name=l17 lab=x2}
C {devices/lab_pin.sym} 1180.0 0.0 0 0 {name=l18 lab=inn}
C {devices/lab_pin.sym} 1220.0 -30.0 0 0 {name=l19 lab=tail}
C {devices/lab_pin.sym} 1220.0 0.0 0 0 {name=l20 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 1500 0 0 0 {name=P3 W=10 L=2 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1520.0 30.0 0 0 {name=l21 lab=outn}
C {devices/lab_pin.sym} 1480.0 0.0 0 0 {name=l22 lab=outp}
C {devices/lab_pin.sym} 1520.0 -30.0 0 0 {name=l23 lab=x1}
C {devices/lab_pin.sym} 1520.0 0.0 0 0 {name=l24 lab=vin}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 0 300 0 0 {name=P4 W=10 L=2 nf=1 mult=2 model=pfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 330.0 0 0 {name=l25 lab=outp}
C {devices/lab_pin.sym} -20.0 300.0 0 0 {name=l26 lab=outn}
C {devices/lab_pin.sym} 20.0 270.0 0 0 {name=l27 lab=x2}
C {devices/lab_pin.sym} 20.0 300.0 0 0 {name=l28 lab=vin}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 300 0 0 {name=N3 W=10 L=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 320.0 270.0 0 0 {name=l29 lab=outn}
C {devices/lab_pin.sym} 280.0 300.0 0 0 {name=l30 lab=outp}
C {devices/lab_pin.sym} 320.0 330.0 0 0 {name=l31 lab=vss}
C {devices/lab_pin.sym} 320.0 300.0 0 0 {name=l32 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 600 300 0 0 {name=N4 W=10 L=2 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 620.0 270.0 0 0 {name=l33 lab=outp}
C {devices/lab_pin.sym} 580.0 300.0 0 0 {name=l34 lab=outn}
C {devices/lab_pin.sym} 620.0 330.0 0 0 {name=l35 lab=vss}
C {devices/lab_pin.sym} 620.0 300.0 0 0 {name=l36 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 900 300 0 0 {name=R1 W=8 L=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 920.0 270.0 0 0 {name=l37 lab=x1}
C {devices/lab_pin.sym} 880.0 300.0 0 0 {name=l38 lab=clkb}
C {devices/lab_pin.sym} 920.0 330.0 0 0 {name=l39 lab=vss}
C {devices/lab_pin.sym} 920.0 300.0 0 0 {name=l40 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1200 300 0 0 {name=R2 W=8 L=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1220.0 270.0 0 0 {name=l41 lab=x2}
C {devices/lab_pin.sym} 1180.0 300.0 0 0 {name=l42 lab=clkb}
C {devices/lab_pin.sym} 1220.0 330.0 0 0 {name=l43 lab=vss}
C {devices/lab_pin.sym} 1220.0 300.0 0 0 {name=l44 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 1500 300 0 0 {name=R3 W=8 L=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 1520.0 270.0 0 0 {name=l45 lab=outn}
C {devices/lab_pin.sym} 1480.0 300.0 0 0 {name=l46 lab=clkb}
C {devices/lab_pin.sym} 1520.0 330.0 0 0 {name=l47 lab=vss}
C {devices/lab_pin.sym} 1520.0 300.0 0 0 {name=l48 lab=vss}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 0 600 0 0 {name=R4 W=8 L=4 nf=1 mult=1 model=nfet_g5v0d10v5 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 570.0 0 0 {name=l49 lab=outp}
C {devices/lab_pin.sym} -20.0 600.0 0 0 {name=l50 lab=clkb}
C {devices/lab_pin.sym} 20.0 630.0 0 0 {name=l51 lab=vss}
C {devices/lab_pin.sym} 20.0 600.0 0 0 {name=l52 lab=vss}
C {sky130_stdcells/inv_1.sym} 300 600 0 0 {name=XIP VGND=vss VNB=vss VPB=vin VPWR=vin prefix=sky130_fd_sc_hvl__}
C {devices/lab_pin.sym} 260.0 600.0 0 0 {name=l53 lab=outp}
C {devices/lab_pin.sym} 340.0 600.0 0 0 {name=l54 lab=outp_b}
C {sky130_stdcells/inv_1.sym} 600 600 0 0 {name=XIN VGND=vss VNB=vss VPB=vin VPWR=vin prefix=sky130_fd_sc_hvl__}
C {devices/lab_pin.sym} 560.0 600.0 0 0 {name=l55 lab=outn}
C {devices/lab_pin.sym} 640.0 600.0 0 0 {name=l56 lab=outn_b}
C {sky130_fd_sc_hvl__lsbufhv2lv_1.sym} 900 600 0 0 {name=XDP}
C {devices/lab_pin.sym} 840.0 610.0 0 0 {name=l57 lab=outp_b}
C {devices/lab_pin.sym} 840.0 630.0 0 0 {name=l58 lab=vdd}
C {devices/lab_pin.sym} 840.0 650.0 0 0 {name=l59 lab=vss}
C {devices/lab_pin.sym} 840.0 670.0 0 0 {name=l60 lab=vss}
C {devices/lab_pin.sym} 840.0 690.0 0 0 {name=l61 lab=vin}
C {devices/lab_pin.sym} 840.0 710.0 0 0 {name=l62 lab=vin}
C {devices/lab_pin.sym} 840.0 730.0 0 0 {name=l63 lab=outp_l}
C {sky130_fd_sc_hvl__lsbufhv2lv_1.sym} 1200 600 0 0 {name=XDN}
C {devices/lab_pin.sym} 1140.0 610.0 0 0 {name=l64 lab=outn_b}
C {devices/lab_pin.sym} 1140.0 630.0 0 0 {name=l65 lab=vdd}
C {devices/lab_pin.sym} 1140.0 650.0 0 0 {name=l66 lab=vss}
C {devices/lab_pin.sym} 1140.0 670.0 0 0 {name=l67 lab=vss}
C {devices/lab_pin.sym} 1140.0 690.0 0 0 {name=l68 lab=vin}
C {devices/lab_pin.sym} 1140.0 710.0 0 0 {name=l69 lab=vin}
C {devices/lab_pin.sym} 1140.0 730.0 0 0 {name=l70 lab=outn_l}
C {sky130_stdcells/nand2_1.sym} 1500 600 0 0 {name=XL1 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 1440.0 580.0 0 0 {name=l71 lab=outn_l}
C {devices/lab_pin.sym} 1440.0 620.0 0 0 {name=l72 lab=qb}
C {devices/lab_pin.sym} 1560.0 600.0 0 0 {name=l73 lab=q_i}
C {sky130_stdcells/nand2_1.sym} 0 900 0 0 {name=XL2 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} -60.0 880.0 0 0 {name=l74 lab=outp_l}
C {devices/lab_pin.sym} -60.0 920.0 0 0 {name=l75 lab=q_i}
C {devices/lab_pin.sym} 60.0 900.0 0 0 {name=l76 lab=qb}
C {sky130_stdcells/buf_1.sym} 300 900 0 0 {name=XB VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 260.0 900.0 0 0 {name=l77 lab=q_i}
C {devices/lab_pin.sym} 340.0 900.0 0 0 {name=l78 lab=q}
