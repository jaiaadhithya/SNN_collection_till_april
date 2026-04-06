# Wiring Guide: SNN Autonomous Car

This guide details how to wire the Arduino Mega 2560 to the Intel DE10-Lite FPGA (MAX 10) for the SNN Car project.

**⚠️ CRITICAL WARNING: VOLTAGE LEVELS**
*   **Arduino Mega operates at 5V.**
*   **DE10-Lite FPGA operates at 3.3V.**
*   **Direct connection will DESTROY the FPGA.**
*   **You MUST use a Logic Level Shifter (5V <-> 3.3V) for all signals between them.**

---

## 1. System Overview
`[Sensors] --> [Arduino Mega] --(UART)--> [Level Shifter] --(UART)--> [FPGA] --> [LEDs/Motors]`

## 2. Arduino Mega 2560 Wiring

### A. Analog Sensors (Input)
Connect your distance sensors (e.g., IR or Ultrasonic with analog out) to these pins:
*   **Sensor 0 (Front-Left?)**: `A0`
*   **Sensor 1 (Front-Right?)**: `A1`
*   **Sensor 2 (Side-Left?)**: `A2`
*   **Sensor 3 (Side-Right?)**: `A3`

### B. Control Buttons (Optional for Training)
Connect pushbuttons between the Pin and GND (Internal Pullups are used).
*   **Train Enable**: `Pin 9`
*   **Train Left**: `Pin 10`
*   **Train Front**: `Pin 11`
*   **Train Back**: `Pin 12`
*   **Train Right**: `Pin 13`

### C. UART Communication (Bi-directional)
*   **TX1 (Arduino Transmit)**: `Pin 18` -> Connects to **HV1** on Level Shifter.
*   **RX1 (Arduino Receive)**: `Pin 19` -> Connects to **HV2** on Level Shifter.
*   **GND**: Connect to Common Ground.

---

## 3. Logic Level Shifter Wiring

This device sits between the Arduino and FPGA to protect the FPGA.

| Level Shifter Pin | Connection |
| :--- | :--- |
| **HV (High Voltage)** | **Arduino 5V** |
| **GND (High Side)** | **Arduino GND** |
| **HV1** | **Arduino Pin 18 (TX1)** |
| **HV2** | **Arduino Pin 19 (RX1)** |
| | |
| **LV (Low Voltage)** | **FPGA 3.3V (GPIO Header)** |
| **GND (Low Side)** | **FPGA GND (GPIO Header)** |
| **LV1** | **FPGA Pin V10 (Arduino_IO0)** |
| **LV2** | **FPGA Pin W10 (Arduino_IO1)** |

---

## 4. FPGA (DE10-Lite) Wiring

Use the **Arduino Header** on the DE10-Lite board.

### A. UART Input/Output (From/To Level Shifter)
*   **RX (Input)**: `Arduino_IO0` (PIN_V10) -> Connect to **LV1**.
*   **TX (Output)**: `Arduino_IO1` (PIN_W10) -> Connect to **LV2**.

### B. Output Display (On-board LEDs)
The `dir_bits` output is mapped to the LEDs for visual feedback.
*   **Forward**: `LEDR0`
*   **Backward**: `LEDR1`
*   **Left**: `LEDR2`
*   **Right**: `LEDR3`

### C. Control Switches (On-board)
*   **Reset**: `SW0` (PIN_C10). UP = Reset, DOWN = Run.

### D. Power & Ground
*   **3.3V**: Take from the Arduino Header 3.3V pin.
*   **GND**: Take from the Arduino Header GND pin.

## 5. FPGA Pin Assignment (Quartus Prime)
If you are setting up the project in Quartus, assign these pins:

| Port Name | FPGA Pin (DE10-Lite) | Description |
| :--- | :--- | :--- |
| **clk** | **PIN_P11** | 50MHz Clock |
| **rst** | **PIN_C10** | Reset (SW0) |
| **uart_rx** | **PIN_V10** | Arduino Header IO0 |
| **uart_tx** | **PIN_W10** | Arduino Header IO1 |
| **dir_bits[0]** | **PIN_A8** | LEDR0 (Front) |
| **dir_bits[1]** | **PIN_A9** | LEDR1 (Back) |
| **dir_bits[2]** | **PIN_A10** | LEDR2 (Left) |
| **dir_bits[3]** | **PIN_B10** | LEDR3 (Right) |

