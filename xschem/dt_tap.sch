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
C {sky130_stdcells/dlygate4sd3_1.sym} 0 0 0 0 {name=X1 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} -40.0 0.0 0 0 {name=l0 lab=in}
C {devices/lab_pin.sym} 40.0 0.0 0 0 {name=l1 lab=a1}
C {sky130_stdcells/dlygate4sd3_1.sym} 300 0 0 0 {name=X2 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 260.0 0.0 0 0 {name=l2 lab=a1}
C {devices/lab_pin.sym} 340.0 0.0 0 0 {name=l3 lab=a2}
C {sky130_stdcells/dlygate4sd3_1.sym} 600 0 0 0 {name=X3 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 560.0 0.0 0 0 {name=l4 lab=a2}
C {devices/lab_pin.sym} 640.0 0.0 0 0 {name=l5 lab=a3}
C {sky130_stdcells/dlygate4sd3_1.sym} 900 0 0 0 {name=X4 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 860.0 0.0 0 0 {name=l6 lab=a3}
C {devices/lab_pin.sym} 940.0 0.0 0 0 {name=l7 lab=a4}
C {sky130_stdcells/dlygate4sd3_1.sym} 1200 0 0 0 {name=X5 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 1160.0 0.0 0 0 {name=l8 lab=a4}
C {devices/lab_pin.sym} 1240.0 0.0 0 0 {name=l9 lab=out}
