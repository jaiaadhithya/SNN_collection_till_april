// =============================================================================
// Testbench: snn_tb.v
// DUT      : snn_top_uart
// Purpose  : Verifies the full UART RX -> frame_rx -> snn_core pipeline.
//
// Packet format (bytes sent over UART):
//   [0xAA] [0x55] [0x09] [S0_H][S0_L] [S1_H][S1_L] [S2_H][S2_L] [S3_H][S3_L]
//   [BTN_MASK] [XOR_CHECKSUM]
//
//   - Header:   0xAA, 0x55   (sync bytes, not checksummed)
//   - Length:   0x09         (9 payload bytes, not checksummed)
//   - Payload:  9 bytes      (checksummed by XOR)
//   - Checksum: XOR of all 9 payload bytes
//
// Sensor value interpretation in snn_core:
//   sensors[i] = {S_H[7:0], S_L[7:0]}[11:0]  -> upper 12 bits of 16-bit word
//   Firing threshold = 800 (0x320)
//   So a sensor value >= 0x320 fires.
//
// Test Scenarios:
//   1. INFERENCE  : All 4 sensors above threshold (0xFFF), no training buttons.
//                   Weights are equal (reset=1), so dir_bits should be 0001 (Front wins).
//   2. LEARNING-L : Same sensors, TRAIN=1 + LEFT=1 (btn_mask=0x05).
//                   Weights for Left (out[2]) should increase each packet.
//   3. INFERENCE2 : Send sensor packet again with no buttons.
//                   After enough training LEFT should now win -> dir_bits = 0100.
// =============================================================================

`timescale 1us / 1ns

module snn_tb;

// -----------------------------------------------------------------------
// Clock & reset
// -----------------------------------------------------------------------
reg clk = 0;
reg rst = 1;
always #0.5 clk = ~clk;          // 1 us period = 1 MHz

// -----------------------------------------------------------------------
// DUT – use 1 MHz clock + 9600 baud so bit period = 104.167 us
// -----------------------------------------------------------------------
reg rx = 1;
wire [3:0] dir;

snn_top_uart #(
    .CLK_FREQ(1_000_000),
    .BAUD    (9_600)
) DUT (
    .clk     (clk),
    .rst     (rst),
    .uart_rx (rx),
    .dir_bits(dir)
);

// -----------------------------------------------------------------------
// Waveform dump
// -----------------------------------------------------------------------
initial begin
    $dumpfile("sim/snn_dump.vcd");
    $dumpvars(0, snn_tb);       // dump everything in the testbench hierarchy
end

// -----------------------------------------------------------------------
// UART bit period at 9600 baud with 1 MHz clock = 1,000,000/9600 = 104.167 us
// -----------------------------------------------------------------------
localparam real BIT_PERIOD = 104.167;

// -----------------------------------------------------------------------
// Task: send one byte LSB-first, no parity, 1 stop bit (8N1)
// -----------------------------------------------------------------------
task send_byte;
    input [7:0] b;
    integer i;
    begin
        rx = 0;                 // start bit
        #(BIT_PERIOD);
        for (i = 0; i < 8; i = i + 1) begin
            rx = b[i];
            #(BIT_PERIOD);
        end
        rx = 1;                 // stop bit
        #(BIT_PERIOD);
    end
endtask

// -----------------------------------------------------------------------
// Task: send a complete SNN frame
//   sensors_val : 12-bit value to use for ALL 4 sensors (packed into 2 bytes each)
//   btn         : btn_mask byte
//
// Packet layout (9 payload bytes):
//   b[0]=S0_H  b[1]=S0_L  b[2]=S1_H  b[3]=S1_L
//   b[4]=S2_H  b[5]=S2_L  b[6]=S3_H  b[7]=S3_L
//   b[8]=BTN_MASK
//
// frame_rx reads  sensors[0] = {b[3],b[4]}[11:0]  (indices relative to buffer)
//   BUT the buffer fills from idx=3, so b[3..11] in the buffer map to bytes 0..8 sent.
//
// frame_rx.v line 40: sensors[0] = {b[3], b[4]}[11:0]
//   b[3] = first payload byte  = S0_H  (upper byte of sensor 0)
//   b[4] = second payload byte = S0_L  (lower byte)
//
// To get sensors[0]=0xFFF (all ones, 12 bits):
//   16-bit word = 0xFFFF, upper 12 bits = {S0_H[7:0], S0_L[7:0]}[11:0]
//   So send S0_H=0xFF, S0_L=0xFF -> {0xFF,0xFF}=0xFFFF -> [11:0]=0xFFF  ✓
// -----------------------------------------------------------------------
task send_frame;
    input [11:0] sensor_val;   // same value for all 4 sensors
    input [7:0]  btn;
    reg [7:0] sh, sl;          // sensor high / low bytes
    reg [7:0] cs;              // checksum accumulator
    begin
        // Pack sensor value into two bytes so that {sh,sl}[11:0] == sensor_val
        // We use the full 16-bit word = {sensor_val, 4'b0} so upper 12 bits = sensor_val
        sh = sensor_val[11:4];          // bits [11:4]
        sl = {sensor_val[3:0], 4'b0};   // bits [3:0] in upper nibble of lower byte

        // XOR checksum over 9 payload bytes
        cs = sh ^ sl ^ sh ^ sl ^ sh ^ sl ^ sh ^ sl ^ btn;

        // Send header + length (not covered by checksum)
        send_byte(8'hAA);
        send_byte(8'h55);
        send_byte(8'h09);   // length = 9 payload bytes

        // Send payload (4 sensor pairs + btn_mask)
        send_byte(sh); send_byte(sl);   // sensor 0
        send_byte(sh); send_byte(sl);   // sensor 1
        send_byte(sh); send_byte(sl);   // sensor 2
        send_byte(sh); send_byte(sl);   // sensor 3
        send_byte(btn);

        // Send checksum
        send_byte(cs);
    end
endtask

// -----------------------------------------------------------------------
// Monitor: print whenever dir_bits changes
// -----------------------------------------------------------------------
reg [3:0] dir_prev = 4'hX;
always @(posedge clk) begin
    if (dir !== dir_prev) begin
        $display("[%0t us] dir_bits changed: %b  (F=%b B=%b L=%b R=%b)",
                 $time, dir, dir[0], dir[1], dir[2], dir[3]);
        dir_prev <= dir;
    end
end

// -----------------------------------------------------------------------
// Main test sequence
// -----------------------------------------------------------------------
integer k;
initial begin
    $display("=== SNN Simulation Start ===");

    // Release reset after 10 us
    #10;
    rst = 0;
    #10;

    // ------------------------------------------------------------------
    // TEST 1: INFERENCE ONLY
    // NOTE: h_act is registered, so packet #1 loads h_act, packet #2 uses it.
    // All 4 sensors fire (value = 0xFFF > threshold 0x320).
    // Weights equal (all=1), sum=4 > thr_out=2 -> WTA -> dir_bits[0] = Front.
    // Expected: dir_bits = 0001
    // ------------------------------------------------------------------
    $display("\n[TEST 1] Inference - all sensors active, no training");
    send_frame(12'hFFF, 8'h00);   // priming packet: loads h_act
    #200;
    send_frame(12'hFFF, 8'h00);   // inference packet: uses h_act
    #500;   // wait for SNN core to settle
    $display("[TEST 1] dir_bits = %b (expect 0001 = Front)", dir);

    // ------------------------------------------------------------------
    // TEST 2: LEARNING - Train LEFT button
    // btn_mask[0]=TRAIN=1, btn_mask[1]=LEFT=1 -> btn = 8'b0000_0011 = 0x03
    // (wire assignments in snn_core: train=btn[0], left=btn[1])
    // Send 10 training packets so Left weights saturate well above others.
    // ------------------------------------------------------------------
    $display("\n[TEST 2] Training LEFT with all sensors active (10 packets)");
    for (k = 0; k < 10; k = k + 1) begin
        send_frame(12'hFFF, 8'h03);   // TRAIN=1, LEFT=1
        #200;
    end
    $display("[TEST 2] Training done. dir_bits mid-training = %b", dir);

    // ------------------------------------------------------------------
    // TEST 3: INFERENCE AFTER LEARNING
    // Left weights should now be dominant -> dir_bits[2] fires (Left).
    // Expected: dir_bits = 0100
    // ------------------------------------------------------------------
    $display("\n[TEST 3] Inference after training LEFT");
    send_frame(12'hFFF, 8'h00);   // priming packet
    #200;
    send_frame(12'hFFF, 8'h00);   // inference packet
    #500;
    $display("[TEST 3] dir_bits = %b (expect 0100 = Left)", dir);

    // ------------------------------------------------------------------
    // TEST 4: SENSOR BELOW THRESHOLD (no neurons fire)
    // All sensors = 0x100 < threshold 0x320 -> no hidden neurons active.
    // Needs 3 packets to fully propagate through the h_act pipeline:
    //   Packet 1: loads h_act = 0000 (clears training state)
    //   Packet 2: uses h_act=0, out_sum=0, dir_bits -> 0
    //   Packet 3: confirm steady state
    // Expected: dir_bits = 0000
    // ------------------------------------------------------------------
    $display("\n[TEST 4] Sensors below threshold - expect no direction");
    send_frame(12'h100, 8'h00);   // clears h_act from training
    #200;
    send_frame(12'h100, 8'h00);   // out_sum=0, dir_bits clears
    #200;
    send_frame(12'h100, 8'h00);   // steady state
    #500;
    $display("[TEST 4] dir_bits = %b (expect 0000 = No direction)", dir);

    $display("\n=== SNN Simulation Complete ===");
    #100;
    $finish;
end

endmodule

