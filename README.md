# ESP8266 Smart Home Hub

## Requirements

- ESP8266 (NodeMCU)
- NodeMCU pin extension board
- DHT11 (Temperature and humidity sensor)
- HCSR04 (Ultrasonic sensor)
- MFRC522 (RFID sensor)
- SG90 (Servo motor)

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
