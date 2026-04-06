// Motor Output: Convert neuron spikes to PWM duty
// - Accumulate spikes within a window to estimate rate
// - Map rate to duty cycle

module motor_output #(
    parameter PWM_W     = 10,   // PWM resolution
    parameter WINDOW_W  = 16    // accumulation window length in cycles
) (
    input  wire                 clk,
    input  wire                 reset,
    input  wire                 spike_left,
    input  wire                 spike_right,
    input  wire [WINDOW_W-1:0]  window_len,
    output reg                  pwm_left,
    output reg                  pwm_right,
    output reg [PWM_W-1:0]      duty_left_out,
    output reg [PWM_W-1:0]      duty_right_out
);

    reg [WINDOW_W-1:0] win_cnt;
    reg [PWM_W-1:0]    acc_left;
    reg [PWM_W-1:0]    acc_right;
    reg [PWM_W-1:0]    duty_left;
    reg [PWM_W-1:0]    duty_right;
    reg [PWM_W-1:0]    pwm_cnt;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            win_cnt    <= 0;
            acc_left   <= 0;
            acc_right  <= 0;
            duty_left  <= 0;
            duty_right <= 0;
            pwm_cnt    <= 0;
            pwm_left   <= 0;
            pwm_right  <= 0;
        end else begin
            // Accumulate spikes over window
            if (win_cnt >= window_len) begin
                win_cnt   <= 0;
                duty_left <= acc_left;
                duty_right<= acc_right;
                duty_left_out  <= acc_left;
                duty_right_out <= acc_right;
                acc_left  <= 0;
                acc_right <= 0;
            end else begin
                win_cnt <= win_cnt + 1'b1;
                if (spike_left)  acc_left  <= acc_left  + 1'b1;
                if (spike_right) acc_right <= acc_right + 1'b1;
            end

            // PWM generation
            pwm_cnt  <= pwm_cnt + 1'b1;
            pwm_left <= (pwm_cnt < duty_left);
            pwm_right<= (pwm_cnt < duty_right);
        end
    end

endmodule
