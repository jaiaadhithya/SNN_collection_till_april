// snn_top_uart.v — Top-level SNN with expanded TX protocol
// Sends membrane potentials + spikes back to Arduino/PC for dashboard
module snn_car #(parameter CLK_FREQ = 50000000, parameter BAUD = 115200)(
    input  clk,
    input  rst,
    input  uart_rx,
    output uart_tx,
    output [9:0] leds
);

  wire [7:0] d;
  wire v;

  // UART RX
  uart_rx #(.CLK_FREQ(CLK_FREQ), .BAUD(BAUD)) RX (
      .clk(clk), .rst(rst), .rx(uart_rx), .data(d), .valid(v)
  );

  // Frame Parser
  wire [11:0] s0, s1, s2, s3;
  wire [7:0]  mask;
  wire        fv;

  frame_rx FR (
      .clk(clk), .rst(rst),
      .rx_data(d), .rx_valid(v),
      .s0(s0), .s1(s1), .s2(s2), .s3(s3),
      .btn_mask(mask), .frame_valid(fv)
  );

  // SNN Core (LIF + Memristor)
  wire [3:0]  dir_bits;
  wire [31:0] h_spike; // Expanded to 32 bits
  wire [255:0] monitor_v_h; // 32 neurons * 8 bits = 256 bits
  wire [15:0] v_o0, v_o1, v_o2, v_o3;

  snn_core CORE (
      .clk(clk), .rst(rst), .frame_valid(fv),
      .s0(s0), .s1(s1), .s2(s2), .s3(s3),
      .btn_mask(mask),
      .dir_bits(dir_bits),
      .h_spike(h_spike),
      .monitor_v_h(monitor_v_h),
      .v_o0(v_o0), .v_o1(v_o1), .v_o2(v_o2), .v_o3(v_o3)
  );

  // UART TX
  reg  [7:0] tx_data;
  reg        tx_start;
  wire       tx_ready;

  uart_tx #(.CLK_FREQ(CLK_FREQ), .BAUD(BAUD)) TX (
      .clk(clk), .rst(rst),
      .data(tx_data), .valid(tx_start),
      .tx(uart_tx), .ready(tx_ready)
  );

  // --- DEBUG LEDS ---
  assign leds[0] = dir_bits[0];  // Forward
  assign leds[1] = dir_bits[1];  // Backward
  assign leds[2] = dir_bits[2];  // Left
  assign leds[3] = ~uart_rx;     // RX Activity
  assign leds[4] = uart_rx;      // RX Line State
  assign leds[5] = uart_tx;      // TX Line State
  assign leds[6] = fv;           // Frame Valid
  assign leds[7] = v;            // Byte Valid
  assign leds[8] = dir_bits[3];  // Right

  // Heartbeat LED
  reg [25:0] hb_cnt;
  always @(posedge clk) begin
      if (rst) hb_cnt <= 0;
      else hb_cnt <= hb_cnt + 1;
  end
  assign leds[9] = hb_cnt[25];

  // ==========================================================
  // TX STATE MACHINE — Send 43-byte packet on each frame_valid
  // Packet: [0xBB][LEN=41][v_h 0..31][v_o 0..3][h_spike 31..0][dir_bits]
  // ==========================================================
  reg [2:0]  tx_state;
  reg [5:0]  tx_idx; // Increased width for 43 bytes
  reg [7:0]  tx_buf [0:42]; // Increased buffer size
  reg        fv_d;

  integer i;

  always @(posedge clk) begin
    if (rst) begin
      tx_state <= 0;
      tx_start <= 0;
      tx_idx   <= 0;
      fv_d     <= 1'b0;
    end else begin
      tx_start <= 0; // default
      fv_d <= fv;

      case (tx_state)
        // IDLE — wait for frame_valid, latch all data
        0: begin
          if (fv_d) begin
            tx_buf[0]  <= 8'hBB;                       // header
            tx_buf[1]  <= 8'd41;                       // payload length
            
            // Load 32 hidden neuron potentials
            // monitor_v_h is [255:0], where neuron 0 is [7:0], neuron 1 is [15:8]...
            for (i=0; i<32; i=i+1) begin
               tx_buf[2+i] <= monitor_v_h[i*8 +: 8];
            end

            // Load 4 output neuron potentials (indices 34, 35, 36, 37)
            tx_buf[34] <= v_o0[7:0];
            tx_buf[35] <= v_o1[7:0];
            tx_buf[36] <= v_o2[7:0];
            tx_buf[37] <= v_o3[7:0];

            // Load 32 hidden spikes (packed into 4 bytes)
            // h_spike is [31:0]. 
            // Byte 38: [7:0], Byte 39: [15:8], Byte 40: [23:16], Byte 41: [31:24]
            tx_buf[38] <= h_spike[7:0];
            tx_buf[39] <= h_spike[15:8];
            tx_buf[40] <= h_spike[23:16];
            tx_buf[41] <= h_spike[31:24];

            // Load Direction bits / Output spikes
            tx_buf[42] <= {4'b0000, dir_bits};

            tx_idx     <= 0;
            tx_state   <= 1;
          end
        end

        // SEND — load next byte into UART TX
        1: begin
          if (tx_ready) begin
            tx_data  <= tx_buf[tx_idx];
            tx_start <= 1;
            tx_state <= 2;
          end
        end

        // WAIT_BUSY — wait for UART to start transmitting
        2: begin
          if (!tx_ready) tx_state <= 3;
        end

        // WAIT_DONE — wait for UART to finish byte
        3: begin
          if (tx_ready) begin
            if (tx_idx == 6'd42)
              tx_state <= 0; // all bytes sent, back to IDLE
            else begin
              tx_idx   <= tx_idx + 1;
              tx_state <= 1; // send next byte
            end
          end
        end
      endcase
    end
  end

endmodule
