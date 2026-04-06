// Top-Level SNN for 3x3 LDR grid -> 2 motor outputs
// - Two LIF neurons
// - 9x2 memristor crossbar (virtual or real)
// - Training controller for supervised updates
// - PWM motor drivers

module snn_top #(
    parameter N_INPUTS   = 9,
    parameter SENSOR_W   = 12,
    parameter V_WIDTH    = 24,
    parameter I_WIDTH    = 16
) (
    input  wire                     clk_50mhz,
    input  wire                     reset_n,

    // Mode select: 1=virtual memristors, 0=real
    input  wire                     mode_virtual,

    // Packed ADC sensor inputs (12-bit each)
    input  wire [N_INPUTS*SENSOR_W-1:0] sensor_in,

    // Buttons
    input  wire                     train_btn,
    input  wire                     left_btn,
    input  wire                     right_btn,

    // SPI interfaces
    output wire                     dac_sclk,
    output wire                     dac_mosi,
    input  wire                     dac_miso,
    output wire                     dac_cs_n,
    output wire                     adc_sclk,
    output wire                     adc_mosi,
    input  wire                     adc_miso,
    output wire                     adc_cs_n,

    // Motor PWM outputs
    output wire                     pwm_left,
    output wire                     pwm_right,

    // Debug
    output wire signed [V_WIDTH-1:0] v_left_dbg,
    output wire signed [V_WIDTH-1:0] v_right_dbg
);

    wire reset = ~reset_n;

    // Input encoder
    wire [N_INPUTS-1:0] spikes_in;
    input_encoder #(.N_INPUTS(N_INPUTS), .SENSOR_W(SENSOR_W)) u_enc (
        .clk       (clk_50mhz),
        .reset     (reset),
        .sensor_in (sensor_in),
        .spike_out (spikes_in)
    );

    // Crossbar interface (virtual summation)
    wire signed [23:0] i_syn_left_24;
    wire signed [23:0] i_syn_right_24;
    wire [1:0]         upd_sel;
    wire [8:0]         upd_mask;
    wire               upd_en;
    wire [15:0]        delta_val;
    crossbar_interface #(.N_IN(N_INPUTS), .N_OUT(2)) u_xbar (
        .clk         (clk_50mhz),
        .reset       (reset),
        .mode_real   (~mode_virtual),
        .pre_spike   (spikes_in),
        .v_spike     (16'h0100),
        .update_en   (upd_en),
        .update_sel  (upd_sel),
        .update_mask (upd_mask),
        .delta_val   (delta_val),
        .g_min       (16'h0000),
        .g_max       (16'hFFFF),
        .i_syn_left  (i_syn_left_24),
        .i_syn_right (i_syn_right_24),
        .dac_sclk    (dac_sclk),
        .dac_mosi    (dac_mosi),
        .dac_miso    (dac_miso),
        .dac_cs_n    (dac_cs_n),
        .adc_sclk    (adc_sclk),
        .adc_mosi    (adc_mosi),
        .adc_miso    (adc_miso),
        .adc_cs_n    (adc_cs_n)
    );

    // LIF neurons
    wire spike_left, spike_right;
    wire signed [V_WIDTH-1:0] v_left, v_right;
    // Scale 24-bit syn current down to 16-bit
    wire signed [I_WIDTH-1:0] i_left  = i_syn_left_24[23:8];
    wire signed [I_WIDTH-1:0] i_right = i_syn_right_24[23:8];

    lif_neuron #(.V_WIDTH(V_WIDTH), .I_WIDTH(I_WIDTH)) u_lif_left (
        .clk       (clk_50mhz),
        .reset     (reset),
        .enable    (1'b1),
        .i_syn     (i_left),
        .tau_shift (5'd4),
        .threshold ($signed(24'sh000500)),
        .v_reset   ($signed(24'sh000000)),
        .spike_out (spike_left),
        .v_out     (v_left)
    );

    lif_neuron #(.V_WIDTH(V_WIDTH), .I_WIDTH(I_WIDTH)) u_lif_right (
        .clk       (clk_50mhz),
        .reset     (reset),
        .enable    (1'b1),
        .i_syn     (i_right),
        .tau_shift (5'd4),
        .threshold ($signed(24'sh000500)),
        .v_reset   ($signed(24'sh000000)),
        .spike_out (spike_right),
        .v_out     (v_right)
    );

    assign v_left_dbg  = v_left;
    assign v_right_dbg = v_right;

    // Training controller
    training_controller #(.N_IN(N_INPUTS), .N_OUT(2)) u_train (
        .clk         (clk_50mhz),
        .reset       (reset),
        .train       (train_btn),
        .btn_left    (left_btn),
        .btn_right   (right_btn),
        .pre_spike   (spikes_in),
        .post_spike  ({spike_right, spike_left}),
        .delta_base  (16'h0010),
        .update_en   (upd_en),
        .update_sel  (upd_sel),
        .update_mask (upd_mask),
        .delta_val   (delta_val)
    );

    // Motor outputs
    motor_output u_motor (
        .clk        (clk_50mhz),
        .reset      (reset),
        .spike_left (spike_left),
        .spike_right(spike_right),
        .window_len (16'd4096),
        .pwm_left   (pwm_left),
        .pwm_right  (pwm_right)
    );

endmodule

