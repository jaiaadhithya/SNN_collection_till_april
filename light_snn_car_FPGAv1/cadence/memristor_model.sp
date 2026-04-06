* Memristor SPICE Subcircuit
* Based on VTEAM model approximation
* Terminals: P (Positive), N (Negative)

.subckt memristor P N
    * Parameters
    .param Ron=100
    .param Roff=10k
    .param Rinit=5k
    .param D=10n
    .param uv=10n
    .param p=1
    
    * State integration capacitor (Voltage across Cmem represents state 'w')
    Cmem state 0 1nIC={ (Rinit-Ron)/(Roff-Ron) }
    
    * Resistor to avoid floating node
    Rdummy state 0 100G
    
    * State equation implementation (Behavioral Source)
    * I(Cmem) = dw/dt
    * If V(P,N) > Vth_off -> Resistance Increases (Depression)
    * If V(P,N) < Vth_on  -> Resistance Decreases (Potentiation)
    
    Bstate 0 state I = ((V(P,N) > 0.5) * 1e4 * (1-V(state))) + ((V(P,N) < -0.5) * -1e4 * V(state))
    
    * Variable Resistor implementation
    * R = Ron + (Roff - Ron) * State
    Gmem P N value = { V(P,N) / (Ron + (Roff - Ron) * V(state)) }

.ends memristor
