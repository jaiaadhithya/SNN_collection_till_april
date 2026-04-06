module snn_top_uart_2x2 (
    input  wire clk_50mhz,
    input  wire reset_n,
    input  wire uart_rx,
    input  wire train_btn,
    input  wire left_btn,
    input  wire right_btn,
    output wire pwm_left,
    output wire pwm_right,
    output wire signed [23:0] v_left_dbg,
    output wire signed [23:0] v_right_dbg
);
    snn_top_uart #(.N_INPUTS(4), .SENSOR_W(12), .V_WIDTH(24), .I_WIDTH(16)) u_top (
        .clk_50mhz (clk_50mhz),
        .reset_n   (reset_n),
        .uart_rx   (uart_rx),
        .train_btn (train_btn),
        .left_btn  (left_btn),
        .right_btn (right_btn),
        .pwm_left  (pwm_left),
        .pwm_right (pwm_right),
        .v_left_dbg(v_left_dbg),
        .v_right_dbg(v_right_dbg)
    );
endmodule

