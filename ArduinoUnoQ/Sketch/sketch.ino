#include <Arduino_RouterBridge.h>

// Sketch ist minimal - Audio wird über USB-Mikrofon am Linux-Teil erfasst

void setup() {
  Bridge.begin();
}

void loop() {
  delay(1000);
}