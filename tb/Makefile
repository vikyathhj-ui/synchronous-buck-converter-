# cocotb testbench for the controller. Run inside iic-osic:
#   make -C tb              (all tests, Icarus)
#   make -C tb QUICK=1      (short version, used by CI)
#   COCOTB_TEST_FILTER=test_load_step make -C tb
SIM ?= icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(abspath ../rtl/therm2bin.v) $(abspath ../rtl/buck_ctrl_top.v)
COCOTB_TOPLEVEL = buck_ctrl_top
# 15.625 ns clock: needs fs precision for an exact 50 % duty cycle
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1fs
COCOTB_TEST_MODULES = test_buck_ctrl
export PYTHONPATH := $(abspath ..):$(abspath .):$(PYTHONPATH)
export QUICK ?= 0

include $(shell cocotb-config --makefiles)/Makefile.sim
