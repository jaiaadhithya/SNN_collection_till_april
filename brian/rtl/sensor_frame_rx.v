module sensor_frame_rx #(
    parameter N_INPUTS = 9
) (
    input  wire              clk,
    input  wire              reset,
    input  wire [7:0]        byte_in,
    input  wire              byte_valid,
    output reg  [N_INPUTS*12-1:0] sensor_bus,
    output reg               frame_valid
);
    reg [1:0] state;
    reg [5:0] idx;
    reg [15:0] word;
    reg header1;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state       <= 2'd0;
            idx         <= 6'd0;
            word        <= 16'd0;
            header1     <= 1'b0;
            sensor_bus  <= {N_INPUTS*12{1'b0}};
            frame_valid <= 1'b0;
        end else begin
            frame_valid <= 1'b0;
            if (byte_valid) begin
                case (state)
                    2'd0: begin
                        if (byte_in == 8'hAA) header1 <= 1'b1; else header1 <= 1'b0;
                        state <= 2'd1;
                    end
                    2'd1: begin
                        if (header1 && byte_in == 8'h55) begin
                            state <= 2'd2;
                            idx   <= 6'd0;
                        end else begin
                            state <= 2'd0;
                        end
                    end
                    2'd2: begin
                        word[15:8] <= byte_in;
                        state <= 2'd3;
                    end
                    2'd3: begin
                        word[7:0] <= byte_in;
                        sensor_bus[(idx+1)*12-1 -: 12] <= word[11:0];
                        idx <= idx + 1'b1;
                        if (idx == (N_INPUTS-1)) begin
                            frame_valid <= 1'b1;
                            state <= 2'd0;
                        end else begin
                            state <= 2'd2;
                        end
                    end
                endcase
            end
        end
    end
endmodule

