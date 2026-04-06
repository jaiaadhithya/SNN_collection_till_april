# AUTOMATED PROJECT CREATION SCRIPT
# Run this in Quartus Tcl Console: source create_project.tcl

# Ensure we operate relative to this script's directory (so files are found and
# the project is created next to the RTL).
set script_path [info script]
if {$script_path eq ""} {
    post_message "ERROR: info script is empty. Run via: source <full_path>/create_project.tcl"
    return
}
set script_dir [file normalize [file dirname $script_path]]
cd $script_dir
post_message "Using script directory: $script_dir"

# 1. Define Project Name
set project_name "light_snn_car"
set top_entity "snn_car"

# 2. Close any open project and clean up
post_message "Attempting to close any open project..."
if {[is_project_open]} {
    if {[catch {project_close} err]} {
        post_message "WARNING: Could not close project automatically: $err"
        post_message "Please manually close the project (File -> Close Project) and re-run this script."
    }
}

# 2.1 Delete old project files to avoid locks
set files_to_clean {light_snn_car.qpf light_snn_car.qsf db incremental_db}
foreach f $files_to_clean {
    if {[file exists $f]} {
        post_message "Deleting old '$f'..."
        if {[catch {file delete -force -- $f} err]} {
             post_message "ERROR: Could not delete '$f'. It might be open or locked by OneDrive."
             post_message "Please close Quartus, delete the 'db' and 'incremental_db' folders manually, then reopen Quartus."
             return
        }
    }
}

# 3. Create New Project
project_new ${project_name} -revision ${project_name} -overwrite
project_open -current_revision ${project_name}

post_message "Project ${project_name} created/opened."

# 4. Device Settings
set_global_assignment -name FAMILY "MAX 10"
set_global_assignment -name DEVICE 10M50DAF484C7G
set_global_assignment -name TOP_LEVEL_ENTITY ${top_entity}

# 5. Add Files
set_global_assignment -name VERILOG_FILE rtl/uart_rx.v
set_global_assignment -name VERILOG_FILE rtl/uart_tx.v
set_global_assignment -name VERILOG_FILE rtl/frame_rx.v
set_global_assignment -name VERILOG_FILE rtl/snn_core.v
set_global_assignment -name VERILOG_FILE rtl/snn_top_uart.v

# 6. Pin Assignments
# Clock & Reset
set_location_assignment PIN_P11 -to clk
set_location_assignment PIN_C10 -to rst

# UART
set_location_assignment PIN_V10 -to uart_rx
set_location_assignment PIN_W10 -to uart_tx

# Debug LEDs (LEDR0-9)
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

# IO Standard (3.3-V LVTTL)
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

# 7. Commit & Export
export_assignments
if {[llength [info commands project_save]] != 0} {
    project_save
} else {
    post_message "NOTE: 'project_save' not available in this Quartus version; continuing."
}
post_message "Created project files (should exist now):"
catch { post_message "  [glob -nocomplain *.qpf *.qsf]" }
post_message "--------------------------------------------------------"
post_message "PROJECT CREATED SUCCESSFULLY!"
post_message "Now click 'Start Compilation' (Play Button)."
post_message "--------------------------------------------------------"
