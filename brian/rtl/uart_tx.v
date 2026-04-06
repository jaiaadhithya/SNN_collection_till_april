module uart_tx #(
    parameter CLK_FREQ = 50000000,
    parameter BAUD     = 115200
) (
    input  wire clk,
    input  wire reset,
    input  wire start,
    input  wire [7:0] data_in,
    output reg        busy,
    output reg        tx
);
    localparam integer DIV = CLK_FREQ / BAUD;
    reg [31:0] cnt;
    reg [3:0]  bit_idx;
    reg [9:0]  shifter;
    reg        running;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            cnt     <= 0;
            bit_idx <= 0;
            shifter <= 10'b1111111111;
            running <= 1'b0;
            busy    <= 1'b0;
            tx      <= 1'b1;
        end else begin
            if (!running) begin
                if (start) begin
                    shifter <= {1'b1, data_in, 1'b0};
                    bit_idx <= 4'd0;
                    cnt     <= DIV-1;
                    running <= 1'b1;
                    busy    <= 1'b1;
                end
            end else begin
                if (cnt == 0) begin
                    tx <= shifter[0];
                    shifter <= {1'b1, shifter[9:1]};
                    bit_idx <= bit_idx + 1'b1;
                    cnt <= DIV-1;
                    if (bit_idx == 4'd9) begin
                        running <= 1'b0;
                        busy    <= 1'b0;
                        tx      <= 1'b1;
                    end
                end else begin
                    cnt <= cnt - 1'b1;
                end
            end
        end
    end
endmodule

