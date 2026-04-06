module uart_rx #(
    parameter CLK_FREQ = 50000000,
    parameter BAUD     = 115200
) (
    input  wire clk,
    input  wire reset,
    input  wire rx,
    output reg  [7:0] data_out,
    output reg        data_valid
);
    localparam integer DIV = CLK_FREQ / BAUD;
    reg [31:0] cnt;
    reg [3:0]  bit_idx;
    reg [7:0]  shifter;
    reg        rx_sync1, rx_sync2;
    reg        busy;
    reg        start_seen;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            rx_sync1   <= 1'b1;
            rx_sync2   <= 1'b1;
            cnt        <= 0;
            bit_idx    <= 0;
            shifter    <= 0;
            busy       <= 1'b0;
            start_seen <= 1'b0;
            data_out   <= 8'd0;
            data_valid <= 1'b0;
        end else begin
            rx_sync1 <= rx;
            rx_sync2 <= rx_sync1;
            data_valid <= 1'b0;
            if (!busy) begin
                if (rx_sync2 == 1'b0) begin
                    busy       <= 1'b1;
                    start_seen <= 1'b1;
                    cnt        <= DIV/2;
                    bit_idx    <= 4'd0;
                end
            end else begin
                if (cnt == 0) begin
                    if (start_seen) begin
                        start_seen <= 1'b0;
                        cnt        <= DIV-1;
                    end else if (bit_idx < 8) begin
                        shifter    <= {rx_sync2, shifter[7:1]};
                        bit_idx    <= bit_idx + 1'b1;
                        cnt        <= DIV-1;
                    end else begin
                        data_out   <= {rx_sync2, shifter[7:1]};
                        data_valid <= 1'b1;
                        busy       <= 1'b0;
                    end
                end else begin
                    cnt <= cnt - 1'b1;
                end
            end
        end
    end
endmodule

