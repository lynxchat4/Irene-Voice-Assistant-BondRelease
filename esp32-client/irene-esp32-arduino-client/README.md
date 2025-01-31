# Прошивка для клиента на ESP32

> :warning: **Данный проект работает только с оригинальными ESP32.**
>
> ESP32S2 и ESP32S3 **не поддерживаются**.

## Зависимости

Для сборки прошивки потребуется Arduino IDE, а так же следующие библиотеки:

- https://github.com/gilmaimon/ArduinoWebsockets
- https://github.com/schreibfaul1/ESP32-audioI2S
- https://github.com/arduino-libraries/Arduino_JSON

## Настройка

Настройка клиента осуществляется изменением констант, определённых в файле [config.h](config.h) перед сборкой прошивки.

Основные значения, на которые стоит обратить внимание - это имя и пароль WiFi-сети, к которой будет подключаться клиент
(`WIFI_SSID` и `WIFI_PASS`) а так же IP-адрес и порт сервера (`SERVER_HOSTNAME` и `SERVER_PORT`).

## Известные проблемы

- иногда может зависать при воспроизведении. Похоже, ESP32-audioI2S не всегда позволяет корректно отследить окончание
  воспроизведения. Плавающий баг, возможно, коррелирует с предшествующей попыткой воспроизведения некорректного файла.
- web-socket соединения не устойчивы. Соединения разрываются примерно раз в 10-20 минут. Если разрыв произойдёт во время
  взаимодействия с ассистентом - то выйдет неудобно.
