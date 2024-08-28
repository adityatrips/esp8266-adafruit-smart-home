from machine import Pin, PWM
from read import do_read
from hcsr04 import HCSR04
from mfrc522 import MFRC522
import uasyncio as asyncio
from network import WLAN, STA_IF
import sys

import dht
import umqtt.robust as mqtt
import json

from _global import (
    TRIG,
    ECHO,
    DHTPIN,
    LED,
    SCK,
    MOSI,
    MISO,
    RST,
    SDA,
    SERVO,
    SSID,
    PASS,
    MQTTBROKER,
    MQTTPORT,
    MQTTUSER,
    MQTTPASS,
    TEMP_PUBTOPIC,
    HUMI_PUBTOPIC,
    DOOR_PUBSUBTOPIC,
    SERVO_PUBTOPIC,
    LED_SUBTOPIC,
    BUTTON,
)

button_pin = Pin(BUTTON, Pin.IN, Pin.PULL_UP)

radar_sensor = HCSR04(trigger_pin=TRIG, echo_pin=ECHO, echo_timeout_us=10000)
dht_sensor = dht.DHT11(Pin(DHTPIN))
led_pin = Pin(LED, Pin.OUT)
rfid = MFRC522(SCK, MOSI, MISO, RST, SDA)
servo = PWM(Pin(SERVO, Pin.OUT), freq=50)
led = Pin(LED, Pin.OUT)

led.off()
client = None

def message_callback(topic, msg):
    print(topic)
    print(msg)
    if topic == b"Anjali_Chauhan/feeds/led-feed":
        if msg == b"1":
            led.on()
        elif msg == b"0":
            led.off()
    elif topic == DOOR_PUBSUBTOPIC:
        if msg == b"0":
            servo.duty(77)
        elif msg == b"0":
            servo.duty(130)


def setup_mqtt():
    try:
        global client
        client = mqtt.MQTTClient(
            "ESP8266",
            MQTTBROKER,
            port=MQTTPORT,
            user=MQTTUSER,
            password=MQTTPASS,
        )
        client.set_callback(message_callback)
        client.connect()
        client.subscribe(LED_SUBTOPIC)
        client.subscribe(DOOR_PUBSUBTOPIC)
    except OSError:
        print("MQTT broker not found!")
        setup_mqtt()


async def sub_task():
    while True:
        client.check_msg()
        await asyncio.sleep(1)


async def pub_task():
    while True:
        if button_pin.value():  # Publish only if button is not pressed
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            humi = dht_sensor.humidity()

            temp_json = json.dumps({"value": temp})
            humi_json = json.dumps({"value": humi})
            us_json = json.dumps({"value": radar_sensor.distance_cm()})

            print("Publishing temperature, humidity, and servo data")
            client.publish(TEMP_PUBTOPIC, temp_json)
            client.publish(HUMI_PUBTOPIC, humi_json)
            client.publish(SERVO_PUBTOPIC, us_json)
        await asyncio.sleep(10)  # Publish sensor data every 10 seconds


async def button_monitor():
    global client
    while True:
        if not button_pin.value():  # Check if the button is pressed
            print("Button pressed, hold the card close...")
            led_pin.off()
            try:
                read_msg = do_read()
            except Exception as e:
                read_msg = None
            finally:
                led_pin.on()

            door_json = None

            if isinstance(read_msg, type(None)):
                door_json = json.dumps({"value": 0})
            else:
                if read_msg == "Authorized":
                    print("Publishing authorized access")
                    door_json = json.dumps({"value": 1})
                elif read_msg == "Unauthorized":
                    print("Publishing unauthorized access")
                    door_json = json.dumps({"value": 0})
            client.publish(DOOR_PUBSUBTOPIC, door_json)

            # Halt other tasks until the button is released
            while not button_pin.value():
                await asyncio.sleep(0.1)  # Check every 100 ms

        await asyncio.sleep(0.1)  # Check every 100 ms


async def handle_mqtt():
    sub = asyncio.create_task(sub_task())
    pub = asyncio.create_task(pub_task())
    button = asyncio.create_task(button_monitor())

    await asyncio.gather(sub, pub, button)


def main():
    try:
        #connect_to_wifi()
        print("SETUP MQTT")
        setup_mqtt()
        print("SETUP MQTT DONE")
        asyncio.run(handle_mqtt())
    except KeyboardInterrupt:
        sys.exit(0)

main()
