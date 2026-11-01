# Learning notes

## Phase 0
- A plain `docker exec` does not load the tool environment; `bash -lc` is required.
- ngspice `d_cosim` loads a shared library built by `vlnggen` (Verilator). Verilog vector ports appear
  as separate digital nodes, most-significant bit first.
- Digital nodes need `adc_bridge` / `dac_bridge` to connect to analog nodes.
