# FPGA-Based Spiking Neural Network (SNN) for Autonomous Car Control

## 1. Project Overview
This project implements a hardware-accelerated **Spiking Neural Network (SNN)** on an Intel DE10-Lite FPGA (MAX 10). The system is designed to control a self-driving car by processing sensor data in real-time and making navigation decisions (Forward, Backward, Left, Right).

Unlike traditional software-based AI, this SNN runs on "bare metal" hardware logic, offering:
*   **Low Latency**: Decisions are made in microseconds.
*   **On-Chip Learning**: The FPGA can be trained interactively without a PC.
*   **Efficiency**: No operating system overhead.

## 2. System Architecture

The system follows a pipeline architecture:
`Sensors (Arduino) -> UART Bridge -> FPGA RX -> SNN Core -> Motor Control`

### Hardware Components
1.  **Arduino Mega 2560**: Acts as the sensory cortex. It reads 4 analog distance sensors and 5 control buttons, packages the data, and transmits it via UART.
2.  **Logic Level Shifter**: Safely translates 5V signals (Arduino) to 3.3V (FPGA).
3.  **DE10-Lite FPGA**: The "Brain". Receives data, runs the neural network, and outputs direction commands.

## 3. Verilog Module Breakdown

### 3.1 Top Level: `snn_top_uart.v`
*   **Role**: The main wrapper connecting all sub-modules.
*   **Inputs**: `clk` (50MHz), `rst`, `uart_rx` (from Arduino).
*   **Outputs**: `dir_bits` (4-bit motor control: Front, Back, Left, Right).
*   **Function**: Instantiates the UART Receiver, Frame Parser, and SNN Core.

### 3.2 UART Receiver: `uart_rx.v`
*   **Role**: Physical layer communication.
*   **Parameters**: `BAUD=115200`.
*   **Function**: Oversamples the incoming serial line to robustly detect bits. Converts serial stream into parallel 8-bit bytes.

### 3.3 Frame Parser: `frame_rx.v`
*   **Role**: Protocol decoding.
*   **Packet Structure**:
    *   `[0xAA][0x55]`: Sync Header (Start of Frame).
    *   `[0x09]`: Length.
    *   `[S0_H][S0_L]...[S3_H][S3_L]`: 4 Sensors (16-bit, using top 12 bits).
    *   `[BTN_MASK]`: Training buttons state.
    *   `[CHECKSUM]`: XOR integrity check.
*   **Function**: Reconstructs the 12-bit sensor values and validates data integrity before passing it to the brain.

### 3.4 The Brain: `snn_core.v`
*   **Architecture**: 2-Layer Neural Network.
    *   **Input Layer**: 4 Neurons (mapped to 4 sensors).
    *   **Hidden Layer**: 4 Neurons.
    *   **Output Layer**: 4 Neurons (Directions).
*   **Operation**:
    1.  **Encoding**: Analog sensor values are thresholded (If > 800, neuron fires).
    2.  **Inference**:
        *   Signals propagate from Input -> Hidden -> Output.
        *   Weights are summed: `Sum = Σ (Active_Hidden_Neuron * Weight)`.
        *   **Winner-Take-All**: The output direction with the highest sum wins.
    3.  **Learning (Hebbian)**:
        *   If `Train_Btn` is held + `Direction_Btn` is pressed:
        *   **Potentiation**: Strengthens weights between *active* sensors and the *chosen* direction.
        *   **Depression**: Weakens weights to *other* directions.
        *   This allows the car to learn "If Sensor 1 is active, go Left" by demonstration.

### 3.5 UART Transmitter: `uart_tx.v` (Optional)
*   **Role**: Feedback channel.
*   **Function**: Allows the FPGA to send status or debug data back to the Arduino (e.g., "I decided to turn Left").

## 4. Signal Flow Summary
1.  **Arduino** samples A0-A3 at 100Hz.
2.  **Packet** is sent: `AA 55 09 ...`
3.  **FPGA** `frame_rx` detects valid packet, extracts `sensors[0:3]`.
4.  **SNN Core** checks `sensors > threshold`.
5.  **SNN Core** calculates dot-product of inputs & weights.
6.  **SNN Core** updates `dir_bits` (e.g., `0100` for Left).
7.  **(Future)** `dir_bits` drive motor H-Bridge to move car.

## 5. How to Run
1.  **Flash Arduino**: Upload `mega_snn_bridge.ino`.
2.  **Synthesize FPGA**: Compile project in Quartus Prime Lite Edition (Free).
3.  **Pin Planner**:
    *   `uart_rx` -> Arduino_IO0 (Pin V10 on DE10-Lite).
    *   `dir_bits` -> LEDs (LEDR0-LEDR3) for visual testing.
4.  **Train**:
    *   Trigger sensor 1 (put hand in front).
    *   Hold Arduino Button 2 (Train) + Button 3 (Left).
    *   Release.
5.  **Test**:
    *   Trigger sensor 1.
    *   Watch "Left" LED light up automatically.
