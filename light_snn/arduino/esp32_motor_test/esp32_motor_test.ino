#include <Arduino.h>

const int L_ENA = 19;
const int L_IN1 = 18;
const int L_IN2 = 5;
const int L_IN3 = 17;
const int L_IN4 = 16;
const int L_ENB = 4;

const int R_ENA = 12;
const int R_IN1 = 14;
const int R_IN2 = 27;
const int R_IN3 = 26;
const int R_IN4 = 25;
const int R_ENB = 33;

const int PWM_RES = 8; // analogWrite uses 8-bit duty by default

static inline void writeDuty(int enPin, int duty) {
  analogWrite(enPin, duty);
}

void setMotor(int enPin, int inA, int inB, int pwmCh, float s) {
  float v = s;
  if (v > 1.0f) v = 1.0f;
  if (v < -1.0f) v = -1.0f;
  if (v >= 0) {
    digitalWrite(inA, HIGH);
    digitalWrite(inB, LOW);
    int duty = (1 << PWM_RES) - 1;
    writeDuty(enPin, duty);
  } else {
    digitalWrite(inA, LOW);
    digitalWrite(inB, HIGH);
    int duty = (1 << PWM_RES) - 1;
    writeDuty(enPin, duty);
  }
}

void setLeft(float s) {
  setMotor(L_ENA, L_IN1, L_IN2, 0, s);
  setMotor(L_ENB, L_IN3, L_IN4, 0, s);
}

void setRight(float s) {
  setMotor(R_ENA, R_IN1, R_IN2, 0, s);
  setMotor(R_ENB, R_IN3, R_IN4, 0, s);
}

void setDrive(float l, float r) {
  setLeft(l);
  setRight(r);
}

void forward(float power, uint32_t ms) {
  setDrive(power, power);
  delay(ms);
  setDrive(0, 0);
}

void back(float power, uint32_t ms) {
  setDrive(-power, -power);
  delay(ms);
  setDrive(0, 0);
}

void leftTurn(float power, uint32_t ms) {
  setDrive(-power, power);
  delay(ms);
  setDrive(0, 0);
}

void rightTurn(float power, uint32_t ms) {
  setDrive(power, -power);
  delay(ms);
  setDrive(0, 0);
}

void setup() {
  Serial.begin(115200);
  pinMode(L_IN1, OUTPUT);
  pinMode(L_IN2, OUTPUT);
  pinMode(L_IN3, OUTPUT);
  pinMode(L_IN4, OUTPUT);
  pinMode(R_IN1, OUTPUT);
  pinMode(R_IN2, OUTPUT);
  pinMode(R_IN3, OUTPUT);
  pinMode(R_IN4, OUTPUT);
  pinMode(L_ENA, OUTPUT);
  pinMode(L_ENB, OUTPUT);
  pinMode(R_ENA, OUTPUT);
  pinMode(R_ENB, OUTPUT);
  setDrive(0, 0);
}

void loop() {
  float power = 1.0f;
  uint32_t ms = 1500;
  forward(power, ms);
  delay(1500);
}
