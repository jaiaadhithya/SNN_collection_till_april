// Memristor Model
// Mode 1: Real memristor handled by crossbar interface (external programming/read)
// Mode 2: Virtual memristor conductance register (I_syn = G_mem * V_spike)

module memristor_model #(
    parameter G_WIDTH   = 16,
    parameter VSPK_WIDTH= 16,
    parameter I_WIDTH   = 24,
    parameter MUL_SHIFT = 8
) (
    input  wire                     clk,
    input  wire                     reset,
    input  wire                     mode_virtual, // 1: virtual, 0: real
    input  wire                     pre_spike,
    input  wire [G_WIDTH-1:0]       g_mem,
    input  wire [VSPK_WIDTH-1:0]    v_spike,
    input  wire [I_WIDTH-1:0]       i_real,      // from real crossbar sense path
    output reg  signed [I_WIDTH-1:0] i_out
);

    wire [G_WIDTH+VSPK_WIDTH-1:0] mul_full = g_mem * v_spike; // unsigned
    wire [I_WIDTH-1:0]            i_virtual = mul_full >> MUL_SHIFT;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            i_out <= {I_WIDTH{1'b0}};
        end else begin
            if (mode_virtual) begin
                if (pre_spike)
                    i_out <= $signed({1'b0, i_virtual[I_WIDTH-2:0]});
                else
                    i_out <= {I_WIDTH{1'b0}};
            end else begin
                i_out <= $signed(i_real);
            end
        end
    end

endmodule

