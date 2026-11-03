v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=vout}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=vdiv}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=vss}
C {sky130_fd_pr/res_xhigh_po_1p41.sym} 0 0 0 0 {name=D0 L=4 mult=1 model=res_xhigh_po_1p41 spiceprefix=X}
C {devices/lab_pin.sym} 0.0 -30.0 0 0 {name=l0 lab=vout}
C {devices/lab_pin.sym} 0.0 30.0 0 0 {name=l1 lab=d1}
C {devices/lab_pin.sym} -20.0 0.0 0 0 {name=l2 lab=vss}
C {sky130_fd_pr/res_xhigh_po_1p41.sym} 300 0 0 0 {name=D1 L=4 mult=1 model=res_xhigh_po_1p41 spiceprefix=X}
C {devices/lab_pin.sym} 300.0 -30.0 0 0 {name=l3 lab=d1}
C {devices/lab_pin.sym} 300.0 30.0 0 0 {name=l4 lab=d2}
C {devices/lab_pin.sym} 280.0 0.0 0 0 {name=l5 lab=vss}
C {sky130_fd_pr/res_xhigh_po_1p41.sym} 600 0 0 0 {name=D2 L=4 mult=1 model=res_xhigh_po_1p41 spiceprefix=X}
C {devices/lab_pin.sym} 600.0 -30.0 0 0 {name=l6 lab=d2}
C {devices/lab_pin.sym} 600.0 30.0 0 0 {name=l7 lab=vdiv}
C {devices/lab_pin.sym} 580.0 0.0 0 0 {name=l8 lab=vss}
C {sky130_fd_pr/res_xhigh_po_1p41.sym} 900 0 0 0 {name=D3 L=4 mult=1 model=res_xhigh_po_1p41 spiceprefix=X}
C {devices/lab_pin.sym} 900.0 -30.0 0 0 {name=l9 lab=vdiv}
C {devices/lab_pin.sym} 900.0 30.0 0 0 {name=l10 lab=d4}
C {devices/lab_pin.sym} 880.0 0.0 0 0 {name=l11 lab=vss}
C {sky130_fd_pr/res_xhigh_po_1p41.sym} 1200 0 0 0 {name=D4 L=4 mult=1 model=res_xhigh_po_1p41 spiceprefix=X}
C {devices/lab_pin.sym} 1200.0 -30.0 0 0 {name=l12 lab=d4}
C {devices/lab_pin.sym} 1200.0 30.0 0 0 {name=l13 lab=d5}
C {devices/lab_pin.sym} 1180.0 0.0 0 0 {name=l14 lab=vss}
C {sky130_fd_pr/res_xhigh_po_1p41.sym} 1500 0 0 0 {name=D5 L=4 mult=1 model=res_xhigh_po_1p41 spiceprefix=X}
C {devices/lab_pin.sym} 1500.0 -30.0 0 0 {name=l15 lab=d5}
C {devices/lab_pin.sym} 1500.0 30.0 0 0 {name=l16 lab=vss}
C {devices/lab_pin.sym} 1480.0 0.0 0 0 {name=l17 lab=vss}
C {sky130_fd_pr/cap_mim_m3_1.sym} 0 300 0 0 {name=CD W=70 L=70 MF=1 model=cap_mim_m3_1 spiceprefix=X}
C {devices/lab_pin.sym} 0.0 270.0 0 0 {name=l18 lab=vdiv}
C {devices/lab_pin.sym} 0.0 330.0 0 0 {name=l19 lab=vss}
