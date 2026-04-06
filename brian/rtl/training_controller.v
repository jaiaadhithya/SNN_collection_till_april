// Training Controller
// - Supervised event-based updates using TRAIN, LEFT, RIGHT buttons
// - Increments conductance for active pre-synaptic spikes toward selected outputs
// - Optional gating by post-synaptic spikes

module training_controller #(
    parameter N_IN    = 9,
    parameter N_OUT   = 2,
    parameter G_WIDTH = 16
) (
    input  wire                    clk,
    input  wire                    reset,
    input  wire                    train,
    input  wire                    btn_left,
    input  wire                    btn_right,
    input  wire [N_IN-1:0]        pre_spike,
    input  wire [N_OUT-1:0]       post_spike,
    input  wire [G_WIDTH-1:0]     delta_base,
    output reg                     update_en,
    output reg  [N_OUT-1:0]       update_sel,
    output reg  [N_IN-1:0]        update_mask,
    output reg  [G_WIDTH-1:0]     delta_val
);

    // Simple timing: one-cycle update when train is high and a button is pressed
    // Event-based: pre_spike are considered "active synapses"
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            update_en   <= 1'b0;
            update_sel  <= {N_OUT{1'b0}};
            update_mask <= {N_IN{1'b0}};
            delta_val   <= {G_WIDTH{1'b0}};
        end else begin
            update_en   <= 1'b0;
            update_sel  <= {N_OUT{1'b0}};
            update_mask <= {N_IN{1'b0}};
            delta_val   <= {G_WIDTH{1'b0}};
            if (train) begin
                if (btn_left || btn_right) begin
                    update_en   <= 1'b1;
                    update_sel  <= {btn_right, btn_left};
                    // Optionally require post_spike correlation to strengthen
                    // Here we allow immediate supervised strengthening
                    update_mask <= pre_spike;
                    delta_val   <= delta_base;
                end
            end
        end
    end

endmodule

