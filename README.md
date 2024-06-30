# ESP8266 Smart Home Hub

## Requirements

### Hardware

- ESP8266 (NodeMCU)
- NodeMCU pin extension board
- DHT11 (Temperature and humidity sensor)
- HCSR04 (Ultrasonic sensor)
- MFRC522 (RFID sensor)
- SG90 (Servo motor)

### Software

- EasyEDA (for schematic diagram)
- AdafruitIO (for MQTT server)
- Thonny/uPyCraft (for editing code on the micro-controller)
- IFTTT (for interaction between the MQTT server and Google assistant)

## Globals

- Edit the `_global.py` file to edit global data that is shared among the files.

## Functions

- The micro-controller connects to AdafruitIO MQTT server, using an internet connection.
- You are provided with two RFID cards with `AUTHORIZED` and `UNAUTHORIZED` access.
- When the board runs, it will flash a on-board LED light (blue color), that is the time when you are given a chance to present the RFID sensor with one of those cards.
  - If the card has the message `AUTHORIZED`, it will publish `1` to `SERVO_PUBTOPIC`
  - If the card has the message `UNAUTHORIZED`, it will publish `0` to `SERVO_PUBTOPIC`.
  - This will cause an indicator on the dashboard to turn `red` for `UNAUTHORIZED` and will turn `green` for `AUTHORIZED`.
- When the on-board LED on the boards switches off, it will publish the temperature, humidity, and the ultrasonic sensor data on the AdafruitIO dashboard.

## Connections

![Image](/Schematics.png)

| ESP8266 | DHT11 | HCSR04 | MFRC522 | SG90 |
| ------- | ----- | ------ | ------- | ---- |
| IO16    | -     | TRIG   | -       | -    |
| IO05    | -     | -      | RST     | -    |
| IO04    | -     | -      | MISO    | -    |
| IO00    | -     | -      | SCK     | -    |
| IO02    | -     | -      | MOSI    | -    |
| IO14    | -     | -      | SDA     | -    |
| IO12    | -     | -      | -       | DATA |
| IO13    | DATA  | -      | -       | -    |
| IO15    | -     | ECHO   | -       | -    |
| GND     | GND   | GND    | GND     | VCC  |
| 3V3     | VCC   | VCC    | VCC     | VCC  |
