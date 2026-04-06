// Testbench for SNN Top (Virtual Memristor Mode)

`timescale 1ns/1ps

module snn_tb;
    localparam N_INPUTS = 9;
    localparam SENSOR_W = 12;

    reg clk;
    reg reset_n;
    reg mode_virtual;
    reg [N_INPUTS*SENSOR_W-1:0] sensor_in;
    reg train_btn, left_btn, right_btn;
    wire pwm_left, pwm_right;
    wire signed [23:0] v_left_dbg, v_right_dbg;

    // Unused SPI in TB
    wire dac_sclk, dac_mosi, dac_cs_n;
    wire adc_sclk, adc_mosi, adc_cs_n;
    wire dac_miso = 1'b0;
    wire adc_miso = 1'b0;

    snn_top #(.N_INPUTS(N_INPUTS), .SENSOR_W(SENSOR_W)) dut (
        .clk_50mhz (clk),
        .reset_n   (reset_n),
        .mode_virtual(mode_virtual),
        .sensor_in (sensor_in),
        .train_btn (train_btn),
        .left_btn  (left_btn),
        .right_btn (right_btn),
        .dac_sclk  (dac_sclk),
        .dac_mosi  (dac_mosi),
        .dac_miso  (dac_miso),
        .dac_cs_n  (dac_cs_n),
        .adc_sclk  (adc_sclk),
        .adc_mosi  (adc_mosi),
        .adc_miso  (adc_miso),
        .adc_cs_n  (adc_cs_n),
        .pwm_left  (pwm_left),
        .pwm_right (pwm_right),
        .v_left_dbg(v_left_dbg),
        .v_right_dbg(v_right_dbg)
    );

    // 50MHz clock
    initial begin
        clk = 0;
        forever #10 clk = ~clk; // 20ns period
    end

    integer t;
    initial begin
        reset_n = 0;
        mode_virtual = 1'b1;
        sensor_in = {N_INPUTS*SENSOR_W{1'b0}};
        train_btn = 1'b0; left_btn = 1'b0; right_btn = 1'b0;
        #200;
        reset_n = 1;

        // Stimulate sensors with varying values
        for (t=0; t<100000; t=t+1) begin
            // Simple pattern: left-side sensors stronger initially
            sensor_in[ 11:  0] <= 12'd3000;
            sensor_in[ 23: 12] <= 12'd2800;
            sensor_in[ 35: 24] <= 12'd2600;
            sensor_in[ 47: 36] <= 12'd2000;
            sensor_in[ 59: 48] <= 12'd1800;
            sensor_in[ 71: 60] <= 12'd1600;
            sensor_in[ 83: 72] <= 12'd1000;
            sensor_in[ 95: 84] <= 12'd800;
            sensor_in[107: 96] <= 12'd600;

            // Training pulse: strengthen left after some time
            if (t == 20000) begin
                train_btn <= 1'b1; left_btn <= 1'b1; right_btn <= 1'b0;
            end
            if (t == 22000) begin
                train_btn <= 1'b0; left_btn <= 1'b0; right_btn <= 1'b0;
            end

            // Switch preference to right later
            if (t == 60000) begin
                train_btn <= 1'b1; left_btn <= 1'b0; right_btn <= 1'b1;
            end
            if (t == 62000) begin
                train_btn <= 1'b0; left_btn <= 1'b0; right_btn <= 1'b0;
            end

            // Observe debug periodically
            if (t % 10000 == 0) begin
                $display("t=%0d vL=%0d vR=%0d pwmL=%b pwmR=%b", t, v_left_dbg, v_right_dbg, pwm_left, pwm_right);
            end
            #20; // one clock period
        end

        $display("TB completed");
        $finish;
    end

endmodule

