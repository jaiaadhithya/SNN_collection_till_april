// Simple SPI Master (Mode 0: CPOL=0, CPHA=0)
// Parameterizable clock divider and transaction width

module spi_master #(
    parameter DIV_WIDTH = 16,
    parameter DATA_W    = 16
) (
    input  wire                 clk,
    input  wire                 reset,
    input  wire [DIV_WIDTH-1:0] clk_div, // SCLK = clk / (2*clk_div)
    input  wire                 start,
    input  wire [DATA_W-1:0]    data_in,
    input  wire [7:0]           n_bits,
    output reg                  busy,
    output reg                  done,
    output reg  [DATA_W-1:0]    data_out,
    // SPI pins
    output reg                  sclk,
    output reg                  mosi,
    input  wire                 miso,
    output reg                  cs_n
);

    reg [DIV_WIDTH-1:0] div_cnt;
    reg [7:0]           bit_cnt;
    reg [DATA_W-1:0]    shifter;
    reg                 sclk_en;

    localparam IDLE=0, ASSERT_CS=1, TRANSFER=2, DEASSERT_CS=3;
    reg [1:0] state;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            div_cnt  <= 0;
            bit_cnt  <= 0;
            shifter  <= 0;
            sclk     <= 0;
            sclk_en  <= 0;
            mosi     <= 0;
            cs_n     <= 1;
            busy     <= 0;
            done     <= 0;
            data_out <= 0;
            state    <= IDLE;
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    sclk <= 1'b0;
                    cs_n <= 1'b1;
                    if (start) begin
                        shifter <= data_in;
                        bit_cnt <= n_bits;
                        sclk_en <= 1'b1;
                        busy    <= 1'b1;
                        state   <= ASSERT_CS;
                    end
                end
                ASSERT_CS: begin
                    cs_n <= 1'b0;
                    state<= TRANSFER;
                end
                TRANSFER: begin
                    // Clock divider
                    if (div_cnt == clk_div) begin
                        div_cnt <= 0;
                        sclk    <= ~sclk;
                        if (sclk == 1'b0) begin
                            // Rising edge: sample MISO
                            data_out <= {data_out[DATA_W-2:0], miso};
                        end else begin
                            // Falling edge: shift out MOSI
                            mosi    <= shifter[DATA_W-1];
                            shifter <= {shifter[DATA_W-2:0], 1'b0};
                            if (bit_cnt != 0)
                                bit_cnt <= bit_cnt - 1'b1;
                            if (bit_cnt == 1) begin
                                state <= DEASSERT_CS;
                            end
                        end
                    end else begin
                        div_cnt <= div_cnt + 1'b1;
                    end
                end
                DEASSERT_CS: begin
                    cs_n  <= 1'b1;
                    sclk  <= 1'b0;
                    busy  <= 1'b0;
                    done  <= 1'b1;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule

