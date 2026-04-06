/*
 * Arduino Mega 2560 - SNN Bridge for FPGA
 * 
 * Function: 
 * 1. Bridges PC (Serial) <-> FPGA (Serial2) for Python control.
 * 2. Parses FPGA SNN results (0xBB header) and prints them to PC.
 * 3. (Optional) Reads analog sensors for autonomous driving (uncomment ENABLE_SENSORS).
 * 
 * Wiring:
 *   - PC: USB Cable
 *   - FPGA RX: Pin 16 (TX2) -> Level Shifter -> FPGA RX (V10)
 *   - FPGA TX: Pin 17 (RX2) -> Level Shifter -> FPGA TX (W10)
 *   - GND: Common Ground
 * 
 * Baud Rate: 9600 (Must match FPGA)
 */

#define ENABLE_SENSORS // Uncomment this line to enable autonomous sensor-based driving

// Sensor update period (ms). Lower = faster frames into the FPGA.
const unsigned long SENSOR_PERIOD_MS = 10;  // was ~33 Hz (30 ms), now ~100 Hz

const int SENSOR_PINS[4] = {A0, A1, A2, A3};
const int BTN_TRAIN = 9;  // Example button pins
const int BTN_LEFT  = 10;
const int BTN_FRONT = 11;
const int BTN_BACK  = 12;
const int BTN_RIGHT = 13;

void setup() {
  // Initialize USB Serial for PC
  Serial.begin(115200);
  
  // Initialize FPGA UART (Serial1) - Pin 18 (TX1), Pin 19 (RX1)
  Serial1.begin(115200); // MUST match FPGA BAUD parameter
  
  // Initialize Button Inputs
  pinMode(BTN_TRAIN, INPUT);
  pinMode(BTN_LEFT,  INPUT);
  pinMode(BTN_RIGHT, INPUT);
  pinMode(BTN_FRONT, INPUT);
  pinMode(BTN_BACK,  INPUT);
  
  Serial.println("Arduino Mega SNN Bridge Started");
  Serial.println("Listening for 0xBB packets from FPGA...");
}

unsigned long last_sensor_time = 0;

void loop() {
  // ---------------------------------------------------------
  // 1. PC -> FPGA (Forward data from PC to FPGA)
  // ---------------------------------------------------------
  while (Serial.available()) {
    uint8_t inByte = Serial.read();
    Serial1.write(inByte); // Send directly to FPGA
  }

  // ---------------------------------------------------------
  // 2. FPGA -> PC (Parse length-prefixed 0xBB Packet)
  // ---------------------------------------------------------
  // Packet Format: [0xBB] [LEN] [LEN bytes of data]
  if (Serial1.available()) {
    uint8_t b = Serial1.read();
    
    // Check for Header 0xBB
    if (b == 0xBB) {
      // Wait for length byte (with timeout)
      unsigned long start = millis();
      while (!Serial1.available()) {
        if (millis() - start > 20) break; // 20ms timeout
      }
      
      if (Serial1.available()) {
        uint8_t pkt_len = Serial1.read();
        
        // Sanity check length (max 64 bytes for extended packet)
        if (pkt_len > 0 && pkt_len <= 64) {
          uint8_t fpga_buf[64];
          uint8_t got = 0;
          unsigned long start = millis();
          
          // Read all data bytes
          while (got < pkt_len) {
            if (Serial1.available()) {
              fpga_buf[got++] = Serial1.read();
            }
            if (millis() - start > 50) break; // Timeout
          }
          
          if (got == pkt_len) {
            // Forward complete packet to PC: [0xBB][LEN][DATA...]
            Serial.write(0xBB);
            Serial.write(pkt_len);
            Serial.write(fpga_buf, pkt_len); // Write buffer at once
          }
        }
      }
    }
  }

  // ---------------------------------------------------------
  // 3. Autonomous Sensor Mode (Optional)
  // ---------------------------------------------------------
  #ifdef ENABLE_SENSORS
  // Drive frames into the FPGA at a higher rate for faster SNN dynamics.
  if (millis() - last_sensor_time > SENSOR_PERIOD_MS) {
    last_sensor_time = millis();
    sendSensorPacket();
  }
  #endif
}

// Function to read sensors and send formatted SNN packet
void sendSensorPacket() {
  // Read Analog Sensors (0-1023 -> Scale to 12-bit if needed, or send raw)
  // Protocol expects 12-bit values split into bytes.
  // s0, s1, s2, s3 are 12-bit.
  
  uint16_t s[4];
  for(int i=0; i<4; i++) {
    s[i] = analogRead(SENSOR_PINS[i]); // 10-bit value (0-1023)
  }

  // Read Buttons for Mask
  uint8_t btn_mask = 0;
  if (digitalRead(BTN_TRAIN) == HIGH) btn_mask |= 0x01; // Bit 0 = train (btn_mask[0])
  if (digitalRead(BTN_LEFT)  == HIGH) btn_mask |= 0x02; // Bit 1 = left  (btn_mask[1])
  if (digitalRead(BTN_RIGHT) == HIGH) btn_mask |= 0x04; // Bit 2 = right (btn_mask[2])
  if (digitalRead(BTN_FRONT) == HIGH) btn_mask |= 0x08; // Bit 3 = front (btn_mask[3])
  if (digitalRead(BTN_BACK)  == HIGH) btn_mask |= 0x10; // Bit 4 = back  (btn_mask[4])

  // Construct Payload
  // Byte 3: s0[11:8] + s0[7:0]
  // frame_rx.v: s0 <= {b[3][3:0], b[4]}; -> b[3] is high nibble, b[4] is low byte.
  
  uint8_t payload[9];
  payload[0] = (s[0] >> 8) & 0x0F; // s0 High
  payload[1] = s[0] & 0xFF;        // s0 Low
  payload[2] = (s[1] >> 8) & 0x0F;
  payload[3] = s[1] & 0xFF;
  payload[4] = (s[2] >> 8) & 0x0F;
  payload[5] = s[2] & 0xFF;
  payload[6] = (s[3] >> 8) & 0x0F;
  payload[7] = s[3] & 0xFF;
  payload[8] = btn_mask;

  // Calculate Checksum (XOR of payload)
  uint8_t checksum = 0;
  for(int i=0; i<9; i++) checksum ^= payload[i];

  // Send Packet to FPGA (AA 55 LEN Payload CS)
  Serial1.write(0xAA);
  Serial1.write(0x55);
  Serial1.write(0x09); // Length
  for(int i=0; i<9; i++) Serial1.write(payload[i]);
  Serial1.write(checksum);

  // Send Packet to PC (CC DD Payload CS) - For Dashboard
  // Format: [CC][DD][Payload 9 bytes][CS] -> Total 12 bytes
  Serial.write(0xCC);
  Serial.write(0xDD);
  for(int i=0; i<9; i++) Serial.write(payload[i]);
  Serial.write(checksum);
}
