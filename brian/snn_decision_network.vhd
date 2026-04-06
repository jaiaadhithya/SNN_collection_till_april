
-- Top-level SNN with Decision Making
-- Multiple input neurons, competitive output layer

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity SNN_Decision_Network is
    Port (
        clk : in STD_LOGIC;
        rst : in STD_LOGIC;
        enable : in STD_LOGIC;
        -- Input stimuli (3 inputs)
        input_stimulus_0 : in signed(15 downto 0);
        input_stimulus_1 : in signed(15 downto 0);
        input_stimulus_2 : in signed(15 downto 0);
        -- Decision outputs (2 outputs)
        decision_0 : out STD_LOGIC;
        decision_1 : out STD_LOGIC;
        -- Debug outputs
        neuron_0_voltage : out signed(15 downto 0);
        neuron_1_voltage : out signed(15 downto 0)
    );
end SNN_Decision_Network;

architecture Behavioral of SNN_Decision_Network is
    -- Component declarations
    component LIF_Neuron is
        Port (
            clk : in STD_LOGIC;
            rst : in STD_LOGIC;
            enable : in STD_LOGIC;
            input_current : in signed(15 downto 0);
            spike_out : out STD_LOGIC;
            voltage_out : out signed(15 downto 0)
        );
    end component;
    
    component Memristor_Synapse is
        Port (
            clk : in STD_LOGIC;
            rst : in STD_LOGIC;
            pre_spike : in STD_LOGIC;
            post_spike : in STD_LOGIC;
            learning_enable : in STD_LOGIC;
            synaptic_current : out signed(15 downto 0)
        );
    end component;
    
    -- Internal signals
    signal neuron_0_current, neuron_1_current : signed(15 downto 0);
    signal syn_currents : array(0 to 5) of signed(15 downto 0);
    signal input_spikes : std_logic_vector(2 downto 0);
    signal output_spikes : std_logic_vector(1 downto 0);
    
begin
    -- Input spike generation (simple threshold)
    input_spikes(0) <= '1' when input_stimulus_0 > x"1000" else '0';
    input_spikes(1) <= '1' when input_stimulus_1 > x"1000" else '0';
    input_spikes(2) <= '1' when input_stimulus_2 > x"1000" else '0';
    
    -- Synaptic connections (3 inputs × 2 outputs = 6 synapses)
    syn_gen: for i in 0 to 2 generate
        syn_to_n0: Memristor_Synapse port map (
            clk => clk, rst => rst,
            pre_spike => input_spikes(i),
            post_spike => output_spikes(0),
            learning_enable => enable,
            synaptic_current => syn_currents(i)
        );
        
        syn_to_n1: Memristor_Synapse port map (
            clk => clk, rst => rst,
            pre_spike => input_spikes(i),
            post_spike => output_spikes(1),
            learning_enable => enable,
            synaptic_current => syn_currents(i+3)
        );
    end generate;
    
    -- Sum synaptic currents for each neuron
    neuron_0_current <= syn_currents(0) + syn_currents(1) + syn_currents(2);
    neuron_1_current <= syn_currents(3) + syn_currents(4) + syn_currents(5);
    
    -- Output neurons
    neuron_0: LIF_Neuron port map (
        clk => clk, rst => rst, enable => enable,
        input_current => neuron_0_current,
        spike_out => output_spikes(0),
        voltage_out => neuron_0_voltage
    );
    
    neuron_1: LIF_Neuron port map (
        clk => clk, rst => rst, enable => enable,
        input_current => neuron_1_current,
        spike_out => output_spikes(1),
        voltage_out => neuron_1_voltage
    );
    
    -- Output assignments
    decision_0 <= output_spikes(0);
    decision_1 <= output_spikes(1);
    
end Behavioral;
