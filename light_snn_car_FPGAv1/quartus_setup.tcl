# FULL PROJECT SETUP SCRIPT for DE10-Lite SNN Car
# Run this in Quartus Tcl Console: source quartus_setup.tcl

set script_path [info script]
if {$script_path eq ""} {
    post_message "ERROR: info script is empty. Run via: source <full_path>/quartus_setup.tcl"
    return
}
set script_dir [file normalize [file dirname $script_path]]
cd $script_dir
post_message "Starting Full Project Setup in: $script_dir"

# If no project is open, try to open the generated one.
if {[llength [info commands is_project_open]] != 0 && [llength [info commands project_open]] != 0} {
    if {[catch {is_project_open} is_open] == 0 && !$is_open} {
        if {[file exists "light_snn_car.qpf"]} {
            catch {project_open -current_revision "light_snn_car"}
        } else {
            post_message "ERROR: No project open and light_snn_car.qpf not found. Run create_project.tcl first."
            return
        }
    }
}

# 1. Set Device (DE10-Lite)
set_global_assignment -name FAMILY "MAX 10"
set_global_assignment -name DEVICE 10M50DAF484C7G

# 2. Set Top Level Entity
# The module in 'snn_top_uart.v' is named 'snn_car'
set_global_assignment -name TOP_LEVEL_ENTITY snn_car

# 3. Add Design Files
# (Remove old assignments first to avoid duplicates)
set_global_assignment -name VERILOG_FILE rtl/uart_rx.v
set_global_assignment -name VERILOG_FILE rtl/uart_tx.v
set_global_assignment -name VERILOG_FILE rtl/frame_rx.v
set_global_assignment -name VERILOG_FILE rtl/snn_core.v
set_global_assignment -name VERILOG_FILE rtl/snn_top_uart.v

# 4. Apply Pin Assignments
# Clock
set_location_assignment PIN_P11 -to clk

# Reset (SW0)
set_location_assignment PIN_C10 -to rst

# UART
set_location_assignment PIN_V10 -to uart_rx
set_location_assignment PIN_W10 -to uart_tx

# Debug LEDs
set_location_assignment PIN_A8 -to leds[0]
set_location_assignment PIN_A9 -to leds[1]
set_location_assignment PIN_A10 -to leds[2]
set_location_assignment PIN_B10 -to leds[3]
set_location_assignment PIN_D13 -to leds[4]
set_location_assignment PIN_C13 -to leds[5]
set_location_assignment PIN_E14 -to leds[6]
set_location_assignment PIN_D14 -to leds[7]
set_location_assignment PIN_A11 -to leds[8]
set_location_assignment PIN_B11 -to leds[9]

# IO Standard
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to clk
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to rst
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to uart_rx
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to uart_tx
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to leds[9]

export_assignments
if {[llength [info commands project_save]] != 0} {
    project_save
} else {
    post_message "NOTE: 'project_save' not available in this Quartus version; continuing."
}
post_message "Project files in current directory:"
catch { post_message "  [glob -nocomplain *.qpf *.qsf]" }

post_message "--------------------------------------------------------"
post_message "SUCCESS! Project Configured."
post_message "1. Click 'Start Compilation' (Play Button)."
post_message "2. Open Programmer and Upload the NEW .sof file."
post_message "--------------------------------------------------------"
