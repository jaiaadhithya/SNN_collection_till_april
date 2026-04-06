// LIF Neuron (Discrete-Time, Fixed-Point)
// V[n+1] = V[n] + (I_syn - V[n]) / tau
// - 24-bit signed internal membrane potential
// - 16-bit input current
// - Threshold and reset programmable

module lif_neuron #(
    parameter V_WIDTH = 24,
    parameter I_WIDTH = 16
) (
    input  wire                     clk,
    input  wire                     reset,
    input  wire                     enable,
    input  wire signed [I_WIDTH-1:0] i_syn,
    input  wire [4:0]               tau_shift,     // division by 2^tau_shift
    input  wire signed [V_WIDTH-1:0] threshold,
    input  wire signed [V_WIDTH-1:0] v_reset,
    output reg                      spike_out,
    output reg signed [V_WIDTH-1:0] v_out
);

    reg signed [V_WIDTH-1:0] v_reg;
    wire signed [V_WIDTH-1:0] i_syn_ext = {{(V_WIDTH-I_WIDTH){i_syn[I_WIDTH-1]}}, i_syn};
    wire signed [V_WIDTH-1:0] sub_term  = i_syn_ext - v_reg;
    wire signed [V_WIDTH-1:0] delta     = sub_term >>> tau_shift; // arithmetic shift
    wire signed [V_WIDTH-1:0] v_next    = v_reg + delta;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            v_reg    <= v_reset;
            v_out    <= v_reset;
            spike_out<= 1'b0;
        end else if (enable) begin
            if (v_reg >= threshold) begin
                spike_out <= 1'b1;
                v_reg     <= v_reset;
            end else begin
                spike_out <= 1'b0;
                v_reg     <= v_next;
            end
            v_out <= v_reg;
        end else begin
            spike_out <= 1'b0;
            v_out     <= v_reg;
        end
    end

endmodule

