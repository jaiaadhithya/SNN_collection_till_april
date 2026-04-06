
-- LIF Neuron Implementation for FPGA
-- Fixed-point arithmetic, 16-bit precision

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity LIF_Neuron is
    Port (
        clk : in STD_LOGIC;
        rst : in STD_LOGIC;
        enable : in STD_LOGIC;
        input_current : in signed(15 downto 0);  -- 16-bit input current
        spike_out : out STD_LOGIC;
        voltage_out : out signed(15 downto 0)    -- 16-bit membrane potential
    );
end LIF_Neuron;

architecture Behavioral of LIF_Neuron is
    -- Fixed-point parameters (scaled by 2^8 = 256)
    constant V_REST : signed(15 downto 0) := to_signed(-17920, 16);     -- -70mV * 256
    constant V_THRESHOLD : signed(15 downto 0) := to_signed(-12800, 16); -- -50mV * 256
    constant V_RESET : signed(15 downto 0) := to_signed(-17920, 16);     -- -70mV * 256
    
    -- Time constant parameters (pre-computed)
    constant DECAY_FACTOR : signed(15 downto 0) := to_signed(58982, 16); -- 0.9 * 2^16
    constant INPUT_GAIN : signed(15 downto 0) := to_signed(410, 16);     -- 0.1 * 2^12
    
    -- State variables
    signal voltage : signed(15 downto 0) := V_REST;
    signal temp_voltage : signed(31 downto 0);
    
begin
    process(clk, rst)
    begin
        if rst = '1' then
            voltage <= V_REST;
            spike_out <= '0';
        elsif rising_edge(clk) then
            if enable = '1' then
                -- Leaky integration: V = decay * V + gain * I + rest_bias
                temp_voltage <= voltage * DECAY_FACTOR;
                voltage <= temp_voltage(31 downto 16) + 
                          (input_current * INPUT_GAIN)(27 downto 12) +
                          ((V_REST * (65536 - DECAY_FACTOR))(31 downto 16));
                
                -- Spike generation and reset
                if voltage > V_THRESHOLD then
                    spike_out <= '1';
                    voltage <= V_RESET;
                else
                    spike_out <= '0';
                end if;
            end if;
        end if;
    end process;
    
    voltage_out <= voltage;
    
end Behavioral;
