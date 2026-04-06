# System Setup and Architecture Overview

## Goal
- Build a light-seeking robot using a 2×2 LDR sensor grid driving two DC motors via a 4×2 memristor crossbar and two fixed-point LIF neurons on the DE10-Lite FPGA.
- Operates in virtual memristor mode now; structured to support real memristors with DAC/ADC/pulse driver (SPI) later.

## End-to-End Flow
- Sensors: Four analog LDR voltages are read by an Arduino and streamed to the FPGA over UART.
- Encoder: `input_encoder` converts 4×12-bit sensor values to Poisson-like spikes per channel.
- Crossbar: `crossbar_interface` holds 4×2 conductances (`g_mem`) initialized from `weights_rom.hex`, multiplies each active pre-spike by `v_spike`, and sums to left/right currents.
- Neurons: Two `lif_neuron` modules integrate currents using discrete-time LIF, spike on threshold, and reset (c:\Users\jaiaa\OneDrive\Desktop\stuff\study\snn\brian\rtl\snn_top.v:95–117).
- Training: `training_controller` strengthens active synapses for selected outputs when `TRAIN` and `LEFT`/`RIGHT` are pressed; updates saturate at `g_max` (c:\Users\jaiaa\OneDrive\Desktop\stuff\study\snn\brian\rtl\snn_top.v:122–136 and c:\Users\jaiaa\OneDrive\Desktop\stuff\study\snn\brian\rtl\crossbar_interface.v:91–116).
- Motors: `motor_output` converts output spike rates into PWM duty for the L298N enable pins (c:\Users\jaiaa\OneDrive\Desktop\stuff\study\snn\brian\rtl\snn_top.v:138–147).

## Modules
- `rtl/snn_top_uart_2x2.v`: Top that ingests Arduino UART frames, parses to a 4×12-bit bus, encodes spikes, projects through crossbar, integrates in LIF, trains, and drives PWM.
- `rtl/snn_top_de10lite_2x2.v`: Wrapper that maps `KEY0/KEY1` to left/right buttons (active-low) and `SW0` to training enable.
- `rtl/uart_rx.v`: UART receiver (115200 bps @ 50 MHz) for sensor frames.
- `rtl/sensor_frame_rx.v`: Parses frames `0xAA 0x55 + 9×16-bit words` and packs lower 12 bits per channel into `sensor_bus`.
- `rtl/input_encoder.v`: Per-channel LFSR-based stochastic spiking from sensor magnitudes.
- `rtl/crossbar_interface.v`: 9×2 conductances, virtual-mode MAC and summation, saturating updates, `$readmemh` ROM init (c:\Users\jaiaa\OneDrive\Desktop\stuff\study\snn\brian\rtl\crossbar_interface.v:46–48).
- `rtl/lif_neuron.v`: Fixed-point LIF: `V[n+1] = V[n] + (I_syn − V[n]) >> tau_shift`, programmable threshold/reset.
- `rtl/training_controller.v`: Event-based supervised update masked by active pre-spikes.
- `rtl/motor_output.v`: Spike-rate accumulation to PWM duty.
- `rtl/spi_master.v`: Mode-0 SPI master for future DAC/ADC/pulse driver integration.

## Weight Assignment Logic
- Generator: `scripts/weights_init.py --size 2` produces `weights_rom.hex` for the crossbar.
- Mapping: Deterministic `W(i,j) = θ_line + exp(((x+1)*(y+1))/denominator) + ε_j` with origin override `W(0,0)=0`.
  - Line classification: main diagonal (`x==y`), anti-diagonal (`x+y==2`), otherwise horizontal lines (`y=k`).
  - Denominator: precomputed vector length per line, providing normalization and spatial decay.
  - θ: unique per direction in `[0, π/2]` to avoid collisions.
  - ε: tiny per-output offset to maintain uniqueness after quantization.
- Normalization: Values are scaled to 16-bit conductances `[0,65535]` with duplicate resolution.

## Hardware Hook-Up
- Sensors: 4 LDR voltage dividers to Arduino `A0..A3`.
- Arduino→FPGA: UART 115200 bps from Mega TX via 5V→3.3V level shifter to FPGA `uart_rx`; common ground.
- Buttons→FPGA: `TRAIN`, `LEFT`, `RIGHT` to FPGA GPIO with 3.3V pull-ups; press pulls to GND.
- FPGA→Motor Driver: `pwm_left`→`ENA`, `pwm_right`→`ENB`; direction pins `IN1..IN4` fixed or driven by FPGA.
- Power: Separate motor battery to L298N; FPGA and Arduino powered as recommended; share ground only.

## Modes
- Virtual Memristor: Active now; currents computed by integer MAC from `g_mem` and `v_spike`.
- Real Memristor: SPI pins exposed; add DAC/ADC programming and read-verify FSM in `crossbar_interface` to control physical devices.

## Training Behavior
- Hold `TRAIN`:
  - Press `LEFT` to strengthen active synapses to the left output.
  - Press `RIGHT` to strengthen to the right output.
  - Press both for straight-ahead stimuli (increase both).
- Updates saturate at `g_max` to prevent runaway.

## Debug
- Membrane potentials exposed: `v_left_dbg`, `v_right_dbg` (c:\Users\jaiaa\OneDrive\Desktop\stuff\study\snn\brian\rtl\snn_top.v:119–120).
- Optional: add SignalTap to observe spikes, update masks, and conductances.

## Goal Recap
- A resource-efficient, real-time spiking controller that seeks light by mapping sensed brightness to motor PWM through a spatially structured, learnable synaptic crossbar.

- FPGA-Only Variant
- `rtl/snn_top_adc_2x2.v`: Reads four 12-bit ADC channels (`adc_ch0..adc_ch3`), encodes spikes, projects through the 4×2 crossbar, integrates LIF, supports training, and drives PWM. Use MAX 10 Modular ADC IP to provide channel data.
