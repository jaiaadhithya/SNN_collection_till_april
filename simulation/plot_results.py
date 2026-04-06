import csv
import matplotlib.pyplot as plt
import os

# Paths
INPUT_DIR = "simulation_output"
OUTPUT_DIR = "output_and_explanations"

# --- 1. Load Data ---
weights = []
membrane = []
spikes = []

# Read Weights
with open(os.path.join(INPUT_DIR, "weights.csv"), "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        weights.append([int(x) for x in row])

# Read Membrane
with open(os.path.join(INPUT_DIR, "membrane.csv"), "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        membrane.append([int(x) for x in row])

# Read Spikes
with open(os.path.join(INPUT_DIR, "spikes.csv"), "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    spikes_header = header
    for row in reader:
        # Columns: Frame, Input_S0, Input_S1, Input_S2, Input_S3, Train, Btn, Dir
        frame = int(row[0])
        s0 = int(row[1])
        s1 = int(row[2])
        s2 = int(row[3])
        s3 = int(row[4])
        train = int(row[5])
        btn = row[6]
        d_str = row[7]
        d_val = int(d_str, 2) if d_str else 0
        spikes.append([frame, s0, s1, s2, s3, train, btn, d_val])

# Convert to columns for plotting
w_frames = [r[0] for r in weights]
w_Gio13 = [r[1] for r in weights] # Left->Right (Potentiation)
w_Gio12 = [r[2] for r in weights] # Left->Left (Depression)
w_Gio00 = [r[3] for r in weights] # Front->Fwd (Stable)
w_Gio31 = [r[4] for r in weights] # Back->Bwd (Stable)

m_frames = [r[0] for r in membrane]
m_v0 = [r[1] for r in membrane]
m_v1 = [r[2] for r in membrane]
m_v2 = [r[3] for r in membrane]
m_v3 = [r[4] for r in membrane]

s_frames = [r[0] for r in spikes]
s_s0 = [r[1] for r in spikes]
s_s1 = [r[2] for r in spikes]
s_s2 = [r[3] for r in spikes]
s_s3 = [r[4] for r in spikes]
s_train = [r[5] for r in spikes]
s_dir = [r[7] for r in spikes]

# --- 2. Plot Weight Evolution ---
plt.figure(figsize=(10, 6))
plt.plot(w_frames, w_Gio13, label="G_io[Left->Right] (Potentiation)", linewidth=2, color='blue')
plt.plot(w_frames, w_Gio12, label="G_io[Left->Left] (Depression)", linewidth=2, color='red', linestyle='--')
plt.plot(w_frames, w_Gio00, label="G_io[Front->Fwd] (Stable)", color='gray', linestyle=':')
plt.plot(w_frames, w_Gio31, label="G_io[Back->Bwd] (Stable)", color='gray', linestyle='-.')
plt.title("Synaptic Weight Evolution (Learning)")
plt.xlabel("Frame")
plt.ylabel("Weight Value (0-255)")
plt.axvspan(10, 60, color='yellow', alpha=0.2, label="Train: Left->Right")
plt.axvspan(60, 110, color='green', alpha=0.2, label="Train: Right->Left")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(OUTPUT_DIR, "1_weight_evolution.png"))
plt.close()

# --- 3. Plot Membrane Potentials ---
plt.figure(figsize=(12, 8))
plt.subplot(2, 1, 1)
plt.plot(m_frames, m_v3, label="V_mem Output 3 (Right)", color='red')
plt.plot(m_frames, m_v2, label="V_mem Output 2 (Left)", color='blue')
plt.axhline(y=1000, color='k', linestyle='--', label="Threshold")
plt.title("Membrane Potential Dynamics (Output Neurons)")
plt.ylabel("Potential (mV equivalent)")
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(s_frames, s_s1, label="Sensor Left (S1)", color='orange')
plt.plot(s_frames, s_s2, label="Sensor Right (S2)", color='purple')
plt.plot(s_frames, s_s0, label="Sensor Front (S0)", color='gray', alpha=0.5)
plt.plot(s_frames, s_s3, label="Sensor Back (S3)", color='gray', alpha=0.5)
plt.ylabel("Sensor Value")
plt.xlabel("Frame")
plt.legend()
plt.grid(True)

plt.savefig(os.path.join(OUTPUT_DIR, "2_membrane_dynamics.png"))
plt.close()

# --- 4. Plot Spike Raster / Decisions ---
plt.figure(figsize=(10, 5))
# Decode Direction Bits: 3=Right (1000? No, 0001?), 2=Left, 0=Fwd, 1=Bwd?
# My simulation uses: 0=Fwd, 1=Bwd, 2=Left, 3=Right.
# dir_bits is array [Fwd, Bwd, Left, Right]
# So 1000 = Fwd(0), 0100 = Bwd(1), 0010 = Left(2), 0001 = Right(3)
# Let's verify from snn_behavioral_model.py
# dir_bits = [Fwd, Bwd, Left, Right]
# If dir_bits[3] is 1, then Right.
# If dir_bits[2] is 1, then Left.

decisions = []
for d in s_dir:
    # d is int from binary string "Fwd Bwd Left Right"
    # e.g. 1000 = 8 (Fwd), 0100 = 4 (Bwd), 0010 = 2 (Left), 0001 = 1 (Right)
    if d & 1: decisions.append(3) # Right
    elif d & 2: decisions.append(2) # Left
    elif d & 4: decisions.append(1) # Bwd
    elif d & 8: decisions.append(0) # Fwd
    else: decisions.append(-1) # None

plt.scatter(s_frames, decisions, c=decisions, cmap='viridis', s=20)
plt.yticks([-1, 0, 1, 2, 3], ["None", "Fwd", "Bwd", "Left", "Right"])
plt.title("SNN Output Decisions over Time")
plt.xlabel("Frame")
plt.grid(True)
plt.axvspan(110, 140, color='gray', alpha=0.2, label="Test: Left Obstacle")
plt.axvspan(140, 170, color='lightgray', alpha=0.2, label="Test: Right Obstacle")
plt.legend()
plt.savefig(os.path.join(OUTPUT_DIR, "3_decisions_raster.png"))
plt.close()

print("Plots generated in", OUTPUT_DIR)
