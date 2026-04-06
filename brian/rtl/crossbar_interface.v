// 9x2 Memristor Crossbar Interface
// - Virtual mode: internal conductance registers and summation
// - Real mode: placeholders for DAC/ADC SPI programming and readback
// - Training updates via external controller

module crossbar_interface #(
    parameter N_IN     = 9,
    parameter N_OUT    = 2,
    parameter G_WIDTH  = 16,
    parameter I_WIDTH  = 24
) (
    input  wire                     clk,
    input  wire                     reset,
    input  wire                     mode_real,

    input  wire [N_IN-1:0]         pre_spike,
    input  wire [15:0]             v_spike,

    // Training update interface
    input  wire                     update_en,
    input  wire [N_OUT-1:0]        update_sel,    // bitmask per output neuron
    input  wire [N_IN-1:0]         update_mask,   // which inputs are active
    input  wire [G_WIDTH-1:0]      delta_val,
    input  wire [G_WIDTH-1:0]      g_min,
    input  wire [G_WIDTH-1:0]      g_max,

    // Summed synaptic currents to outputs
    output reg  signed [I_WIDTH-1:0] i_syn_left,
    output reg  signed [I_WIDTH-1:0] i_syn_right,

    // SPI to DAC (program) and ADC (sense)
    output wire                     dac_sclk,
    output wire                     dac_mosi,
    input  wire                     dac_miso,
    output wire                     dac_cs_n,
    output wire                     adc_sclk,
    output wire                     adc_mosi,
    input  wire                     adc_miso,
    output wire                     adc_cs_n
);

    // Conductance storage (flattened: index = i*N_OUT + j)
    reg [G_WIDTH-1:0] g_mem [0:N_IN*N_OUT-1];

    // Optional ROM init for simulation / synthesis-supported init
    initial begin
        $readmemh("weights_rom.hex", g_mem);
    end

    // Summation logic for virtual mode
    integer ii;
    wire [I_WIDTH-1:0] contrib_left [0:N_IN-1];
    wire [I_WIDTH-1:0] contrib_right[0:N_IN-1];
    generate
        genvar k;
        for (k=0; k<N_IN; k=k+1) begin : GEN_CONTRIB
            wire [G_WIDTH-1:0] gL = g_mem[k*N_OUT + 0];
            wire [G_WIDTH-1:0] gR = g_mem[k*N_OUT + 1];
            wire [G_WIDTH+15:0] mulL = gL * v_spike;
            wire [G_WIDTH+15:0] mulR = gR * v_spike;
            assign contrib_left[k]  = pre_spike[k] ? (mulL[ I_WIDTH-1:0 ]) : {I_WIDTH{1'b0}};
            assign contrib_right[k] = pre_spike[k] ? (mulR[ I_WIDTH-1:0 ]) : {I_WIDTH{1'b0}};
        end
    endgenerate

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            i_syn_left  <= {I_WIDTH{1'b0}};
            i_syn_right <= {I_WIDTH{1'b0}};
        end else begin
            if (!mode_real) begin
                // Virtual mode: sum contributions
                reg [I_WIDTH-1:0] sumL;
                reg [I_WIDTH-1:0] sumR;
                sumL = {I_WIDTH{1'b0}};
                sumR = {I_WIDTH{1'b0}};
                for (ii=0; ii<N_IN; ii=ii+1) begin
                    sumL = sumL + contrib_left[ii];
                    sumR = sumR + contrib_right[ii];
                end
                i_syn_left  <= $signed({1'b0, sumL[I_WIDTH-2:0]});
                i_syn_right <= $signed({1'b0, sumR[I_WIDTH-2:0]});
            end else begin
                // Real mode: currents will come from sense path (not implemented here)
                i_syn_left  <= {I_WIDTH{1'b0}};
                i_syn_right <= {I_WIDTH{1'b0}};
            end
        end
    end

    // Training updates: synchronous saturating add
    integer j;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            // no-op
        end else if (update_en) begin
            for (j=0; j<N_IN; j=j+1) begin
                if (update_mask[j]) begin
                    if (update_sel[0]) begin
                        // left neuron
                        if (g_mem[j*N_OUT+0] + delta_val > g_max)
                            g_mem[j*N_OUT+0] <= g_max;
                        else
                            g_mem[j*N_OUT+0] <= g_mem[j*N_OUT+0] + delta_val;
                    end
                    if (update_sel[1]) begin
                        // right neuron
                        if (g_mem[j*N_OUT+1] + delta_val > g_max)
                            g_mem[j*N_OUT+1] <= g_max;
                        else
                            g_mem[j*N_OUT+1] <= g_mem[j*N_OUT+1] + delta_val;
                    end
                end
            end
        end
    end

    // SPI wiring placeholders (can be connected to spi_master instances externally)
    assign dac_sclk = 1'b0;
    assign dac_mosi = 1'b0;
    assign dac_cs_n = 1'b1;
    assign adc_sclk = 1'b0;
    assign adc_mosi = 1'b0;
    assign adc_cs_n = 1'b1;

endmodule

