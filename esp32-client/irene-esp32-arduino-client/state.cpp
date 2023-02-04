#include <memory>

#include <Print.h>

#include "logging.h"
#include "state.h"

State::~State() {}

void State::enter() {
  log_print("Entering state: ");
  log_println(*this);
}

void State::leave() {
  log_print("Leaving state: ");
  log_println(*this);
}

StatePtr State::loop() {
  return shared_from_this();
}

StatePtr State::receiveCommand(const String& commandName, JSONVar& args) {
  return shared_from_this();
}

size_t State::printTo(Print& print) const {
  return print.print("unknown");
}

CompositeState::CompositeState(const StateVecFactory& nestedStatesFactory) {
  auto nestedStates = nestedStatesFactory();

  nestedStateManagers.reserve(nestedStates.size());

  for (StatePtr state: nestedStates) {
    nestedStateManagers.push_back(StateManager(state));
  }
}

void CompositeState::enter() {
  State::enter();

  for (StateManager& sm: nestedStateManagers) {
    sm->enter();
  }
};

void CompositeState::leave() {
  State::leave();

  for (StateManager& sm: nestedStateManagers) {
    sm->leave();
  }
};

StatePtr CompositeState::loop() {
  for (StateManager& sm: nestedStateManagers) {
    sm.loop();
  }

  return State::loop();
};

StatePtr CompositeState::receiveCommand(const String& commandName, JSONVar& args) {
  for (StateManager& sm: nestedStateManagers) {
    sm.changeState(sm->receiveCommand(commandName, args));
  }

  return shared_from_this();
}

size_t CompositeState::printTo(Print& print) const {
  return print.print("composite");
}
