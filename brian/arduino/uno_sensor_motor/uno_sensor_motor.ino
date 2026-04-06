#include <Arduino.h>

#define GRID_SIZE 2
#define N_CH 4
const uint8_t pins[N_CH] = {A0, A1, A2, A3};

const uint8_t ENA = 5;
const uint8_t ENB = 6;
const uint8_t IN1 = 7;
const uint8_t IN2 = 8;
const uint8_t IN3 = 9;
const uint8_t IN4 = 10;

void setup() {
  Serial.begin(115200);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void sendSensors() {
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
    Serial.write((uint8_t)((vals[i] >> 8) & 0xFF));
    Serial.write((uint8_t)(vals[i] & 0xFF));
  }
}

bool readMotorCmd(uint16_t &left, uint16_t &right) {
  if (Serial.available() < 6) return false;
  if (Serial.peek() != 0xAC) { Serial.read(); return false; }
  Serial.read();
  if (Serial.read() != 0x53) return false;
  uint8_t h1 = Serial.read();
  uint8_t l1 = Serial.read();
  uint8_t h2 = Serial.read();
  uint8_t l2 = Serial.read();
  left  = ((uint16_t)(h1 & 0x03) << 8) | l1;
  right = ((uint16_t)(h2 & 0x03) << 8) | l2;
  return true;
}

void loop() {
  static uint32_t t0 = 0;
  if (millis() - t0 > 10) { t0 = millis(); sendSensors(); }
  uint16_t dl, dr;
  if (readMotorCmd(dl, dr)) {
    uint8_t pwmL = (dl > 1023 ? 255 : (dl >> 2));
    uint8_t pwmR = (dr > 1023 ? 255 : (dr >> 2));
    analogWrite(ENA, pwmL);
    analogWrite(ENB, pwmR);
  }
}

