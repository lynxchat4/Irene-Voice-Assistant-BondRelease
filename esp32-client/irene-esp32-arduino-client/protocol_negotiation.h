#pragma once

#include "state.h"

namespace websockets {
class WebSocketsClient;
struct WebsocketsMessage;
};

class NegotiatingProtocolsState : public State {
private:
  std::shared_ptr<websockets::WebsocketsClient> wsClient;
  StateVecFactory negotiatedStatesFactory;
public:
  NegotiatingProtocolsState(std::shared_ptr<websockets::WebsocketsClient> wsClient, StateVecFactory negotiatedStatesFactory);

  virtual void enter();

  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);

  virtual size_t printTo(Print& print) const;
};

class ProtocolsNegotiatedState : public CompositeState {
public:
  ProtocolsNegotiatedState(StateVecFactory nestedStatesFactory);

  virtual size_t printTo(Print& print) const;
};
