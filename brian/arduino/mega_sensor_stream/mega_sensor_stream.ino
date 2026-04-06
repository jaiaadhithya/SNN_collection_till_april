#include <Arduino.h>

#define GRID_SIZE 2  // set to 3 for 3x3; 2 for 2x2

#if GRID_SIZE == 2
const uint8_t pins[4] = {A0, A1, A2, A3};
#define N_CH 4
#elif GRID_SIZE == 3
const uint8_t pins[9] = {A0, A1, A2, A3, A4, A5, A6, A7, A8};
#define N_CH 9
#else
#error Unsupported GRID_SIZE
#endif

void setup() {
  Serial.begin(115200);
}

void loop() {
  uint16_t vals[N_CH];
  for (uint8_t i = 0; i < N_CH; i++) {
    int v = analogRead(pins[i]);
    if (v < 0) v = 0;
    if (v > 1023) v = 1023;
    vals[i] = (uint16_t)(v << 2);
  }
  Serial.write(0xAA);
  Serial.write(0x55);
  for (uint8_t i = 0; i < N_CH; i++) {
    uint8_t hi = (uint8_t)((vals[i] >> 8) & 0xFF);
    uint8_t lo = (uint8_t)(vals[i] & 0xFF);
    Serial.write(hi);
    Serial.write(lo);
  }
  delay(5);
}
