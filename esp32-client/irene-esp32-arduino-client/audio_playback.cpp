#include "esp32-hal-gpio.h"
#include "logging.h"
#include "config.h"
#include <memory>
#include <Arduino.h>
#include <ArduinoWebsockets.h>
#include <Arduino_JSON.h>
#include <Audio.h>

#include "audio_playback.h"

void audio_info(const char* info) {
  log_print("audio_info: ");
  log_println(info);
}

/*
Изначально я хотел создавать объект Audio только в состоянии AudioPlaybackProgressState, чтобы он не занимал место в памяти когда не нужен.
Однако, MAX98357A ведёт себя нестабильно если интерфейс I2S включать и выключать - иногда воспроизведение работает нормально, иногда начинается с щелчком,
иногда вообще не происходит (предположительно, MAX98357A переходит в рехим TDM) при том, что все сигналы I2S на месте. Передёргивание сигнала SD_MODE не помогает.
Библиотека Audio не позволяет отделить инициализацию I2S от создания объекта Audio, так что объект пришлось сделать глобальным.
 */
static Audio audio = Audio(false, 3, OUT_I2S_PORT);

void audioPlaybackInit() {
  audio.setPinout(OUT_I2S_BCLK, OUT_I2S_LRC, OUT_I2S_DOUT);
  audio.setVolume(PLAYBACK_VOLUME);
};

AudioPlaybackReadyState::AudioPlaybackReadyState(std::shared_ptr<websockets::WebsocketsClient> wsClient)
  : wsClient(wsClient){};

StatePtr AudioPlaybackReadyState::receiveCommand(const String& commandName, JSONVar& args) {
  if (commandName == "out.audio.link/playback-request") {
    return std::make_shared<AudioPlaybackProgressState>(
      wsClient,
      args["url"],
      args["playbackId"]);
  }

  return shared_from_this();
};

size_t AudioPlaybackReadyState::printTo(Print& print) const {
  return print.print("ready to play audio");
}

static String makePlaybackProgressMessage(const String& playbackId) {
  JSONVar msg;

  msg["type"] = "out.audio.link/playback-progress";
  msg["playbackId"] = playbackId;

  return JSON.stringify(msg);
}

static String makePlaybackEndMessage(const String& playbackId) {
  JSONVar msg;

  msg["type"] = "out.audio.link/playback-done";
  msg["playbackId"] = playbackId;

  return JSON.stringify(msg);
}

static String makeCanonicalPlaybackURL(const String& url) {
  // TODO: Do not modify URL when it is a full URL if server will be able to send such URLs

  String result;

  result += SERVER_HOSTNAME;
  result += ":";
  result += SERVER_PORT;
  result += url;

  return result;
}

AudioPlaybackProgressState::AudioPlaybackProgressState(
  std::shared_ptr<websockets::WebsocketsClient> wsClient,
  String url,
  String playbackId)
  : wsClient(wsClient), playbackId(playbackId), url(makeCanonicalPlaybackURL(url)), playbackNotificationMessage(makePlaybackProgressMessage(playbackId)) {}

void AudioPlaybackProgressState::enter() {
  State::enter();

  audio.connecttohost(url.c_str());
}

void AudioPlaybackProgressState::leave() {
  State::leave();

  wsClient->send(makePlaybackEndMessage(playbackId));

  audio.stopSong();
}

StatePtr AudioPlaybackProgressState::loop() {
  if (notificationInterval.tick(1000)) {
    wsClient->send(playbackNotificationMessage);
    log_format("sent ping message for playback %s\n", playbackId.c_str());
  }

  audio.loop();

  // TODO: Похоже, иногда isRunning() возвращает некорректное значение и устройство зависает в этом состоянии.
  if (!audio.isRunning()) {
    return std::make_shared<AudioPlaybackReadyState>(wsClient);
  }

  return shared_from_this();
}

size_t AudioPlaybackProgressState::printTo(Print& print) const {
  return print.print("playing audio from ") + print.print(url);
}
