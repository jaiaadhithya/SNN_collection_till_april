module uart_rx#(parameter CLK_FREQ=50000000, parameter BAUD=115200)(
input clk,
input rst,
input rx,
output reg [7:0] data,
output reg valid
);

localparam integer TICKS_PER_BIT = CLK_FREQ/BAUD;
localparam integer HALF_TICKS = TICKS_PER_BIT / 2;

reg [31:0] tick_cnt;
reg [3:0] bit_cnt;
reg [7:0] sh;
reg [1:0] state; // 0=IDLE, 1=START, 2=DATA, 3=STOP
reg rx_sync0, rx_sync1;

always @(posedge clk) begin
  rx_sync0 <= rx;
  rx_sync1 <= rx_sync0;
end

always @(posedge clk) begin
  if (rst) begin
    state <= 0;
    tick_cnt <= 0;
    bit_cnt <= 0;
    sh <= 0;
    data <= 0;
    valid <= 0;
  end else begin
    valid <= 0;
    
    case (state)
      0: begin // IDLE
         if (rx_sync1 == 0) begin // Detect Start Bit (Falling Edge)
           state <= 1;
           tick_cnt <= 0;
         end
      end
      
      1: begin // START BIT (Check middle of start bit)
         if (tick_cnt == HALF_TICKS) begin
            if (rx_sync1 == 0) begin
                state <= 2;
                tick_cnt <= 0;
                bit_cnt <= 0;
            end else begin
                state <= 0; // False start
            end
         end else begin
            tick_cnt <= tick_cnt + 1;
         end
      end
      
      2: begin // DATA BITS
         if (tick_cnt == TICKS_PER_BIT) begin
            tick_cnt <= 0;
            sh <= {rx_sync1, sh[7:1]}; // LSB first
            if (bit_cnt == 7) begin
                state <= 3;
            end else begin
                bit_cnt <= bit_cnt + 1;
            end
         end else begin
            tick_cnt <= tick_cnt + 1;
         end
      end
      
      3: begin // STOP BIT
         if (tick_cnt == TICKS_PER_BIT) begin
             state <= 0;
             data <= sh;
             valid <= 1; // Valid pulse
         end else begin
             tick_cnt <= tick_cnt + 1;
         end
      end
    endcase
  end
end
endmodule
