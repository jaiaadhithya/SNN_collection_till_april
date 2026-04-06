import random
import csv

# --- Configuration ---
N_IN = 4       # Number of input sensors (Front, Back, Left, Right)
N_H = 8        # Number of hidden neurons
N_OUT = 4      # Number of output neurons (Forward, Backward, Left, Right)

# LIF Parameters (Matching Verilog)
V_THRESH_H = 1000
LEAK_H = 50
REF_H_FRAMES = 5

V_THRESH_O = 1000
LEAK_O = 50
REF_O_FRAMES = 2

# Learning Parameters
G_MAX = 255
G_MIN = 1
D_POT = 15     # Potentiation step
D_DEP = 5      # Depression step

# Input Scaling
INPUT_SHIFT = 6 # Shift right by 6 (divide by 64)

class SNN:
    def __init__(self):
        # State Variables
        self.v_mem_h = [0] * N_H
        self.v_mem_o = [0] * N_OUT
        self.ref_h = [0] * N_H
        self.ref_o = [0] * N_OUT
        self.h_spike = [0] * N_H
        self.dir_bits = [0] * N_OUT # [Fwd, Bwd, Left, Right]

        # Weights
        # G (Hidden -> Output): Init 50
        self.G = [[50 for _ in range(N_OUT)] for _ in range(N_H)]
        
        # G_io (Sensor -> Output): Init 20 (Weak/Untrained)
        # But set "Wrong Reflex" high:
        # S1(Left) -> Out2(Left) = High (200) - Car turns INTO obstacle initially
        # S2(Right) -> Out3(Right) = High (200) - Car turns INTO obstacle initially
        self.G_io = [[20 for j in range(N_OUT)] for i in range(N_IN)]
        self.G_io[1][2] = 200 # Wrong Reflex: Left Sensor -> Turn Left
        self.G_io[2][3] = 200 # Wrong Reflex: Right Sensor -> Turn Right

    def update_weights(self):
        # Weight Update (Simplified STDP)
        if self.train_mode:
            for j in range(N_OUT):
                if self.spike_out[j]: # Post-synaptic spike (Teacher Force)
                    for i in range(N_IN):
                        if self.spike_in[i]: # Pre-synaptic spike (Coincidence)
                            # Potentiation: Correlated firing
                            self.G_io[i][j] = min(self.G_io[i][j] + D_POT, G_MAX)
                        else:
                            # Depression: Post without Pre (uncorrelated)
                            self.G_io[i][j] = max(self.G_io[i][j] - D_DEP, G_MIN)
                else: # Post did NOT fire
                    for i in range(N_IN):
                        if self.spike_in[i]: # Pre fired, but Post didn't
                             # Depression: Pre without Post (uncorrelated)
                             self.G_io[i][j] = max(self.G_io[i][j] - D_DEP, G_MIN)

    def process_frame(self, sensors, train=False, label_dir_override=[0,0,0,0]):
        # 1. Input Processing with Baseline Subtraction
        # Remove baseline noise (e.g. ambient light/floor reflection)
        # 210 is slightly above the 200 mean noise
        clean_sensors = [max(0, s - 210) for s in sensors]
        
        # Scale down
        current = [s >> INPUT_SHIFT for s in clean_sensors]

        # 2. Neuron Update
        self.spike_in = [0] * N_IN
        # Check for input spikes (simplified rate coding: if current > threshold)
        # Actually, let's just use the current as "synaptic drive" directly
        # But for STDP "Pre-synaptic spike", we need a boolean
        # Let's say if current > 0, we consider it "active" (Pre-spike) for learning
        for i in range(N_IN):
            if current[i] > 0:
                self.spike_in[i] = 1

        syn_current = [0] * N_OUT
        for j in range(N_OUT):
            for k in range(N_IN):
                # (Input * Weight) >> 2
                contribution = (current[k] * self.G_io[k][j]) >> 2
                syn_current[j] += contribution

        # 3. LIF Dynamics
        self.spike_out = [0] * N_OUT
        for j in range(N_OUT):
            # Leak
            self.v_mem_o[j] = max(0, self.v_mem_o[j] - LEAK_O)
            
            # Integrate
            self.v_mem_o[j] += syn_current[j]

            # Fire?
            if self.v_mem_o[j] >= V_THRESH_O:
                self.v_mem_o[j] = 0
                self.spike_out[j] = 1

        # 4. Teacher Override (Training)
        if train:
            # If teacher says "Turn Right" (Index 3), we force Output 3 to Spike
            # And inhibit others?
            # For simplicity, we just overwrite spike_out with the label
            # This ensures "Post-synaptic spike" occurs where desired
            self.train_mode = True
            # Check which output is active in label
            # label_dir_override is [Fwd, Bwd, Left, Right]
            # If any is 1, we force it.
            # But we must respect the "Button Press" timing.
            # If label is [0,0,0,0], no training happens this frame?
            # User said "press button".
            if sum(label_dir_override) > 0:
                 self.spike_out = list(label_dir_override)
            else:
                 # If no button pressed, we don't force, but we might still learn?
                 # Usually training happens ONLY when button is pressed.
                 self.train_mode = False 
        else:
            self.train_mode = False

        # 5. Weight Update
        self.update_weights()

        return {
            "v_mem_o": list(self.v_mem_o),
            "dir_bits": self.spike_out,
            "weights": self.G_io
        }

# --- Simulation Setup ---
def run_simulation():
    snn = SNN()
    
    f_weights = open("simulation_output/weights.csv", "w", newline='')
    f_membrane = open("simulation_output/membrane.csv", "w", newline='')
    f_spikes = open("simulation_output/spikes.csv", "w", newline='')
    
    w_writer = csv.writer(f_weights)
    m_writer = csv.writer(f_membrane)
    s_writer = csv.writer(f_spikes)
    
    # Headers
    w_writer.writerow(["Frame", "Gio_1_3", "Gio_1_2", "Gio_0_0", "Gio_3_1"]) # Weights: Left->Right, Left->Left(Depress), Front->Fwd, Back->Bwd
    m_writer.writerow(["Frame", "Vo_0", "Vo_1", "Vo_2", "Vo_3"])
    s_writer.writerow(["Frame", "Input_S0", "Input_S1", "Input_S2", "Input_S3", "Train", "Btn", "Dir"])
    
    # 1. Baseline (No input)
    print("Phase 1: Baseline...")
    for f in range(10):
        # Baseline noise around 100
        sensors = [
            int(random.gauss(100, 10)),
            int(random.gauss(100, 10)),
            int(random.gauss(100, 10)),
            int(random.gauss(100, 10))
        ]
        # Clamp to 0-4095
        sensors = [max(0, min(x, 4095)) for x in sensors]
        
        res = snn.process_frame(sensors)
        # Log
        s_writer.writerow([f, sensors[0], sensors[1], sensors[2], sensors[3], 0, 0, "".join([str(x) for x in res["dir_bits"]])])
        m_writer.writerow([f] + res["v_mem_o"])
        # Log: G_io[1][3](Left->Right), G_io[1][2](Left->Left - Should depress), G_io[0][0](Front->Fwd), G_io[3][1](Back->Bwd)
        w_writer.writerow([f, snn.G_io[1][3], snn.G_io[1][2], snn.G_io[0][0], snn.G_io[3][1]])

    # 2. Training: Obstacle Left (S1) -> Turn Right (Btn=Right)
    print("Phase 2: Training (Left Obstacle -> Turn Right)...")
    for f in range(10, 60):
        # Left Obstacle ~3000 (Strong Signal), others ~100
        sensors = [
            int(random.gauss(100, 10)),
            int(random.gauss(3000, 100)), # Left
            int(random.gauss(100, 10)),
            int(random.gauss(100, 10))
        ]
        sensors = [max(0, min(x, 4095)) for x in sensors]
        
        # Btn Right (Bit 3) -> [0,0,0,1]
        res = snn.process_frame(sensors, train=True, label_dir_override=[0,0,0,1])
        
        s_writer.writerow([f, sensors[0], sensors[1], sensors[2], sensors[3], 1, "Right", "".join([str(x) for x in res["dir_bits"]])])
        m_writer.writerow([f] + res["v_mem_o"])
        w_writer.writerow([f, snn.G_io[1][3], snn.G_io[1][2], snn.G_io[0][0], snn.G_io[3][1]])

    # 3. Training: Obstacle Right (S2) -> Turn Left (Btn=Left)
    print("Phase 3: Training (Right Obstacle -> Turn Left)...")
    for f in range(60, 110):
        # Right Obstacle ~3000
        sensors = [
            int(random.gauss(100, 10)),
            int(random.gauss(100, 10)),
            int(random.gauss(3000, 100)), # Right
            int(random.gauss(100, 10))
        ]
        sensors = [max(0, min(x, 4095)) for x in sensors]
        
        # Btn Left (Bit 2) -> [0,0,1,0]
        res = snn.process_frame(sensors, train=True, label_dir_override=[0,0,1,0])
        
        s_writer.writerow([f, sensors[0], sensors[1], sensors[2], sensors[3], 1, "Left", "".join([str(x) for x in res["dir_bits"]])])
        m_writer.writerow([f] + res["v_mem_o"])
        w_writer.writerow([f, snn.G_io[1][3], snn.G_io[1][2], snn.G_io[0][0], snn.G_io[3][1]])

    # 4. Testing: Obstacle Left -> Should Turn Right
    print("Phase 4: Testing (Left Obstacle)...")
    for f in range(110, 140):
        # Left Obstacle ~3000
        sensors = [
            int(random.gauss(100, 10)),
            int(random.gauss(3000, 100)), # Left
            int(random.gauss(100, 10)),
            int(random.gauss(100, 10))
        ]
        sensors = [max(0, min(x, 4095)) for x in sensors]

        res = snn.process_frame(sensors, train=False)
        
        s_writer.writerow([f, sensors[0], sensors[1], sensors[2], sensors[3], 0, 0, "".join([str(x) for x in res["dir_bits"]])])
        m_writer.writerow([f] + res["v_mem_o"])
        w_writer.writerow([f, snn.G_io[1][3], snn.G_io[1][2], snn.G_io[0][0], snn.G_io[3][1]])

    # 5. Testing: Obstacle Right -> Should Turn Left
    print("Phase 5: Testing (Right Obstacle)...")
    for f in range(140, 170):
        # Right Obstacle ~3000
        sensors = [
            int(random.gauss(100, 10)),
            int(random.gauss(100, 10)),
            int(random.gauss(3000, 100)), # Right
            int(random.gauss(100, 10))
        ]
        sensors = [max(0, min(x, 4095)) for x in sensors]

        res = snn.process_frame(sensors, train=False)
        
        s_writer.writerow([f, sensors[0], sensors[1], sensors[2], sensors[3], 0, 0, "".join([str(x) for x in res["dir_bits"]])])
        m_writer.writerow([f] + res["v_mem_o"])
        w_writer.writerow([f, snn.G_io[1][3], snn.G_io[1][2], snn.G_io[0][0], snn.G_io[3][1]])

    f_weights.close()
    f_membrane.close()
    f_spikes.close()
    print("Simulation Complete. Data saved to simulation_output/")

if __name__ == "__main__":
    run_simulation()
