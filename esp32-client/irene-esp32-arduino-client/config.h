#pragma once

#include <HardwareSerial.h>

#define LOGGING_PORT Serial  // Порт, используемый для вывода логов. Если LOGGING_PORT не defined, то логи выводиться не будут.

/* Настройки подключения к WiFi.
 */
#define WIFI_SSID "iot_test_ap"
#define WIFI_PASS "080430a8f3c5"

/* Настройки подключения к серверу голосового ассистента.
 */
#define SERVER_HOSTNAME "192.168.99.248"  // IP-адрес
#define SERVER_PORT 8086                  // Номер порта, на котором работает сервер

#define WEBSOCKET_RECONNECT_INTERVAL 1000                    // Интервал между попытками подключения к веб-сокету
#define WEBSOCKET_RECONNECT_INTERVAL_AFTER_DISCONNECT 10000  // Интервал перед повторной попыткой подключения в случае разрыва соединения с веб-сокетом


/* Настройки устройства вывода звука, подключенного по I2S шине.
 *
 * Протестировано с модулем на основе MAX98357A.
 */
#define OUT_I2S_PORT I2S_NUM_0  // Номер порта I2S, используемого для вывода звука
#define OUT_I2S_DOUT 5          // Номер вывода контроллера, подключенного к линии данных устройства вывода (DIN на MAX98357A)
#define OUT_I2S_BCLK 17         // Номер вывода контроллера, подключенного к линии bit clock устройства вывода
#define OUT_I2S_LRC 16          // Номер вывода контроллера, подключенного к линии left/right clock устройства вывода

#define PLAYBACK_VOLUME 21  // Громкость воспроизведения


/* Настройки устройства ввода звука, подключенного по I2S шине.
 *
 * Проверено с модулем на основе INMP441.
 */
#define IN_I2S_PORT I2S_NUM_1    // Номер порта I2S, используемого для ввода звука
#define IN_SAMPLE_RATE 16000     // Чатота дискретизации
#define IN_I2S_DIN 35            // Номер вывода контроллера, подключенного к линии данных устройства ввода (SD на INMP441)
#define IN_I2S_BCLK 33           // Номер вывода контроллера, подключенного к линии bit clock устройства ввода (SCK на INMP441)
#define IN_I2S_LRC 32            // Номер вывода контроллера, подключенного к линии left/right clock устройства ввода (WS на INMP441)
#define IN_DMA_BUFFER_COUNT 8    // Количество DMA-буферов, создаваемых драйвером
#define IN_DMA_BUFFER_SIZE 256   // Размер одного DMA-буфера в сэмплах
#define IN_SEND_BUFFER_SIZE 256  // Размер буфера отправляемого сообщения в сэмплах
