from machine import Pin
from read import do_read
from hcsr04 import HCSR04
from mfrc522 import MFRC522
from network import WLAN, STA_IF

import dht
import umqtt.robust as mqtt
import time
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
    MQTTBROKER,
    MQTTPORT,
    MQTTUSER,
    MQTTPASS,
    TEMP_PUBTOPIC,
    HUMI_PUBTOPIC,
    SERVO_PUBTOPIC,
)

radar_sensor = HCSR04(trigger_pin=TRIG, echo_pin=ECHO, echo_timeout_us=10000)
dht_sensor = dht.DHT11(Pin(DHTPIN))
led_pin = Pin(LED, Pin.OUT)
rfid = MFRC522(SCK, MOSI, MISO, RST, SDA)


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
    print("Received message on topic {}: {}".format(topic.decode(), msg.decode()))


def setup_mqtt():
    client = mqtt.MQTTClient(
        "ESP8266",
        MQTTBROKER,
        port=MQTTPORT,
        user=MQTTUSER,
        password=MQTTPASS,
    )
    client.set_callback(message_callback)
    client.connect()
    return client


def handle_mqtt(client):
    last_publish_time = 0
    publish_interval = 10

    try:
        while True:
            client.check_msg()
            current_time = time.time()
            if current_time - last_publish_time > publish_interval:
                dht_sensor.measure()
                temp = dht_sensor.temperature()
                humi = dht_sensor.humidity()

                led_pin.off()
                read_msg = do_read()
                print("READ_MSG:", read_msg)
                led_pin.on()

                servo_json = None

                if read_msg is None or read_msg == "":
                    servo_json = json.dumps({"value": 0})
                else:
                    if read_msg == "Authorized":
                        print("Publishing authorized access")
                        servo_json = json.dumps({"value": 1})
                    elif read_msg == "Unauthorized":
                        print("Publishing authorized access")
                        servo_json = json.dumps({"value": 0})

                temp_json = json.dumps({"value": temp})
                humi_json = json.dumps({"value": humi})
                servo_json = json.dumps({"value": radar_sensor.distance_cm()})

                print("Publishing temperature, humidity, and servo data")
                client.publish(TEMP_PUBTOPIC, temp_json)
                client.publish(HUMI_PUBTOPIC, humi_json)
                client.publish(SERVO_PUBTOPIC, servo_json)
                client.publish(SERVO_PUBTOPIC, servo_json)

                last_publish_time = current_time
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user")


def main():
    connect_to_wifi()
    client = setup_mqtt()
    handle_mqtt(client)


main()
