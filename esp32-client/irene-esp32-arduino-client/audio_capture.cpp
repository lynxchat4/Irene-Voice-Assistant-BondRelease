#include <memory>

#include <driver/i2s.h>

#include <Arduino_JSON.h>
#include <ArduinoWebsockets.h>

#include "state.h"
#include "logging.h"
#include "audio_capture.h"

static String addCaptureURLParameters(const String& path) {
  return path + "?sample_rate=" + IN_SAMPLE_RATE;
};

AudioCaptureWaiting::AudioCaptureWaiting()
  : captureContext(std::make_shared<CaptureContext>(makeWebsocketClient())){};

StatePtr AudioCaptureWaiting::receiveCommand(const String& commandName, JSONVar& args) {
  if (commandName == "in.stt.serverside/ready") {
    String path = addCaptureURLParameters(args["path"]);

    return std::make_shared<AudioCaptureConnecting>(captureContext, path);
  } else {
    captureContext->acceptCommand(commandName);
  }

  return shared_from_this();
};

size_t AudioCaptureWaiting::printTo(Print& print) const {
  return print.print("waiting for audio capture web-socket address");
};

AudioCaptureConnecting::AudioCaptureConnecting(CaptureContextPtr captureContext, const String& path)
  : WebsocketConnectingState(captureContext->getWsClient(), path, [captureContext](StatePtr reconnectState) {
      return std::make_shared<AudioCaptureConnected>(reconnectState, captureContext);
    }),
    captureContext(captureContext){};

StatePtr AudioCaptureConnecting::receiveCommand(const String& commandName, JSONVar& args) {
  captureContext->acceptCommand(commandName);
};

size_t AudioCaptureConnecting::printTo(Print& print) const {
  return print.print("connecting to audio capture web-socket");
};

static StateVecFactory makeConnectedStatesFactory(const CaptureContextPtr captureContext) {
  return [captureContext]() -> StateVec {
    return {
      captureContext->isMuted() ? (StatePtr)std::make_shared<AudioCaptureMuted>(captureContext) : (StatePtr)std::make_shared<AudioCapturing>(captureContext)
    };
  };
};

AudioCaptureConnected::AudioCaptureConnected(
  StatePtr reconnectState,
  CaptureContextPtr captureContext)
  : WebSocketConnectedState(reconnectState, captureContext->getWsClient(), makeConnectedStatesFactory(captureContext)){};

void AudioCaptureConnected::onMessage(websockets::WebsocketsMessage msg) {
  log_println("Unexpected inbound message on audio capture websocket");
};

size_t AudioCaptureConnected::printTo(Print& print) const {
  return print.print("audio capture web-socket connected");
};

AudioCapturing::AudioCapturing(CaptureContextPtr captureContext)
  : captureContext(captureContext){};

void AudioCapturing::enter() {
  State::enter();
  // TODO:: Setup driver, prepare buffers, etc
};

void AudioCapturing::leave() {
  State::leave();
  // TODO:: Shutdown driver, free buffers, etc
};

StatePtr AudioCapturing::loop() {
  // TODO:: Get data from I2S, send it to websocket

  return shared_from_this();
};

StatePtr AudioCapturing::receiveCommand(const String& commandName, JSONVar& args) {
  if (commandName == "in.mute/mute") {
    captureContext->setMuted(true);

    return std::make_shared<AudioCaptureMuted>(captureContext);
  }

  return shared_from_this();
};

size_t AudioCapturing::printTo(Print& print) const {
  return print.print("capturing audio");
};

AudioCaptureMuted::AudioCaptureMuted(CaptureContextPtr captureContext)
  : captureContext(captureContext){};

StatePtr AudioCaptureMuted::receiveCommand(const String& commandName, JSONVar& args) {
  if (commandName == "in.mute/unmute") {
    captureContext->setMuted(false);

    return std::make_shared<AudioCapturing>(captureContext);
  }

  return shared_from_this();
};

size_t AudioCaptureMuted::printTo(Print& print) const {
  return print.print("audio capture muted");
};
