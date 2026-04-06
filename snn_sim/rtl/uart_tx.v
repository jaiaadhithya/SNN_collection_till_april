module uart_tx #(parameter CLK_FREQ=50000000, parameter BAUD=115200) (
    input clk,
    input rst,
    input [7:0] data,
    input valid,
    output reg tx,
    output reg ready
);

localparam CLKS_PER_BIT = CLK_FREQ / BAUD;
reg [15:0] clk_cnt;
reg [3:0] bit_cnt;
reg [9:0] shift_reg; // Start bit + 8 data bits + Stop bit

always @(posedge clk) begin
    if (rst) begin
        tx <= 1'b1; // Idle state is high
        ready <= 1'b1;
        clk_cnt <= 0;
        bit_cnt <= 0;
    end else begin
        if (ready) begin
            if (valid) begin
                ready <= 0;
                shift_reg <= {1'b1, data, 1'b0}; // Stop(1) - Data - Start(0)
                clk_cnt <= 0;
                bit_cnt <= 0;
            end
        end else begin
            if (clk_cnt >= CLKS_PER_BIT - 1) begin
                clk_cnt <= 0;
                tx <= shift_reg[0];
                shift_reg <= {1'b1, shift_reg[9:1]};
                if (bit_cnt >= 9) begin // 1 Start + 8 Data + 1 Stop = 10 bits (0-9)
                    ready <= 1'b1;
                end
                bit_cnt <= bit_cnt + 1;
            end else begin
                clk_cnt <= clk_cnt + 1;
            end
        end
    end
end

endmodule
