* SPICE Testbench for On-Chip Learning (STDP / Hebbian-like)
* Demonstrates Potentiation and Depression

.include "memristor_model.sp"

* Circuit Definition
* Voltage Source connected to Memristor
Vtrain input 0 PULSE(0 1 1ms 1ns 1ns 5ms 10ms)

* The Memristor
Xmem input 0 memristor

* Simulation Command
.tran 10u 50ms

* Measurements (Resistance Calculation)
.print tran V(input) I(Xmem) Rmem=PAR('V(input)/I(Xmem)')

.end
