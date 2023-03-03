#include <memory>
#include <WiFi.h>

#include "wifi_connection.h"
#include "config.h"
#include "logging.h"

WiFiConnectingState::WiFiConnectingState(StateVecFactory connectedInitialStates)
  : connectedInitialStates(connectedInitialStates) {
}

void WiFiConnectingState::enter() {
  State::enter();

  WiFi.disconnect();
  delay(1000);

  WiFi.mode(WIFI_STA);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

std::shared_ptr<State> WiFiConnectingState::loop() {
  auto status = WiFi.status();

  if (status == WL_CONNECTED) {
    log_print("WiFi connected.\n");

    auto ipStr = WiFi.localIP().toString();
    log_format("IP address: %s\n", ipStr.c_str());

    return std::make_shared<WiFiConnectedState>(connectedInitialStates);
  }

  return shared_from_this();
}

size_t WiFiConnectingState::printTo(Print& print) const {
  return print.print("connecting to WiFi (") + print.print(WIFI_SSID) + print.print(")");
};

WiFiConnectedState::WiFiConnectedState(StateVecFactory initialStates)
  : CompositeState(initialStates) {
  reconnectInitialStates = std::move(initialStates);
}

std::shared_ptr<State> WiFiConnectedState::loop() {
  if (WiFi.status() != WL_CONNECTED) {
    return std::make_shared<WiFiConnectingState>(reconnectInitialStates);
  }

  CompositeState::loop();

  return shared_from_this();
}

size_t WiFiConnectedState::printTo(Print& print) const {
  return print.print("connected to WiFi (") + print.print(WIFI_SSID) + print.print(")");
};
