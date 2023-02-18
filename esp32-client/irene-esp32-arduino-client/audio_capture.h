#pragma once

#include <memory>

#include "state.h"
#include "websocket_connection.h"

class CaptureContext : public std::enable_shared_from_this<CaptureContext> {
private:
  bool muted;
  std::shared_ptr<websockets::WebsocketsClient> wsClient;
public:
  CaptureContext(std::shared_ptr<websockets::WebsocketsClient> wsClient)
    : muted(false), wsClient(wsClient){};

  inline bool isMuted() const {
    return muted;
  };

  inline void setMuted(bool muted) {
    this->muted = muted;
  };

  inline void acceptCommand(const String& command) {
    if (command == "in.mute/mute") {
      muted = true;
    } else if (command == "in.mute/unmute") {
      muted = false;
    };
  };

  inline std::shared_ptr<websockets::WebsocketsClient> getWsClient() {
    return wsClient;
  };
};

using CaptureContextPtr = std::shared_ptr<CaptureContext>;

/**
 * Ожидаем сообщения типа "in.stt.serverside/ready", чтобы, взяв из него путь, начать подключение к вебсокету для передачи аудио-данных.
 *
 * Пока сообщение не получено, запоминаем, должен ли микрофон быть включён - реагируя на коменды "in.mute/mute" и "in.mute/unmute".
 */
class AudioCaptureWaiting : public State {
private:
  CaptureContextPtr captureContext;
public:
  AudioCaptureWaiting();

  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);

  virtual size_t printTo(Print& print) const;
};

/**
 * Подключаемся к вебсокету для передачи аудио-данных.
 *
 * Всё ещё реагируем на команды "in.mute/mute" и "in.mute/unmute", чтобы знать, нужно ли будет включить микрофон сразу после успешного подключения. 
 */
class AudioCaptureConnecting : public WebsocketConnectingState {
private:
  CaptureContextPtr captureContext;
public:
  AudioCaptureConnecting(CaptureContextPtr captureContext, const String& path);

  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);

  virtual size_t printTo(Print& print) const;
};

/**
 * Веб-сокет для передачи аудио-данных подключен, микрофон включен или выключен в зависимости от вложенных состояний - AudioCapturing или AudioCaptureMuted.
 */
class AudioCaptureConnected : public WebSocketConnectedState {
protected:
  virtual void onMessage(websockets::WebsocketsMessage);
public:
  AudioCaptureConnected(
    StatePtr reconnectState,
    CaptureContextPtr captureContext);

  virtual size_t printTo(Print& print) const;
};

/**
 * Микрофон включен, данные отправляются в веб-сокет.
 *
 * При получении команды "in.mute/mute" микрофон отключается и состояние меняется на AudioCaptureMuted.
 */
class AudioCapturing : public State {
private:
  CaptureContextPtr captureContext;
public:
  AudioCapturing(CaptureContextPtr captureContext);

  virtual void enter();
  virtual void leave();

  virtual StatePtr loop();
  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);

  virtual size_t printTo(Print& print) const;
};

/**
 * Микрофон выключен, ждём команды "in.mute/unmute", чтобы включить микрофон.
 */
class AudioCaptureMuted : public State {
private:
  CaptureContextPtr captureContext;
public:
  AudioCaptureMuted(CaptureContextPtr captureContext);

  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);

  virtual size_t printTo(Print& print) const;
};
