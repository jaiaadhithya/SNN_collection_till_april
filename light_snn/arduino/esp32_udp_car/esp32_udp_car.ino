#include <WiFi.h>
#include <WiFiUdp.h>
#include <ctype.h>

const char* WIFI_SSID = "snn_car";
const char* WIFI_PASS = "12345678";
const int UDP_PORT = 12345;

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

WiFiUDP udp;
WiFiServer server(12345);
char buf[512];
#if defined(LED_BUILTIN)
const int STATUS_LED = LED_BUILTIN;
#else
const int STATUS_LED = -1;
#endif

static bool boot_test_done = false;

void setMotor(int enPin, int inA, int inB, int pwmCh, float s) {
  float v = s;
  if (v > 1.0f) v = 1.0f;
  if (v < -1.0f) v = -1.0f;
  bool on = (v > 0.01f) || (v < -0.01f);
  if (v >= 0) {
    digitalWrite(inA, HIGH);
    digitalWrite(inB, LOW);
  } else {
    digitalWrite(inA, LOW);
    digitalWrite(inB, HIGH);
  }
  digitalWrite(enPin, on ? HIGH : LOW);
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

float parsePower(const String& s) {
  int i = s.indexOf("\"power\":");
  if (i < 0) return 0.5f;
  int j = i + 8;
  while (j < s.length() && (s[j] == ' ' || s[j] == '"')) j++;
  int k = j;
  while (k < s.length() && (isdigit(s[k]) || s[k] == '.' || s[k] == '-')) k++;
  return s.substring(j, k).toFloat();
}

String parseDir(const String& s) {
  int i = s.indexOf("\"dir\":");
  if (i < 0) return String("FRONT");
  int j = s.indexOf('"', i + 6);
  if (j < 0) return String("FRONT");
  int k = s.indexOf('"', j + 1);
  if (k < 0) return String("FRONT");
  return s.substring(j + 1, k);
}

bool isMove(const String& s) {
  int i = s.indexOf("\"cmd\"");
  if (i < 0) return false;
  int colon = s.indexOf(':', i);
  if (colon < 0) return false;
  int q1 = s.indexOf('"', colon);
  if (q1 < 0) return false;
  int q2 = s.indexOf('"', q1 + 1);
  if (q2 < 0) return false;
  String v = s.substring(q1 + 1, q2);
  v.toUpperCase();
  return v == "MOVE";
}

bool isStop(const String& s) {
  int i = s.indexOf("\"cmd\"");
  if (i < 0) return false;
  int colon = s.indexOf(':', i);
  if (colon < 0) return false;
  int q1 = s.indexOf('"', colon);
  if (q1 < 0) return false;
  int q2 = s.indexOf('"', q1 + 1);
  if (q2 < 0) return false;
  String v = s.substring(q1 + 1, q2);
  v.toUpperCase();
  return v == "STOP";
}

void setup() {
  Serial.begin(115200);
  if (STATUS_LED >= 0) {
    pinMode(STATUS_LED, OUTPUT);
    digitalWrite(STATUS_LED, LOW);
  }
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
  WiFi.mode(WIFI_AP);
  WiFi.softAP(WIFI_SSID, WIFI_PASS);
  WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
  IPAddress ip = WiFi.softAPIP();
  Serial.print("AP IP: ");
  Serial.println(ip);
  Serial.print("UDP port: ");
  Serial.println(UDP_PORT);
  udp.begin(UDP_PORT);
  server.begin();
}

void loop() {
  if (!boot_test_done) {
    setDrive(1.0f, 1.0f);
    delay(800);
    setDrive(0.0f, 0.0f);
    boot_test_done = true;
  }
  int p = udp.parsePacket();
  if (p > 0) {
    int n = udp.read((uint8_t*)buf, sizeof(buf) - 1);
    if (n > 0) {
      buf[n] = 0;
      String s = String(buf);
      if (isStop(s)) {
        setDrive(0, 0);
        if (STATUS_LED >= 0) digitalWrite(STATUS_LED, LOW);
        Serial.println("STOP");
        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        udp.print("ACK STOP\n");
        udp.endPacket();
      } else if (isMove(s)) {
        float pow = parsePower(s);
        String dir = parseDir(s);
        Serial.print("MOVE ");
        Serial.print(dir);
        Serial.print(" ");
        Serial.println(pow);
        if (STATUS_LED >= 0) digitalWrite(STATUS_LED, HIGH);
        if (dir == "FRONT") {
          setDrive(pow, pow);
        } else if (dir == "BACK") {
          setDrive(-pow, -pow);
        } else if (dir == "LEFT") {
          setDrive(-pow, pow);
        } else if (dir == "RIGHT") {
          setDrive(pow, -pow);
        } else {
          setDrive(0, 0);
        }
        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        udp.print("ACK MOVE ");
        udp.print(dir);
        udp.print(" ");
        udp.print(pow, 2);
        udp.print("\n");
        udp.endPacket();
      } else {
        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        udp.print("ACK UNKNOWN\n");
        udp.endPacket();
      }
    }
  }
  WiFiClient c = server.available();
  if (c) {
    c.setTimeout(500);
    unsigned long t0 = millis();
    while (!c.available() && millis() - t0 < 500) { delay(1); }
    if (c.available()) {
      int n = c.readBytes(buf, sizeof(buf) - 1);
      if (n > 0) {
        buf[n] = 0;
        String s = String(buf);
        Serial.println(s);
        if (isStop(s)) {
          setDrive(0, 0);
          if (STATUS_LED >= 0) digitalWrite(STATUS_LED, LOW);
          c.println("ACK STOP");
          c.flush();
        } else if (isMove(s)) {
          float pow = parsePower(s);
          String dir = parseDir(s);
          if (STATUS_LED >= 0) digitalWrite(STATUS_LED, HIGH);
          if (dir == "FRONT") {
            setDrive(pow, pow);
          } else if (dir == "BACK") {
            setDrive(-pow, -pow);
          } else if (dir == "LEFT") {
            setDrive(-pow, pow);
          } else if (dir == "RIGHT") {
            setDrive(pow, -pow);
          } else {
            setDrive(0, 0);
          }
          c.print("ACK MOVE ");
          c.print(dir);
          c.print(" ");
          c.println(pow, 2);
          c.flush();
        } else {
          c.println("ACK UNKNOWN");
          c.flush();
        }
      }
      delay(300);
      c.stop();
    } else {
      c.stop();
    }
  }
}
