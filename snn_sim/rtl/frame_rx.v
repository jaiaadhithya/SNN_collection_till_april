// frame_rx.v - Icarus Verilog compatible version
// Ports use flat packed buses instead of unpacked arrays
// sensors output: 48 bits = 4 x 12-bit sensor values, packed:
//   sensors[47:36]=sensor3, [35:24]=sensor2, [23:12]=sensor1, [11:0]=sensor0
module frame_rx(
    input  clk,
    input  rst,
    input  [7:0]  rx_data,
    input         rx_valid,
    output reg [47:0] sensors,   // 4 x 12-bit packed: {s3,s2,s1,s0}
    output reg [7:0]  btn_mask,
    output reg        frame_valid
);
    reg [7:0] b [0:15]; // Buffer
    reg [4:0] idx;      // Index counter
    reg [7:0] checksum; // Rolling checksum
    reg [15:0] tmp;

    always @(posedge clk) begin
        if (rst) begin
            idx        <= 0;
            frame_valid <= 0;
            btn_mask   <= 0;
            checksum   <= 0;
            sensors    <= 0;
        end else begin
            frame_valid <= 0;
            if (rx_valid) begin
                case (idx)
                    0: if (rx_data == 8'hAA) idx <= 1; else idx <= 0;
                    1: if (rx_data == 8'h55) idx <= 2; else idx <= 0;
                    2: begin
                            if (rx_data == 8'h09) begin
                                idx      <= 3;
                                checksum <= 0;
                            end else idx <= 0;
                       end
                    default: begin
                        if (idx < 12) begin
                            b[idx]   <= rx_data;
                            checksum <= checksum ^ rx_data;
                            idx      <= idx + 1;
                        end else if (idx == 12) begin
                            if (rx_data == checksum) begin
                                // Valid packet - unpack sensors (Icarus compatible)
                                // sensor[n] = upper 12 bits of {b[3+2n], b[4+2n]}
                                tmp = {b[3], b[4]};
                                sensors[11:0]  <= tmp[15:4];
                                tmp = {b[5], b[6]};
                                sensors[23:12] <= tmp[15:4];
                                tmp = {b[7], b[8]};
                                sensors[35:24] <= tmp[15:4];
                                tmp = {b[9], b[10]};
                                sensors[47:36] <= tmp[15:4];
                                btn_mask       <= b[11];
                                frame_valid    <= 1;
                            end
                            idx <= 0;
                        end
                    end
                endcase
            end
        end
    end
endmodule
