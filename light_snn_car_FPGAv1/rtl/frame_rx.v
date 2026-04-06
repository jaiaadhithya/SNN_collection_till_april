module frame_rx(
input clk,
input rst,
input [7:0] rx_data,
input rx_valid,
output reg [11:0] s0,
output reg [11:0] s1,
output reg [11:0] s2,
output reg [11:0] s3,
output reg [7:0] btn_mask,
output reg frame_valid
);
reg [7:0] b [0:15]; // Buffer
reg [4:0] idx;      // Index counter
reg [7:0] checksum; // Rolling checksum

always @(posedge clk) begin
  if (rst) begin
    idx <= 0;
    frame_valid <= 0;
    btn_mask <= 0;
    checksum <= 0;
    s0 <= 0; s1 <= 0; s2 <= 0; s3 <= 0;
  end else begin
    frame_valid <= 0;
    if (rx_valid) begin
      case (idx)
        0: if (rx_data == 8'hAA) idx <= 1; else idx <= 0;
        1: if (rx_data == 8'h55) idx <= 2; else idx <= 0;
        2: begin // LEN byte (Expected 0x09)
             if (rx_data == 8'h09) begin
                idx <= 3;
                checksum <= 0; // Reset checksum
             end else idx <= 0;
           end
        default: begin // Data Payload + Checksum
           if (idx < 12) begin // Reading Payload (Bytes 3 to 11)
             b[idx] <= rx_data;
             checksum <= checksum ^ rx_data; // XOR Checksum calculation
             idx <= idx + 1;
           end else if (idx == 12) begin // Checksum Byte
             if (rx_data == checksum) begin
               // Valid Packet - Update Outputs
               s0 <= {b[3][3:0], b[4]};
               s1 <= {b[5][3:0], b[6]};
               s2 <= {b[7][3:0], b[8]};
               s3 <= {b[9][3:0], b[10]};
               btn_mask   <= b[11];
               frame_valid <= 1;
             end
             idx <= 0; // Reset for next packet
           end
        end
      endcase
    end
  end
end
endmodule
