# 05 — Frontend

## Стек и сборка

- Vue 3.2 + TypeScript 4.7 + Vite 3 + XState 4.33 + vue-router 4 + axios 0.27 + zod 3.18 + vosk-browser 0.0.7
- `vite.config.ts`: alias `@ → src`, proxy `/api → http://localhost:8086 (ws:true)`, `manualChunks: config-page`, `outDir dist`
- Сборка: `cd frontend && npm ci && npm run build` → `dist/` → Docker копирует в `irene_plugin_web_face_frontend/frontend-dist/`
- Dev: `npm run dev` (host 0.0.0.0, порт vite по-умолчанию 5173), `npm run type-check` (vue-tsc)
- `index.html` → `src/main.ts` → `src/app.ts:initApplication()`

## Инициализация (`src/app.ts`)

```
loadConfig() → fetchConfig(FRONTEND_CONFIG_SCOPE) + zod FrontendConfig
  {preferStreamingInput, audioInputEnabled, audioOutputEnabled, microphoneSampleRate, hideConfiguration, requestWakeLock}
    + retry 5s при ошибке
→ getProtocolRequirements(config) → ProtocolRequirements[][]
→ createApp(App)
  provide('frontendConfiguration', config)
  provide('eventBus', new EventBus())
  provide 7 машин xstate (interpret(...).start())
  createRouter(routes: / → DialogPage, /config → ConfigsPage (если !hideConfig), /about → AboutPage)
  app.mount('#app')
```

`getProtocolRequirements` логика:
- всегда `['in.text-direct','in.text-indirect']`
- если `audioOutputEnabled`: `['out.audio.link']` + `['out.tts.serverside','out.text-plain']` иначе `['out.text-plain']`
- если `audioInputEnabled`: streaming? + prefer? → `['in.stt.serverside','in.stt.clientside','in.text-indirect']` или наоборот, иначе `['in.stt.clientside','in.text-indirect']` + `['in.mute']`
- `streamingSupported` из `streamingService.ts` (проверяет MediaStream + AudioWorklet)

`enableWakeLock()` если `requestWakeLock` (не даёт экрану гаснуть).

## EventBus (`src/components/eventBus.ts`)

Центральная шина между машинами. `busConnector(events)` — xstate invoke, пересылает события.

## State Machines (`src/components/dialog/` + `src/audio-input-streaming/` + `src/local-recognizer/`)

Все машины используют `eventBus` + `sm-helpers.ts`:
- `eventNameForMessageType(type) → "WS_RECEIVED(<type>)"`
- `eventNameForProtocolName(proto) → "WS_READY(<proto>)"`

| Машина | Файл | Состояния | Ключевое |
|--------|------|-----------|----------|
| `connectionStateMachine` | `sm-connection.ts` | `active:{connecting:{opening,negotiating},connected}` ↔ `disconnected (1s retry)` | WebSocket `/api/face_web/ws`, `negotiate/request`, `forwardWsProtocolEvents`/`forwardIncommingMessage` |
| `textInputMachine` | `sm-input-text.ts` | inactive→active, sending | Отправка `in.text-direct/text` или `in.text-indirect/text` по Enter |
| `messageHistoryMachine` | `sm-message-history.ts` | — | Хранит `messages[]`, событие `HISTORY_ADD_MESSAGE {direction,text}` |
| `audioOutputMachine` | `sm-output-audio.ts` | inactive→active:{waiting→playing} | `out.audio.link/playback-request` → `new Audio(url)` → `TICK(1s)`→`playback-progress`, `ended`→`playback-done` |
| `plaintextOutputMachine` | `sm-output-plaintext.ts` | inactive→active | `out.text-plain/text` → `HISTORY_ADD_MESSAGE` |
| `localRecognizerStateMachine` | `local-recognizer/sm.ts` | inactive→loading→active | Клиентский Vosk: грузит модель, `recognizerWorklet.js`, шлёт `in.stt.clientside/recognized` |
| `inputStreamingStateMachine` | `audio-input-streaming/sm.ts` | inactive→active:{connecting,streaming} | Серверный STT: ждёт `in.stt.serverside/ready {path}`, коннектит `audioStreamWsService` с `sampleRate`, стримит PCM |

### connection подробно (`sm-connection.ts`)

```
websocketService: new WebSocket(url{wss|ws} + /api/face_web/ws)
  on open → WS_OPEN → actions.requestNegotiation → WS_SEND {type:negotiate/request, protocols}
  on message → WS_RECEIVED → negotiating: forwardWsProtocolEvents → parses NegotiationAgreeMessage → sends WS_READY(proto) per proto → connected
  connected: WS_RECEIVED → forwardIncommingMessage → WS_RECEIVED(type) на eventBus
           WS_SEND → forwardToWebsocket
  on error/close → disconnected → after 1s → active
```

### local-recognizer (`sm.ts` + `voskService.ts` + `recognizerWorklet.js`)

- `voskService.ts` грузит `vosk-browser` модель (путь из `/api/plugin_expose_vosk_model/...` или `resources/vosk-models`)
- `recognizerWorklet.js` — AudioWorklet, ресемплит к `microphoneSampleRate`
- Состояния: пока `WS_READY(in.stt.clientside)` не придёт — `inactive`; после — грузит модель → `active` → слушает микрофон → каждое распознание → `WS_SEND {type:in.stt.clientside/recognized, text}`

### audio-input-streaming (`sm.ts` + `streamingService.ts` + `audioStreamWsService.ts`)

- `streamingService.ts:streamingSupported` — проверка `navigator.mediaDevices.getUserMedia` + `AudioWorklet`
- `audioStreamWebsocketService(path,sampleRate)` — коннектит `wss://host{path}?sample_rate=N`, шлёт `SEND_DATA` (PCM Float32→Int16)
- Машина ждёт `WS_RECEIVED(in.stt.serverside/ready)` → извлекает `path` → `invoke audioStreamWebsocketService` → `AUDIO_WS_OPEN` → стримит

## Компоненты

```
App.vue
  Header.vue (shared) — статус соединения + микрофон + бургер
  RouterView main: DialogPage.vue / ConfigsPage.vue / AboutPage.vue
    DialogPage.vue — список Message.vue + поле ввода
    Message.vue — direction in/out, markdown (vue3-markdown-it)
    ConfigEditPanel.vue — vue3-json-editor для YAML/JSON конфига
    Container.vue / Header.vue / HeaderTitle.vue — UI примитивы
    ConnectionStatus.vue / MicrophoneStatus.vue — индикаторы
AboutPage.vue — инфо о версии
```

## Конфиг фронтенда

Хранится на беке как конфиг плагина `web_face_frontend` (доступ через `fetchConfig(FRONTEND_CONFIG_SCOPE)`):
```ts
FrontendConfig = z.object({
  preferStreamingInput: z.boolean().default(true),
  audioInputEnabled: z.boolean().default(true),
  audioOutputEnabled: z.boolean().default(true),
  microphoneSampleRate: z.number(), // обязателен
  hideConfiguration: z.boolean().default(false),
  requestWakeLock: z.boolean().default(true),
})
```

## Сборка и деплой фронта

- `irene_plugin_web_face_frontend/plugin_web_face_frontend.py` — FastAPI `StaticFiles` раздача `frontend-dist/` + fallback `index.html` для SPA роутинга
- В Docker `frontend/dist` уже скопирован
- При dev — Vite proxy прозрачно форвардит `/api` на `localhost:8086`, фронт на `5173` может работать без сборки
