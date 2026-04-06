module snn_top_uart #(
    parameter N_INPUTS = 9,
    parameter SENSOR_W = 12,
    parameter V_WIDTH  = 24,
    parameter I_WIDTH  = 16
) (
    input  wire clk_50mhz,
    input  wire reset_n,
    input  wire uart_rx,
    input  wire train_btn,
    input  wire left_btn,
    input  wire right_btn,
    output wire pwm_left,
    output wire pwm_right,
    output wire [9:0] duty_left_10,
    output wire [9:0] duty_right_10,
    output wire signed [V_WIDTH-1:0] v_left_dbg,
    output wire signed [V_WIDTH-1:0] v_right_dbg
);
    wire reset = ~reset_n;
    wire [7:0] rx_byte;
    wire       rx_valid;
    uart_rx #(.CLK_FREQ(50000000), .BAUD(115200)) u_uart (
        .clk(clk_50mhz), .reset(reset), .rx(uart_rx), .data_out(rx_byte), .data_valid(rx_valid)
    );
    wire [N_INPUTS*SENSOR_W-1:0] sensor_bus;
    wire frame_valid;
    sensor_frame_rx #(.N_INPUTS(N_INPUTS)) u_fr (
        .clk(clk_50mhz), .reset(reset), .byte_in(rx_byte), .byte_valid(rx_valid), .sensor_bus(sensor_bus), .frame_valid(frame_valid)
    );
    wire [N_INPUTS-1:0] spikes_in;
    input_encoder #(.N_INPUTS(N_INPUTS), .SENSOR_W(SENSOR_W)) u_enc (
        .clk(clk_50mhz), .reset(reset), .sensor_in(sensor_bus), .spike_out(spikes_in)
    );
    wire signed [23:0] i_syn_left_24;
    wire signed [23:0] i_syn_right_24;
    wire [1:0]  upd_sel;
    wire [8:0]  upd_mask;
    wire        upd_en;
    wire [15:0] delta_val;
    crossbar_interface #(.N_IN(N_INPUTS), .N_OUT(2)) u_xbar (
        .clk(clk_50mhz), .reset(reset), .mode_real(1'b0), .pre_spike(spikes_in), .v_spike(16'h0100),
        .update_en(upd_en), .update_sel(upd_sel), .update_mask(upd_mask), .delta_val(delta_val), .g_min(16'h0000), .g_max(16'hFFFF),
        .i_syn_left(i_syn_left_24), .i_syn_right(i_syn_right_24),
        .dac_sclk(), .dac_mosi(), .dac_miso(1'b0), .dac_cs_n(), .adc_sclk(), .adc_mosi(), .adc_miso(1'b0), .adc_cs_n()
    );
    wire spike_left, spike_right;
    wire signed [V_WIDTH-1:0] v_left, v_right;
    wire signed [I_WIDTH-1:0] i_left  = i_syn_left_24[23:8];
    wire signed [I_WIDTH-1:0] i_right = i_syn_right_24[23:8];
    lif_neuron #(.V_WIDTH(V_WIDTH), .I_WIDTH(I_WIDTH)) u_lif_left (
        .clk(clk_50mhz), .reset(reset), .enable(1'b1), .i_syn(i_left), .tau_shift(5'd4), .threshold($signed(24'sh000500)), .v_reset($signed(24'sh000000)), .spike_out(spike_left), .v_out(v_left)
    );
    lif_neuron #(.V_WIDTH(V_WIDTH), .I_WIDTH(I_WIDTH)) u_lif_right (
        .clk(clk_50mhz), .reset(reset), .enable(1'b1), .i_syn(i_right), .tau_shift(5'd4), .threshold($signed(24'sh000500)), .v_reset($signed(24'sh000000)), .spike_out(spike_right), .v_out(v_right)
    );
    assign v_left_dbg  = v_left;
    assign v_right_dbg = v_right;
    training_controller #(.N_IN(N_INPUTS), .N_OUT(2)) u_train (
        .clk(clk_50mhz), .reset(reset), .train(train_btn), .btn_left(left_btn), .btn_right(right_btn), .pre_spike(spikes_in), .post_spike({spike_right, spike_left}), .delta_base(16'h0010),
        .update_en(upd_en), .update_sel(upd_sel), .update_mask(upd_mask), .delta_val(delta_val)
    );
    motor_output u_motor (
        .clk(clk_50mhz), .reset(reset), .spike_left(spike_left), .spike_right(spike_right), .window_len(16'd4096), .pwm_left(pwm_left), .pwm_right(pwm_right), .duty_left_out(duty_left_10), .duty_right_out(duty_right_10)
    );
endmodule
