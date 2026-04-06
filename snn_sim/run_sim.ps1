# run_sim.ps1
# =============================================================================
# One-click simulation script for snn_sim
# Requires Icarus Verilog (iverilog + vvp) to be installed and on PATH
# =============================================================================

$ErrorActionPreference = "Stop"

# Move to the snn_sim root
$root = $PSScriptRoot
Set-Location $root

Write-Host "=== SNN Simulation Runner ===" -ForegroundColor Cyan

# 1. Compile
Write-Host "`n[1/3] Compiling RTL + Testbench..." -ForegroundColor Yellow
iverilog -g2012 `
    -o sim/snn_sim.vvp `
    sim/snn_tb.v `
    rtl/snn_top_uart.v `
    rtl/uart_rx.v `
    rtl/frame_rx.v `
    rtl/snn_core.v

if ($LASTEXITCODE -ne 0) {
    Write-Host "Compilation FAILED." -ForegroundColor Red; exit 1
}
Write-Host "Compilation OK." -ForegroundColor Green

# 2. Run simulation
Write-Host "`n[2/3] Running simulation..." -ForegroundColor Yellow
vvp sim/snn_sim.vvp

if ($LASTEXITCODE -ne 0) {
    Write-Host "Simulation FAILED." -ForegroundColor Red; exit 1
}
Write-Host "Simulation OK." -ForegroundColor Green

# 3. Open GTKWave
Write-Host "`n[3/3] Opening GTKWave waveform viewer..." -ForegroundColor Yellow
if (Test-Path "sim/snn_dump.vcd") {
    gtkwave sim/snn_dump.vcd
} else {
    Write-Host "VCD file not found - GTKWave skipped." -ForegroundColor Red
}
