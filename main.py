from machine import Pin, PWM
from read import do_read
from hcsr04 import HCSR04
from mfrc522 import MFRC522
from network import WLAN, STA_IF
import uasyncio as asyncio

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
    SSID,
    PASS,
    SERVO,
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

# Initialize the button pin
button_pin = Pin(
    BUTTON, Pin.IN, Pin.PULL_UP
)  # Adjust pull depending on your circuit (PULL_UP if button connects to ground when pressed)

radar_sensor = HCSR04(trigger_pin=TRIG, echo_pin=ECHO, echo_timeout_us=10000)
dht_sensor = dht.DHT11(Pin(DHTPIN))
led_pin = Pin(LED, Pin.OUT)
rfid = MFRC522(SCK, MOSI, MISO, RST, SDA)
servo = PWM(Pin(SERVO, Pin.OUT), freq=50)
led = Pin(LED, Pin.OUT)

client = None


def connect_to_wifi():
    wlan = WLAN(STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to network...")
        wlan.connect(SSID, PASS)
        while not wlan.isconnected():
            pass
    print("Network connected!")


def message_callback(topic, msg):
    print(topic)
    print(msg)
    if topic == LED_SUBTOPIC:
        if msg == b"1":
            led.on()
        else:
            led.off()
    elif topic == DOOR_PUBSUBTOPIC:
        if msg == b"0":
            servo.duty(77)
        elif msg == b"1":
            servo.duty(130)


def setup_mqtt():
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


async def sub_task():
    while True:
        client.check_msg()
        await asyncio.sleep(1)


async def pub_task():
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


# Add an asynchronous function to monitor the button
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


def main():
    connect_to_wifi()
    setup_mqtt()
    asyncio.run(asyncio.gather(button_monitor(), sub_task(), pub_task()))


main()
