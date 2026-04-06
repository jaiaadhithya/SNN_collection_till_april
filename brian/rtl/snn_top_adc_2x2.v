module snn_top_adc_2x2 (
    input  wire        clk_50mhz,
    input  wire        reset_n,
    input  wire [11:0] adc_ch0,
    input  wire [11:0] adc_ch1,
    input  wire [11:0] adc_ch2,
    input  wire [11:0] adc_ch3,
    input  wire        train_btn,
    input  wire        left_btn,
    input  wire        right_btn,
    output wire        pwm_left,
    output wire        pwm_right,
    output wire signed [23:0] v_left_dbg,
    output wire signed [23:0] v_right_dbg
);
    wire [47:0] sensor_bus;
    assign sensor_bus = {adc_ch3, adc_ch2, adc_ch1, adc_ch0};
    wire [3:0] spikes_in;
    input_encoder #(.N_INPUTS(4), .SENSOR_W(12)) u_enc (
        .clk(clk_50mhz), .reset(~reset_n), .sensor_in(sensor_bus), .spike_out(spikes_in)
    );
    wire signed [23:0] i_syn_left_24;
    wire signed [23:0] i_syn_right_24;
    wire [1:0]  upd_sel;
    wire [3:0]  upd_mask;
    wire        upd_en;
    wire [15:0] delta_val;
    crossbar_interface #(.N_IN(4), .N_OUT(2)) u_xbar (
        .clk(clk_50mhz), .reset(~reset_n), .mode_real(1'b0), .pre_spike(spikes_in), .v_spike(16'h0100),
        .update_en(upd_en), .update_sel(upd_sel), .update_mask(upd_mask), .delta_val(delta_val), .g_min(16'h0000), .g_max(16'hFFFF),
        .i_syn_left(i_syn_left_24), .i_syn_right(i_syn_right_24),
        .dac_sclk(), .dac_mosi(), .dac_miso(1'b0), .dac_cs_n(), .adc_sclk(), .adc_mosi(), .adc_miso(1'b0), .adc_cs_n()
    );
    wire spike_left, spike_right;
    wire signed [23:0] v_left, v_right;
    wire signed [15:0] i_left  = i_syn_left_24[23:8];
    wire signed [15:0] i_right = i_syn_right_24[23:8];
    lif_neuron #(.V_WIDTH(24), .I_WIDTH(16)) u_lif_left (
        .clk(clk_50mhz), .reset(~reset_n), .enable(1'b1), .i_syn(i_left), .tau_shift(5'd4), .threshold($signed(24'sh000500)), .v_reset($signed(24'sh000000)), .spike_out(spike_left), .v_out(v_left)
    );
    lif_neuron #(.V_WIDTH(24), .I_WIDTH(16)) u_lif_right (
        .clk(clk_50mhz), .reset(~reset_n), .enable(1'b1), .i_syn(i_right), .tau_shift(5'd4), .threshold($signed(24'sh000500)), .v_reset($signed(24'sh000000)), .spike_out(spike_right), .v_out(v_right)
    );
    assign v_left_dbg  = v_left;
    assign v_right_dbg = v_right;
    training_controller #(.N_IN(4), .N_OUT(2)) u_train (
        .clk(clk_50mhz), .reset(~reset_n), .train(train_btn), .btn_left(left_btn), .btn_right(right_btn), .pre_spike(spikes_in), .post_spike({spike_right, spike_left}), .delta_base(16'h0010),
        .update_en(upd_en), .update_sel(upd_sel), .update_mask(upd_mask), .delta_val(delta_val)
    );
    motor_output u_motor (
        .clk(clk_50mhz), .reset(~reset_n), .spike_left(spike_left), .spike_right(spike_right), .window_len(16'd4096), .pwm_left(pwm_left), .pwm_right(pwm_right), .duty_left_out(), .duty_right_out()
    );
endmodule

