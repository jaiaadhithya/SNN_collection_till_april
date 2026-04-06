module snn_top_de10lite_2x2 (
    input  wire        clk_50mhz,
    input  wire        reset_n,
    input  wire [11:0] adc_ch0,
    input  wire [11:0] adc_ch1,
    input  wire [11:0] adc_ch2,
    input  wire [11:0] adc_ch3,
    input  wire [1:0]  KEY,
    input  wire [0:0]  SW,
    output wire        pwm_left,
    output wire        pwm_right,
    output wire signed [23:0] v_left_dbg,
    output wire signed [23:0] v_right_dbg
);
    wire train_btn  = SW[0];
    wire left_btn   = ~KEY[0];
    wire right_btn  = ~KEY[1];
    snn_top_adc_2x2 u_top (
        .clk_50mhz (clk_50mhz),
        .reset_n   (reset_n),
        .adc_ch0   (adc_ch0),
        .adc_ch1   (adc_ch1),
        .adc_ch2   (adc_ch2),
        .adc_ch3   (adc_ch3),
        .train_btn (train_btn),
        .left_btn  (left_btn),
        .right_btn (right_btn),
        .pwm_left  (pwm_left),
        .pwm_right (pwm_right),
        .v_left_dbg(v_left_dbg),
        .v_right_dbg(v_right_dbg)
    );
endmodule

