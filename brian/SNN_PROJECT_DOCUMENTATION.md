# Spiking Neural Network (SNN) Project Documentation

## Project Overview

This project implements a complete Spiking Neural Network (SNN) system for decision-making applications, progressing from basic neuron models to FPGA-ready hardware implementations. The system demonstrates biologically-inspired neural computation using the Brian2 simulator and provides hardware conversion tools for FPGA deployment.

## Project Structure

### Core Implementation Files

#### 1. Basic LIF Neuron Implementation (`01_lif_basics.py`)

**Purpose**: Demonstrates fundamental Leaky Integrate-and-Fire (LIF) neuron behavior

**Key Components**:
- **LIF Differential Equation**: `tau_m * dV/dt = -(V - V_rest) + R * I(t)`
- **Biological Parameters**: 
  - Membrane time constant (tau_m): 10ms
  - Resting potential (V_rest): -70mV
  - Spike threshold (V_threshold): -50mV
  - Membrane resistance (R): 100MΩ
- **Input Scenarios**: Constant, step, and varying current inputs
- **Monitoring**: Membrane potential, input current, and spike times

**Generated Outputs**:
- Voltage traces showing membrane potential dynamics
- Spike raster plots
- Input-output relationship analysis

#### 2. Multi-Input Decision Network (`02_multi_input_decision.py`)

**Purpose**: Implements decision-making through competitive neural dynamics

**Architecture**:
- **Simple Decision Neuron**: Single neuron integrating multiple weighted inputs
- **Competitive Network**: Multiple neurons with lateral inhibition
- **Winner-Take-All Mechanism**: Strongest input suppresses competitors

**Key Features**:
- Time-varying input scenarios
- Lateral inhibition implementation
- Decision period analysis
- Firing rate computation

**Decision Logic**:
- Neurons receive external inputs with different strengths
- Lateral inhibition creates competition between options
- Winning neuron corresponds to selected decision

#### 3. Memristor Synapse Integration (`03_memristor_synapses.py`)

**Purpose**: Incorporates adaptive synapses using memristor models

**Memristor Model**:
- **Resistance States**: 16 discrete levels (4-bit quantization)
- **State Transitions**: Voltage-dependent switching
- **STDP Learning**: Spike-timing dependent plasticity
- **Conductance Range**: 1μS to 100μS

**Network Integration**:
- Memristor synapses between input and output neurons
- Adaptive weight updates based on spike timing
- Learning-induced network behavior changes

#### 4. FPGA Preparation (`04_fpga_preparation.py`)

**Purpose**: Converts floating-point models to fixed-point hardware implementations

**Fixed-Point Analysis**:
- **Voltage Representation**: 16-bit signed fixed-point
- **Current Representation**: 12-bit signed fixed-point
- **Scaling Factors**: Optimized for hardware precision
- **Overflow Protection**: Saturation arithmetic

**Hardware Generation**:
- VHDL template generation
- Resource estimation
- Timing analysis
- Hardware/software comparison

### Generated VHDL Files

#### 1. LIF Neuron (`lif_neuron.vhd`)

**Implementation Details**:
- **Architecture**: Behavioral VHDL with fixed-point arithmetic
- **Clock Domain**: Synchronous design with reset
- **Precision**: 16-bit voltage, 12-bit current
- **Features**: Leaky integration, spike generation, reset mechanism

**Port Interface**:
```vhdl
entity lif_neuron is
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        enable      : in  std_logic;
        input_current : in  signed(11 downto 0);
        spike_out   : out std_logic;
        voltage_out : out signed(15 downto 0)
    );
end lif_neuron;
```

#### 2. Memristor Synapse (`memristor_synapse.vhd`)

**Implementation Details**:
- **State Machine**: 4-bit memristor state (16 levels)
- **Lookup Table**: Resistance-to-conductance mapping
- **STDP Windows**: Pre/post-synaptic timing detection
- **Learning Logic**: State update based on spike correlation

**Key Features**:
- Bidirectional state transitions
- Configurable learning rates
- Synaptic current computation
- State persistence

#### 3. SNN Decision Network (`snn_decision_network.vhd`)

**System Integration**:
- **Multiple LIF Neurons**: Instantiated decision units
- **Interconnect Matrix**: Configurable connectivity
- **Input Interface**: External stimulus handling
- **Output Arbitration**: Winner selection logic

## Mathematical Foundations

### LIF Neuron Model

The core neuron model implements the standard LIF equation:

```
τ_m * dV/dt = -(V - V_rest) + R * I(t)
```

Where:
- V: Membrane potential
- τ_m: Membrane time constant
- V_rest: Resting potential
- R: Membrane resistance
- I(t): Input current

**Spike Condition**: V > V_threshold
**Reset Condition**: V = V_reset after spike

### Memristor Dynamics

Memristor resistance follows:

```
R(x) = R_off * x + R_on * (1 - x)
```

Where:
- x: Normalized state variable (0 to 1)
- R_off: High resistance state
- R_on: Low resistance state

**State Update**:
```
dx/dt = f(V) * window_function(x)
```

### Fixed-Point Conversion

**Voltage Scaling**:
- Range: -100mV to +50mV
- Resolution: 16-bit signed
- Scale Factor: 2^10 = 1024

**Current Scaling**:
- Range: -2nA to +2nA
- Resolution: 12-bit signed
- Scale Factor: 2^10 = 1024

## Verification and Testing

### Spike Authenticity Verification

The project includes comprehensive verification scripts that prove the authenticity of spike generation:

1. **Mathematical Verification**: Comparison with analytical solutions
2. **Statistical Analysis**: Poisson process validation
3. **Hardware Comparison**: Fixed-point vs floating-point accuracy

### Performance Metrics

- **Simulation Speed**: Real-time capable for networks up to 1000 neurons
- **Hardware Resources**: Estimated FPGA utilization provided
- **Timing Analysis**: Critical path delays calculated
- **Power Estimation**: Dynamic and static power consumption

## FPGA Deployment Guide

### Prerequisites

**Hardware Requirements**:
- FPGA Development Board (Xilinx Zynq-7000 or Intel Cyclone V recommended)
- Minimum 50K logic elements
- 2MB block RAM
- High-speed I/O pins for external interfaces

**Software Requirements**:
- Xilinx Vivado or Intel Quartus Prime
- ModelSim or equivalent for simulation
- Python 3.8+ with Brian2 for model generation

### Step 1: Model Preparation

1. **Run Fixed-Point Analysis**:
   ```bash
   python 04_fpga_preparation.py
   ```
   This generates optimized fixed-point parameters and VHDL templates.

2. **Verify Hardware Models**:
   Compare hardware vs software neuron outputs to ensure accuracy.

### Step 2: VHDL Integration

1. **Import Generated Files**:
   - Add `lif_neuron.vhd` to your FPGA project
   - Add `memristor_synapse.vhd` for adaptive synapses
   - Add `snn_decision_network.vhd` as top-level entity

2. **Configure Network Parameters**:
   ```vhdl
   -- Network configuration
   constant NUM_NEURONS : integer := 8;
   constant NUM_INPUTS : integer := 16;
   constant SYNAPSE_MATRIX : synapse_array_t := (
       -- Define connectivity matrix
   );
   ```

### Step 3: Clock and Reset Design

1. **Clock Domain**:
   - Use 100MHz system clock for neural updates
   - Implement clock enable for 1kHz neural simulation rate
   - Add reset synchronization

2. **Timing Constraints**:
   ```tcl
   create_clock -period 10.0 [get_ports clk]
   set_input_delay 2.0 [get_ports input_data]
   set_output_delay 2.0 [get_ports spike_output]
   ```

### Step 4: Memory Architecture

1. **Neuron State Storage**:
   - Use block RAM for voltage states
   - Implement dual-port access for parallel updates
   - Size: NUM_NEURONS × 16 bits

2. **Synapse Weight Storage**:
   - Store memristor states in distributed RAM
   - Implement read-modify-write for learning
   - Size: NUM_SYNAPSES × 4 bits

### Step 5: Input/Output Interface

1. **Input Interface**:
   ```vhdl
   -- Spike input interface
   type spike_input_t is record
       valid : std_logic;
       neuron_id : unsigned(7 downto 0);
       timestamp : unsigned(31 downto 0);
   end record;
   ```

2. **Output Interface**:
   ```vhdl
   -- Decision output interface
   type decision_output_t is record
       decision_valid : std_logic;
       winning_neuron : unsigned(7 downto 0);
       confidence : unsigned(15 downto 0);
   end record;
   ```

### Step 6: Simulation and Verification

1. **Testbench Creation**:
   - Create comprehensive testbenches for each module
   - Implement stimulus generation for various input patterns
   - Compare outputs with Python reference models

2. **Timing Simulation**:
   - Run post-synthesis timing simulation
   - Verify setup/hold times
   - Check for timing violations

### Step 7: Synthesis and Implementation

1. **Synthesis Settings**:
   ```tcl
   set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY none [get_runs synth_1]
   set_property STEPS.SYNTH_DESIGN.ARGS.KEEP_EQUIVALENT_REGISTERS true [get_runs synth_1]
   ```

2. **Implementation Strategy**:
   - Use "Performance_ExplorePostRoutePhysOpt" for timing closure
   - Enable aggressive optimization for area if needed
   - Monitor resource utilization

### Step 8: Hardware Testing

1. **Functional Testing**:
   - Load bitstream to FPGA
   - Send test patterns via UART/SPI interface
   - Verify decision outputs match expected behavior

2. **Performance Validation**:
   - Measure actual power consumption
   - Verify timing margins
   - Test under various operating conditions

## Resource Utilization Estimates

### Single LIF Neuron
- **Logic Elements**: ~200 LEs
- **Memory**: 32 bits (voltage + current state)
- **DSP Blocks**: 2 (for multiplication)
- **Maximum Frequency**: ~150MHz

### 8-Neuron Decision Network
- **Logic Elements**: ~2000 LEs
- **Block RAM**: 2 M9K blocks
- **DSP Blocks**: 16
- **I/O Pins**: 32 (16 input + 16 output)

### Scaling Considerations

**Linear Scaling Factors**:
- Neurons: O(N) logic and memory
- Synapses: O(N²) for full connectivity
- Update Rate: Inversely proportional to network size

**Optimization Strategies**:
- Sparse connectivity to reduce synapse count
- Time-multiplexed neuron updates
- Hierarchical network partitioning

## Performance Optimization

### Computational Efficiency

1. **Pipeline Architecture**:
   - Separate pipeline stages for different operations
   - Overlap membrane potential updates with spike detection
   - Parallel synapse weight updates

2. **Memory Optimization**:
   - Use shift registers for delay lines
   - Implement circular buffers for spike history
   - Optimize memory access patterns

### Power Optimization

1. **Clock Gating**:
   - Disable clocks to inactive neurons
   - Use enable signals for conditional updates
   - Implement sleep modes for idle periods

2. **Voltage Scaling**:
   - Use multiple voltage domains
   - Scale voltage based on performance requirements
   - Implement dynamic voltage and frequency scaling

## Applications and Extensions

### Potential Applications

1. **Real-Time Decision Making**:
   - Autonomous vehicle control
   - Robotic path planning
   - Financial trading algorithms

2. **Pattern Recognition**:
   - Image classification
   - Speech recognition
   - Sensor data analysis

3. **Adaptive Control Systems**:
   - Motor control with learning
   - Adaptive filtering
   - System identification

### Extension Possibilities

1. **Network Architectures**:
   - Convolutional SNN layers
   - Recurrent connections
   - Hierarchical processing

2. **Learning Algorithms**:
   - Reinforcement learning integration
   - Unsupervised feature extraction
   - Online adaptation mechanisms

3. **Hardware Enhancements**:
   - Custom ASIC implementation
   - Neuromorphic chip integration
   - Optical interconnects

## Troubleshooting Guide

### Common Issues

1. **Timing Violations**:
   - Reduce clock frequency
   - Add pipeline stages
   - Optimize critical paths

2. **Resource Overflow**:
   - Reduce network size
   - Use time-multiplexing
   - Optimize data widths

3. **Functional Mismatches**:
   - Verify fixed-point scaling
   - Check initialization values
   - Validate state machine logic

### Debug Strategies

1. **Simulation Debug**:
   - Use waveform viewers
   - Add debug signals
   - Compare with reference models

2. **Hardware Debug**:
   - Use integrated logic analyzers
   - Add LED indicators
   - Implement UART debug output

## Conclusion

This SNN implementation provides a complete pathway from high-level neural modeling to hardware deployment. The modular design allows for easy customization and scaling, while the comprehensive verification ensures reliable operation. The FPGA implementation enables real-time neural computation for practical applications requiring low-latency decision making.

The project demonstrates the feasibility of implementing biologically-inspired neural networks in hardware, opening possibilities for neuromorphic computing applications in embedded systems, robotics, and edge AI devices.