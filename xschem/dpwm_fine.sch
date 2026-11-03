v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=pwm_set}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=pwm_rst}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=s0}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=s1}
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=s2}
C {devices/iopin.sym} -600 200 0 0 {name=p5 lab=hs_pwm}
C {devices/iopin.sym} -600 240 0 0 {name=p6 lab=vdd}
C {devices/iopin.sym} -600 280 0 0 {name=p7 lab=vss}
C {dt_tap.sym} 0 0 0 0 {name=XT1 }
C {devices/lab_pin.sym} -60.0 10.0 0 0 {name=l0 lab=pwm_rst}
C {devices/lab_pin.sym} -60.0 30.0 0 0 {name=l1 lab=d1}
C {devices/lab_pin.sym} -60.0 50.0 0 0 {name=l2 lab=vdd}
C {devices/lab_pin.sym} -60.0 70.0 0 0 {name=l3 lab=vss}
C {dt_tap.sym} 300 0 0 0 {name=XT2 }
C {devices/lab_pin.sym} 240.0 10.0 0 0 {name=l4 lab=d1}
C {devices/lab_pin.sym} 240.0 30.0 0 0 {name=l5 lab=d2}
C {devices/lab_pin.sym} 240.0 50.0 0 0 {name=l6 lab=vdd}
C {devices/lab_pin.sym} 240.0 70.0 0 0 {name=l7 lab=vss}
C {dt_tap.sym} 600 0 0 0 {name=XT3 }
C {devices/lab_pin.sym} 540.0 10.0 0 0 {name=l8 lab=d2}
C {devices/lab_pin.sym} 540.0 30.0 0 0 {name=l9 lab=d3}
C {devices/lab_pin.sym} 540.0 50.0 0 0 {name=l10 lab=vdd}
C {devices/lab_pin.sym} 540.0 70.0 0 0 {name=l11 lab=vss}
C {dt_tap.sym} 900 0 0 0 {name=XT4 }
C {devices/lab_pin.sym} 840.0 10.0 0 0 {name=l12 lab=d3}
C {devices/lab_pin.sym} 840.0 30.0 0 0 {name=l13 lab=d4}
C {devices/lab_pin.sym} 840.0 50.0 0 0 {name=l14 lab=vdd}
C {devices/lab_pin.sym} 840.0 70.0 0 0 {name=l15 lab=vss}
C {dt_tap.sym} 1200 0 0 0 {name=XT5 }
C {devices/lab_pin.sym} 1140.0 10.0 0 0 {name=l16 lab=d4}
C {devices/lab_pin.sym} 1140.0 30.0 0 0 {name=l17 lab=d5}
C {devices/lab_pin.sym} 1140.0 50.0 0 0 {name=l18 lab=vdd}
C {devices/lab_pin.sym} 1140.0 70.0 0 0 {name=l19 lab=vss}
C {dt_tap.sym} 1500 0 0 0 {name=XT6 }
C {devices/lab_pin.sym} 1440.0 10.0 0 0 {name=l20 lab=d5}
C {devices/lab_pin.sym} 1440.0 30.0 0 0 {name=l21 lab=d6}
C {devices/lab_pin.sym} 1440.0 50.0 0 0 {name=l22 lab=vdd}
C {devices/lab_pin.sym} 1440.0 70.0 0 0 {name=l23 lab=vss}
C {dt_tap.sym} 0 300 0 0 {name=XT7 }
C {devices/lab_pin.sym} -60.0 310.0 0 0 {name=l24 lab=d6}
C {devices/lab_pin.sym} -60.0 330.0 0 0 {name=l25 lab=d7}
C {devices/lab_pin.sym} -60.0 350.0 0 0 {name=l26 lab=vdd}
C {devices/lab_pin.sym} -60.0 370.0 0 0 {name=l27 lab=vss}
C {sky130_stdcells/mux2_1.sym} 300 300 0 0 {name=XM0 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 260.0 280.0 0 0 {name=l28 lab=pwm_rst}
C {devices/lab_pin.sym} 260.0 320.0 0 0 {name=l29 lab=d1}
C {devices/lab_pin.sym} 260.0 360.0 0 0 {name=l30 lab=s0}
C {devices/lab_pin.sym} 340.0 300.0 0 0 {name=l31 lab=m01}
C {sky130_stdcells/mux2_1.sym} 600 300 0 0 {name=XM1 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 560.0 280.0 0 0 {name=l32 lab=d2}
C {devices/lab_pin.sym} 560.0 320.0 0 0 {name=l33 lab=d3}
C {devices/lab_pin.sym} 560.0 360.0 0 0 {name=l34 lab=s0}
C {devices/lab_pin.sym} 640.0 300.0 0 0 {name=l35 lab=m23}
C {sky130_stdcells/mux2_1.sym} 900 300 0 0 {name=XM2 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 860.0 280.0 0 0 {name=l36 lab=d4}
C {devices/lab_pin.sym} 860.0 320.0 0 0 {name=l37 lab=d5}
C {devices/lab_pin.sym} 860.0 360.0 0 0 {name=l38 lab=s0}
C {devices/lab_pin.sym} 940.0 300.0 0 0 {name=l39 lab=m45}
C {sky130_stdcells/mux2_1.sym} 1200 300 0 0 {name=XM3 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 1160.0 280.0 0 0 {name=l40 lab=d6}
C {devices/lab_pin.sym} 1160.0 320.0 0 0 {name=l41 lab=d7}
C {devices/lab_pin.sym} 1160.0 360.0 0 0 {name=l42 lab=s0}
C {devices/lab_pin.sym} 1240.0 300.0 0 0 {name=l43 lab=m67}
C {sky130_stdcells/mux2_1.sym} 1500 300 0 0 {name=XM4 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 1460.0 280.0 0 0 {name=l44 lab=m01}
C {devices/lab_pin.sym} 1460.0 320.0 0 0 {name=l45 lab=m23}
C {devices/lab_pin.sym} 1460.0 360.0 0 0 {name=l46 lab=s1}
C {devices/lab_pin.sym} 1540.0 300.0 0 0 {name=l47 lab=m03}
C {sky130_stdcells/mux2_1.sym} 0 600 0 0 {name=XM5 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} -40.0 580.0 0 0 {name=l48 lab=m45}
C {devices/lab_pin.sym} -40.0 620.0 0 0 {name=l49 lab=m67}
C {devices/lab_pin.sym} -40.0 660.0 0 0 {name=l50 lab=s1}
C {devices/lab_pin.sym} 40.0 600.0 0 0 {name=l51 lab=m47}
C {sky130_stdcells/mux2_1.sym} 300 600 0 0 {name=XM6 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 260.0 580.0 0 0 {name=l52 lab=m03}
C {devices/lab_pin.sym} 260.0 620.0 0 0 {name=l53 lab=m47}
C {devices/lab_pin.sym} 260.0 660.0 0 0 {name=l54 lab=s2}
C {devices/lab_pin.sym} 340.0 600.0 0 0 {name=l55 lab=rst_d}
C {sky130_stdcells/nor2_1.sym} 600 600 0 0 {name=XL1 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 540.0 580.0 0 0 {name=l56 lab=rst_d}
C {devices/lab_pin.sym} 540.0 620.0 0 0 {name=l57 lab=qb}
C {devices/lab_pin.sym} 660.0 600.0 0 0 {name=l58 lab=hs_pwm}
C {sky130_stdcells/nor2_1.sym} 900 600 0 0 {name=XL2 VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 840.0 580.0 0 0 {name=l59 lab=pwm_set}
C {devices/lab_pin.sym} 840.0 620.0 0 0 {name=l60 lab=hs_pwm}
C {devices/lab_pin.sym} 960.0 600.0 0 0 {name=l61 lab=qb}
