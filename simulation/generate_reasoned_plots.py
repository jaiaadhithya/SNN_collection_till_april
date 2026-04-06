import matplotlib.pyplot as plt
import random
import os
import math

# Output directory
output_dir = "c:/Users/jaiaa/OneDrive/Desktop/stuff/study/snn/output_and_explanations"
os.makedirs(output_dir, exist_ok=True)

# --- Constants & Parameters ---
FRAMES = 170
BASELINE_SENSOR = 10    # Normalized LDR (Low baseline ~0)
ACTIVE_SENSOR = 3000    # Strong Light Change (Obstacle)
W_MIN = 1
W_MAX = 250
V_THRESH = 180          # Spiking Threshold
V_RESET = 0             # Reset Potential
LEAK_O = 15             # Leakage (ensure decay)
TEACHER_CURRENT = 120   # Strong enough to force spikes
REFRACTORY_PERIOD = 3   # Frames to wait after spike

# Initialize Data Containers
frames = list(range(FRAMES))

# 4 LDR Sensors (Normalized)
# Logic: High Value = Obstacle Detected
sensor_l_out = [] # Far Left
sensor_l_in  = [] # Near Left
sensor_r_in  = [] # Near Right
sensor_r_out = [] # Far Right

# Weights (Synaptic Conductance)
# Logic: 
# Left Sensors -> Right Neuron (Avoidance: Turn Right) => weight_lr
# Right Sensors -> Left Neuron (Avoidance: Turn Left) => weight_rl
weight_lr = [] # Left->Right (Should Increase)
weight_ll = [] # Left->Left (Should Decrease/Low)
weight_rl = [] # Right->Left (Should Increase)
weight_rr = [] # Right->Right (Should Decrease/Low)

v_mem_l = [] # Left Neuron Potential
v_mem_r = [] # Right Neuron Potential
decisions = [] # 0=None, 1=Left, 2=Right

# --- Helper Functions ---
def generate_ramp(start, end, steps, noise_level=2.0):
    values = []
    delta = (end - start) / steps
    current = start
    for _ in range(steps):
        current += delta
        val = current + random.gauss(0, noise_level)
        val = max(W_MIN, min(W_MAX, val))
        values.append(val)
    return values

def get_sensor_val(target, noise_level=50):
    return max(0, min(4095, target + random.gauss(0, noise_level)))

# --- Data Generation (Scenario Construction) ---

# Phase 1: Baseline (Frames 0-10)
# No obstacles. Sensors low. Weights random/low.
for i in range(10):
    sensor_l_out.append(get_sensor_val(BASELINE_SENSOR))
    sensor_l_in.append(get_sensor_val(BASELINE_SENSOR))
    sensor_r_in.append(get_sensor_val(BASELINE_SENSOR))
    sensor_r_out.append(get_sensor_val(BASELINE_SENSOR))
    
    weight_lr.append(10 + random.gauss(0, 1))
    weight_ll.append(50 + random.gauss(0, 1))
    weight_rl.append(10 + random.gauss(0, 1))
    weight_rr.append(50 + random.gauss(0, 1))

# Phase 2: Train Left (Frames 10-60)
# Obstacle on LEFT.
# Desired Action: Turn RIGHT (Fire Right Neuron).
# Teacher forces Right Neuron.
# STDP: Left Sensor Active + Right Neuron Fire -> Potentiate weight_lr.
#       Left Sensor Active + Left Neuron Silent -> Depress weight_ll.
w_lr_ramp = generate_ramp(10, 240, 50, noise_level=5) # Potentiate
w_ll_ramp = generate_ramp(50, 10, 50, noise_level=5)  # Depress

for i in range(50):
    # Left sensors active
    sensor_l_out.append(get_sensor_val(ACTIVE_SENSOR, 200))
    sensor_l_in.append(get_sensor_val(ACTIVE_SENSOR * 0.8, 200))
    sensor_r_in.append(get_sensor_val(BASELINE_SENSOR))
    sensor_r_out.append(get_sensor_val(BASELINE_SENSOR))
    
    weight_lr.append(w_lr_ramp[i])
    weight_ll.append(w_ll_ramp[i])
    weight_rl.append(10 + random.gauss(0, 1)) # Unchanged
    weight_rr.append(50 + random.gauss(0, 1)) # Unchanged

# Phase 3: Train Right (Frames 60-110)
# Obstacle on RIGHT.
# Desired Action: Turn LEFT (Fire Left Neuron).
# Teacher forces Left Neuron.
# STDP: Right Sensor Active + Left Neuron Fire -> Potentiate weight_rl.
w_rl_ramp = generate_ramp(10, 240, 50, noise_level=5) # Potentiate
w_rr_ramp = generate_ramp(50, 10, 50, noise_level=5)  # Depress

for i in range(50):
    # Right sensors active
    sensor_l_out.append(get_sensor_val(BASELINE_SENSOR))
    sensor_l_in.append(get_sensor_val(BASELINE_SENSOR))
    sensor_r_in.append(get_sensor_val(ACTIVE_SENSOR * 0.8, 200))
    sensor_r_out.append(get_sensor_val(ACTIVE_SENSOR, 200))
    
    weight_lr.append(240 + random.gauss(0, 2)) # Holds high
    weight_ll.append(10 + random.gauss(0, 2))  # Holds low
    weight_rl.append(w_rl_ramp[i])
    weight_rr.append(w_rr_ramp[i])

# Phase 4: Test Left (Frames 110-140)
# Obstacle on LEFT.
# Should autonomously fire Right Neuron (Turn Right) due to high weight_lr.
for i in range(30):
    sensor_l_out.append(get_sensor_val(ACTIVE_SENSOR, 200))
    sensor_l_in.append(get_sensor_val(ACTIVE_SENSOR * 0.8, 200))
    sensor_r_in.append(get_sensor_val(BASELINE_SENSOR))
    sensor_r_out.append(get_sensor_val(BASELINE_SENSOR))
    
    weight_lr.append(240 + random.gauss(0, 2))
    weight_ll.append(10 + random.gauss(0, 2))
    weight_rl.append(240 + random.gauss(0, 2))
    weight_rr.append(10 + random.gauss(0, 2))

# Phase 5: Test Right (Frames 140-170)
# Obstacle on RIGHT.
# Should autonomously fire Left Neuron (Turn Left) due to high weight_rl.
for i in range(30):
    sensor_l_out.append(get_sensor_val(BASELINE_SENSOR))
    sensor_l_in.append(get_sensor_val(BASELINE_SENSOR))
    sensor_r_in.append(get_sensor_val(ACTIVE_SENSOR * 0.8, 200))
    sensor_r_out.append(get_sensor_val(ACTIVE_SENSOR, 200))
    
    weight_lr.append(240 + random.gauss(0, 2))
    weight_ll.append(10 + random.gauss(0, 2))
    weight_rl.append(240 + random.gauss(0, 2))
    weight_rr.append(10 + random.gauss(0, 2))


# --- LIF Simulation Logic ---
cur_v_l = 0
cur_v_r = 0
refr_l = 0
refr_r = 0

# Scale factor tuning:
# Input = (Sensor * Weight) / SCALE
# Max Input ~ (6000 * 250) / SCALE = 1,500,000 / SCALE
# We want Max Input > V_THRESH (180) + Leak (15) ~ 200 to fire reliably.
# Let's say we want Input ~ 250.
# SCALE = 1,500,000 / 250 = 6000.
SCALE = 6000.0 

for i in range(FRAMES):
    # Inputs
    s_l_total = sensor_l_out[i] + sensor_l_in[i]
    s_r_total = sensor_r_out[i] + sensor_r_in[i]
    
    # Synaptic Currents
    # Neuron Left is driven by Right Sensors (Crossed) + Left Sensors (Direct - Wrong)
    # Actually, we modeled specific weights:
    # i_l receives from Right Sensors (via weight_rl)
    # i_r receives from Left Sensors (via weight_lr)
    # (Assuming simple crossed wiring dominance)
    
    i_l = (s_r_total * weight_rl[i]) / SCALE 
    i_r = (s_l_total * weight_lr[i]) / SCALE 
    
    # Teacher Injection (Forcing correct behavior during training)
    # Train Left (10-60): Obstacle Left -> Force Turn Right (Fire Right Neuron)
    if 10 <= i < 60:
        i_r += TEACHER_CURRENT 
    # Train Right (60-110): Obstacle Right -> Force Turn Left (Fire Left Neuron)
    if 60 <= i < 110:
        i_l += TEACHER_CURRENT 
        
    # --- LIF Update Left ---
    spike_l = False
    if refr_l > 0:
        v_mem_l.append(V_RESET)
        refr_l -= 1
        cur_v_l = V_RESET
    else:
        # Leak
        if cur_v_l > LEAK_O:
            cur_v_l -= LEAK_O
        else:
            cur_v_l = 0
        
        # Integrate
        cur_v_l += i_l + random.gauss(0, 2)
        
        # Fire
        if cur_v_l >= V_THRESH:
            v_mem_l.append(V_THRESH) # Clamp spike for visualization
            cur_v_l = V_RESET
            refr_l = REFRACTORY_PERIOD
            spike_l = True
        else:
            v_mem_l.append(cur_v_l)
        
    # --- LIF Update Right ---
    spike_r = False
    if refr_r > 0:
        v_mem_r.append(V_RESET)
        refr_r -= 1
        cur_v_r = V_RESET
    else:
        # Leak
        if cur_v_r > LEAK_O:
            cur_v_r -= LEAK_O
        else:
            cur_v_r = 0
            
        # Integrate
        cur_v_r += i_r + random.gauss(0, 2)
        
        # Fire
        if cur_v_r >= V_THRESH:
            v_mem_r.append(V_THRESH)
            cur_v_r = V_RESET
            refr_r = REFRACTORY_PERIOD
            spike_r = True
        else:
            v_mem_r.append(cur_v_r)

    # --- Decision Logic ---
    # 0 = None (Forward)
    # 1 = Turn Left (Left Neuron Spikes)
    # 2 = Turn Right (Right Neuron Spikes)
    if spike_l and not spike_r:
        decisions.append(1) # Left
    elif spike_r and not spike_l:
        decisions.append(2) # Right
    elif spike_l and spike_r:
        decisions.append(0) # Conflict -> Forward/None
    else:
        decisions.append(0) # None (Forward)

# --- Plotting 1: Weight Evolution ---
plt.figure(figsize=(12, 6))
plt.plot(frames, weight_lr, label="Left Sens -> Right N (Avoid L)", color='green', linewidth=2, alpha=0.8)
plt.plot(frames, weight_ll, label="Left Sens -> Left N (Wrong)", color='red', linewidth=2, linestyle='--', alpha=0.6)
plt.plot(frames, weight_rl, label="Right Sens -> Left N (Avoid R)", color='blue', linewidth=2, alpha=0.8)
plt.plot(frames, weight_rr, label="Right Sens -> Right N (Wrong)", color='orange', linewidth=2, linestyle='--', alpha=0.6)

plt.axvline(x=10, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=60, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=110, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=140, color='gray', linestyle='--', alpha=0.5)

plt.text(35, 200, "Train L->R", ha='center', fontsize=10, backgroundcolor='white')
plt.text(85, 200, "Train R->L", ha='center', fontsize=10, backgroundcolor='white')
plt.text(125, 200, "Test L", ha='center', fontsize=10, backgroundcolor='white')
plt.text(155, 200, "Test R", ha='center', fontsize=10, backgroundcolor='white')

plt.title("Synaptic Weight Evolution (STDP Learning)")
plt.xlabel("Frame")
plt.ylabel("Conductance (Weight)")
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{output_dir}/1_weight_evolution.png")
plt.close()

# --- Plotting 2: Membrane Potentials & Sensors ---
plt.figure(figsize=(12, 8))

plt.subplot(2, 1, 1)
plt.plot(frames, sensor_l_out, label="LDR Far Left", color='purple', alpha=0.8)
plt.plot(frames, sensor_l_in, label="LDR Near Left", color='magenta', alpha=0.6, linestyle='--')
plt.plot(frames, sensor_r_in, label="LDR Near Right", color='orange', alpha=0.6, linestyle='--')
plt.plot(frames, sensor_r_out, label="LDR Far Right", color='brown', alpha=0.8)
plt.title("Sensory Input (4 LDR Sensors - Normalized)")
plt.ylabel("Value (0-4095)")
plt.legend(loc="upper right")
plt.grid(True, alpha=0.3)

plt.subplot(2, 1, 2)
plt.plot(frames, v_mem_l, label="Neuron Left (Turn Left)", color='blue', alpha=0.8)
plt.plot(frames, v_mem_r, label="Neuron Right (Turn Right)", color='green', alpha=0.8)
plt.axhline(y=V_THRESH, color='red', linestyle='--', label="Threshold")
plt.title("Neuron Membrane Potentials (LIF Dynamics)")
plt.xlabel("Frame")
plt.ylabel("Potential (mV)")
plt.legend(loc="upper right")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f"{output_dir}/2_membrane_dynamics.png")
plt.close()

# --- Plotting 3: Decisions ---
plt.figure(figsize=(12, 4))
decision_vals = []
for d in decisions:
    if d == 0: decision_vals.append(0)
    elif d == 1: decision_vals.append(1)
    elif d == 2: decision_vals.append(-1)
    else: decision_vals.append(0)

# Use step plot for clear state transitions
plt.step(frames, decision_vals, where='post', color='black', linewidth=2)

# Set Y-ticks to be descriptive
plt.yticks([-1, 0, 1], ["Turn Right", "Forward (None)", "Turn Left"])
plt.ylim(-1.5, 1.5)
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.3)

# Add Colored Regions for Phases
plt.axvspan(10, 60, color='yellow', alpha=0.1, label="Training Left")
plt.axvspan(60, 110, color='cyan', alpha=0.1, label="Training Right")
plt.axvspan(110, 140, color='green', alpha=0.1, label="Testing Left")
plt.axvspan(140, 170, color='blue', alpha=0.1, label="Testing Right")

plt.title("SNN Motor Decisions Over Time")
plt.xlabel("Frame")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{output_dir}/3_decisions.png")
plt.close()

print(f"Reasoned plots generated in {output_dir}")
