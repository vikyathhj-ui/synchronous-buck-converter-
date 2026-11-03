// Digital controller for the SKY130 synchronous buck converter.
//
// Golden model: model/ctrl_ref.py (CtrlRef). The timing contract is documented there; in short,
// with a 64 MHz clock and one switching period = 64 clocks (cnt = 0..63):
//   cycle 63  ilim_sample high: the valley comparator samples iL; registered at edge 0.
//   cycle 0   new period: mode / duty decided last period take effect; pwm_set high unless the
//             converter is stopped, the duty is 0 or the valley comparator tripped.
//             adc_sample high: the window ADC samples VOUT at this edge.
//   end of 1  ADC thermometer registered and decoded (therm2bin): the comparators have two clocks
//             (31 ns) to resolve, which the cold slow corners need.
//   cycle 2   PID products registered.
//   cycle 3   PID sum, integrator, VREF ramp, fault score, CCM/DCM counters and the mode FSM
//             update at the end of this cycle (registers *_nxt, vref_code).
//   cycle coarse  pwm_rst high; the analog delay line ends the HS pulse at the tap selected by
//             tap_sel = round(fine * N / 8), N = calibrated delay elements per clock period.
//   cycle 40  tdc_launch rises into the 72-element replica line; its taps are sampled at the end
//             of cycle 40 (one Tclk later) and counted in cycle 41 (delay-line calibration).
//   cycles > coarse  LS phase; in DCM a zero-cross turns LS off for the rest of the period.
`default_nettype none

module buck_ctrl_top #(
    parameter integer FRAC = 5
) (
    input  wire        clk,
    input  wire        rst_n,
    // APB3 slave (word addresses)
    input  wire        psel,
    input  wire        penable,
    input  wire        pwrite,
    /* verilator lint_off UNUSEDSIGNAL */
    input  wire [5:0]  paddr,         // byte address; bits [1:0] unused (word registers)
    input  wire [31:0] pwdata,        // registers use bits [15:0]
    /* verilator lint_on UNUSEDSIGNAL */
    output reg  [31:0] prdata,
    output wire        pready,
    output wire        pslverr,
    // analog front end
    input  wire [14:0] adc_therm,     // window-ADC comparators
    input  wire        ilim_cmp,      // valley current-limit comparator
    input  wire        zc_cmp,        // zero-cross comparator (clocked every cycle)
    output reg         adc_sample,
    output reg         ilim_sample,
    output reg         pwm_set,
    output reg         pwm_rst,
    output reg  [5:0]  tap_sel,       // main delay-line tap for the fine code (calibrated)
    output reg         tdc_launch,    // edge into the replica delay line (cycles 40..47)
    input  wire [71:0] tdc_therm,     // replica delay-line taps
    output reg         ls_en,
    output reg  [7:0]  vref_code,     // VREF DAC, 10 mV / code
    output wire [7:0]  ilim_code,     // current-limit threshold DAC, 2 mA / code
    output wire [7:0]  dt_hl_therm,   // dead time HS off -> LS on, thermometer, (code + 1) taps
    output wire [7:0]  dt_lh_therm,   // dead time LS off -> HS on
    output reg  [2:0]  mode
);
    localparam [2:0] IDLE = 3'd0, SS = 3'd1, CCM = 3'd2, DCM = 3'd3, FAULT = 3'd4;
    localparam [7:0] N_ZC = 8'd8;
    localparam [7:0] VREF_MIN = 8'd100, VREF_MAX = 8'd250;
    localparam [15:0] SS_LEN_MIN = 16'd256;
    localparam [31:0] ID = 32'hB0C4_0001;

    // ------------------------------------------------------------------ registers
    reg        r_enable, r_dcm_en, fault_clr_pend;
    reg [7:0]  r_vref, r_ilim, r_fault_n;
    reg [11:0] r_kp, r_ki, r_kd;
    reg [2:0]  r_dt_hl, r_dt_lh;
    reg [15:0] r_ss_len;
    reg [8:0]  r_dmax;

    // ------------------------------------------------------------------ datapath state
    reg [5:0]  cnt;
    reg [2:0]  mode_nxt;
    reg [8:0]  duty_cur, duty_nxt;
    /* verilator lint_off UNUSEDSIGNAL */
    reg [8:0]  dmax_lat;                  // DMAX in force this period (used by the formal properties)
    /* verilator lint_on UNUSEDSIGNAL */
    reg        hs_en, trip_q, zc_seen, zc_prev;
    reg signed [3:0]  e_q, e1;
    reg [15:0] acc;
    reg [7:0]  trip_score, zc_run, nzc_run;
    reg [16:0] ss_acc;
    // delay-line calibration (model/ctrl_ref.py: CtrlRef.calibrate)
    reg [71:0] tdc_q;
    reg [6:0]  n_meas;
    reg        n_meas_valid;
    reg [10:0] cal_sum;
    reg [3:0]  cal_cnt;
    reg [10:0] n_cal_q4;
    reg signed [23:0] p_kp, p_ki, p_kd;

    assign pready = 1'b1;
    assign pslverr = 1'b0;
    assign ilim_code = r_ilim;
    // thermometer with (code + 1) ones: code 0 -> 8'h01, code 7 -> 8'hFF
    assign dt_hl_therm = ~(8'hFF << ({1'b0, r_dt_hl} + 4'd1));
    assign dt_lh_therm = ~(8'hFF << ({1'b0, r_dt_lh} + 4'd1));

    wire apb_wr = psel & penable & pwrite;

    // APB writes, with the same clamping as Regs.write() in the golden model
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_enable <= 1'b0;
            r_dcm_en <= 1'b0;
            fault_clr_pend <= 1'b0;
            r_vref <= 8'd180;
            r_kp <= 12'd86;
            r_ki <= 12'd3;
            r_kd <= 12'd1131;
            r_dt_hl <= 3'd3;
            r_dt_lh <= 3'd3;
            r_ilim <= 8'd125;
            r_ss_len <= 16'd1000;
            r_dmax <= 9'd496;
            r_fault_n <= 8'd64;
        end else begin
            if (cnt == 6'd3)
                fault_clr_pend <= 1'b0;          // consumed by the FSM in this cycle
            if (apb_wr) begin
                case (paddr[5:2])
                    4'h0: begin
                        r_enable <= pwdata[0];
                        r_dcm_en <= pwdata[1];
                        if (pwdata[8])
                            fault_clr_pend <= 1'b1;
                    end
                    4'h1: r_vref <= (pwdata[7:0] < VREF_MIN) ? VREF_MIN :
                                    (pwdata[7:0] > VREF_MAX) ? VREF_MAX : pwdata[7:0];
                    4'h2: r_kp <= pwdata[11:0];
                    4'h3: r_ki <= pwdata[11:0];
                    4'h4: r_kd <= pwdata[11:0];
                    4'h5: begin
                        r_dt_hl <= pwdata[2:0];
                        r_dt_lh <= pwdata[6:4];
                    end
                    4'h6: r_ilim <= pwdata[7:0];
                    4'h7: r_ss_len <= (pwdata[15:0] < SS_LEN_MIN) ? SS_LEN_MIN : pwdata[15:0];
                    4'h8: r_dmax <= pwdata[8:0];
                    4'h9: r_fault_n <= pwdata[7:0];
                    default: ;
                endcase
            end
        end
    end

    always @(*) begin
        case (paddr[5:2])
            4'h0:    prdata = {30'd0, r_dcm_en, r_enable};
            4'h1:    prdata = {24'd0, r_vref};
            4'h2:    prdata = {20'd0, r_kp};
            4'h3:    prdata = {20'd0, r_ki};
            4'h4:    prdata = {20'd0, r_kd};
            4'h5:    prdata = {25'd0, r_dt_lh, 1'b0, r_dt_hl};
            4'h6:    prdata = {24'd0, r_ilim};
            4'h7:    prdata = {16'd0, r_ss_len};
            4'h8:    prdata = {23'd0, r_dmax};
            4'h9:    prdata = {24'd0, r_fault_n};
            4'hA:    prdata = {6'd0, hs_en, duty_cur, vref_code, e_q, 1'b0, mode};   // STATUS
            4'hB:    prdata = ID;
            4'hC:    prdata = {21'd0, n_cal_q4};                                   // CAL
            default: prdata = 32'd0;
        endcase
    end

    // ------------------------------------------------------------------ combinational helpers
    wire signed [3:0] e_in;
    therm2bin u_therm2bin (.therm(adc_therm), .code(e_in));

    wire running     = (mode == SS) || (mode == CCM) || (mode == DCM);
    wire running_nxt = (mode_nxt == SS) || (mode_nxt == CCM) || (mode_nxt == DCM);

    wire [8:0] duty_nxt_cl = (duty_nxt > r_dmax) ? r_dmax : duty_nxt;
    wire       hs_en_new   = running_nxt && (duty_nxt_cl != 9'd0) && !ilim_cmp;
    wire [5:0] coarse_cur  = duty_cur[8:3];
    wire [5:0] coarse_eff  = hs_en ? coarse_cur : 6'd0;
    wire       zc_q        = zc_cmp && (cnt > coarse_eff);

    // PID (model/ctrl_ref.py: CtrlRef._pid)
    wire signed [4:0]  de      = {e_q[3], e_q} - {e1[3], e1};
    wire signed [23:0] e_x     = {{20{e_q[3]}}, e_q};
    wire signed [23:0] de_x    = {{19{de[4]}}, de};
    wire signed [23:0] acc_x   = {8'd0, acc};
    wire signed [23:0] acc_hi  = {10'd0, r_dmax, 5'd0};
    wire signed [23:0] acc_sum = acc_x + p_ki;
    wire signed [23:0] acc_cl  = (acc_sum < 0) ? 24'sd0 : (acc_sum > acc_hi) ? acc_hi : acc_sum;
    wire signed [23:0] acc_new = trip_q ? acc_x : acc_cl;
    wire signed [23:0] s_sum   = p_kp + acc_new + p_kd;
    wire signed [23:0] u_r     = (s_sum + (24'sd1 <<< (FRAC - 1))) >>> FRAC;
    wire signed [23:0] dmax_x  = {15'd0, r_dmax};
    wire [8:0]         d_pid   = (u_r < 0) ? 9'd0 : (u_r > dmax_x) ? r_dmax : u_r[8:0];

    // fault score and CCM/DCM run counters
    wire [7:0] trip_score_u = trip_q ? ((trip_score > 8'd252) ? 8'd255 : trip_score + 8'd3)
                                     : ((trip_score == 8'd0) ? 8'd0 : trip_score - 8'd1);
    wire [7:0] zc_run_u  = (mode == CCM) ? (zc_prev ? ((zc_run == 8'd255) ? zc_run : zc_run + 8'd1) : 8'd0)
                                         : zc_run;
    wire [7:0] nzc_run_u = (mode == DCM) ? (!zc_prev ? ((nzc_run == 8'd255) ? nzc_run : nzc_run + 8'd1) : 8'd0)
                                         : nzc_run;

    // VREF ramp, at most one code per period
    wire [16:0] ss_sum   = ss_acc + {9'd0, r_vref};
    wire        ss_step  = (vref_code != r_vref) && (ss_sum >= {1'b0, r_ss_len});
    wire [16:0] ss_acc_u = (vref_code == r_vref) ? 17'd0 : ss_step ? ss_sum - {1'b0, r_ss_len} : ss_sum;
    wire [7:0]  vref_u   = !ss_step ? vref_code : (vref_code < r_vref) ? vref_code + 8'd1 : vref_code - 8'd1;

    // mode FSM
    reg [2:0] nxt;
    always @(*) begin
        nxt = mode;
        if (!r_enable)
            nxt = IDLE;
        else if (mode == IDLE)
            nxt = SS;
        else if (mode == FAULT) begin
            if (fault_clr_pend)
                nxt = SS;
        end else if ((r_fault_n != 8'd0) && (trip_score_u >= r_fault_n))
            nxt = FAULT;
        else if (mode == SS) begin
            if (vref_u == r_vref)
                nxt = CCM;
        end else if (mode == CCM) begin
            if (r_dcm_en && (zc_run_u >= N_ZC))
                nxt = DCM;
        end else if (mode == DCM) begin
            // leave DCM at once if the ADC saturates high (VOUT far below VREF), see D18
            if (!r_dcm_en || (nzc_run_u >= N_ZC) || (e_q == 4'sd7))
                nxt = CCM;
        end
    end
    wire changed   = (nxt != mode);
    wire nxt_run   = (nxt == SS) || (nxt == CCM) || (nxt == DCM);
    wire loop_rst  = changed && ((nxt == IDLE) || (nxt == FAULT) ||
                                 ((nxt == SS) && ((mode == IDLE) || (mode == FAULT))));

    // delay-line calibration: popcount of the sampled replica taps, 16-period average with a
    // half-element hysteresis, tap = (fine * N_q4 + 64) >> 7
    function [6:0] popcount72(input [71:0] v);
        integer k;
        begin
            popcount72 = 7'd0;
            for (k = 0; k < 72; k = k + 1)
                popcount72 = popcount72 + {6'd0, v[k]};
        end
    endfunction
    wire [10:0] cal_sum_n = cal_sum + (n_meas_valid ? {4'd0, n_meas} : 11'd0);
    wire        cal_block = n_meas_valid && (cal_cnt == 4'd15);
    wire [10:0] cal_diff  = (cal_sum_n > n_cal_q4) ? cal_sum_n - n_cal_q4 : n_cal_q4 - cal_sum_n;
    wire [10:0] n_cal_new = (cal_block && (cal_diff > 11'd8)) ? cal_sum_n : n_cal_q4;
    // (fine * N_q4 + 64) >> 7: bits [6:0] are the rounding remainder, bit 13 is always 0
    // because 7 * 1152 + 64 < 2^13
    /* verilator lint_off UNUSEDSIGNAL */
    wire [13:0] tap_prod  = duty_nxt_cl[2:0] * n_cal_new + 14'd64;
    /* verilator lint_on UNUSEDSIGNAL */

    // ------------------------------------------------------------------ sequential datapath
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 6'd0;
            mode <= IDLE;
            mode_nxt <= IDLE;
            duty_cur <= 9'd0;
            duty_nxt <= 9'd0;
            dmax_lat <= 9'd496;
            hs_en <= 1'b0;
            trip_q <= 1'b0;
            zc_seen <= 1'b0;
            zc_prev <= 1'b0;
            e_q <= 4'sd0;
            e1 <= 4'sd0;
            acc <= 16'd0;
            trip_score <= 8'd0;
            zc_run <= 8'd0;
            nzc_run <= 8'd0;
            ss_acc <= 17'd0;
            vref_code <= 8'd0;
            p_kp <= 24'sd0;
            p_ki <= 24'sd0;
            p_kd <= 24'sd0;
            adc_sample <= 1'b0;
            ilim_sample <= 1'b0;
            pwm_set <= 1'b0;
            pwm_rst <= 1'b0;
            tap_sel <= 6'd0;
            tdc_launch <= 1'b0;
            tdc_q <= 72'd0;
            n_meas <= 7'd0;
            n_meas_valid <= 1'b0;
            cal_sum <= 11'd0;
            cal_cnt <= 4'd0;
            n_cal_q4 <= 11'd640;
            ls_en <= 1'b0;
        end else begin
            cnt <= cnt + 6'd1;
            ilim_sample <= (cnt == 6'd62);

            // replica-line TDC: launch high in cycles 40..47, sample at the end of cycle 40
            if (cnt == 6'd39)
                tdc_launch <= 1'b1;
            else if (cnt == 6'd47)
                tdc_launch <= 1'b0;
            if (cnt == 6'd40)
                tdc_q <= tdc_therm;
            if (cnt == 6'd41) begin
                n_meas <= popcount72(tdc_q);
                n_meas_valid <= 1'b1;
            end

            // period boundary (edge at the end of cycle 63)
            if (cnt == 6'd63) begin
                mode <= mode_nxt;
                duty_cur <= duty_nxt_cl;
                dmax_lat <= r_dmax;
                hs_en <= hs_en_new;
                trip_q <= ilim_cmp;
                pwm_set <= hs_en_new;
                pwm_rst <= hs_en_new && (duty_nxt_cl[8:3] == 6'd0);
                tap_sel <= tap_prod[12:7];
                if (n_meas_valid) begin
                    n_cal_q4 <= n_cal_new;
                    cal_sum <= cal_block ? 11'd0 : cal_sum_n;
                    cal_cnt <= cal_block ? 4'd0 : cal_cnt + 4'd1;
                end
                adc_sample <= 1'b1;
                ls_en <= running_nxt;
                zc_prev <= zc_seen | zc_q;
                zc_seen <= 1'b0;
            end else begin
                pwm_set <= 1'b0;
                adc_sample <= 1'b0;
                pwm_rst <= hs_en && (coarse_cur == cnt + 6'd1);
                if (zc_q) begin
                    zc_seen <= 1'b1;
                    if (mode == DCM)
                        ls_en <= 1'b0;       // DCM: LS off for the rest of the period
                end
            end

            // end of cycle 1: register the ADC result (two clocks after the sampling edge)
            if (cnt == 6'd1)
                e_q <= e_in;

            // cycle 2: PID products
            if (cnt == 6'd2) begin
                p_kp <= $signed({12'd0, r_kp}) * e_x;
                p_ki <= $signed({12'd0, r_ki}) * e_x;
                p_kd <= $signed({12'd0, r_kd}) * de_x;
            end

            // cycle 3: loop update and mode decision
            if (cnt == 6'd3) begin
                if (running) begin
                    trip_score <= trip_score_u;
                    zc_run <= zc_run_u;
                    nzc_run <= nzc_run_u;
                    acc <= acc_new[15:0];
                    e1 <= e_q;
                    ss_acc <= ss_acc_u;
                    vref_code <= vref_u;
                end
                mode_nxt <= nxt;
                duty_nxt <= (running && nxt_run && !loop_rst) ? d_pid : 9'd0;
                if (loop_rst) begin
                    acc <= 16'd0;
                    e1 <= 4'sd0;
                    vref_code <= 8'd0;
                    ss_acc <= 17'd0;
                    trip_score <= 8'd0;
                    zc_run <= 8'd0;
                    nzc_run <= 8'd0;
                end else if (changed && (nxt == DCM))
                    nzc_run <= 8'd0;
                else if (changed && (nxt == CCM))
                    zc_run <= 8'd0;
            end
        end
    end

`ifdef FORMAL
    // Safety properties (formal/buck_ctrl.sby), checked by k-induction.
    initial assume (!rst_n);
    always @(*) begin
        if (rst_n) begin
            // FSM stays legal
            assert (mode <= FAULT);
            assert (mode_nxt <= FAULT);
            // duty within limits
            assert (duty_cur <= dmax_lat);
            // anti-windup bounds the integrator to the duty range
            assert (acc <= 16'd16352);
            // dead-time selections are never zero taps
            assert (dt_hl_therm != 8'd0);
            assert (dt_lh_therm != 8'd0);
            // nothing switches unless the converter is running
            if (!running) begin
                assert (!pwm_set);
                assert (!ls_en);
            end
            if (pwm_set)
                assert (hs_en);
            // calibration state stays in range (sum of at most 16 counts of at most 72)
            assert (cal_sum <= 11'd72 * {7'd0, cal_cnt});
            assert (n_cal_q4 <= 11'd1152);
            assert (n_meas <= 7'd72);
        end
    end
`endif
endmodule

`default_nettype wire
