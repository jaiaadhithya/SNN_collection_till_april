`timescale 1ns / 1ps

module tb_snn_paper_data;

  // Parameters
  localparam N_IN  = 4;
  localparam N_H   = 32;
  localparam N_OUT = 4;

  // Signals
  reg clk;
  reg rst;
  reg frame_valid;
  reg [11:0] s0, s1, s2, s3;
  reg [7:0] btn_mask;
  wire [3:0] dir_bits;
  wire [N_H-1:0] h_spike;
  wire [N_H*8-1:0] monitor_v_h;
  wire [15:0] v_o0, v_o1, v_o2, v_o3;

  // Instantiate UUT
  snn_core #(
    .N_IN(N_IN),
    .N_H(N_H),
    .N_OUT(N_OUT)
  ) uut (
    .clk(clk),
    .rst(rst),
    .frame_valid(frame_valid),
    .s0(s0), .s1(s1), .s2(s2), .s3(s3),
    .btn_mask(btn_mask),
    .dir_bits(dir_bits),
    .h_spike(h_spike),
    .monitor_v_h(monitor_v_h),
    .v_o0(v_o0), .v_o1(v_o1), .v_o2(v_o2), .v_o3(v_o3)
  );

  // File Handles
  integer f_weights, f_membrane, f_spikes, f_input;
  integer i, j;
  integer frame_cnt;

  // Clock Generation (100MHz)
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  // Test Sequence
  initial begin
    // Open CSV files
    f_weights  = $fopen("weights.csv", "w");
    f_membrane = $fopen("membrane.csv", "w");
    f_spikes   = $fopen("spikes.csv", "w");
    f_input    = $fopen("inputs.csv", "w");

    // Write Headers
    $fwrite(f_weights, "Frame,Time_ns");
    for (i=0; i<N_H; i=i+1) begin
      for (j=0; j<N_OUT; j=j+1) begin
        $fwrite(f_weights, ",G_%0d_%0d", i, j);
      end
    end
    for (i=0; i<4; i=i+1) begin
      for (j=0; j<N_OUT; j=j+1) begin
        $fwrite(f_weights, ",Gio_%0d_%0d", i, j);
      end
    end
    $fwrite(f_weights, "\n");

    $fwrite(f_membrane, "Frame,Time_ns,Vo_Fwd,Vo_Bwd,Vo_Left,Vo_Right\n");
    $fwrite(f_spikes, "Frame,Time_ns,Input_Pattern,Btn_Mask,Dir_Bits,H_Spikes\n");
    $fwrite(f_input, "Frame,Time_ns,S0,S1,S2,S3,Btn_Mask\n");

    // Initialize
    rst = 1;
    frame_valid = 0;
    s0 = 0; s1 = 0; s2 = 0; s3 = 0;
    btn_mask = 0;
    frame_cnt = 0;

    #100;
    rst = 0;
    #100;

    // 1. Baseline Calibration (10 frames)
    // Ambient light ~200
    repeat(10) begin
      drive_frame(200, 200, 200, 200, 8'd0);
    end

    // 2. Training: Obstacle Left (S1) -> Turn Right (Btn=Right|Train)
    // S1=300 (Active), Others=200. Btn: Train(1) | Right(4) = 5
    // Run for 50 frames to ensure learning
    repeat(50) begin
      drive_frame(200, 300, 200, 200, 8'd5); 
    end

    // 3. Training: Obstacle Right (S2) -> Turn Left (Btn=Left|Train)
    // S2=300 (Active). Btn: Train(1) | Left(2) = 3
    repeat(50) begin
      drive_frame(200, 200, 300, 200, 8'd3);
    end

    // 4. Testing: Obstacle Left -> Expect Right (No Buttons)
    repeat(20) begin
      drive_frame(200, 300, 200, 200, 8'd0);
    end

    // 5. Testing: Obstacle Right -> Expect Left
    repeat(20) begin
      drive_frame(200, 200, 300, 200, 8'd0);
    end

    // 6. Testing: Clear Path -> Expect Forward (No Obstacles)
    // S0,S1,S2,S3 = 200 (Baseline)
    repeat(20) begin
      drive_frame(200, 200, 200, 200, 8'd0);
    end

    $fclose(f_weights);
    $fclose(f_membrane);
    $fclose(f_spikes);
    $fclose(f_input);
    $finish;
  end

  // Task to drive one frame
  task drive_frame;
    input [11:0] in_s0;
    input [11:0] in_s1;
    input [11:0] in_s2;
    input [11:0] in_s3;
    input [7:0]  in_btn;
    begin
      frame_cnt = frame_cnt + 1;
      
      // Set inputs
      s0 = in_s0;
      s1 = in_s1;
      s2 = in_s2;
      s3 = in_s3;
      btn_mask = in_btn;
      
      // Pulse frame_valid
      frame_valid = 1;
      #10; // 1 clock cycle pulse
      frame_valid = 0;
      
      // Wait for processing (approx 50 cycles per frame to be safe)
      #500; 

      // Log Data
      log_data();
    end
  endtask

  // Task to log data to CSV
  task log_data;
    begin
      // Log Weights
      $fwrite(f_weights, "%0d,%0t", frame_cnt, $time);
      for (i=0; i<N_H; i=i+1) begin
        for (j=0; j<N_OUT; j=j+1) begin
          $fwrite(f_weights, ",%0d", uut.G[i][j]);
        end
      end
      for (i=0; i<4; i=i+1) begin
        for (j=0; j<N_OUT; j=j+1) begin
          $fwrite(f_weights, ",%0d", uut.G_io[i][j]);
        end
      end
      $fwrite(f_weights, "\n");

      // Log Membrane Potentials
      $fwrite(f_membrane, "%0d,%0t,%0d,%0d,%0d,%0d\n", 
              frame_cnt, $time, v_o0, v_o1, v_o2, v_o3);

      // Log Spikes / Decisions
      $fwrite(f_spikes, "%0d,%0t,%0d_%0d_%0d_%0d,%0d,%b,%b\n",
              frame_cnt, $time, s0, s1, s2, s3, btn_mask, dir_bits, h_spike);
              
      // Log Inputs
      $fwrite(f_input, "%0d,%0t,%0d,%0d,%0d,%0d,%0d\n",
              frame_cnt, $time, s0, s1, s2, s3, btn_mask);
    end
  endtask

endmodule
