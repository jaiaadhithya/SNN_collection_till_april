import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import threading
import time
import sys
import numpy as np

# --- Configuration ---
# You may need to change this port to match your system (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
SERIAL_PORT = 'COM3' 
BAUD_RATE = 115200
WINDOW_SIZE = 100     # Number of time steps to keep in memory

# --- Data Structures ---
# We store the last N time steps of data.
# For a raster plot, we want to know *when* a neuron fired.
# Let's keep a rolling buffer of activity.
# hidden_spikes[neuron_idx] = deque of time indices (0 to WINDOW_SIZE)
hidden_activity = [deque([0]*WINDOW_SIZE, maxlen=WINDOW_SIZE) for _ in range(4)]
output_activity = [deque([0]*WINDOW_SIZE, maxlen=WINDOW_SIZE) for _ in range(4)]

# Global flag to stop thread
running = True

# --- Serial Reader Thread ---
def read_serial_thread():
    global running
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"Connected to {SERIAL_PORT}")
    except Exception as e:
        print(f"Error opening serial port {SERIAL_PORT}: {e}")
        print("Please check your port name and connection.")
        running = False
        return

    while running:
        try:
            # Read 1 byte
            if ser.in_waiting > 0:
                header = ser.read(1)
                if header == b'\xBB': # Header Byte
                    # Read Data Byte
                    data = ser.read(1)
                    if len(data) == 1:
                        val = ord(data)
                        
                        # Parse Data
                        # Upper 4 bits: Hidden Layer (H3, H2, H1, H0)
                        # Lower 4 bits: Output Layer (Left, Right, Back, Front) -> Mapped to Dir Bits
                        hidden_val = (val >> 4) & 0x0F
                        output_val = val & 0x0F
                        
                        # Shift data into history buffers
                        for i in range(4):
                            # Hidden Layer
                            h_bit = (hidden_val >> i) & 1
                            hidden_activity[i].append(h_bit)
                            
                            # Output Layer
                            o_bit = (output_val >> i) & 1
                            output_activity[i].append(o_bit)
                            
        except Exception as e:
            print(f"Serial Read Error: {e}")
            break
            
    if ser.is_open:
        ser.close()

# Start Thread
t = threading.Thread(target=read_serial_thread, daemon=True)
t.start()

# --- Plotting Setup ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
plt.subplots_adjust(hspace=0.4)

# Hidden Layer Raster
ax1.set_title('Hidden Layer Activity (Live)')
ax1.set_ylabel('Neuron ID')
ax1.set_yticks(range(4))
ax1.set_yticklabels(['H0', 'H1', 'H2', 'H3'])
ax1.set_ylim(-0.5, 3.5)
ax1.set_xlim(0, WINDOW_SIZE)
ax1.grid(True, axis='y', linestyle='--', alpha=0.5)

# Output Layer Raster
ax2.set_title('Motor Output Activity (Live)')
ax2.set_ylabel('Direction')
ax2.set_yticks(range(4))
ax2.set_yticklabels(['Front (0)', 'Back (1)', 'Left (2)', 'Right (3)'])
ax2.set_ylim(-0.5, 3.5)
ax2.set_xlabel('Time Steps (Rolling Window)')
ax2.set_xlim(0, WINDOW_SIZE)
ax2.grid(True, axis='y', linestyle='--', alpha=0.5)

# Initialize Scatter Plots
# We use a list of Line2D objects (markers only) for efficiency
hidden_scatters = [ax1.plot([], [], '|', markersize=10, color='blue')[0] for _ in range(4)]
output_scatters = [ax2.plot([], [], '|', markersize=10, color='red')[0] for _ in range(4)]

def update(frame):
    if not running:
        return
        
    # Update Hidden Layer Plots
    for i in range(4):
        # Get indices where activity is 1
        data = list(hidden_activity[i])
        spikes = [idx for idx, val in enumerate(data) if val == 1]
        
        # X coordinates = spike indices
        # Y coordinates = constant i
        if spikes:
            hidden_scatters[i].set_data(spikes, [i]*len(spikes))
        else:
            hidden_scatters[i].set_data([], [])

    # Update Output Layer Plots
    for i in range(4):
        data = list(output_activity[i])
        spikes = [idx for idx, val in enumerate(data) if val == 1]
        
        if spikes:
            output_scatters[i].set_data(spikes, [i]*len(spikes))
        else:
            output_scatters[i].set_data([], [])
            
    return hidden_scatters + output_scatters

# Animate
ani = animation.FuncAnimation(fig, update, interval=50, blit=True)

print("Starting Raster Plot...")
print("Close the plot window to exit.")

try:
    plt.show()
except KeyboardInterrupt:
    pass
finally:
    running = False
    t.join(timeout=1)
    print("Exiting.")
