// snn_top_uart.v - Icarus Verilog compatible version
// sensors bus: 48-bit packed {s3,s2,s1,s0}
module snn_top_uart #(parameter CLK_FREQ=50000000, parameter BAUD=115200) (
    input  clk,
    input  rst,
    input  uart_rx,
    output [3:0] dir_bits
);
    wire [7:0]  d;
    wire        v;
    uart_rx #(.CLK_FREQ(CLK_FREQ), .BAUD(BAUD)) RX (
        .clk(clk), .rst(rst), .rx(uart_rx), .data(d), .valid(v)
    );

    wire [47:0] sensors;
    wire [7:0]  mask;
    wire        fv;
    frame_rx FR (
        .clk(clk), .rst(rst), .rx_data(d), .rx_valid(v),
        .sensors(sensors), .btn_mask(mask), .frame_valid(fv)
    );

    snn_core CORE (
        .clk(clk), .rst(rst), .frame_valid(fv),
        .sensors(sensors), .btn_mask(mask), .dir_bits(dir_bits)
    );
endmodule
