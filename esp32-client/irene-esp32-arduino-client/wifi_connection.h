#include <memory>
#pragma once

#include "state.h"

class WiFiConnectingState: public State {
private:
  StateVecFactory connectedInitialStates;
public:
  WiFiConnectingState(StateVecFactory connectedInitialStates);

  virtual void enter();

  virtual std::shared_ptr<State> loop();

  virtual size_t printTo(Print& print) const;
};

class WiFiConnectedState: public CompositeState {
private:
  StateVecFactory reconnectInitialStates;
public:
  WiFiConnectedState(StateVecFactory initialStates);

  virtual std::shared_ptr<State> loop();

  virtual size_t printTo(Print& print) const;
};
