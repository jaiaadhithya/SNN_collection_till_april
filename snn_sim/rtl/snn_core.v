// snn_core.v - Icarus Verilog compatible version
// sensors input: 48-bit packed bus {s3,s2,s1,s0}, each 12 bits
module snn_core #(parameter N_IN=4, parameter N_H=4, parameter N_OUT=4) (
    input  clk,
    input  rst,
    input  frame_valid,
    input  [47:0] sensors,    // packed: [11:0]=s0, [23:12]=s1, [35:24]=s2, [47:36]=s3
    input  [7:0]  btn_mask,
    output reg [3:0] dir_bits
);
    reg [7:0]  w_in_h  [0:N_IN-1];
    reg [7:0]  w_h_out [0:N_H-1][0:N_OUT-1];
    reg [11:0] thr_in;
    reg [7:0]  thr_out;
    reg [N_H-1:0] h_act;
    reg [15:0] out_sum [0:N_OUT-1];

    wire train = btn_mask[0];
    wire left  = btn_mask[1];
    wire right = btn_mask[2];
    wire front = btn_mask[3];
    wire back  = btn_mask[4];

    // Unpack sensors from flat bus
    wire [11:0] s [0:3];
    assign s[0] = sensors[11:0];
    assign s[1] = sensors[23:12];
    assign s[2] = sensors[35:24];
    assign s[3] = sensors[47:36];

    integer i, j;

    always @(posedge clk) begin
        if (rst) begin
            dir_bits <= 0;
            thr_in   <= 12'd800;
            thr_out  <= 8'd2;   // lowered: 4 neurons * weight=1 = sum=4 > 2, so fires
            for (i = 0; i < N_IN; i = i + 1) w_in_h[i] <= 8'd1;
            for (i = 0; i < N_H;  i = i + 1)
                for (j = 0; j < N_OUT; j = j + 1) w_h_out[i][j] <= 8'd1;
        end else begin
            if (frame_valid) begin
                // --- Input encoding (uses s[] wire, reflects immediately) ---
                for (i = 0; i < N_H; i = i + 1)
                    h_act[i] <= (s[i] > thr_in) ? 1'b1 : 1'b0;

                // --- Inference -----------------------------------------------
                for (j = 0; j < N_OUT; j = j + 1) out_sum[j] <= 0;
                for (i = 0; i < N_H; i = i + 1) begin
                    if (h_act[i]) begin
                        for (j = 0; j < N_OUT; j = j + 1)
                            out_sum[j] <= out_sum[j] + w_h_out[i][j];
                    end
                end

                // --- Winner-Take-All -----------------------------------------
                dir_bits <= 0;
                if      (out_sum[0] >= out_sum[1] && out_sum[0] >= out_sum[2] && out_sum[0] >= out_sum[3] && out_sum[0] >= thr_out) dir_bits[0] <= 1'b1;
                else if (out_sum[1] >= out_sum[0] && out_sum[1] >= out_sum[2] && out_sum[1] >= out_sum[3] && out_sum[1] >= thr_out) dir_bits[1] <= 1'b1;
                else if (out_sum[2] >= out_sum[0] && out_sum[2] >= out_sum[1] && out_sum[2] >= out_sum[3] && out_sum[2] >= thr_out) dir_bits[2] <= 1'b1;
                else if (out_sum[3] >= out_sum[0] && out_sum[3] >= out_sum[1] && out_sum[3] >= out_sum[2] && out_sum[3] >= thr_out) dir_bits[3] <= 1'b1;

                // --- Hebbian Learning ----------------------------------------
                if (train) begin
                    if (front) begin
                        for (i = 0; i < N_H; i = i + 1) if (h_act[i]) if (w_h_out[i][0] < 8'd250) w_h_out[i][0] <= w_h_out[i][0] + 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][1] > 0) w_h_out[i][1] <= w_h_out[i][1] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][2] > 0) w_h_out[i][2] <= w_h_out[i][2] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][3] > 0) w_h_out[i][3] <= w_h_out[i][3] - 1;
                    end else if (back) begin
                        for (i = 0; i < N_H; i = i + 1) if (h_act[i]) if (w_h_out[i][1] < 8'd250) w_h_out[i][1] <= w_h_out[i][1] + 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][0] > 0) w_h_out[i][0] <= w_h_out[i][0] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][2] > 0) w_h_out[i][2] <= w_h_out[i][2] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][3] > 0) w_h_out[i][3] <= w_h_out[i][3] - 1;
                    end else if (left) begin
                        for (i = 0; i < N_H; i = i + 1) if (h_act[i]) if (w_h_out[i][2] < 8'd250) w_h_out[i][2] <= w_h_out[i][2] + 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][0] > 0) w_h_out[i][0] <= w_h_out[i][0] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][1] > 0) w_h_out[i][1] <= w_h_out[i][1] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][3] > 0) w_h_out[i][3] <= w_h_out[i][3] - 1;
                    end else if (right) begin
                        for (i = 0; i < N_H; i = i + 1) if (h_act[i]) if (w_h_out[i][3] < 8'd250) w_h_out[i][3] <= w_h_out[i][3] + 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][0] > 0) w_h_out[i][0] <= w_h_out[i][0] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][1] > 0) w_h_out[i][1] <= w_h_out[i][1] - 1;
                        for (i = 0; i < N_H; i = i + 1) if (w_h_out[i][2] > 0) w_h_out[i][2] <= w_h_out[i][2] - 1;
                    end
                end
            end
        end
    end
endmodule
