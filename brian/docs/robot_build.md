# Light-Seeking Robot: Wiring, Software, and Deployment Guide

## Overview

- Purpose: Build a light-seeking robot using a 2×2 LDR grid feeding a 4×2 memristor crossbar and two LIF neurons on DE10-Lite. Motor PWM is driven by spike rates. Buttons provide supervised training.
- Modes: Virtual memristor (register-based) ready; Real memristor supported via SPI DAC/ADC hooks.
- Timing: 50 MHz synchronous, fixed-point only.

## Hardware Bill of Materials

- 4 LDR sensors (use 9 for 3×3 if desired)
- Fixed resistors (~10kΩ) for voltage dividers
- Arduino (Mega recommended; Uno/Nano/Due also possible)
- DE10-Lite FPGA
- L298N motor driver
- 2 DC motors, caster, chassis, battery (7–12V for motors)
- Buttons: TRAIN, LEFT, RIGHT
- Level shifter (5V→3.3V) for Arduino TX → FPGA RX
- Wires, breadboards, decoupling capacitors

## Wiring

- Power
  - L298N: motor battery to +Vmot and GND; motors to OUT1/OUT2 and OUT3/OUT4.
  - DE10-Lite: powered via DC/USB as specified.
  - Arduino: USB or barrel jack (7–12V).
  - Common GND: tie Arduino GND, FPGA GND, and L298N GND together.

- Sensors → Arduino
  - Build nine LDR voltage dividers (LDR in series with 10kΩ). Midpoint → Arduino `A0..A8`.
  - Arrange LDRs in 3×3 grid, note coordinates.

- Arduino → FPGA
  - UART 115200 bps from Arduino TX through a level shifter to FPGA `uart_rx` pin.
  - Connect GNDs.

- Buttons → FPGA
  - Three buttons to GPIO: `train_btn`, `left_btn`, `right_btn`.
  - Use pull-ups to 3.3V; buttons pull to GND.

- FPGA → L298N
  - `pwm_left` → `ENA`, `pwm_right` → `ENB`.
  - Direction pins (e.g., left IN1=1, IN2=0; right IN3=1, IN4=0) via FPGA GPIO or fixed logic.

## FPGA Design

- RTL Files
  - `rtl/lif_neuron.v`: Discrete-time LIF neuron.
  - `rtl/input_encoder.v`: 9×12-bit to stochastic spikes.
  - `rtl/crossbar_interface.v`: 9×2 conductance store, summation, training updates.
  - `rtl/training_controller.v`: Supervised updates.
  - `rtl/motor_output.v`: Spike rate to PWM.
  - `rtl/spi_master.v`: SPI master (Mode 0) for future DAC/ADC.
  - `rtl/uart_rx.v`: UART receiver (115200 bps).
  - `rtl/sensor_frame_rx.v`: Frame parser: header 0xAA 0x55 + 9×16-bit words → 9×12-bit bus.
- `rtl/snn_top.v`: Top without UART (expects packed `sensor_in`).
- `rtl/snn_top_uart.v`: Top integrating UART stream into the encoder (parameterized).
- `rtl/snn_top_uart_2x2.v`: Wrapper top configured for 2×2 (N_INPUTS=4).

- Weight ROM
  - Generate `weights_rom.hex` via `scripts/weights_init.py --size 2` (θ + exp logic). Loaded by `crossbar_interface` at startup.

- Pins
  - Assign `uart_rx` (level shifted), `train_btn`, `left_btn`, `right_btn`, `pwm_left`, `pwm_right`, and optional direction pins in Quartus Assignment Editor.
  - I/O standard: 3.3V LVTTL.

## DE10-Lite Controls

- Left button: `KEY0` (active-low), Right button: `KEY1` (active-low)
- Training enable: `SW0` (active-high)
- Top-level for this mapping: `rtl/snn_top_de10lite_2x2.v`

## Arduino–FPGA–Motor Integration

- Arduino Uno handles sensors and L298N motor driver.
- FPGA computes SNN decisions and sends motor duty commands over UART.
- Wiring:
  - Arduino TX (D1) → level shifter HV1 → level shifter LV1 → FPGA pin assigned to `uart_rx`
  - Arduino RX (D0) ← FPGA pin assigned to `uart_tx` (3.3V logic acceptable)
  - GND shared between Arduino and FPGA
  - L298N ENA ← Arduino PWM pin (e.g., D5), ENB ← Arduino PWM pin (e.g., D6)
  - L298N IN1..IN4 ← Arduino digital pins for direction
  - Motor battery to L298N Vmot; common GND

- Software:
  - FPGA top: `rtl/snn_top_de10lite_2x2.v` (includes UART RX, UART TX motor command frames)
  - Arduino sketch: `arduino/uno_sensor_motor/uno_sensor_motor.ino` (streams sensors and applies motor duty from FPGA commands)

## Arduino Sketch

- Read `A0..A3` for 2×2 (or `A0..A8` for 3×3) at ~200–500 Hz.
- Packet format per frame:
  - Header: `0xAA 0x55`
  - Payload: 9×16-bit big-endian words; lower 12 bits contain the ADC value scaled to 0–4095.
  - No checksum required (optional extension).
- Send over 115200 bps UART.

## Software Setup

- Install Intel Quartus Prime Lite and USB-Blaster driver.
- Optional: Install ModelSim/Questa for simulation.
- Install Python 3.
- Install Arduino IDE.

## Build Steps (2×2)

1. Mechanical assembly: mount motors, caster, L298N, DE10-Lite, Arduino, battery, and 3×3 LDR array.
2. Sensor wiring: four voltage dividers → Arduino `A0..A3`. Test in Arduino Serial Monitor.
3. Generate weights: `python scripts/weights_init.py --size 2` → produces `weights_rom.hex`.
4. Quartus project: create for DE10-Lite device; add all RTL and `weights_rom.hex`. Set top to `snn_top_uart_2x2`.
5. Pin assignment: assign UART RX, buttons, PWM pins, direction pins.
6. Compile and program DE10-Lite via USB-Blaster.
7. Upload Arduino sketch; connect Arduino TX through level shifter to FPGA `uart_rx` and tie grounds.
8. Bench test: power boards, observe PWM variation under different light and four sensors; verify training button behavior.
9. Connect motors to L298N: verify forward motion with PWM; ensure motor battery is isolated from logic power.
10. Field training: hold `TRAIN`, press `LEFT`/`RIGHT` based on light position; press both for straight ahead.

## Operation

- Encoder produces spikes proportional to brightness per sensor.
- Crossbar projects spikes through `g_mem` conductances (ROM-initialized) and sums to left/right currents.
- LIF neurons integrate currents, spike on threshold, reset.
- Motor PWM duty follows spike rate; robot steers toward light.
- Training increases conductance for active synapses toward selected outputs with saturation.

## Real Memristor Path (Future)

- Integrate SPI DAC/ADC and a programming/read-verify FSM in `crossbar_interface`.
- Map target conductance from ROM to physical device pulses and verify via ADC.

## Safety Notes

- Never feed 5V signals directly into FPGA. Use level shifting.
- Separate motor and logic supplies; share ground.
- Debounce buttons or tolerate brief pulses.
- Add decoupling capacitors to L298N supply.

## Troubleshooting

- No spikes: verify UART frames and `sensor_frame_rx` `frame_valid`.
- PWM not changing: check button wiring, verify `spike_left/right` in SignalTap, confirm weights ROM loaded.
- Motors not moving: check L298N enable pins and direction wiring; verify motor battery voltage.
## FPGA-Only Path (No Arduino)

- Use MAX 10 Modular ADC IP in Quartus to sample 4 analog channels.
- Wire four LDR voltage dividers to the DE10-Lite analog input header (consult the board manual for ADC channel pins). Keep signals within 0–3.3V.
- Instantiate the ADC IP and export four 12-bit channels to the top-level module `rtl/snn_top_adc_2x2.v` (`adc_ch0..adc_ch3`).
- Training controls remain on DE10-Lite (`KEY0/KEY1`, `SW0`).
- Motor driver outputs (`pwm_left`, `pwm_right`) connect from FPGA to L298N `ENA/ENB` directly.

### Steps
- In Platform Designer (Qsys), add the Modular ADC component, configure for 4 channels, 12-bit, appropriate sampling rate.
- Generate HDL and integrate into your Quartus project; connect ADC channel outputs to `adc_ch0..adc_ch3` of `snn_top_adc_2x2`.
- Map `KEY0/KEY1/SW0` and PWM pins; compile and program the FPGA.
