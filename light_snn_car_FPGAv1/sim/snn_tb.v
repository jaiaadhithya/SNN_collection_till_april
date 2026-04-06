`timescale 1us/1us
module snn_tb;
reg clk=0;
reg rst=1;
reg rx=1;
wire [9:0] leds;
wire tx_out;
integer fwd_cnt, back_cnt, left_cnt, right_cnt;

// Instantiate Top Level
snn_car#(.CLK_FREQ(1000000),.BAUD(9600)) DUT(
  .clk(clk),.rst(rst),.uart_rx(rx),.uart_tx(tx_out),.leds(leds)
);

always #0.5 clk=~clk; // 1MHz Clock

// UART Byte Sender Task
task send_byte(input [7:0] b);
integer i;
begin
  rx<=0; // Start Bit
  #(104.1667); // 1/9600 * 1e6 = 104.16 us
  for(i=0;i<8;i=i+1) begin
    rx<=b[i]; // Data Bits (LSB First)
    #(104.1667);
  end
  rx<=1; // Stop Bit
  #(104.1667);
end
endtask

// Packet Sender Task
task send_packet(
  input [11:0] s0, input [11:0] s1, input [11:0] s2, input [11:0] s3,
  input [7:0] btn
);
reg [7:0] payload [0:8];
reg [7:0] cs;
integer k;
begin
  payload[0] = (s0 >> 8) & 8'h0F;
  payload[1] = s0 & 8'hFF;
  payload[2] = (s1 >> 8) & 8'h0F;
  payload[3] = s1 & 8'hFF;
  payload[4] = (s2 >> 8) & 8'h0F;
  payload[5] = s2 & 8'hFF;
  payload[6] = (s3 >> 8) & 8'h0F;
  payload[7] = s3 & 8'hFF;
  payload[8] = btn;
  
  cs = 0;
  for(k=0; k<9; k=k+1) cs = cs ^ payload[k];
  
  send_byte(8'hAA);
  send_byte(8'h55);
  send_byte(8'h09);
  for(k=0; k<9; k=k+1) send_byte(payload[k]);
  send_byte(cs);
end
endtask

initial begin
  #10 rst=0;

  fwd_cnt = 0;
  back_cnt = 0;
  left_cnt = 0;
  right_cnt = 0;

  send_packet(12'd500, 12'd500, 12'd500, 12'd500, 8'h00);
  #2000;

  send_packet(12'd500, 12'd500, 12'd900, 12'd500, 8'h00);
  #2000;

  send_packet(12'd500, 12'd500, 12'd900, 12'd500, 8'h05);
  #2000;
  send_packet(12'd500, 12'd500, 12'd900, 12'd500, 8'h05);
  #2000;
  send_packet(12'd500, 12'd500, 12'd900, 12'd500, 8'h05);
  #2000;
  send_packet(12'd500, 12'd500, 12'd900, 12'd500, 8'h05);
  #2000;

  repeat (12) begin
    send_packet(12'd500, 12'd500, 12'd900, 12'd500, 8'h00);
    #500;
    if (leds[0]) fwd_cnt = fwd_cnt + 1;
    if (leds[1]) back_cnt = back_cnt + 1;
    if (leds[2]) left_cnt = left_cnt + 1;
    if (leds[8]) right_cnt = right_cnt + 1;
    #1500;
  end
  $display("After training RIGHT on sensor2 stimulus: F=%0d B=%0d L=%0d R=%0d", fwd_cnt, back_cnt, left_cnt, right_cnt);

  fwd_cnt = 0;
  left_cnt = 0;
  repeat (16) begin
    send_packet(12'd900, 12'd500, 12'd900, 12'd500, 8'h00);
    #500;
    if (leds[0]) fwd_cnt = fwd_cnt + 1;
    if (leds[2]) left_cnt = left_cnt + 1;
    #1500;
  end
  $display("Corner equal (sensor0+sensor2): F=%0d L=%0d", fwd_cnt, left_cnt);

  fwd_cnt = 0;
  left_cnt = 0;
  repeat (16) begin
    send_packet(12'd950, 12'd500, 12'd700, 12'd500, 8'h00);
    #500;
    if (leds[0]) fwd_cnt = fwd_cnt + 1;
    if (leds[2]) left_cnt = left_cnt + 1;
    #1500;
  end
  $display("Corner biased (sensor0>sensor2): F=%0d L=%0d", fwd_cnt, left_cnt);
  
  $stop;
end

endmodule
