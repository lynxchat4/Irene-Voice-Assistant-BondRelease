#include <Arduino.h>
#include <WiFi.h>
#include <Audio.h>
#include <Arduino_JSON.h>

#include "config.h"
#include "state.h"
#include "wifi_connection.h"

class PlayerState: public State {
private:
  std::unique_ptr<Audio> audio;
public:
  virtual void enter() {
    State::enter();

    audio.reset(new Audio());

    audio->setPinout(OUT_I2S_BCLK, OUT_I2S_LRC, OUT_I2S_DOUT);
    audio->setVolume(10);
    audio->connecttohost("0n-80s.radionetz.de:8000/0n-70s.mp3");
  }

  virtual void leave() {
    State::leave();

    audio.reset(nullptr);
  }

  virtual std::shared_ptr<State> loop() {
    audio->loop();

    return shared_from_this();
  }

  virtual size_t printTo(Print& print) const {
    return print.print("playing");
  };
};

StateVec makeWiFiConnectedStates() {
  return {
    std::make_shared<PlayerState>()
  };
}

StateManager rootState(std::make_shared<WiFiConnectingState>(makeWiFiConnectedStates));

void setup() {
  Serial.begin(921600);
  Serial.println("\n\nStarting...");

  rootState->enter();
}

void loop() {
  rootState.loop();
}
