#include <memory>
#pragma once

#include "state.h"
#include "interval.h"

namespace websockets {
class WebsocketsClient;
struct WebsocketsMessage;
};

class AudioPlaybackReadyState : public State {
private:
  std::shared_ptr<websockets::WebsocketsClient> wsClient;
public:
  AudioPlaybackReadyState(std::shared_ptr<websockets::WebsocketsClient> wsClient);

  virtual StatePtr receiveCommand(const String& commandName, JSONVar& args);  

  virtual size_t printTo(Print& print) const;
};

class Audio;

class AudioPlaybackProgressState : public State {
private:
  std::shared_ptr<websockets::WebsocketsClient> wsClient;
  std::unique_ptr<Audio> audio;
  String playbackId;
  String playbackNotificationMessage;
  String url;
  Interval notificationInterval;
public:
  AudioPlaybackProgressState(
    std::shared_ptr<websockets::WebsocketsClient> wsClient,
    String url,
    String playbackId
  );

  virtual void enter();

  virtual void leave();

  virtual StatePtr loop();
  
  virtual size_t printTo(Print& print) const;
};
