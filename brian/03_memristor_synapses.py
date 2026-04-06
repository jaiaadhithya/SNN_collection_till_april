#!/usr/bin/env python3
"""
Memristor-Based Synapses Tutorial
=================================

This tutorial demonstrates:
1. Memristor device modeling and I-V characteristics
2. SNN with memristor-based synaptic weights
3. Hardware-friendly discrete memristor model
4. Learning through memristor state changes

Author: SNN Tutorial Series
Date: 2024
"""

import numpy as np
import matplotlib.pyplot as plt
from brian2 import *

# Set Brian2 preferences
prefs.codegen.target = 'numpy'

class MemristorModel:
    """
    Simple memristor model based on linear drift model
    
    Key equations:
    - R(t) = R_on * w + R_off * (1-w)
    - dw/dt = (mu_v * R_on / D^2) * i(t)
    """
    
    def __init__(self, R_on=1e3, R_off=1e6, D=10e-9, mu_v=1e-14):
        self.R_on = R_on      # ON resistance (Ohms)
        self.R_off = R_off    # OFF resistance (Ohms)
        self.D = D            # Device thickness (m)
        self.mu_v = mu_v      # Mobility parameter
        self.w = 0.5          # State variable (0 to 1)
        
        # Derived parameters
        self.k = mu_v * R_on / (D**2)
        
    def get_resistance(self):
        """Get current resistance value"""
        return self.R_on * self.w + self.R_off * (1 - self.w)
    
    def get_conductance(self):
        """Get current conductance value"""
        return 1.0 / self.get_resistance()
    
    def update(self, voltage, dt):
        """Update memristor state based on applied voltage"""
        current = voltage / self.get_resistance()
        
        # State update equation
        dw_dt = self.k * current
        self.w += dw_dt * dt
        
        # Boundary conditions
        self.w = np.clip(self.w, 0.01, 0.99)
        
        return current
    
    def reset_to_weight(self, weight):
        """Set memristor to specific weight (0-1)"""
        self.w = np.clip(weight, 0.01, 0.99)

def memristor_characteristics():
    """
    Demonstrate memristor I-V characteristics
    """
    print("\n=== Memristor I-V Characteristics ===")
    
    # Create memristor
    mem = MemristorModel()
    print(f"Initial resistance: {mem.get_resistance()/1000:.1f} kΩ")
    
    # Apply voltage sweep
    voltages = np.linspace(-2, 2, 1000)
    currents = []
    resistances = []
    
    for v in voltages:
        i = mem.update(v, 1e-6)  # Small time step
        currents.append(i)
        resistances.append(mem.get_resistance())
    
    currents = np.array(currents)
    resistances = np.array(resistances)
    
    print(f"Final resistance: {mem.get_resistance()/1000:.1f} kΩ")
    print(f"Resistance range: {min(resistances)/1000:.1f} - {max(resistances)/1000:.1f} kΩ")
    
    # Plot I-V characteristics
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 3, 1)
    plt.plot(voltages, currents*1e6, 'b-', linewidth=2)
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (μA)')
    plt.title('Memristor I-V Curve')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 2)
    plt.plot(voltages, resistances/1000, 'r-', linewidth=2)
    plt.xlabel('Voltage (V)')
    plt.ylabel('Resistance (kΩ)')
    plt.title('Resistance vs Voltage')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 3)
    plt.plot(voltages, [mem.w for _ in voltages], 'g-', linewidth=2)
    plt.xlabel('Voltage (V)')
    plt.ylabel('State Variable w')
    plt.title('Internal State Evolution')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('memristor_characteristics.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return mem

def memristor_snn_synapses():
    """
    SNN with memristor-based synapses
    """
    print("\n=== SNN with Memristor Synapses ===")
    
    start_scope()
    
    # Network parameters
    n_input = 3
    n_output = 2
    
    # Neuron parameters
    tau_m = 10*ms
    V_rest = -70*mV
    V_threshold = -50*mV
    V_reset = -70*mV
    R = 100*Mohm

    # Input neurons (Poisson spike generators)
    input_rates = [20, 30, 25] * Hz
    input_neurons = PoissonGroup(n_input, rates=input_rates)
    
    # Output neurons (LIF)
    eqs_output = '''
    dv/dt = (V_rest - v + R * I_syn) / tau_m : volt
    I_syn : amp
    '''
    
    output_neurons = NeuronGroup(n_output, eqs_output, 
                                threshold='v > V_threshold', 
                                reset='v = V_reset', 
                                method='euler')
    output_neurons.v = V_rest
    output_neurons.I_syn = 0*amp
    
    # Create memristor synapses
    n_synapses = n_input * n_output
    memristors = [MemristorModel() for _ in range(n_synapses)]
    
    # Initialize memristor weights randomly
    for i, mem in enumerate(memristors):
        weight = 0.3 + 0.4 * np.random.rand()
        mem.reset_to_weight(weight)
    
    # Synaptic connections
    synapses = Synapses(input_neurons, output_neurons, 
                       model='''
                       w : 1
                       g_max : amp
                       ''',
                       on_pre='I_syn_post += w * g_max')
    
    # Connect all-to-all
    synapses.connect()
    synapses.g_max = 2*nA
    
    # Initialize synaptic weights from memristors
    for i in range(len(synapses)):
        synapses.w[i] = memristors[i].get_conductance() * 1e6  # Scale conductance
    
    # Monitors
    input_monitor = SpikeMonitor(input_neurons)
    output_monitor = SpikeMonitor(output_neurons)
    voltage_monitor = StateMonitor(output_neurons, 'v', record=True)
    
    print("Running SNN simulation with memristor synapses...")
    
    # Run simulation
    run(500*ms)
    
    print(f"Input spikes: {len(input_monitor.spike_trains())} neurons")
    print(f"Output spikes: {len(output_monitor.spike_trains())} neurons")
    
    # Calculate firing rates
    for i in range(n_input):
        rate = len(input_monitor.spike_trains()[i]) / (500*ms)
        print(f"Input neuron {i}: {rate:.1f} Hz")
    
    for i in range(n_output):
        rate = len(output_monitor.spike_trains()[i]) / (500*ms)
        print(f"Output neuron {i}: {rate:.1f} Hz")
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Spike raster plot
    plt.subplot(3, 2, 1)
    plt.plot(input_monitor.t/ms, input_monitor.i, '.b', markersize=3, label='Input')
    plt.plot(output_monitor.t/ms, output_monitor.i + n_input, '.r', markersize=5, label='Output')
    plt.xlabel('Time (ms)')
    plt.ylabel('Neuron Index')
    plt.title('Spike Raster Plot')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Membrane potentials
    plt.subplot(3, 2, 2)
    for i in range(n_output):
        plt.plot(voltage_monitor.t/ms, voltage_monitor.v[i]/mV, 
                label=f'Neuron {i}', linewidth=2)
    plt.axhline(y=V_threshold/mV, color='r', linestyle='--', alpha=0.7, label='Threshold')
    plt.xlabel('Time (ms)')
    plt.ylabel('Membrane Potential (mV)')
    plt.title('Output Neuron Voltages')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Synaptic weights visualization
    plt.subplot(3, 2, 3)
    weights_matrix = np.zeros((n_input, n_output))
    for i in range(len(synapses)):
        pre_idx = synapses.i[i]
        post_idx = synapses.j[i]
        weights_matrix[pre_idx, post_idx] = synapses.w[i]
    
    im = plt.imshow(weights_matrix, cmap='viridis', aspect='auto')
    plt.colorbar(im, label='Synaptic Weight')
    plt.xlabel('Output Neuron')
    plt.ylabel('Input Neuron')
    plt.title('Synaptic Weight Matrix')
    
    # Memristor resistances
    plt.subplot(3, 2, 4)
    resistances = [mem.get_resistance()/1000 for mem in memristors]
    plt.bar(range(len(resistances)), resistances, color='orange', alpha=0.7)
    plt.xlabel('Synapse Index')
    plt.ylabel('Resistance (kΩ)')
    plt.title('Memristor Resistances')
    plt.grid(True, alpha=0.3)
    
    # Input-output correlation
    plt.subplot(3, 2, 5)
    input_rates_actual = [len(input_monitor.spike_trains()[i])/(500*ms) for i in range(n_input)]
    output_rates_actual = [len(output_monitor.spike_trains()[i])/(500*ms) for i in range(n_output)]
    
    plt.bar(range(n_input), input_rates_actual, alpha=0.7, label='Input Rates', color='blue')
    plt.bar(range(n_input, n_input + n_output), output_rates_actual, 
           alpha=0.7, label='Output Rates', color='red')
    plt.xlabel('Neuron Index')
    plt.ylabel('Firing Rate (Hz)')
    plt.title('Input vs Output Firing Rates')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Network connectivity
    plt.subplot(3, 2, 6)
    # Create adjacency matrix for visualization
    adj_matrix = np.zeros((n_input + n_output, n_input + n_output))
    for i in range(len(synapses)):
        pre_idx = synapses.i[i]
        post_idx = synapses.j[i] + n_input
        adj_matrix[pre_idx, post_idx] = synapses.w[i]
    
    im = plt.imshow(adj_matrix, cmap='Blues', aspect='auto')
    plt.colorbar(im, label='Connection Strength')
    plt.xlabel('Post-synaptic Neuron')
    plt.ylabel('Pre-synaptic Neuron')
    plt.title('Network Connectivity')
    
    plt.tight_layout()
    plt.savefig('memristor_snn.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return memristors, synapses

def hardware_memristor_model():
    """
    Hardware-friendly discrete memristor model
    """
    print("\n=== Hardware-Friendly Memristor Model ===")
    
    class DiscreteMemristor:
        """Discrete state memristor for FPGA implementation"""
        
        def __init__(self, n_states=16):
            self.n_states = n_states
            self.state = n_states // 2  # Start in middle
            self.R_on = 1e3
            self.R_off = 1e6
            
        def get_resistance(self):
            # Linear interpolation between R_on and R_off
            w = self.state / (self.n_states - 1)
            return self.R_on * w + self.R_off * (1 - w)
        
        def update_state(self, voltage_sign, enable=True):
            """Update state based on voltage polarity"""
            if not enable:
                return
                
            if voltage_sign > 0 and self.state < self.n_states - 1:
                self.state += 1  # Increase conductance
            elif voltage_sign < 0 and self.state > 0:
                self.state -= 1  # Decrease conductance
    
    # Create discrete memristors
    n_memristors = 6
    discrete_mems = [DiscreteMemristor() for _ in range(n_memristors)]
    
    # Simulate learning process
    n_steps = 1000
    time_steps = np.arange(n_steps)
    resistance_history = np.zeros((n_memristors, n_steps))
    
    print("Simulating discrete memristor learning...")
    
    for step in range(n_steps):
        for i, mem in enumerate(discrete_mems):
            # Simulate different learning patterns
            if i < 2:  # Potentiation
                voltage_sign = 1 if np.random.rand() > 0.3 else 0
            elif i < 4:  # Depression
                voltage_sign = -1 if np.random.rand() > 0.3 else 0
            else:  # Random
                voltage_sign = np.random.choice([-1, 0, 1], p=[0.2, 0.6, 0.2])
            
            mem.update_state(voltage_sign, enable=np.random.rand() > 0.1)
            resistance_history[i, step] = mem.get_resistance()
    
    # Plot discrete memristor behavior
    plt.figure(figsize=(15, 8))
    
    plt.subplot(2, 3, 1)
    for i in range(n_memristors):
        plt.plot(time_steps, resistance_history[i]/1000, 
                label=f'Memristor {i}', linewidth=2)
    plt.xlabel('Time Steps')
    plt.ylabel('Resistance (kΩ)')
    plt.title('Discrete Memristor Learning')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 3, 2)
    final_states = [mem.state for mem in discrete_mems]
    plt.bar(range(n_memristors), final_states, color='purple', alpha=0.7)
    plt.xlabel('Memristor Index')
    plt.ylabel('Discrete State')
    plt.title('Final Memristor States')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 3, 3)
    final_resistances = [mem.get_resistance()/1000 for mem in discrete_mems]
    plt.bar(range(n_memristors), final_resistances, color='orange', alpha=0.7)
    plt.xlabel('Memristor Index')
    plt.ylabel('Resistance (kΩ)')
    plt.title('Final Resistances')
    plt.grid(True, alpha=0.3)
    
    # State transition analysis
    plt.subplot(2, 3, 4)
    state_changes = np.diff(resistance_history, axis=1)
    plt.imshow(state_changes, aspect='auto', cmap='RdBu', 
              extent=[0, n_steps-1, 0, n_memristors-1])
    plt.colorbar(label='Resistance Change')
    plt.xlabel('Time Steps')
    plt.ylabel('Memristor Index')
    plt.title('State Transition Heatmap')
    
    # Hardware resource estimation
    plt.subplot(2, 3, 5)
    bit_widths = [4, 6, 8, 10, 12]
    n_states_list = [2**b for b in bit_widths]
    memory_bits = [b * 1000 for b in bit_widths]  # For 1000 synapses
    
    plt.plot(bit_widths, memory_bits, 'o-', linewidth=2, markersize=8)
    plt.xlabel('State Bit Width')
    plt.ylabel('Total Memory (bits)')
    plt.title('Hardware Memory Requirements')
    plt.grid(True, alpha=0.3)
    
    # Precision analysis
    plt.subplot(2, 3, 6)
    precision_errors = []
    for n_states in n_states_list:
        # Calculate quantization error
        continuous_range = np.linspace(0, 1, 1000)
        discrete_range = np.linspace(0, 1, n_states)
        quantized = np.interp(continuous_range, 
                            np.linspace(0, 1, n_states), discrete_range)
        error = np.mean(np.abs(continuous_range - quantized))
        precision_errors.append(error)
    
    plt.semilogy(bit_widths, precision_errors, 's-', linewidth=2, markersize=8)
    plt.xlabel('State Bit Width')
    plt.ylabel('Quantization Error')
    plt.title('Precision vs Bit Width')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hardware_memristor_model.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\nHardware Implementation Summary:")
    print(f"- Recommended bit width: 8 bits (256 states)")
    print(f"- Memory for 1000 synapses: 8000 bits (1 KB)")
    print(f"- Update logic: Simple increment/decrement")
    print(f"- FPGA resources: ~100 LUTs per memristor")
    
    return discrete_mems

def main():
    """Main tutorial function"""
    print("Memristor-Based Synapses Tutorial")
    print("==================================")
    
    # Part 1: Memristor characteristics
    mem = memristor_characteristics()
    
    # Part 2: SNN with memristor synapses
    memristors, synapses = memristor_snn_synapses()
    
    # Part 3: Hardware-friendly model
    discrete_mems = hardware_memristor_model()
    
    print("\n=== Tutorial Complete! ===")
    print("\nKey Concepts Demonstrated:")
    print("1. Memristor I-V hysteresis and state dynamics")
    print("2. SNN with adaptive memristor-based synapses")
    print("3. Hardware-friendly discrete state model")
    print("4. FPGA implementation considerations")
    print("\nNext: Run 04_fpga_preparation.py for hardware conversion!")

if __name__ == "__main__":
    main()