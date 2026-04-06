# Spiking Neural Network (SNN) Decision-Making with Memristors on FPGA

This project implements a complete pipeline from software simulation to hardware implementation of decision-making spiking neural networks using memristor-based synapses on FPGA platforms.

## 🎯 Project Overview

Your professor's vision: Create an SNN that makes decisions based on multiple inputs (not just classification), implemented with memristors on FPGA using leaky integrate-and-fire (LIF) neurons.

**Key Features:**
- Multi-input decision-making architecture
- Memristor-based synaptic weights with plasticity
- Hardware-friendly fixed-point implementation
- Complete FPGA design templates
- Real-time processing capabilities

## 📚 Learning Path

### Phase 1: Fundamentals (Start Here!)
1. **`01_lif_basics.py`** - Learn LIF neuron basics
2. **`02_multi_input_decision.py`** - Implement decision-making behavior
3. **`03_memristor_synapses.py`** - Add memristor modeling
4. **`04_fpga_preparation.py`** - Prepare for hardware implementation

### Phase 2: Hardware Implementation
5. **VHDL files** (auto-generated) - FPGA modules
6. **Synthesis and testing** - Real hardware validation

## 🚀 Quick Start

### Prerequisites
```bash
# Install required packages
pip install -r requirements.txt
```

### Run the Tutorials
```bash
# Start with basics
python 01_lif_basics.py

# Learn decision-making
python 02_multi_input_decision.py

# Explore memristor synapses
python 03_memristor_synapses.py

# Prepare for FPGA
python 04_fpga_preparation.py
```

## 📖 Detailed Tutorial Guide

### Tutorial 1: LIF Neuron Basics (`01_lif_basics.py`)
**What you'll learn:**
- Leaky integrate-and-fire neuron model
- Membrane potential dynamics
- Spike generation mechanisms
- Parameter effects on behavior

**Key equation:**
```
τ_m * dV/dt = -(V - V_rest) + R * I(t)
```

**Outputs:**
- `lif_basic.png` - Basic neuron response
- `lif_varying_input.png` - Response to time-varying input

### Tutorial 2: Multi-Input Decision Making (`02_multi_input_decision.py`)
**What you'll learn:**
- Decision-making with multiple inputs
- Winner-take-all mechanisms
- Competitive neural dynamics
- Lateral inhibition effects

**Architecture:**
```
Input 1 ──┐
Input 2 ──┼──> Decision Neuron ──> Output
Input 3 ──┘
```

**Advanced version:**
```
Input Layer    Decision Layer
[N1] ──────────> [D1]
[N2] ──────────> [D2]  (with lateral inhibition)
[N3] ──────────> [D3]
```

**Outputs:**
- `decision_making_simple.png` - Simple decision neuron
- `competitive_decision_network.png` - Full competitive network

### Tutorial 3: Memristor Synapses (`03_memristor_synapses.py`)
**What you'll learn:**
- Memristor device physics
- I-V hysteresis characteristics
- Synaptic weight storage
- Spike-timing dependent plasticity (STDP)

**Memristor model:**
```
R(t) = R_on * w + R_off * (1-w)
dw/dt = f(V, I)  # State-dependent
```

**Outputs:**
- `memristor_characteristics.png` - Device I-V curves
- `memristor_snn.png` - SNN with memristor synapses
- `hardware_memristor_model.png` - Discrete state model

### Tutorial 4: FPGA Preparation (`04_fpga_preparation.py`)
**What you'll learn:**
- Fixed-point arithmetic conversion
- Hardware-friendly neuron models
- VHDL code generation
- Resource and timing analysis

**Generated files:**
- `lif_neuron.vhd` - LIF neuron VHDL module
- `memristor_synapse.vhd` - Memristor synapse module
- `snn_decision_network.vhd` - Top-level SNN system

**Outputs:**
- `fixed_point_analysis.png` - Precision analysis
- `hardware_software_comparison.png` - Accuracy comparison
- `timing_analysis.png` - Performance analysis

## 🔬 Scientific Background

### Why This Approach?
1. **Biological Inspiration**: Real neurons make decisions through competitive dynamics
2. **Memristor Advantages**: Non-volatile, analog computation, low power
3. **FPGA Benefits**: Parallel processing, real-time operation, reconfigurable

### Key Innovations
1. **Multi-input decision architecture** - Beyond simple classification
2. **Memristor-based plasticity** - Hardware learning without external memory
3. **Fixed-point optimization** - Efficient FPGA implementation
4. **Real-time processing** - Suitable for robotics and control applications

## 🛠️ Hardware Implementation

### FPGA Requirements
- **Minimum**: Xilinx Zynq-7010 or Intel Cyclone V
- **Recommended**: Xilinx Zynq-7020 or higher
- **Resources needed**:
  - DSP blocks: 200-300 (for 100 neurons)
  - LUTs: 25,000-50,000
  - Flip-flops: 12,000-25,000
  - Block RAM: 1-5 MB

### Memristor Integration
- **Interface**: Analog front-end with ADC/DAC
- **Array size**: 32×32 to 128×128 crossbar
- **Control**: Voltage/current programming circuits
- **Readout**: Differential sensing amplifiers

### Performance Targets
- **Clock frequency**: 50-100 MHz
- **Throughput**: 10,000-100,000 spikes/second
- **Power consumption**: 1-10 Watts
- **Decision latency**: 1-10 milliseconds

## 📊 Expected Results

### Decision-Making Performance
- **Accuracy**: >90% for well-separated inputs
- **Response time**: 10-50ms (biological timescale)
- **Adaptability**: Learning through memristor plasticity
- **Robustness**: Noise tolerance through population coding

### Hardware Metrics
- **Area efficiency**: 1000+ neurons per cm²
- **Power efficiency**: <1mW per neuron
- **Speed**: Real-time operation at biological timescales
- **Scalability**: Up to 10,000 neurons on single FPGA

## 🔧 Troubleshooting

### Common Issues
1. **Brian2 installation fails**
   ```bash
   pip install --upgrade pip
   pip install brian2 --no-cache-dir
   ```

2. **Plots not showing**
   ```python
   import matplotlib
   matplotlib.use('TkAgg')  # or 'Qt5Agg'
   ```

3. **Fixed-point overflow**
   - Increase bit width in `FixedPointConverter`
   - Scale input ranges appropriately

4. **VHDL synthesis errors**
   - Check signal bit widths
   - Verify clock domain crossings
   - Use proper reset strategies

## 📈 Next Steps

### Immediate (Week 1-2)
1. Run all tutorials and understand outputs
2. Experiment with different parameters
3. Modify decision-making scenarios

### Short-term (Month 1)
1. Synthesize VHDL code with Vivado/Quartus
2. Simulate on FPGA development board
3. Validate timing and resource usage

### Medium-term (Month 2-3)
1. Interface with memristor test arrays
2. Implement learning algorithms
3. Test decision-making scenarios

### Long-term (Month 4-6)
1. Scale to larger networks (1000+ neurons)
2. Integrate with robotic systems
3. Publish results and optimize performance

## 📚 References

### Key Papers
1. Spiking Neural Networks: An Overview (Ghosh-Dastidar & Adeli, 2009)
2. Memristor-Based Neuromorphic Computing (Prezioso et al., 2015)
3. FPGA Implementation of SNNs (Neil & Liu, 2014)
4. Decision-Making in SNNs (Wang, 2008)

### Useful Resources
- [Brian2 Documentation](https://brian2.readthedocs.io/)
- [Neuromorphic Computing Primer](https://www.intel.com/content/www/us/en/research/neuromorphic-computing.html)
- [FPGA Design Best Practices](https://www.xilinx.com/support/documentation/sw_manuals/xilinx2020_2/ug949-vivado-design-methodology.pdf)

## 🤝 Contributing

This is a research project! Feel free to:
- Experiment with different architectures
- Optimize hardware implementations
- Add new learning rules
- Test on different FPGA platforms

## 📄 License

This project is for educational and research purposes. Please cite appropriately if used in publications.

---

**Happy Learning! 🧠⚡**

*"The best way to understand neural computation is to build it yourself."*