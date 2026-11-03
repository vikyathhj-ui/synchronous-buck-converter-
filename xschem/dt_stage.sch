v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=in}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=out}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=sel}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=vdd}
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=vss}
C {dt_tap.sym} 0 0 0 0 {name=XT }
C {devices/lab_pin.sym} -60.0 10.0 0 0 {name=l0 lab=in}
C {devices/lab_pin.sym} -60.0 30.0 0 0 {name=l1 lab=d}
C {devices/lab_pin.sym} -60.0 50.0 0 0 {name=l2 lab=vdd}
C {devices/lab_pin.sym} -60.0 70.0 0 0 {name=l3 lab=vss}
C {sky130_stdcells/mux2_1.sym} 300 0 0 0 {name=XM VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 260.0 -20.0 0 0 {name=l4 lab=in}
C {devices/lab_pin.sym} 260.0 20.0 0 0 {name=l5 lab=d}
C {devices/lab_pin.sym} 260.0 60.0 0 0 {name=l6 lab=sel}
C {devices/lab_pin.sym} 340.0 0.0 0 0 {name=l7 lab=out}
