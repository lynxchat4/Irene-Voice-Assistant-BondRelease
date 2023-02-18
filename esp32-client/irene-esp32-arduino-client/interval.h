#include "esp32-hal.h"
#pragma once

#include <Arduino.h>

class Interval {
private:
  unsigned long lastTick;
public:
  inline Interval()
    : lastTick(0){};

  inline bool tick(int interval) {
    unsigned long t = millis();

    if ((t - lastTick) >= interval) {
      lastTick = t;
      return true;
    }

    return false;
  }
};
