module uart_rx#(parameter CLK_FREQ=50000000, parameter BAUD=115200)(
input clk,
input rst,
input rx,
output reg [7:0] data,
output reg valid
);
localparam integer TICKS_PER_BIT = CLK_FREQ/BAUD;
reg [31:0] tick;
reg [3:0] bit_cnt;
reg [7:0] sh;
reg busy;
reg rx_sync0, rx_sync1;
always @(posedge clk) begin
  rx_sync0 <= rx;
  rx_sync1 <= rx_sync0;
end
always @(posedge clk) begin
  if (rst) begin
    tick <= 0;
    bit_cnt <= 0;
    sh <= 0;
    busy <= 0;
    data <= 0;
    valid <= 0;
  end else begin
    valid <= 0;
    if (!busy) begin
      if (rx_sync1 == 0) begin
        busy <= 1;
        tick <= TICKS_PER_BIT + (TICKS_PER_BIT>>1);
        bit_cnt <= 0;
      end
    end else begin
      if (tick == 0) begin
        tick <= TICKS_PER_BIT;
        if (bit_cnt < 8) begin
          sh <= {rx_sync1, sh[7:1]};
          bit_cnt <= bit_cnt + 1;
        end else begin
          data <= sh;
          valid <= 1;
          busy <= 0;
        end
      end else begin
        tick <= tick - 1;
      end
    end
  end
end
endmodule
