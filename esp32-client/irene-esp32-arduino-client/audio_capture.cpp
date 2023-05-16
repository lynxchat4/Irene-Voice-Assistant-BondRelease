#include "hal/i2s_types.h"
#include <memory>

#include <driver/i2s.h>
#include <driver/adc.h>

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

  sendBuffer.resize(IN_SEND_BUFFER_SIZE * 2);
  sendBufferFilled = 0;

  i2s_config_t conf = {
#ifdef IN_I2S_BUILTIN
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_ADC_BUILT_IN),
#else
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
#endif
    .sample_rate = IN_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = 0,
    .dma_buf_count = IN_DMA_BUFFER_COUNT,
    .dma_buf_len = IN_DMA_BUFFER_SIZE,
    .use_apll = false,
  };

  i2s_driver_install(IN_I2S_PORT, &conf, 0, nullptr);

#ifdef IN_I2S_BUILTIN
  i2s_set_adc_mode(ADC_UNIT_1, IN_ADC_CHANNEL);

  adc1_config_channel_atten(IN_ADC_CHANNEL, IN_ADC_ATTEN);

  i2s_adc_enable(IN_I2S_PORT);
#else
  i2s_pin_config_t pin_conf = {
    .mck_io_num = I2S_PIN_NO_CHANGE,
    .bck_io_num = IN_I2S_BCLK,
    .ws_io_num = IN_I2S_LRC,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = IN_I2S_DIN,
  };

  i2s_set_pin(IN_I2S_PORT, &pin_conf);
#endif
};

void AudioCapturing::leave() {
  State::leave();

  i2s_adc_disable(IN_I2S_PORT);

  i2s_driver_uninstall(IN_I2S_PORT);
};

StatePtr AudioCapturing::loop() {
  size_t bytesRead = 0;

  i2s_read(IN_I2S_PORT, &sendBuffer[sendBufferFilled], sendBuffer.size() - sendBufferFilled, &bytesRead, 0);

  sendBufferFilled += bytesRead;

  if (sendBufferFilled >= sendBuffer.size()) {
    captureContext->getWsClient()->sendBinary((const char*)&sendBuffer[0], sendBuffer.size());

    sendBufferFilled = 0;
  }

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
