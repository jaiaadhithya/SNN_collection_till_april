
-- Memristor Synapse Implementation
-- 4-bit state, 16 discrete resistance levels

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity Memristor_Synapse is
    Port (
        clk : in STD_LOGIC;
        rst : in STD_LOGIC;
        pre_spike : in STD_LOGIC;
        post_spike : in STD_LOGIC;
        learning_enable : in STD_LOGIC;
        synaptic_current : out signed(15 downto 0)
    );
end Memristor_Synapse;

architecture Behavioral of Memristor_Synapse is
    -- Memristor state (4-bit = 16 levels)
    signal memristor_state : unsigned(3 downto 0) := "1000"; -- Start at middle
    
    -- Resistance lookup table (in kOhms, scaled)
    type resistance_array is array (0 to 15) of unsigned(15 downto 0);
    constant RESISTANCE_LUT : resistance_array := (
        x"03E8", x"04E2", x"05DC", x"06D6", x"07D0", x"08CA", x"09C4", x"0ABE",
        x"0BB8", x"0CB2", x"0DAC", x"0EA6", x"0FA0", x"109A", x"1194", x"128E"
    );
    
    -- STDP timing windows
    signal pre_spike_history : std_logic_vector(7 downto 0) := (others => '0');
    signal post_spike_history : std_logic_vector(7 downto 0) := (others => '0');
    
begin
    process(clk, rst)
    begin
        if rst = '1' then
            memristor_state <= "1000";
            pre_spike_history <= (others => '0');
            post_spike_history <= (others => '0');
        elsif rising_edge(clk) then
            -- Shift spike history registers
            pre_spike_history <= pre_spike_history(6 downto 0) & pre_spike;
            post_spike_history <= post_spike_history(6 downto 0) & post_spike;
            
            -- STDP learning rule
            if learning_enable = '1' then
                -- Potentiation: pre before post
                if pre_spike = '1' and (post_spike_history(1) = '1' or post_spike_history(2) = '1') then
                    if memristor_state < 15 then
                        memristor_state <= memristor_state + 1;
                    end if;
                -- Depression: post before pre
                elsif post_spike = '1' and (pre_spike_history(1) = '1' or pre_spike_history(2) = '1') then
                    if memristor_state > 0 then
                        memristor_state <= memristor_state - 1;
                    end if;
                end if;
            end if;
        end if;
    end process;
    
    -- Calculate synaptic current based on resistance
    -- I = V / R, where V is fixed at 1V for simplicity
    synaptic_current <= signed('0' & (x"FFFF" / RESISTANCE_LUT(to_integer(memristor_state))));
    
end Behavioral;
