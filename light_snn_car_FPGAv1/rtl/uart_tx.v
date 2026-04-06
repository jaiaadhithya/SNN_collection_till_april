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
reg [9:0] shift_reg; // Stop(1) + 8 Data + Start(0)

always @(posedge clk) begin
    if (rst) begin
        tx <= 1'b1; // Idle state is high
        ready <= 1'b1;
        clk_cnt <= 0;
        bit_cnt <= 0;
        shift_reg <= 10'b1111111111;
    end else begin
        if (ready) begin
            if (valid) begin
                ready <= 0;
                shift_reg <= {1'b1, data, 1'b0}; // Stop(1) - Data - Start(0)
                clk_cnt <= 0;
                bit_cnt <= 0;
                tx <= 0; // Start bit immediately (shift_reg[0] is 0)
            end else begin
                tx <= 1'b1;
            end
        end else begin
            if (clk_cnt >= CLKS_PER_BIT - 1) begin
                clk_cnt <= 0;
                if (bit_cnt < 9) begin
                     shift_reg <= {1'b1, shift_reg[9:1]};
                     tx <= shift_reg[1]; // Shift out next bit
                     bit_cnt <= bit_cnt + 1;
                end else begin
                     ready <= 1'b1; // Done
                     tx <= 1'b1;
                end
            end else begin
                clk_cnt <= clk_cnt + 1;
            end
        end
    end
end

endmodule
