# FPGA SNN Car — Live Learning Demo Video Script

## Goal of the Video

Show clear, repeatable, real-time, on-chip learning on the FPGA:

- **Single direction training**: strong LEFT stimulus + TRAIN+RIGHT makes RIGHT output reliably fire afterward, with competing outputs suppressed.
- **Corner recognition**: two adjacent sensors equal → both corresponding outputs fire approximately equally.
- **Weighted response**: biased two-sensor input → stronger direction fires more strongly (higher rate / higher membrane potential).

This video is designed for a 3–5 minute demo.

## What to Capture On Screen

- A live window of `snn_dashboard.py` showing:
  - sensor grid
  - output spikes raster (4 outputs)
  - hidden spikes raster (optional, but helps credibility)
  - status text
- A camera shot of:
  - your hand moving near sensors
  - your TRAIN + direction buttons
  - FPGA board LEDs (optional, but nice reinforcement)

## Quick Setup Checklist (Before Recording)

- FPGA programmed with the latest build.
- Arduino running `mega_snn_bridge.ino`.
- Dashboard running and receiving sensor + FPGA frames.
- Do a reset and keep sensors neutral for ~1 second so baseline captures ambient.

Optional: put a small label on the sensor layout so viewers understand LEFT/FRONT/etc.

## Script (with timestamps, actions, and narration)

### 0:00 — Hook (show it learning live)

**Action**
- Start with dashboard visible.
- Quick camera shot of the FPGA + sensors.

**Say**
“This is an FPGA-based spiking neural network controlling a car. The important part is that it learns live, on-chip, in real time—no offline training and no external computation.”

### 0:15 — Architecture in one sentence

**Action**
- Point at sensors, then UART wiring / level shifter, then FPGA.
- Keep dashboard visible.

**Say**
“Sensors stream into the FPGA over UART. The FPGA runs a spiking neural network: sensors drive hidden spiking neurons, which drive four output neurons—Forward, Back, Left, Right—and we stream internal activity back to the dashboard so you can see learning happen.”

“For this demo we’re using a 2×2 LDR array (4 sensors), which are the top 4 cells of a physically built 3×3 sensor grid—so the hardware is already laid out for a future 3×3 upgrade.”

“Wiring note: each LDR is a simple voltage divider into Arduino analog inputs A0–A3, then the Arduino sends those readings over UART through a 5V↔3.3V level shifter into the DE10-Lite FPGA.”

### 0:35 — What “on-chip learning” means here

**Action**
- Put your hand near a sensor to create visible sensor activity on the dashboard.

**Say**
“Learning here means the FPGA updates synaptic weights inside hardware registers. When I hold TRAIN and choose a direction label, the FPGA strengthens the synapses from the active input into that labeled output, and weakens synapses into the competing outputs.”

“Those synaptic weights are memristor-modeled: we treat each connection like a bounded conductance that can be potentiated or depressed, which is a hardware-friendly way to represent non-volatile, analog-like learning behavior.”

“Structurally, the SNN is set up like a memristor crossbar array: inputs connect through a grid of programmable conductances into neuron sums, and learning is literally updating those conductance values on-chip.”

### 0:45 — Training loop + why it’s wired this way (demo-friendly explanation)

**Action**
- Point to the Arduino, then the level shifter, then the FPGA.
- On the dashboard, briefly point at: sensor grid → hidden spikes → output spikes.

**Say**
“Here’s the training loop in plain terms. Every frame, the Arduino reads the 4 LDRs and the training buttons, packs them into a short UART packet with a checksum, and sends it to the FPGA.”

“The FPGA verifies the packet, converts the sensor changes into spike-like input currents, and the hidden neurons integrate-and-fire. Those hidden spikes, in the same frame, drive the four output neurons.”

“When TRAIN is held with a direction button, the FPGA does supervised learning on-chip: it increases the weights going into the labeled output and decreases the weights into the other outputs, using the currently active sensors and spikes as the learning signal.”

“We wire it this way because it’s reliable on camera: the Arduino handles noisy analog sensing, the FPGA handles fast deterministic learning, the level shifter keeps the voltage safe, and the UART telemetry lets the dashboard show spikes and membrane potentials live as proof of learning.”

### 0:55 — What was wrong before (keep it short)

**Say**
“Earlier, training was inconsistent because of timing and output suppression. Now training uses same-frame spiking activity for updates, outputs can co-activate for corner recognition, and the neuron dynamics are rescaled to stay stable and proportional.”

### 1:15 — Baseline / calibration step (important for repeatability)

**Action**
- Reset FPGA.
- Keep sensors neutral for ~1 second.

**Say**
“First, we capture an ambient baseline so lighting conditions don’t break the demo. After this moment, changes in sensor input drive spikes.”

### 1:35 — Demo 1: Single Direction Training (required behavior)

**Action**
- Present a strong **LEFT stimulus** (use your actual physical “left” sensor).
- Keep it steady so the sensor grid shows a strong left activation.

**Say**
“Right now, the stimulus is clearly on the LEFT side.”

**Action**
- Hold **TRAIN + RIGHT** for ~1–2 seconds.
- Release buttons while keeping the same LEFT stimulus.

**Say (while holding buttons)**
“While TRAIN is held, the FPGA is strengthening the synapses from the currently active input into the RIGHT output neuron, and weakening synapses into the other outputs.”

**Say (after releasing buttons)**
“Now watch: even though the input is still LEFT, the RIGHT output neuron fires reliably after training, and the competing outputs are suppressed.”

**What viewers should see**
- Output raster: RIGHT spikes dominate.
- Other outputs: much fewer spikes (or nearly none).
- Output potentials: RIGHT generally higher / crosses threshold more often.

### 2:25 — Demo 2: Symmetric Corner Recognition (required behavior)

**Action**
- Activate two adjacent sensors equally, for example **FRONT + LEFT**, with no training buttons pressed.

**Say**
“Now I’m giving a symmetric corner input: FRONT and LEFT are equally active.”

**Say**
“Because the outputs are not forced into a strict winner-take-all, you can see both FRONT and LEFT outputs firing at similar rates.”

**What viewers should see**
- Output raster: FRONT and LEFT spike about equally.
- Output potentials: similar levels over time.

### 3:05 — Demo 3: Weighted Directional Response (required behavior)

**Action**
- Keep the same two sensors active but bias one stronger, e.g. **FRONT stronger than LEFT**.

**Say**
“Now I bias the input: FRONT is stronger than LEFT.”

**Say**
“You can see the output activity reflects that proportion: FRONT spikes more frequently than LEFT, and its membrane potential runs higher more often.”

**What viewers should see**
- Output raster: FRONT spikes more frequent than LEFT.
- Output potentials: FRONT higher distribution than LEFT.

### 3:40 — Summary (what this proves)

**Say**
“This demonstrates real-time on-chip learning on the FPGA: consistent training updates, suppression of competing outputs, corner recognition via balanced activation, and proportional response to biased inputs—all computed in hardware with a simple UART sensor stream.”

### 4:00 — Close shot

**Action**
- Show FPGA and sensor array again.

**Say**
“That’s the live-learning SNN car demo.”

## Notes for a Clean Recording

- Before each demo segment, pause for 1–2 seconds so the dashboard stabilizes.
- Narrate expectations before they happen: “you should see RIGHT dominate,” etc.
- Avoid starting with a strong stimulus immediately after reset—do baseline first.

## Fill-In Mapping (optional, for accurate narration)

Write down your physical mapping so the words match the visuals:

- Sensor 0 (s0 / A0) = ____________________
- Sensor 1 (s1 / A1) = ____________________
- Sensor 2 (s2 / A2) = ____________________
- Sensor 3 (s3 / A3) = ____________________
