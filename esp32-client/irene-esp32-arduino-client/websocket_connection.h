#include <functional>
#pragma once

#include <memory>

#include "state.h"

namespace websockets {
class WebsocketsClient;
struct WebsocketsMessage;
};

using ConnectedStateFactory = std::function<StatePtr(StatePtr reconnectState)>;

std::shared_ptr<websockets::WebsocketsClient> makeWebsocketClient();

class WebsocketConnectingState : public State {
private:
  std::shared_ptr<websockets::WebsocketsClient> wsClient;
  String path;
  ConnectedStateFactory connectedStateFactory;
public:
  WebsocketConnectingState(
    std::shared_ptr<websockets::WebsocketsClient> wsClient,
    String path,
    ConnectedStateFactory connectedStateFactory
  );

  virtual void enter();

  virtual StatePtr loop();

  virtual size_t printTo(Print& print) const;
};

class WebSocketConnectedState : public CompositeState {
private:
  StatePtr reconnectState;
  std::shared_ptr<websockets::WebsocketsClient> wsClient;
protected:
  virtual void onMessage(websockets::WebsocketsMessage)=0;
public:
  WebSocketConnectedState(
    StatePtr reconnectState,
    std::shared_ptr<websockets::WebsocketsClient> wsClient,
    StateVecFactory nestedStatesFactory
  );

  virtual void enter();
  
  virtual StatePtr loop();

  virtual size_t printTo(Print& print) const;
};

class WebSocketControlConnectionConnectedState : public WebSocketConnectedState {
protected:
  virtual void onMessage(websockets::WebsocketsMessage);
public:
  WebSocketControlConnectionConnectedState(
    StatePtr reconnectState,
    std::shared_ptr<websockets::WebsocketsClient> wsClient,
    StateVecFactory nestedStatesFactory
  );

  virtual size_t printTo(Print& print) const;
};

