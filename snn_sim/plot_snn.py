import matplotlib.pyplot as plt
import re
import os

def parse_vcd(vcd_path):
    times = []
    values = []
    
    current_time = 0
    # Map for dir_bits (ID is '!')
    # Binary string values to integer
    
    if not os.path.exists(vcd_path):
        print(f"Error: {vcd_path} not found. Run the simulation first.")
        return None, None

    with open(vcd_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                current_time = int(line[1:])
            elif line.startswith('b') and line.endswith(' !'):
                # Format: b0001 ! or b0 !
                val_str = line.split()[0][1:]
                if 'x' in val_str or 'z' in val_str:
                    continue
                val = int(val_str, 2)
                times.append(current_time / 1000.0) # Convert to us
                values.append(val)
                
    return times, values

def plot_snn():
    vcd_file = "sim/snn_dump.vcd"
    times, values = parse_vcd(vcd_file)
    
    if times is None:
        return

    # Create step plot
    plt.figure(figsize=(12, 6))
    
    # Add an end point to see the last state
    if times:
        times.append(times[-1] + 100)
        values.append(values[-1])

    plt.step(times, values, where='post', color='blue', linewidth=2)
    
    # Labels and Titles
    plt.title('SNN dir_bits Transition Over Time', fontsize=16)
    plt.xlabel('Time (us)', fontsize=12)
    plt.ylabel('dir_bits Value (Decimal)', fontsize=12)
    
    # Customize Y-axis to show specific directions
    plt.yticks([0, 1, 2, 4, 8], ['None (0)', 'Front (1)', 'Back (2)', 'Left (4)', 'Right (8)'])
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Annotate test phases
    plt.annotate('Test 1: Front', xy=(55046, 1), xytext=(60000, 1.5),
                 arrowprops=dict(facecolor='black', shrink=0.05), fontsize=10)
    plt.annotate('Test 3: Left', xy=(68788, 4), xytext=(80000, 4.5),
                 arrowprops=dict(facecolor='black', shrink=0.05), fontsize=10)
    plt.annotate('Test 4: None', xy=(233988, 0), xytext=(240000, 0.5),
                 arrowprops=dict(facecolor='black', shrink=0.05), fontsize=10)

    plt.tight_layout()
    
    plot_path = "sim/snn_plot.png"
    plt.savefig(plot_path)
    print(f"Plot saved to {plot_path}")
    plt.show()

if __name__ == "__main__":
    plot_snn()
