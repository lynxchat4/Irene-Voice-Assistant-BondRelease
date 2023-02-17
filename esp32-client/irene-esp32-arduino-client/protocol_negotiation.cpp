#include <Arduino.h>
#include <ArduinoWebsockets.h>

#include "logging.h"
#include "protocol_negotiation.h"

auto NEGOTIATION_REQUEST_MESSAGE = F(
  "{\"type\":\"negotiate/request\",\"protocols\":["
  /* Вывод аудио и речи */
  "[\"out.audio.link\"],[\"out.tts.serverside\"]"
  /* Ввод аудио для распознания на сервере */
  ",[\"in.stt.serverside\"]"
  /* Отключение микрофона по команде с сервера */
  ",[\"in.mute\"]"
  "]}");

NegotiatingProtocolsState::NegotiatingProtocolsState(
  std::shared_ptr<websockets::WebsocketsClient> wsClient,
  StateVecFactory negotiatedStatesFactory)
  : wsClient(wsClient),
    negotiatedStatesFactory(negotiatedStatesFactory) {}

void NegotiatingProtocolsState::enter() {
  State::enter();

  String msg = NEGOTIATION_REQUEST_MESSAGE;

  wsClient->send(msg);
}

StatePtr NegotiatingProtocolsState::receiveCommand(const String& commandName, JSONVar& args) {
  if (commandName == "negotiate/agree") {
    log_println("Protocols negotiated with server.");

    return std::make_shared<ProtocolsNegotiatedState>(negotiatedStatesFactory);
  }

  log_format("Received unexpected message of type %s while negotiating protocols.", commandName);
}

size_t NegotiatingProtocolsState::printTo(Print& print) const {
  return print.print("negotiating protocols");
}

ProtocolsNegotiatedState::ProtocolsNegotiatedState(StateVecFactory nestedStatesFactory)
  : CompositeState(std::move(nestedStatesFactory)) {}

size_t ProtocolsNegotiatedState::printTo(Print& print) const {
  return print.print("protocols negotiated");
}
