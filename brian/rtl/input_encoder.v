// Input Encoder: 9-channel LDR analog-to-spike converter
// - Accepts packed sensor values (12-bit each)
// - Generates Poisson-like spikes using per-channel LFSR

module input_encoder #(
    parameter N_INPUTS   = 9,
    parameter SENSOR_W   = 12,
    parameter RNG_W      = 16,
    parameter SCALE_SHIFT= 2
) (
    input  wire                       clk,
    input  wire                       reset,
    input  wire [N_INPUTS*SENSOR_W-1:0] sensor_in,
    output reg  [N_INPUTS-1:0]        spike_out
);

    // Per-channel LFSRs
    reg [RNG_W-1:0] lfsr [0:N_INPUTS-1];

    integer k;
    wire [SENSOR_W-1:0] sensor_val [0:N_INPUTS-1];
    generate
        genvar i;
        for (i=0; i<N_INPUTS; i=i+1) begin : UNPACK
            assign sensor_val[i] = sensor_in[(i+1)*SENSOR_W-1 -: SENSOR_W];
        end
    endgenerate

    // Initialize LFSRs differently per channel
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (k=0;k<N_INPUTS;k=k+1) begin
                lfsr[k]    <= (16'hACE1 ^ (k*16'h1357));
                spike_out[k]<= 1'b0;
            end
        end else begin
            for (k=0;k<N_INPUTS;k=k+1) begin
                // x^16 + x^14 + x^13 + x^11 + 1
                lfsr[k] <= {lfsr[k][RNG_W-2:0],
                           lfsr[k][15] ^ lfsr[k][13] ^ lfsr[k][12] ^ lfsr[k][10]};
                // Scale sensor value to RNG width
                // prob ~ sensor_val << (RNG_W - SENSOR_W - SCALE_SHIFT)
                // clamp to RNG_W bits
                // Compare RNG to probability threshold
                if ( { { (RNG_W-(SENSOR_W+SCALE_SHIFT)){1'b0} }, sensor_val[k], {SCALE_SHIFT{1'b0}} } > lfsr[k] )
                    spike_out[k] <= 1'b1;
                else
                    spike_out[k] <= 1'b0;
            end
        end
    end

endmodule

