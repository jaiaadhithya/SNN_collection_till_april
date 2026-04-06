import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.widgets import Button
from matplotlib.patches import Circle, FancyArrowPatch
import numpy as np
import threading
import time
import collections
import csv
from datetime import datetime

# --- Configuration ---
BAUD_RATE = 115200
HISTORY_LEN = 50  # Shorter history keeps UI snappier

# Optional manual override for the Arduino port on Windows, e.g. "COM3".
# Leave as None to auto-detect based on port description.
PREFERRED_PORT = None

# These thresholds should roughly match the FPGA values after down-scaling.
# snn_core.v: V_THRESH_H = 120 (12-bit), snn_top_uart.v sends v_h[8:1] -> 120/2 = 60
HIDDEN_THRESH_8BIT = 60
# snn_core.v: V_THRESH_O = 180 (16-bit), LSB sent directly
OUTPUT_THRESH_8BIT = 200

# --- Data Stores ---
sensor_data = collections.deque(maxlen=HISTORY_LEN)
hidden_spike_data = collections.deque(maxlen=HISTORY_LEN)
output_spike_data = collections.deque(maxlen=HISTORY_LEN)
v_hidden_data = collections.deque(maxlen=HISTORY_LEN)  # [{0:val, 1:val, ...}, ...]
v_output_data = collections.deque(maxlen=HISTORY_LEN)
latest_sensors = [0, 0, 0, 0]
latest_btn = 0

# Logging / recording
recording = False
log_rows = []  # each entry is one FPGA frame for CSV export

# Connection / activity flags
fpga_connected = False
arduino_connected = False
last_fpga_time = 0
last_arduino_time = 0

# Frame counter for logging
frame_counter = 0

# --- Serial Reader Thread ---
def read_serial():
    global fpga_connected, arduino_connected
    global last_fpga_time, last_arduino_time
    global latest_sensors, latest_btn
    global frame_counter, log_rows, recording
    
    # Auto-detect Arduino (or use preferred port)
    ports = list(serial.tools.list_ports.comports())
    arduino_port = None
    if PREFERRED_PORT is not None:
        arduino_port = PREFERRED_PORT
    else:
        for p in ports:
            desc = (p.description or "").lower()
            if "arduino" in desc or "usb serial" in desc or "ch340" in desc:
                arduino_port = p.device
                break
        # Fallback: just grab the first available port
        if arduino_port is None and len(ports) > 0:
            arduino_port = ports[0].device
            
    if not arduino_port:
        print("Error: Arduino not found. Please connect it.")
        return

    try:
        ser = serial.Serial(arduino_port, BAUD_RATE, timeout=0.1)
        print(f"Connected to {arduino_port}")
        arduino_connected = True
        last_arduino_time = time.time()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    buffer = bytearray()
    
    while True:
        try:
            if ser.in_waiting:
                buffer.extend(ser.read(ser.in_waiting))
                
                # Process Buffer
                while len(buffer) > 0:
                    # --- FPGA Packet: [0xBB][LEN][DATA...] ---
                    if len(buffer) >= 2 and buffer[0] == 0xBB:
                        pkt_len = buffer[1]
                        
                        # Wait for full packet
                        if len(buffer) < 2 + pkt_len:
                            break  # need more data
                        
                        if pkt_len == 9:
                            # LEGACY PACKET (4 neurons)
                            # [v_h0..3][v_o0..3][spikes]
                            v_h = [buffer[2], buffer[3], buffer[4], buffer[5]]
                            # Pad with zeros for remaining 28 neurons
                            v_h.extend([0]*28)
                            
                            v_o = [buffer[6], buffer[7], buffer[8], buffer[9]]
                            spikes = buffer[10]
                            
                            h_act = (spikes >> 4) & 0x0F
                            d_act = spikes & 0x0F
                            
                            # Update plotting histories
                            v_hidden_data.append(v_h)
                            v_output_data.append(v_o)
                            hidden_spike_data.append(h_act)
                            output_spike_data.append(d_act)
                            
                            frame_counter += 1
                            fpga_connected = True
                            last_fpga_time = time.time()
                            last_arduino_time = time.time()

                        elif pkt_len == 41:
                            # NEW PACKET (32 neurons)
                            # [v_h 0..31] (32 bytes)
                            # [v_o 0..3]  (4 bytes)
                            # [h_spike]   (4 bytes)
                            # [dir_bits]  (1 byte)
                            
                            # Hidden Potentials
                            v_h = list(buffer[2:34]) # 32 bytes
                            
                            # Output Potentials
                            v_o = list(buffer[34:38]) # 4 bytes
                            
                            # Hidden Spikes (4 bytes, Little Endian)
                            # h_spike[7:0] is at index 38
                            h_bytes = buffer[38:42]
                            h_act = int.from_bytes(h_bytes, byteorder='little')
                            
                            # Output Spikes / Dir Bits
                            d_act = buffer[42] & 0x0F
                            
                            # Update plotting histories
                            v_hidden_data.append(v_h)
                            v_output_data.append(v_o)
                            hidden_spike_data.append(h_act)
                            output_spike_data.append(d_act)
                            
                            # Log (Extended for 32 neurons would be huge, simplified logging for now)
                            if recording:
                                log_rows.append({
                                    "frame_idx": frame_counter,
                                    "timestamp": time.time(),
                                    "hidden_spikes": h_act,
                                    "dir_bits": d_act,
                                    # Add first 4 potentials for continuity
                                    "h0_v": v_h[0], "h1_v": v_h[1], "h2_v": v_h[2], "h3_v": v_h[3]
                                })

                            frame_counter += 1
                            fpga_connected = True
                            last_fpga_time = time.time()
                            last_arduino_time = time.time()
                        
                        del buffer[0:2 + pkt_len]
                        continue
                        
                    # --- Arduino Sensor Packet: [0xCC][0xDD][9 bytes][CS] ---
                    elif len(buffer) >= 12 and buffer[0] == 0xCC and buffer[1] == 0xDD:
                        # Verify Checksum
                        calc_cs = 0
                        for i in range(2, 11):
                            calc_cs ^= buffer[i]
                        
                        if calc_cs == buffer[11]:
                            s0 = (buffer[2] << 8) | buffer[3]
                            s1 = (buffer[4] << 8) | buffer[5]
                            s2 = (buffer[6] << 8) | buffer[7]
                            s3 = (buffer[8] << 8) | buffer[9]
                            btn = buffer[10]
                            
                            latest_sensors = [s0, s1, s2, s3]
                            latest_btn = btn
                            sensor_data.append(latest_sensors)
                            arduino_connected = True
                            last_arduino_time = time.time()
                        
                        del buffer[0:12]
                        continue
                        
                    else:
                        # Scan for next header
                        found = False
                        for i in range(1, len(buffer)):
                            if buffer[i] == 0xBB or (i < len(buffer)-1 and buffer[i] == 0xCC and buffer[i+1] == 0xDD):
                                del buffer[0:i]
                                found = True
                                break
                        if not found:
                            if buffer[-1] in (0xCC, 0xBB):
                                del buffer[0:-1]
                            else:
                                buffer.clear()
                        break
                            
            now = time.time()
            if now - last_fpga_time > 2.0:
                fpga_connected = False
            if now - last_arduino_time > 2.0:
                arduino_connected = False
                
            time.sleep(0.01)
            
        except Exception as e:
            print(f"Serial Error: {e}")
            break

# --- Visualization ---
def update_plot(frame):
    global log_rows
    now = time.time()
    fpga_ok = (now - last_fpga_time) <= 2.0
    arduino_ok = (now - last_arduino_time) <= 2.0

    grid_vals = np.array([
        [latest_sensors[0], latest_sensors[1]],
        [latest_sensors[2], latest_sensors[3]]
    ])
    im_sensors.set_data(grid_vals)
    for i in range(2):
        for j in range(2):
            text_annotations[i][j].set_text(str(grid_vals[i, j]))

    status_text.set_text(
        f"Arduino: {'OK' if arduino_ok else 'NO DATA'}   FPGA: {'OK' if fpga_ok else 'NO DATA'}   Raw mask: {latest_btn:05b}"
    )

    if len(output_spike_data) > 0:
        spike_vals = list(output_spike_data)
        x_off = HISTORY_LEN - len(spike_vals)
        for n in range(4):
            xs = []
            ys = []
            for t, val in enumerate(spike_vals):
                if (val >> n) & 1:
                    xs.append(x_off + t)
                    ys.append(n)
            if len(xs) == 0:
                raster_scatters[n].set_offsets(np.empty((0, 2)))
            else:
                raster_scatters[n].set_offsets(np.column_stack([xs, ys]))

    if len(v_output_data) > 0:
        v_vals = list(v_output_data)
        pad = HISTORY_LEN - len(v_vals)
        y0 = np.full(HISTORY_LEN, np.nan)
        y1 = np.full(HISTORY_LEN, np.nan)
        y2 = np.full(HISTORY_LEN, np.nan)
        y3 = np.full(HISTORY_LEN, np.nan)
        y0[pad:] = [v[0] for v in v_vals]
        y1[pad:] = [v[1] for v in v_vals]
        y2[pad:] = [v[2] for v in v_vals]
        y3[pad:] = [v[3] for v in v_vals]
        out_lines[0].set_ydata(y0)
        out_lines[1].set_ydata(y1)
        out_lines[2].set_ydata(y2)
        out_lines[3].set_ydata(y3)

    if len(output_spike_data) > 0:
        win = min(len(output_spike_data), RATE_WINDOW_FRAMES)
        counts = [0, 0, 0, 0]
        for val in list(output_spike_data)[-win:]:
            for n in range(4):
                if (val >> n) & 1:
                    counts[n] += 1
        rates = [c / win for c in counts]
        raw_x = rates[3] - rates[2]
        raw_y = rates[0] - rates[1]
        ema_vec[0] = EMA_ALPHA * raw_x + (1.0 - EMA_ALPHA) * ema_vec[0]
        ema_vec[1] = EMA_ALPHA * raw_y + (1.0 - EMA_ALPHA) * ema_vec[1]

    end_x = (ema_vec[0] / np.sqrt(2.0)) * COMPASS_RADIUS * 0.92
    end_y = (ema_vec[1] / np.sqrt(2.0)) * COMPASS_RADIUS * 0.92
    arrow_patch.set_positions((0.0, 0.0), (end_x, end_y))

    return (
        [im_sensors, status_text, arrow_patch]
        + [t for row in text_annotations for t in row]
        + raster_scatters
        + out_lines
    )

# --- Setup ---
# Start Thread
t = threading.Thread(target=read_serial, daemon=True)
t.start()

BG = "#0B1020"
PANEL = "#0F172A"
FG = "#E5E7EB"
MUTED = "#94A3B8"
ACCENT = "#38BDF8"
ACCENT_2 = "#F59E0B"

plt.rcParams.update(
    {
        "figure.facecolor": BG,
        "axes.facecolor": PANEL,
        "axes.edgecolor": PANEL,
        "axes.labelcolor": FG,
        "text.color": FG,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "font.size": 11,
        "axes.titleweight": "bold",
    }
)

fig = plt.figure(figsize=(14, 9), constrained_layout=True)
gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.6], width_ratios=[1.0, 1.0])

ax_sensors = fig.add_subplot(gs[0, 0])
im_sensors = ax_sensors.imshow([[0, 0], [0, 0]], cmap="magma", vmin=0, vmax=1023, animated=True)
ax_sensors.set_title("Inputs", loc="left")
ax_sensors.set_xticks([])
ax_sensors.set_yticks([])

text_annotations = [[None, None], [None, None]]
for i in range(2):
    for j in range(2):
        text_annotations[i][j] = ax_sensors.text(j, i, '0', ha='center', va='center',
                                                  color=FG, fontsize=16, fontweight='bold', animated=True)
cb = plt.colorbar(im_sensors, ax=ax_sensors, fraction=0.05, pad=0.02)
cb.outline.set_visible(False)
cb.ax.tick_params(colors=MUTED, labelsize=9)

RATE_WINDOW_FRAMES = 25
EMA_ALPHA = 0.22
ema_vec = np.array([0.0, 0.0], dtype=float)
COMPASS_RADIUS = 1.0

ax_dir = fig.add_subplot(gs[0, 1])
ax_dir.set_title("Direction", loc="left")
ax_dir.set_xlim(-1.15, 1.15)
ax_dir.set_ylim(-1.15, 1.15)
ax_dir.set_aspect("equal", adjustable="box")
ax_dir.axis("off")

circle = Circle((0.0, 0.0), COMPASS_RADIUS, edgecolor=MUTED, facecolor="none", linewidth=1.6, alpha=0.9)
ax_dir.add_patch(circle)
ax_dir.text(0.0, 1.10, "Front", ha="center", va="center", color=FG, fontsize=12, fontweight="bold")
ax_dir.text(0.0, -1.10, "Back", ha="center", va="center", color=FG, fontsize=12, fontweight="bold")
ax_dir.text(-1.10, 0.0, "Left", ha="center", va="center", color=FG, fontsize=12, fontweight="bold")
ax_dir.text(1.10, 0.0, "Right", ha="center", va="center", color=FG, fontsize=12, fontweight="bold")

arrow_patch = FancyArrowPatch(
    (0.0, 0.0),
    (0.0, 0.0),
    arrowstyle="Simple,tail_width=2.6,head_width=11.5,head_length=13.0",
    mutation_scale=1.0,
    linewidth=0.0,
    facecolor=ACCENT,
    edgecolor="none",
    alpha=0.95,
    animated=True,
)
ax_dir.add_patch(arrow_patch)

ax_sensors.text(
    0.02,
    -0.08,
    "",
    transform=ax_sensors.transAxes,
)
status_text = ax_sensors.text(
    0.0,
    -0.12,
    "Arduino: NO DATA   FPGA: NO DATA   Raw mask: 00000",
    transform=ax_sensors.transAxes,
    ha="left",
    va="top",
    color=MUTED,
    fontsize=10,
    animated=True,
)

gs_bottom = GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[1, :], height_ratios=[0.55, 1.0], hspace=0.18)

ax_raster = fig.add_subplot(gs_bottom[0, 0])
ax_raster.set_title("Output Spikes", loc="left")
ax_raster.set_xlim(-0.5, HISTORY_LEN - 0.5)
ax_raster.set_ylim(-0.6, 3.6)
ax_raster.set_yticks([0, 1, 2, 3])
ax_raster.set_yticklabels(["Forward", "Backward", "Left", "Right"])
ax_raster.set_xticks([])
for spine in ax_raster.spines.values():
    spine.set_visible(False)
ax_raster.grid(axis="x", color="#1F2937", linewidth=0.6, alpha=0.35)

OUT_COLORS = [ACCENT, ACCENT_2, "#A78BFA", "#34D399"]
raster_scatters = []
for n in range(4):
    sc = ax_raster.scatter([], [], s=170, marker="|", linewidths=2.4, color=OUT_COLORS[n], animated=True)
    raster_scatters.append(sc)

gs_v = GridSpecFromSubplotSpec(2, 2, subplot_spec=gs_bottom[1, 0], hspace=0.28, wspace=0.18)
out_axes = [
    fig.add_subplot(gs_v[0, 0]),
    fig.add_subplot(gs_v[0, 1]),
    fig.add_subplot(gs_v[1, 0]),
    fig.add_subplot(gs_v[1, 1]),
]
out_titles = ["Forward", "Backward", "Left", "Right"]
out_lines = []
xs = np.arange(HISTORY_LEN)
for idx, ax in enumerate(out_axes):
    ax.set_title(out_titles[idx], loc="left", fontsize=11, fontweight="bold")
    ax.set_xlim(0, HISTORY_LEN - 1)
    ax.set_ylim(0, 255)
    ax.set_xticks([])
    ax.set_yticks([0, 128, 255])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(color="#1F2937", linewidth=0.6, alpha=0.35)
    ax.axhline(OUTPUT_THRESH_8BIT, color=MUTED, linewidth=1.2, alpha=0.55)
    line, = ax.plot(xs, np.zeros(HISTORY_LEN), color=OUT_COLORS[idx], linewidth=2.0, animated=True)
    out_lines.append(line)

# --- Record / Export button ---
def toggle_record(event):
    global recording, log_rows, frame_counter
    if not recording:
        # Start a new recording session
        recording = True
        log_rows = []
        frame_counter = 0
        btn_record.label.set_text("Recording...")
    else:
        # Stop and write CSV file
        recording = False
        btn_record.label.set_text("Record OFF")
        if log_rows:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snn_log_{timestamp}.csv"
            fieldnames = list(log_rows[0].keys())
            with open(filename, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(log_rows)
            print(f"Saved recording to {filename}")

ax_btn = ax_dir.inset_axes([0.62, 0.03, 0.36, 0.14])
btn_record = Button(ax_btn, "Record OFF", color="#111827", hovercolor="#1F2937")
btn_record.on_clicked(toggle_record)

ani = animation.FuncAnimation(fig, update_plot, interval=60, blit=True,
                              cache_frame_data=False)
plt.show()
