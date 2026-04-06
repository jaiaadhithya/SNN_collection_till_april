// snn_core.v — LIF Neuron Model with Memristor-Based Synaptic Weights
// Architecture: 4 LIF Hidden Neurons → 4 LIF Output Neurons (WTA)
// Weights modeled as bounded memristor conductance [G_MIN, G_MAX]
module snn_core #(
  parameter N_IN   = 4,
  parameter N_H    = 32,  // Upgraded to 32 Neurons
  parameter N_OUT  = 4,
  // LIF parameters
  parameter V_THRESH_H   = 12'd120,
  parameter V_THRESH_O   = 16'd200,
  parameter LEAK_H       = 12'd5,
  parameter LEAK_O       = 16'd5,
  parameter INPUT_SHIFT  = 2,       // Lowered from 3 — double sensor gain for more hidden current
  parameter NOISE_MARGIN = 10'd20,  // Lowered from 40 — trigger learning on weaker signals
  // Memristor parameters
  parameter G_MIN   = 8'd1,
  parameter G_MAX   = 8'd250,
  parameter G_INIT  = 8'd10,
  parameter D_POT   = 8'd32,
  parameter D_DEP   = 8'd8,
  parameter D_POT_IN     = 8'd8,
  parameter IN_TO_H_SHIFT = 4'd3,
  parameter H_TO_O_SHIFT = 4'd4,
  parameter REF_H_FRAMES = 4'd2,
  parameter REF_O_FRAMES = 4'd2,
  parameter WTA_HYST     = 16'd16,
  parameter INHIB_O      = 16'd24,
  parameter TRAIN_MIN_CUR = 12'd12
)(
  input  clk,
  input  rst,
  input  frame_valid,
  input  [11:0] s0, s1, s2, s3,
  input  [7:0]  btn_mask,
  output reg [3:0] dir_bits,
  output reg [N_H-1:0] h_spike, // Expanded to 32 bits
  // Debug / Dashboard signals
  output [N_H*8-1:0] monitor_v_h, // Flattened 8-bit potentials (v[8:1]) for all neurons
  output [15:0] v_o0, v_o1, v_o2, v_o3
);

  // --- Membrane potentials ---
  reg [11:0] v_mem_h [0:N_H-1];   // hidden layer
  reg [15:0] v_mem_o [0:N_OUT-1]; // output layer

  // Refractory counters (counts down to zero)
  reg [3:0]  ref_h   [0:N_H-1];
  reg [3:0]  ref_o   [0:N_OUT-1];

  // Baseline sensor values (captured once at startup) for normalization
  reg        baseline_valid;
  reg [9:0]  baseline [0:3];

  // Map internal potentials to flattened output for dashboard
  // We extract bits [8:1] (divide by 2) to fit 0..255 range
  genvar k;
  generate
    for (k=0; k<N_H; k=k+1) begin : mon_map
      assign monitor_v_h[k*8 +: 8] = v_mem_h[k][8:1];
    end
  endgenerate

  assign v_o0 = v_mem_o[0];
  assign v_o1 = v_mem_o[1];
  assign v_o2 = v_mem_o[2];
  assign v_o3 = v_mem_o[3];

  // --- Memristor-modeled synaptic weights ---
  // G_in[input_i][hidden_j] — conductance value (Input -> Hidden crossbar)
  reg [7:0] G_in [0:N_IN-1][0:N_H-1];

  // G[hidden_i][output_j] — conductance value (Hidden -> Output crossbar)
  reg [7:0] G [0:N_H-1][0:N_OUT-1];

  // --- Sensor mapping ---
  // Baseline‑normalize 10‑bit sensor values so that ambient light at
  // startup becomes "zero" input, and deviations (brighter or darker)
  // generate LIF current. This removes the need for a dark room.
  wire [11:0] sensor [0:3];
  assign sensor[0] = s0;
  assign sensor[1] = s1;
  assign sensor[2] = s2;
  assign sensor[3] = s3;

  // Raw 10‑bit readings
  wire [9:0]  s0_10 = sensor[0][9:0];
  wire [9:0]  s1_10 = sensor[1][9:0];
  wire [9:0]  s2_10 = sensor[2][9:0];
  wire [9:0]  s3_10 = sensor[3][9:0];

  // Absolute deviation from baseline (0 when baseline is not yet valid)
  wire [9:0]  diff0_10 = baseline_valid ?
                         (s0_10 > baseline[0] ? (s0_10 - baseline[0]) : (baseline[0] - s0_10)) :
                         10'd0;
  wire [9:0]  diff1_10 = baseline_valid ?
                         (s1_10 > baseline[1] ? (s1_10 - baseline[1]) : (baseline[1] - s1_10)) :
                         10'd0;
  wire [9:0]  diff2_10 = baseline_valid ?
                         (s2_10 > baseline[2] ? (s2_10 - baseline[2]) : (baseline[2] - s2_10)) :
                         10'd0;
  wire [9:0]  diff3_10 = baseline_valid ?
                         (s3_10 > baseline[3] ? (s3_10 - baseline[3]) : (baseline[3] - s3_10)) :
                         10'd0;

  // Scaled sensor current (baseline‑normalized, then right-shift)
  // Apply Noise Margin (Deadband) to prevent noise accumulation
  wire [11:0] current [0:3];
  assign current[0] = (diff0_10 > NOISE_MARGIN) ? ({2'b00, diff0_10} >> INPUT_SHIFT) : 12'd0;
  assign current[1] = (diff1_10 > NOISE_MARGIN) ? ({2'b00, diff1_10} >> INPUT_SHIFT) : 12'd0;
  assign current[2] = (diff2_10 > NOISE_MARGIN) ? ({2'b00, diff2_10} >> INPUT_SHIFT) : 12'd0;
  assign current[3] = (diff3_10 > NOISE_MARGIN) ? ({2'b00, diff3_10} >> INPUT_SHIFT) : 12'd0;

  reg [15:0] lfsr [0:N_IN-1];
  wire fb0 = lfsr[0][15] ^ lfsr[0][13] ^ lfsr[0][12] ^ lfsr[0][10];
  wire fb1 = lfsr[1][15] ^ lfsr[1][13] ^ lfsr[1][12] ^ lfsr[1][10];
  wire fb2 = lfsr[2][15] ^ lfsr[2][13] ^ lfsr[2][12] ^ lfsr[2][10];
  wire fb3 = lfsr[3][15] ^ lfsr[3][13] ^ lfsr[3][12] ^ lfsr[3][10];

  wire [7:0] rate0 = (current[0] > 12'd255) ? 8'hFF : current[0][7:0];
  wire [7:0] rate1 = (current[1] > 12'd255) ? 8'hFF : current[1][7:0];
  wire [7:0] rate2 = (current[2] > 12'd255) ? 8'hFF : current[2][7:0];
  wire [7:0] rate3 = (current[3] > 12'd255) ? 8'hFF : current[3][7:0];

  wire [3:0] in_spike;
  assign in_spike[0] = (lfsr[0][7:0] < rate0);
  assign in_spike[1] = (lfsr[1][7:0] < rate1);
  assign in_spike[2] = (lfsr[2][7:0] < rate2);
  assign in_spike[3] = (lfsr[3][7:0] < rate3);

  wire train = btn_mask[0];
  wire left  = btn_mask[1];
  wire right = btn_mask[2];
  wire front = btn_mask[3];
  wire back  = btn_mask[4];

  // Decode Training Label (Priority: Front > Back > Left > Right)
  wire [3:0] label_dir_override;
  assign label_dir_override = front ? 4'b0001 :
                              back  ? 4'b0010 :
                              left  ? 4'b0100 :
                              right ? 4'b1000 : 4'b0000;
  wire [1:0] label_idx = front ? 2'd0 :
                         back  ? 2'd1 :
                         left  ? 2'd2 :
                         right ? 2'd3 : 2'd0;

  integer i, j;
  integer k;

  // Temporary variables for Hidden Layer Loop
  reg [11:0] in_current;
  reg [12:0] v_h_tmp;

  reg [N_H-1:0] h_spike_next;
  reg [3:0]     o_spike_next;
  reg [15:0]    syn_current_j;
  reg [15:0]    v_o_tmp;
  reg [11:0]    max_cur;
  reg [13:0]    max_cur_x3;
  reg [15:0]    v_o_next [0:N_OUT-1];
  reg [15:0]    max_val;
  reg [1:0]     max_idx;
  reg [1:0]     sel_idx;
  reg [15:0]    cur_val;
  reg [1:0]     winner_idx;

  // --- Sequential: LIF dynamics + learning ---
  always @(posedge clk) begin
    if (rst) begin
      dir_bits <= 0;
      h_spike  <= 0;
      baseline_valid <= 1'b0;
      winner_idx <= 2'd0;
      for (i = 0; i < N_H; i = i + 1) begin
        v_mem_h[i] <= 0;
        ref_h[i]   <= 0;
      end
      for (j = 0; j < N_OUT; j = j + 1) begin
        v_mem_o[j] <= 0;
        ref_o[j]   <= 0;
      end
      for (i = 0; i < 4; i = i + 1)
        baseline[i] <= 10'd0;
      lfsr[0] <= 16'hACE1;
      lfsr[1] <= 16'hBEEF;
      lfsr[2] <= 16'h1234;
      lfsr[3] <= 16'hD00D;
      for (i = 0; i < N_IN; i = i + 1) begin
        for (j = 0; j < N_H; j = j + 1) begin
          G_in[i][j] <= G_INIT;
        end
      end
      for (i = 0; i < N_H; i = i + 1) begin
        for (j = 0; j < N_OUT; j = j + 1) begin
          G[i][j] <= G_INIT;
        end
      end
    end else if (frame_valid) begin
      lfsr[0] <= {lfsr[0][14:0], fb0};
      lfsr[1] <= {lfsr[1][14:0], fb1};
      lfsr[2] <= {lfsr[2][14:0], fb2};
      lfsr[3] <= {lfsr[3][14:0], fb3};
      // On the very first valid frame, capture ambient sensor values
      // as baseline and skip LIF / learning for that frame.
      if (!baseline_valid) begin
        baseline[0] <= s0_10;
        baseline[1] <= s1_10;
        baseline[2] <= s2_10;
        baseline[3] <= s3_10;
        baseline_valid <= 1'b1;
        h_spike  <= 0;
        dir_bits <= 4'b0000;
      end else begin

      // =============================================
      // 1. HIDDEN LAYER — Leak, Integrate, Fire (LIF + refractory)
      // =============================================
      h_spike_next = {N_H{1'b0}};
      for (i = 0; i < N_H; i = i + 1) begin
        if (ref_h[i] != 0) begin
          // In refractory: hold at 0, count down, no spike
          ref_h[i]   <= ref_h[i] - 1;
          h_spike_next[i] = 1'b0;
          v_mem_h[i] <= 12'd0;
        end else begin
          in_current = 12'd0;
          for (k = 0; k < N_IN; k = k + 1) begin
            if (in_spike[k])
              in_current = in_current + {4'd0, (G_in[k][i] >> IN_TO_H_SHIFT)};
          end

          // Compute next membrane potential
          // reg [12:0] v_h_tmp; // Moved to module scope
          if (v_mem_h[i] > LEAK_H)
            v_h_tmp = {1'b0, v_mem_h[i] - LEAK_H} + {1'b0, in_current};
          else
            v_h_tmp = {1'b0, in_current};

          if (v_h_tmp >= V_THRESH_H) begin
            // Spike
            h_spike_next[i] = 1'b1;
            v_mem_h[i]  <= 12'd0;
            ref_h[i]    <= REF_H_FRAMES;
          end else begin
            h_spike_next[i] = 1'b0;
            // Clamp to 12‑bit
            if (v_h_tmp[12])
              v_mem_h[i] <= 12'hFFF;
            else
              v_mem_h[i] <= v_h_tmp[11:0];
          end
        end
      end
      h_spike <= h_spike_next;

      // =============================================
      // 2. OUTPUT LAYER — Leak, Integrate, Fire (independent outputs)
      // =============================================
      o_spike_next = 4'b0000;
      for (j = 0; j < N_OUT; j = j + 1) begin
        if (ref_o[j] != 0) begin
          ref_o[j] <= ref_o[j] - 1;
          v_o_next[j] = 16'd0;
        end else begin
          syn_current_j = 16'd0;
          for (i = 0; i < N_H; i = i + 1) begin
            if (h_spike_next[i])
              syn_current_j = syn_current_j + ({8'd0, (G[i][j] >> H_TO_O_SHIFT)});
          end

          if (v_mem_o[j] > LEAK_O)
            v_o_tmp = (v_mem_o[j] - LEAK_O) + syn_current_j;
          else
            v_o_tmp = syn_current_j;

          if (v_o_tmp > 16'd255)
            v_o_tmp = 16'd255;
          v_o_next[j] = v_o_tmp;
        end
      end

      max_idx = 2'd0;
      max_val = v_o_next[0];
      for (j = 1; j < N_OUT; j = j + 1) begin
        if (v_o_next[j] > max_val) begin
          max_val = v_o_next[j];
          max_idx = j[1:0];
        end
      end

      cur_val = v_o_next[winner_idx];
      if (cur_val + WTA_HYST >= max_val) sel_idx = winner_idx;
      else sel_idx = max_idx;
      winner_idx <= sel_idx;

      for (j = 0; j < N_OUT; j = j + 1) begin
        if (j[1:0] == sel_idx && v_o_next[j] >= V_THRESH_O) begin
          o_spike_next[j] = 1'b1;
          v_mem_o[j] <= 16'd0;
          ref_o[j] <= REF_O_FRAMES;
        end else begin
          o_spike_next[j] = 1'b0;
          if (j[1:0] == sel_idx) begin
            v_mem_o[j] <= v_o_next[j];
          end else begin
            if (v_o_next[j] > INHIB_O) v_mem_o[j] <= v_o_next[j] - INHIB_O;
            else v_mem_o[j] <= 16'd0;
          end
        end
      end

      dir_bits <= o_spike_next;

      // =============================================
      // 3. MEMRISTOR LEARNING (supervised, bounded conductance updates)
      // =============================================
      if (train) begin
        if (label_dir_override != 4'b0000) begin
          max_cur = current[0];
          if (current[1] > max_cur) max_cur = current[1];
          if (current[2] > max_cur) max_cur = current[2];
          if (current[3] > max_cur) max_cur = current[3];

          if (max_cur >= TRAIN_MIN_CUR) begin
            for (i = 0; i < N_H; i = i + 1) begin
              if (h_spike_next[i]) begin
                for (j = 0; j < N_OUT; j = j + 1) begin
                  if (j[1:0] == label_idx) begin
                    if (G[i][j] >= (G_MAX - D_POT)) G[i][j] <= G_MAX;
                    else G[i][j] <= G[i][j] + D_POT;
                  end else begin
                    if (G[i][j] <= (G_MIN + D_DEP)) G[i][j] <= G_MIN;
                    else G[i][j] <= G[i][j] - D_DEP;
                  end
                end

                for (k = 0; k < N_IN; k = k + 1) begin
                  if (in_spike[k]) begin
                    if (G_in[k][i] >= (G_MAX - D_POT_IN)) G_in[k][i] <= G_MAX;
                    else G_in[k][i] <= G_in[k][i] + D_POT_IN;
                  end
                end
              end
            end
          end
        end
      end  // train

      end  // baseline_valid else

    end // frame_valid
  end
endmodule
