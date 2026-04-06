#include <Arduino.h>

// Row-major order: (0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)
const uint8_t SENSOR_PINS[9] = {A15, A3, A0, A14, A4, A1, A13, A5, A2};
const uint8_t BTN_TRAIN = 9;
const uint8_t BTN_LEFT  = 10;
const uint8_t BTN_FRONT = 11;
const uint8_t BTN_BACK  = 12;
const uint8_t BTN_RIGHT = 13;

const uint32_t BAUD = 9600;
const uint16_t FRAME_INTERVAL_MS = 20;
const uint8_t DEBUG_TEXT = 0;

uint8_t readButtonsMask() {
  uint8_t train = (digitalRead(BTN_TRAIN) == LOW) ? 0x01 : 0x00;
  uint8_t left  = (digitalRead(BTN_LEFT)  == LOW) ? 0x02 : 0x00;
  uint8_t right = (digitalRead(BTN_RIGHT) == LOW) ? 0x04 : 0x00;
  uint8_t front = (digitalRead(BTN_FRONT) == LOW) ? 0x08 : 0x00;
  uint8_t back  = (digitalRead(BTN_BACK)  == LOW) ? 0x10 : 0x00;
  return train | left | right | front | back;
}

void setup() {
  pinMode(BTN_TRAIN, INPUT_PULLUP);
  pinMode(BTN_LEFT,  INPUT_PULLUP);
  pinMode(BTN_FRONT, INPUT_PULLUP);
  pinMode(BTN_BACK,  INPUT_PULLUP);
  pinMode(BTN_RIGHT, INPUT_PULLUP);
  Serial.begin(BAUD);
}

void loop() {
  uint16_t sensors12[9];
  for (uint8_t i = 0; i < 9; i++) {
    uint16_t v10 = analogRead(SENSOR_PINS[i]);
    sensors12[i] = (uint16_t)(v10 << 2);
  }
  uint8_t mask = readButtonsMask();
  if (DEBUG_TEXT) {
    Serial.print("AA55 ");
    for (uint8_t i = 0; i < 9; i++) {
      Serial.print(sensors12[i]);
      if (i < 8) Serial.print(",");
    }
    Serial.print(" ");
    Serial.println(mask);
  } else {
    Serial.write(0xAA);
    Serial.write(0x55);
    for (uint8_t i = 0; i < 9; i++) {
      uint8_t hi = (uint8_t)((sensors12[i] >> 8) & 0xFF);
      uint8_t lo = (uint8_t)(sensors12[i] & 0xFF);
      Serial.write(hi);
      Serial.write(lo);
    }
    Serial.write(mask);
  }

  delay(FRAME_INTERVAL_MS);
}
