#!/usr/bin/env python3
"""
Tutorial 1: Basic Leaky Integrate-and-Fire (LIF) Neuron with Brian2

This tutorial covers:
1. Understanding the LIF neuron model
2. Creating a simple LIF neuron
3. Visualizing membrane potential dynamics
4. Understanding spike generation

The LIF model equation:
τ_m * dV/dt = -(V - V_rest) + R * I(t)

Where:
- V(t): membrane potential
- V_rest: resting potential
- R: membrane resistance
- I(t): input current
- τ_m: membrane time constant

When V(t) > V_threshold, neuron fires and resets to V_rest
"""

import numpy as np
import matplotlib.pyplot as plt
from brian2 import *

# Set up Brian2 preferences
prefs.codegen.target = 'numpy'  # Use numpy backend for compatibility

def basic_lif_neuron():
    """
    Create and simulate a basic LIF neuron with constant input current
    """
    print("=== Basic LIF Neuron Simulation ===")
    
    # Clear any previous Brian2 objects
    start_scope()
    
    # Neuron parameters
    tau_m = 10*ms      # Membrane time constant
    V_rest = -70*mV    # Resting potential
    V_threshold = -50*mV  # Spike threshold
    V_reset = -70*mV   # Reset potential after spike
    R = 100*Mohm       # Membrane resistance
    
    # LIF neuron equations
    eqs = '''
    dv/dt = (V_rest - v + R * I) / tau_m : volt
    I : amp
    '''
    
    # Create neuron group
    neuron = NeuronGroup(1, eqs, threshold='v > V_threshold', 
                        reset='v = V_reset', method='euler')
    
    # Set initial conditions
    neuron.v = V_rest
    neuron.I = 0.5*nA  # Constant input current
    
    # Monitors to record data
    voltage_monitor = StateMonitor(neuron, 'v', record=True)
    spike_monitor = SpikeMonitor(neuron)
    
    # Run simulation
    run(100*ms)
    
    # Plot results
    plt.figure(figsize=(12, 6))
    
    plt.subplot(2, 1, 1)
    plt.plot(voltage_monitor.t/ms, voltage_monitor.v[0]/mV, 'b-', linewidth=2)
    plt.axhline(y=V_threshold/mV, color='r', linestyle='--', label='Threshold')
    plt.axhline(y=V_rest/mV, color='g', linestyle='--', label='Resting potential')
    plt.ylabel('Membrane Potential (mV)')
    plt.title('LIF Neuron: Membrane Potential vs Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.plot(spike_monitor.t/ms, np.ones(len(spike_monitor.t)), 'ro', markersize=8)
    plt.ylabel('Spikes')
    plt.xlabel('Time (ms)')
    plt.title('Spike Times')
    plt.ylim(0.5, 1.5)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lif_basic.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"Number of spikes: {len(spike_monitor.t)}")
    print(f"Spike times: {spike_monitor.t/ms} ms")
    print(f"Average firing rate: {len(spike_monitor.t)/(100*ms)} Hz")

def lif_with_varying_input():
    """
    LIF neuron with time-varying input current
    """
    print("\n=== LIF Neuron with Varying Input ===")
    
    start_scope()
    
    # Parameters
    tau_m = 10*ms
    V_rest = -70*mV
    V_threshold = -50*mV
    V_reset = -70*mV
    R = 100*Mohm
    
    # Equations with time-varying input
    eqs = '''
    dv/dt = (V_rest - v + R * I) / tau_m : volt
    I = I_base + I_amp * sin(2 * pi * f * t) : amp
    I_base : amp
    I_amp : amp
    f : Hz
    '''
    
    neuron = NeuronGroup(1, eqs, threshold='v > V_threshold', 
                        reset='v = V_reset', method='euler')
    
    # Set parameters
    neuron.v = V_rest
    neuron.I_base = 0.3*nA  # Base current
    neuron.I_amp = 0.2*nA   # Amplitude of oscillation
    neuron.f = 10*Hz        # Frequency of oscillation
    
    # Monitors
    voltage_monitor = StateMonitor(neuron, ['v', 'I'], record=True)
    spike_monitor = SpikeMonitor(neuron)
    
    run(200*ms)
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    plt.subplot(3, 1, 1)
    plt.plot(voltage_monitor.t/ms, voltage_monitor.I[0]/nA, 'g-', linewidth=2)
    plt.ylabel('Input Current (nA)')
    plt.title('Time-Varying Input Current')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 1, 2)
    plt.plot(voltage_monitor.t/ms, voltage_monitor.v[0]/mV, 'b-', linewidth=2)
    plt.axhline(y=V_threshold/mV, color='r', linestyle='--', label='Threshold')
    plt.axhline(y=V_rest/mV, color='g', linestyle='--', label='Resting potential')
    plt.ylabel('Membrane Potential (mV)')
    plt.title('Membrane Potential Response')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 1, 3)
    plt.plot(spike_monitor.t/ms, np.ones(len(spike_monitor.t)), 'ro', markersize=8)
    plt.ylabel('Spikes')
    plt.xlabel('Time (ms)')
    plt.title('Spike Times')
    plt.ylim(0.5, 1.5)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lif_varying_input.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"Number of spikes: {len(spike_monitor.t)}")
    print(f"Average firing rate: {len(spike_monitor.t)/(200*ms)} Hz")

if __name__ == "__main__":
    print("LIF Neuron Tutorial - Part 1: Basics")
    print("=====================================")
    
    # Run basic LIF simulation
    basic_lif_neuron()
    
    # Run LIF with varying input
    lif_with_varying_input()
    
    print("\nTutorial completed! Check the generated plots.")
    print("Next: Run 02_multi_input_decision.py for decision-making behavior")