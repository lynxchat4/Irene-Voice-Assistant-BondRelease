#pragma once

#include <utility>
#include <memory>
#include <vector>
#include <cassert>
#include <functional>

#include <Printable.h>
#include <Arduino.h>

class JSONVar;

class State;

using StatePtr = std::shared_ptr<State>;
using StateVec = std::vector<StatePtr>;

using StateVecFactory = std::function<StateVec()>;

class State : public std::enable_shared_from_this<State>, public Printable {
public:
  virtual ~State();

  virtual size_t printTo(Print& print) const;

  /**
   * Вызывается когда состояние становится активным.
   */
  virtual void enter();

  /**
   * Вызывается когда состояние перестаёт быть активным.
   */
  virtual void leave();

  /**
   * Вызывается периодически когда состояние активно.
   *
   * Возвращает указатель на состояние, которое должно заменить текущее или указатель на текущее состояние, если заменять его не нужно.
   */
  virtual StatePtr loop();

  /**
   * Вызывается при получении команды от сервера.
   *
   * Возвращает указатель на состояние, которое должно заменить текущее или указатель на текущее состояние, если заменять его не нужно.
   */
  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);
};

class StateManager: std::shared_ptr<State> {
public:
  inline StateManager(StatePtr state)
    : shared_ptr(std::move(state)) {
    assert((*this) != nullptr);
  }

  /**
   * Заменяет текущее состояние на переданное.
   *
   * Не делает ничего если переданный указатель указывает на текущее состояние.
   */
  inline void changeState(StatePtr state) {
    assert(state != nullptr);

    if (state == *this) {
      return;
    }

    (*this)->leave();

    std::swap(*this, state);

    (*this)->enter();
  }

  inline State* operator -> () const {
    return &**this;
  }

  inline void loop() {
    changeState((*this)->loop());
  }
};

class CompositeState : public State {
private:
  std::vector<StateManager> nestedStateManagers;
public:
  CompositeState(const StateVecFactory& nestedStatesFactory);

  virtual void enter();

  virtual void leave();

  virtual StatePtr loop();
  
  virtual size_t printTo(Print& print) const;

  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);
};
