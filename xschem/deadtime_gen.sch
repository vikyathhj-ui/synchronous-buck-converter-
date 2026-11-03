v {xschem version=3.4.7RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -600 0 0 0 {name=p0 lab=pwm}
C {devices/iopin.sym} -600 40 0 0 {name=p1 lab=ls_en}
C {devices/iopin.sym} -600 80 0 0 {name=p2 lab=hs_on_s}
C {devices/iopin.sym} -600 120 0 0 {name=p3 lab=ls_on_s}
C {devices/iopin.sym} -600 160 0 0 {name=p4 lab=hs_on}
C {devices/iopin.sym} -600 200 0 0 {name=p5 lab=ls_on}
C {devices/iopin.sym} -600 240 0 0 {name=p6 lab=hl0}
C {devices/iopin.sym} -600 280 0 0 {name=p7 lab=hl1}
C {devices/iopin.sym} -600 320 0 0 {name=p8 lab=hl2}
C {devices/iopin.sym} -600 360 0 0 {name=p9 lab=hl3}
C {devices/iopin.sym} -600 400 0 0 {name=p10 lab=hl4}
C {devices/iopin.sym} -600 440 0 0 {name=p11 lab=hl5}
C {devices/iopin.sym} -600 480 0 0 {name=p12 lab=hl6}
C {devices/iopin.sym} -600 520 0 0 {name=p13 lab=hl7}
C {devices/iopin.sym} -600 560 0 0 {name=p14 lab=lh0}
C {devices/iopin.sym} -600 600 0 0 {name=p15 lab=lh1}
C {devices/iopin.sym} -600 640 0 0 {name=p16 lab=lh2}
C {devices/iopin.sym} -600 680 0 0 {name=p17 lab=lh3}
C {devices/iopin.sym} -600 720 0 0 {name=p18 lab=lh4}
C {devices/iopin.sym} -600 760 0 0 {name=p19 lab=lh5}
C {devices/iopin.sym} -600 800 0 0 {name=p20 lab=lh6}
C {devices/iopin.sym} -600 840 0 0 {name=p21 lab=lh7}
C {devices/iopin.sym} -600 880 0 0 {name=p22 lab=vdd}
C {devices/iopin.sym} -600 920 0 0 {name=p23 lab=vin}
C {devices/iopin.sym} -600 960 0 0 {name=p24 lab=vss}
C {sky130_fd_sc_hvl__lsbufhv2lv_1.sym} 0 0 0 0 {name=XSH}
C {devices/lab_pin.sym} -60.0 10.0 0 0 {name=l0 lab=hs_on_s}
C {devices/lab_pin.sym} -60.0 30.0 0 0 {name=l1 lab=vdd}
C {devices/lab_pin.sym} -60.0 50.0 0 0 {name=l2 lab=vss}
C {devices/lab_pin.sym} -60.0 70.0 0 0 {name=l3 lab=vss}
C {devices/lab_pin.sym} -60.0 90.0 0 0 {name=l4 lab=vin}
C {devices/lab_pin.sym} -60.0 110.0 0 0 {name=l5 lab=vin}
C {devices/lab_pin.sym} -60.0 130.0 0 0 {name=l6 lab=hs_on_lv}
C {sky130_fd_sc_hvl__lsbufhv2lv_1.sym} 300 0 0 0 {name=XSL}
C {devices/lab_pin.sym} 240.0 10.0 0 0 {name=l7 lab=ls_on_s}
C {devices/lab_pin.sym} 240.0 30.0 0 0 {name=l8 lab=vdd}
C {devices/lab_pin.sym} 240.0 50.0 0 0 {name=l9 lab=vss}
C {devices/lab_pin.sym} 240.0 70.0 0 0 {name=l10 lab=vss}
C {devices/lab_pin.sym} 240.0 90.0 0 0 {name=l11 lab=vin}
C {devices/lab_pin.sym} 240.0 110.0 0 0 {name=l12 lab=vin}
C {devices/lab_pin.sym} 240.0 130.0 0 0 {name=l13 lab=ls_on_lv}
C {sky130_stdcells/inv_1.sym} 600 0 0 0 {name=XIH VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 560.0 0.0 0 0 {name=l14 lab=hs_on_lv}
C {devices/lab_pin.sym} 640.0 0.0 0 0 {name=l15 lab=hs_off_ok}
C {sky130_stdcells/inv_1.sym} 900 0 0 0 {name=XIL VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 860.0 0.0 0 0 {name=l16 lab=ls_on_lv}
C {devices/lab_pin.sym} 940.0 0.0 0 0 {name=l17 lab=ls_off_ok}
C {dt_prog.sym} 1200 0 0 0 {name=XDH }
C {devices/lab_pin.sym} 1140.0 10.0 0 0 {name=l18 lab=hs_off_ok}
C {devices/lab_pin.sym} 1140.0 30.0 0 0 {name=l19 lab=hl_ok}
C {devices/lab_pin.sym} 1140.0 50.0 0 0 {name=l20 lab=hl0}
C {devices/lab_pin.sym} 1140.0 70.0 0 0 {name=l21 lab=hl1}
C {devices/lab_pin.sym} 1140.0 90.0 0 0 {name=l22 lab=hl2}
C {devices/lab_pin.sym} 1140.0 110.0 0 0 {name=l23 lab=hl3}
C {devices/lab_pin.sym} 1140.0 130.0 0 0 {name=l24 lab=hl4}
C {devices/lab_pin.sym} 1140.0 150.0 0 0 {name=l25 lab=hl5}
C {devices/lab_pin.sym} 1140.0 170.0 0 0 {name=l26 lab=hl6}
C {devices/lab_pin.sym} 1140.0 190.0 0 0 {name=l27 lab=hl7}
C {devices/lab_pin.sym} 1140.0 210.0 0 0 {name=l28 lab=vdd}
C {devices/lab_pin.sym} 1140.0 230.0 0 0 {name=l29 lab=vss}
C {dt_prog.sym} 1500 0 0 0 {name=XDL }
C {devices/lab_pin.sym} 1440.0 10.0 0 0 {name=l30 lab=ls_off_ok}
C {devices/lab_pin.sym} 1440.0 30.0 0 0 {name=l31 lab=lh_ok}
C {devices/lab_pin.sym} 1440.0 50.0 0 0 {name=l32 lab=lh0}
C {devices/lab_pin.sym} 1440.0 70.0 0 0 {name=l33 lab=lh1}
C {devices/lab_pin.sym} 1440.0 90.0 0 0 {name=l34 lab=lh2}
C {devices/lab_pin.sym} 1440.0 110.0 0 0 {name=l35 lab=lh3}
C {devices/lab_pin.sym} 1440.0 130.0 0 0 {name=l36 lab=lh4}
C {devices/lab_pin.sym} 1440.0 150.0 0 0 {name=l37 lab=lh5}
C {devices/lab_pin.sym} 1440.0 170.0 0 0 {name=l38 lab=lh6}
C {devices/lab_pin.sym} 1440.0 190.0 0 0 {name=l39 lab=lh7}
C {devices/lab_pin.sym} 1440.0 210.0 0 0 {name=l40 lab=vdd}
C {devices/lab_pin.sym} 1440.0 230.0 0 0 {name=l41 lab=vss}
C {sky130_stdcells/inv_1.sym} 0 300 0 0 {name=XIP VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} -40.0 300.0 0 0 {name=l42 lab=pwm}
C {devices/lab_pin.sym} 40.0 300.0 0 0 {name=l43 lab=pwm_n}
C {sky130_stdcells/and2_1.sym} 300 300 0 0 {name=XAH VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 240.0 280.0 0 0 {name=l44 lab=pwm}
C {devices/lab_pin.sym} 240.0 320.0 0 0 {name=l45 lab=lh_ok}
C {devices/lab_pin.sym} 360.0 300.0 0 0 {name=l46 lab=hs_on}
C {sky130_stdcells/and3_1.sym} 600 300 0 0 {name=XAL VGND=vss VNB=vss VPB=vdd VPWR=vdd prefix=sky130_fd_sc_hd__}
C {devices/lab_pin.sym} 540.0 260.0 0 0 {name=l47 lab=pwm_n}
C {devices/lab_pin.sym} 540.0 300.0 0 0 {name=l48 lab=ls_en}
C {devices/lab_pin.sym} 540.0 340.0 0 0 {name=l49 lab=hl_ok}
C {devices/lab_pin.sym} 660.0 300.0 0 0 {name=l50 lab=ls_on}
