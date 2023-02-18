#include <Arduino.h>
#include <WiFi.h>
#include <Audio.h>
#include <Arduino_JSON.h>

#include "config.h"
#include "state.h"
#include "wifi_connection.h"
#include "websocket_connection.h"
#include "protocol_negotiation.h"
#include "audio_playback.h"
#include "audio_capture.h"

StateVec makeMainStates(std::shared_ptr<websockets::WebsocketsClient> wsClient) {
  return {
    std::make_shared<AudioCaptureWaiting>(),
    std::make_shared<AudioPlaybackReadyState>(wsClient)
  };
}

StatePtr makeProtocolNegotiationState(std::shared_ptr<websockets::WebsocketsClient> wsClient) {
	return std::make_shared<NegotiatingProtocolsState>(
		wsClient,
		[=]() -> StateVec {
			return makeMainStates(wsClient);
		}
	);
}

StateVec makeWiFiConnectedStates() {
  std::shared_ptr<websockets::WebsocketsClient> controlConnectioClient = makeWebsocketClient();

  return {
    //std::make_shared<PlayerState>()
    std::make_shared<WebsocketConnectingState>(
      controlConnectioClient,
      "/api/face_web/ws",
      [=](StatePtr reconnectState) -> StatePtr {
        return std::make_shared<WebSocketControlConnectionConnectedState>(
          reconnectState,
          controlConnectioClient,
          [=]() -> StateVec {
            return {
              makeProtocolNegotiationState(controlConnectioClient)
            };
          }
        );
      }
    )
  };
}

StateManager rootState(std::make_shared<WiFiConnectingState>(makeWiFiConnectedStates));

void setup() {
  Serial.begin(921600);
  Serial.println("\n\nStarting...");

  rootState->enter();
}

void loop() {
  rootState.loop();
}
