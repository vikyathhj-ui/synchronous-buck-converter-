v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=sw}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=ls_g}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=vsh}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=vth}
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=clk}
C {devices/iopin.sym} -600 200 0 0 {name=p5 lab=q}
C {devices/iopin.sym} -600 240 0 0 {name=p6 lab=vin}
C {devices/iopin.sym} -600 280 0 0 {name=p7 lab=vdd}
C {devices/iopin.sym} -600 320 0 0 {name=p8 lab=vss}
C {sw_sense.sym} 0 0 0 0 {name=XS }
C {devices/lab_pin.sym} -60.0 10.0 0 0 {name=l0 lab=sw}
C {devices/lab_pin.sym} -60.0 30.0 0 0 {name=l1 lab=ls_g}
C {devices/lab_pin.sym} -60.0 50.0 0 0 {name=l2 lab=vs}
C {devices/lab_pin.sym} -60.0 70.0 0 0 {name=l3 lab=vss}
C {sky130_fd_pr/res_xhigh_po_5p73.sym} 300 0 0 0 {name=RA L=28 mult=1 model=res_xhigh_po_5p73 spiceprefix=X}
C {devices/lab_pin.sym} 300.0 -30.0 0 0 {name=l4 lab=vs}
C {devices/lab_pin.sym} 300.0 30.0 0 0 {name=l5 lab=inp}
C {devices/lab_pin.sym} 280.0 0.0 0 0 {name=l6 lab=vss}
C {sky130_fd_pr/res_xhigh_po_5p73.sym} 600 0 0 0 {name=RB L=28 mult=1 model=res_xhigh_po_5p73 spiceprefix=X}
C {devices/lab_pin.sym} 600.0 -30.0 0 0 {name=l7 lab=vsh}
C {devices/lab_pin.sym} 600.0 30.0 0 0 {name=l8 lab=inp}
C {devices/lab_pin.sym} 580.0 0.0 0 0 {name=l9 lab=vss}
C {sw_sense.sym} 900 0 0 0 {name=XT }
C {devices/lab_pin.sym} 840.0 10.0 0 0 {name=l10 lab=vth}
C {devices/lab_pin.sym} 840.0 30.0 0 0 {name=l11 lab=ls_g}
C {devices/lab_pin.sym} 840.0 50.0 0 0 {name=l12 lab=vt}
C {devices/lab_pin.sym} 840.0 70.0 0 0 {name=l13 lab=vss}
C {sky130_fd_pr/res_xhigh_po_5p73.sym} 1200 0 0 0 {name=RC L=28 mult=1 model=res_xhigh_po_5p73 spiceprefix=X}
C {devices/lab_pin.sym} 1200.0 -30.0 0 0 {name=l14 lab=vt}
C {devices/lab_pin.sym} 1200.0 30.0 0 0 {name=l15 lab=inn}
C {devices/lab_pin.sym} 1180.0 0.0 0 0 {name=l16 lab=vss}
C {sky130_fd_pr/res_xhigh_po_5p73.sym} 1500 0 0 0 {name=RD L=28 mult=1 model=res_xhigh_po_5p73 spiceprefix=X}
C {devices/lab_pin.sym} 1500.0 -30.0 0 0 {name=l17 lab=vsh}
C {devices/lab_pin.sym} 1500.0 30.0 0 0 {name=l18 lab=inn}
C {devices/lab_pin.sym} 1480.0 0.0 0 0 {name=l19 lab=vss}
C {cmp_hv.sym} 0 300 0 0 {name=XC }
C {devices/lab_pin.sym} -60.0 310.0 0 0 {name=l20 lab=inp}
C {devices/lab_pin.sym} -60.0 330.0 0 0 {name=l21 lab=inn}
C {devices/lab_pin.sym} -60.0 350.0 0 0 {name=l22 lab=clk}
C {devices/lab_pin.sym} -60.0 370.0 0 0 {name=l23 lab=q}
C {devices/lab_pin.sym} -60.0 390.0 0 0 {name=l24 lab=vin}
C {devices/lab_pin.sym} -60.0 410.0 0 0 {name=l25 lab=vdd}
C {devices/lab_pin.sym} -60.0 430.0 0 0 {name=l26 lab=vss}
