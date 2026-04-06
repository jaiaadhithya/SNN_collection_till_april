#!/usr/bin/env python3
"""
Tutorial 2: Multi-Input Decision-Making with LIF Neurons

This tutorial implements a decision-making SNN that:
1. Takes multiple inputs (representing different choices/stimuli)
2. Uses competitive dynamics to make decisions
3. Demonstrates winner-take-all behavior
4. Shows how input strength affects decision outcomes

Architecture:
- Input layer: Multiple input neurons providing different stimuli
- Decision layer: LIF neurons that compete for dominance
- Winner-take-all mechanism through lateral inhibition
"""

import numpy as np
import matplotlib.pyplot as plt
from brian2 import *

# Set up Brian2 preferences
prefs.codegen.target = 'numpy'

def simple_decision_neuron():
    """
    Simple decision neuron with 3 inputs - fires based on dominant input
    """
    print("=== Simple Decision-Making Neuron ===")
    
    start_scope()
    
    # Neuron parameters
    tau_m = 10*ms
    V_rest = -70*mV
    V_threshold = -50*mV
    V_reset = -70*mV
    R = 50*Mohm  # Lower resistance for faster integration
    
    # Decision neuron with 3 inputs
    eqs = '''
    dv/dt = (V_rest - v + R * (I1 + I2 + I3)) / tau_m : volt
    I1 : amp  # Input 1 (e.g., "go left")
    I2 : amp  # Input 2 (e.g., "go right")
    I3 : amp  # Input 3 (e.g., "stay")
    '''
    
    decision_neuron = NeuronGroup(1, eqs, threshold='v > V_threshold', 
                                 reset='v = V_reset', method='euler')
    
    # Set initial conditions
    decision_neuron.v = V_rest
    
    # Create time-varying inputs to simulate different scenarios
    @network_operation(dt=1*ms)
    def update_inputs():
        t_now = defaultclock.t
        
        # Scenario 1 (0-50ms): Input 1 dominates
        if t_now < 50*ms:
            decision_neuron.I1 = 0.8*nA  # Strong input 1
            decision_neuron.I2 = 0.2*nA  # Weak input 2
            decision_neuron.I3 = 0.1*nA  # Weak input 3
        
        # Scenario 2 (50-100ms): Input 2 dominates
        elif t_now < 100*ms:
            decision_neuron.I1 = 0.1*nA  # Weak input 1
            decision_neuron.I2 = 0.9*nA  # Strong input 2
            decision_neuron.I3 = 0.2*nA  # Weak input 3
        
        # Scenario 3 (100-150ms): Balanced inputs (competition)
        elif t_now < 150*ms:
            decision_neuron.I1 = 0.4*nA  # Moderate input 1
            decision_neuron.I2 = 0.45*nA # Slightly stronger input 2
            decision_neuron.I3 = 0.3*nA  # Moderate input 3
        
        # Scenario 4 (150-200ms): Input 3 dominates
        else:
            decision_neuron.I1 = 0.1*nA  # Weak input 1
            decision_neuron.I2 = 0.2*nA  # Weak input 2
            decision_neuron.I3 = 0.7*nA  # Strong input 3
    
    # Monitors
    voltage_monitor = StateMonitor(decision_neuron, ['v', 'I1', 'I2', 'I3'], record=True)
    spike_monitor = SpikeMonitor(decision_neuron)
    
    # Run simulation
    run(200*ms)
    
    # Plot results
    plt.figure(figsize=(14, 10))
    
    # Input currents
    plt.subplot(4, 1, 1)
    plt.plot(voltage_monitor.t/ms, voltage_monitor.I1[0]/nA, 'r-', linewidth=2, label='Input 1 (Left)')
    plt.plot(voltage_monitor.t/ms, voltage_monitor.I2[0]/nA, 'g-', linewidth=2, label='Input 2 (Right)')
    plt.plot(voltage_monitor.t/ms, voltage_monitor.I3[0]/nA, 'b-', linewidth=2, label='Input 3 (Stay)')
    plt.ylabel('Input Current (nA)')
    plt.title('Decision-Making Inputs Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Total input
    total_input = voltage_monitor.I1[0] + voltage_monitor.I2[0] + voltage_monitor.I3[0]
    plt.subplot(4, 1, 2)
    plt.plot(voltage_monitor.t/ms, total_input/nA, 'k-', linewidth=2)
    plt.ylabel('Total Input (nA)')
    plt.title('Total Input Current')
    plt.grid(True, alpha=0.3)
    
    # Membrane potential
    plt.subplot(4, 1, 3)
    plt.plot(voltage_monitor.t/ms, voltage_monitor.v[0]/mV, 'purple', linewidth=2)
    plt.axhline(y=V_threshold/mV, color='r', linestyle='--', label='Threshold')
    plt.axhline(y=V_rest/mV, color='gray', linestyle='--', label='Resting potential')
    plt.ylabel('Membrane Potential (mV)')
    plt.title('Decision Neuron Response')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Spikes
    plt.subplot(4, 1, 4)
    if len(spike_monitor.t) > 0:
        plt.plot(spike_monitor.t/ms, np.ones(len(spike_monitor.t)), 'ro', markersize=8)
    plt.ylabel('Spikes')
    plt.xlabel('Time (ms)')
    plt.title('Decision Spikes')
    plt.ylim(0.5, 1.5)
    plt.grid(True, alpha=0.3)
    
    # Add scenario labels
    plt.axvspan(0, 50, alpha=0.2, color='red', label='Input 1 dominates')
    plt.axvspan(50, 100, alpha=0.2, color='green', label='Input 2 dominates')
    plt.axvspan(100, 150, alpha=0.2, color='blue', label='Competition')
    plt.axvspan(150, 200, alpha=0.2, color='orange', label='Input 3 dominates')
    
    plt.tight_layout()
    plt.savefig('decision_making_simple.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"Total spikes: {len(spike_monitor.t)}")
    if len(spike_monitor.t) > 0:
        print(f"Spike times: {spike_monitor.t/ms} ms")
        print(f"Average firing rate: {len(spike_monitor.t)/(200*ms)} Hz")

def competitive_decision_network():
    """
    More sophisticated decision network with multiple competing neurons
    Each neuron represents a different decision option
    """
    print("\n=== Competitive Decision Network ===")
    
    start_scope()
    
    # Network parameters
    n_options = 3  # Number of decision options
    tau_m = 10*ms
    V_rest = -70*mV
    V_threshold = -50*mV
    V_reset = -70*mV
    R = 80*Mohm
    
    # Decision neurons (one per option)
    eqs_decision = '''
    dv/dt = (V_rest - v + R * (I_ext - I_inhib)) / tau_m : volt
    I_ext : amp      # External input (evidence for this option)
    I_inhib : amp    # Inhibitory input from other neurons
    '''
    
    decision_neurons = NeuronGroup(n_options, eqs_decision, 
                                  threshold='v > V_threshold', 
                                  reset='v = V_reset', method='euler')
    
    # Initialize
    decision_neurons.v = V_rest
    decision_neurons.I_inhib = 0*nA
    
    # Lateral inhibition synapses (winner-take-all)
    inhibition_strength = 0.3*nA
    
    @network_operation(dt=1*ms)
    def lateral_inhibition():
        # Each neuron inhibits all others based on its recent activity
        # Simple approximation: inhibition proportional to how close to threshold
        for i in range(n_options):
            inhibition = 0*nA
            for j in range(n_options):
                if i != j:
                    # Inhibition based on other neuron's membrane potential
                    activation = max(0, (decision_neurons.v[j] - V_rest) / (V_threshold - V_rest))
                    inhibition += inhibition_strength * activation
            decision_neurons.I_inhib[i] = inhibition
    
    # Time-varying external inputs (evidence for each option)
    @network_operation(dt=1*ms)
    def update_evidence():
        t_now = defaultclock.t
        
        # Scenario 1 (0-100ms): Option 0 gets strong evidence
        if t_now < 100*ms:
            decision_neurons.I_ext[0] = 0.7*nA + 0.1*nA*np.random.randn()  # Strong + noise
            decision_neurons.I_ext[1] = 0.3*nA + 0.1*nA*np.random.randn()  # Weak + noise
            decision_neurons.I_ext[2] = 0.2*nA + 0.1*nA*np.random.randn()  # Weak + noise
        
        # Scenario 2 (100-200ms): Option 1 gets strong evidence
        elif t_now < 200*ms:
            decision_neurons.I_ext[0] = 0.2*nA + 0.1*nA*np.random.randn()
            decision_neurons.I_ext[1] = 0.8*nA + 0.1*nA*np.random.randn()  # Strong + noise
            decision_neurons.I_ext[2] = 0.3*nA + 0.1*nA*np.random.randn()
        
        # Scenario 3 (200-300ms): Close competition between options 0 and 2
        else:
            decision_neurons.I_ext[0] = 0.5*nA + 0.15*nA*np.random.randn()  # Moderate + more noise
            decision_neurons.I_ext[1] = 0.2*nA + 0.1*nA*np.random.randn()
            decision_neurons.I_ext[2] = 0.52*nA + 0.15*nA*np.random.randn() # Slightly stronger + noise
    
    # Monitors
    voltage_monitor = StateMonitor(decision_neurons, ['v', 'I_ext', 'I_inhib'], record=True)
    spike_monitor = SpikeMonitor(decision_neurons)
    
    # Run simulation
    run(300*ms)
    
    # Plot results
    plt.figure(figsize=(16, 12))
    
    # External inputs (evidence)
    plt.subplot(5, 1, 1)
    colors = ['red', 'green', 'blue']
    labels = ['Option 0', 'Option 1', 'Option 2']
    for i in range(n_options):
        plt.plot(voltage_monitor.t/ms, voltage_monitor.I_ext[i]/nA, 
                color=colors[i], linewidth=2, label=labels[i])
    plt.ylabel('External Input (nA)')
    plt.title('Evidence for Each Decision Option')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Inhibitory inputs
    plt.subplot(5, 1, 2)
    for i in range(n_options):
        plt.plot(voltage_monitor.t/ms, voltage_monitor.I_inhib[i]/nA, 
                color=colors[i], linewidth=2, label=f'Inhibition to {labels[i]}')
    plt.ylabel('Inhibitory Input (nA)')
    plt.title('Lateral Inhibition Between Options')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Membrane potentials
    plt.subplot(5, 1, 3)
    for i in range(n_options):
        plt.plot(voltage_monitor.t/ms, voltage_monitor.v[i]/mV, 
                color=colors[i], linewidth=2, label=labels[i])
    plt.axhline(y=V_threshold/mV, color='black', linestyle='--', label='Threshold')
    plt.ylabel('Membrane Potential (mV)')
    plt.title('Decision Neuron Membrane Potentials')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Spike raster
    plt.subplot(5, 1, 4)
    if len(spike_monitor.t) > 0:
        plt.scatter(spike_monitor.t/ms, spike_monitor.i, 
                   c=[colors[i] for i in spike_monitor.i], s=50, alpha=0.7)
    plt.ylabel('Neuron Index')
    plt.title('Spike Raster Plot')
    plt.ylim(-0.5, n_options-0.5)
    plt.grid(True, alpha=0.3)
    
    # Firing rates over time (sliding window)
    plt.subplot(5, 1, 5)
    window_size = 20*ms
    time_bins = np.arange(0, 300, 5) * ms
    
    for i in range(n_options):
        rates = []
        for t_bin in time_bins:
            spikes_in_window = spike_monitor.t[(spike_monitor.t >= t_bin) & 
                                             (spike_monitor.t < t_bin + window_size) & 
                                             (spike_monitor.i == i)]
            rate = len(spikes_in_window) / window_size
            rates.append(rate)
        plt.plot(time_bins/ms, rates, color=colors[i], linewidth=2, label=labels[i])
    
    plt.ylabel('Firing Rate (Hz)')
    plt.xlabel('Time (ms)')
    plt.title('Instantaneous Firing Rates (20ms sliding window)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('competitive_decision_network.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # Analysis
    print("\nDecision Analysis:")
    for i in range(n_options):
        option_spikes = spike_monitor.t[spike_monitor.i == i]
        print(f"{labels[i]}: {len(option_spikes)} spikes, avg rate: {len(option_spikes)/(300*ms):.2f} Hz")
    
    # Determine winner in each time period
    periods = [(0, 100), (100, 200), (200, 300)]
    period_names = ['Period 1 (0-100ms)', 'Period 2 (100-200ms)', 'Period 3 (200-300ms)']
    
    for period, name in zip(periods, period_names):
        period_spikes = []
        for i in range(n_options):
            spikes_in_period = spike_monitor.t[(spike_monitor.t >= period[0]*ms) & 
                                             (spike_monitor.t < period[1]*ms) & 
                                             (spike_monitor.i == i)]
            period_spikes.append(len(spikes_in_period))
        
        winner = np.argmax(period_spikes)
        print(f"{name}: Winner is {labels[winner]} with {period_spikes[winner]} spikes")

if __name__ == "__main__":
    print("Multi-Input Decision-Making Tutorial")
    print("====================================")
    
    # Run simple decision neuron
    simple_decision_neuron()
    
    # Run competitive network
    competitive_decision_network()
    
    print("\nTutorial completed!")
    print("Key concepts demonstrated:")
    print("1. Input integration in LIF neurons")
    print("2. Decision-making based on input dominance")
    print("3. Competitive dynamics with lateral inhibition")
    print("4. Winner-take-all behavior")
    print("\nNext: Run 03_memristor_synapses.py for memristor modeling")