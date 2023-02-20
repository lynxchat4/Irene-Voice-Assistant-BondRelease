#include "esp32-hal.h"
#include <memory>
#include "state.h"
#include <ArduinoWebsockets.h>
#include <Arduino_JSON.h>

#include "config.h"
#include "logging.h"

#include "websocket_connection.h"

std::shared_ptr<websockets::WebsocketsClient> makeWebsocketClient() {
  return std::make_shared<websockets::WebsocketsClient>();  
}

WebsocketConnectingState::WebsocketConnectingState(
  std::shared_ptr<websockets::WebsocketsClient> wsClient,
  String path,
  ConnectedStateFactory connectedStateFactory)
  : wsClient(std::move(wsClient)),
    path(std::move(path)),
    connectedStateFactory(connectedStateFactory){};

void WebsocketConnectingState::enter() {
  State::enter();

  wsClient->close();
}

StatePtr WebsocketConnectingState::loop() {
  bool connected = wsClient->connect(SERVER_HOSTNAME, SERVER_PORT, path);

  if (connected) {
    log_format("Connected to web-socket at %s\n", path.c_str());

    return connectedStateFactory(shared_from_this());
  }

  log_format("Could not connect to web-socket at %s\n", path.c_str());

  delay(WEBSOCKET_RECONNECT_INTERVAL);

  return shared_from_this();
};

size_t WebsocketConnectingState::printTo(Print& print) const {
  return print.print("connecting to websocket at ") + print.print(path);
};


WebSocketConnectedState::WebSocketConnectedState(
  StatePtr reconnectState,
  std::shared_ptr<websockets::WebsocketsClient> wsClient,
  StateVecFactory nestedStatesFactory)
  : CompositeState(nestedStatesFactory), reconnectState(reconnectState), wsClient(wsClient){};

void WebSocketConnectedState::enter() {
  CompositeState::enter();

  std::weak_ptr<WebSocketConnectedState> weak_this = std::static_pointer_cast<WebSocketConnectedState>(shared_from_this());
  wsClient->onMessage([weak_this](websockets::WebsocketsMessage msg) {
    if (std::shared_ptr<WebSocketConnectedState> shared_this = weak_this.lock()) {
      shared_this->onMessage(std::move(msg));
    }
  });

  wsClient->ping();
}

StatePtr WebSocketConnectedState::loop() {
  wsClient->poll();

  if (!wsClient->available()) {
    log_println("Lost connection to websocket");

    delay(WEBSOCKET_RECONNECT_INTERVAL_AFTER_DISCONNECT);

    return reconnectState;
  }

  return CompositeState::loop();
}

size_t WebSocketConnectedState::printTo(Print& print) const {
  return print.print("connected to websocket");
};


WebSocketControlConnectionConnectedState::WebSocketControlConnectionConnectedState(
  StatePtr reconnectState,
  std::shared_ptr<websockets::WebsocketsClient> wsClient,
  StateVecFactory nestedStatesFactory)
  : WebSocketConnectedState(reconnectState, wsClient, nestedStatesFactory){};

void WebSocketControlConnectionConnectedState::onMessage(websockets::WebsocketsMessage message) {
  if (!message.isComplete()) {
    // TODO: обрабатывать фрагментированные сообщения
    log_println("Unexpected incomplete message");

    return;
  }

  if (!message.isText()) {
    return;
  }

  JSONVar parsed = JSON.parse(message.c_str());

  JSONVar messageType = parsed["type"];

  if (JSONVar::typeof_(messageType) != "string") {
    log_print("Invalid control connection inbound message: ");
    log_println(JSONVar::stringify(parsed));
    return;
  }

  CompositeState::receiveCommand(messageType, parsed);
};

size_t WebSocketControlConnectionConnectedState::printTo(Print& print) const {
  return print.print("connected to control websocket");
};
