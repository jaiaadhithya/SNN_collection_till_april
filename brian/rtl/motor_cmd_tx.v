module motor_cmd_tx (
    input  wire        clk,
    input  wire        reset,
    input  wire [9:0]  duty_left,
    input  wire [9:0]  duty_right,
    input  wire        send,
    output wire        tx,
    output wire        busy
);
    reg [2:0] idx;
    reg       start;
    reg [7:0] byte;
    wire      tx_busy;
    uart_tx u0 (.clk(clk), .reset(reset), .start(start), .data_in(byte), .busy(tx_busy), .tx(tx));
    assign busy = tx_busy;
    reg sending;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            idx <= 3'd0;
            start <= 1'b0;
            sending <= 1'b0;
        end else begin
            start <= 1'b0;
            if (!sending && send) begin
                sending <= 1'b1;
                idx <= 3'd0;
            end
            if (sending && !tx_busy) begin
                case (idx)
                    3'd0: begin byte <= 8'hAC; start <= 1'b1; idx <= 3'd1; end
                    3'd1: begin byte <= 8'h53; start <= 1'b1; idx <= 3'd2; end
                    3'd2: begin byte <= {6'b0, duty_left[9:8]}; start <= 1'b1; idx <= 3'd3; end
                    3'd3: begin byte <= duty_left[7:0]; start <= 1'b1; idx <= 3'd4; end
                    3'd4: begin byte <= {6'b0, duty_right[9:8]}; start <= 1'b1; idx <= 3'd5; end
                    3'd5: begin byte <= duty_right[7:0]; start <= 1'b1; idx <= 3'd6; end
                    default: begin sending <= 1'b0; end
                endcase
            end
        end
    end
endmodule

