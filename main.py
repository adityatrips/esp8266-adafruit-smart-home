from hcsr04 import HCSR04
from machine import Pin
from mfrc522 import MFRC522
from read import do_read

import umqtt.robust as mqtt
import network
import time
import dht
import json

echo = 15
trig = 16
servo = 12
dht_pin = 13
led = 2
sda = 14
sck = 0
mosi = 2
miso = 4
rst = 5

temp = 0
humi = 0

ssid = "Airtel_Aditya"
password = "kk9310028206"

mqtt_broker = "io.adafruit.com"
mqtt_port = 1883
mqtt_user = "axitya"
mqtt_password = "b01317a9cbfa49f097c1e750a9de43bd"
publish_door_topic = b"axitya/feeds/door-feed"
publish_temp_topic = b"axitya/feeds/temp-feed"
publish_humi_topic = b"axitya/feeds/humi-feed"
publish_servo_topic = b"axitya/feeds/servo-feed"

radar_sensor = HCSR04(trigger_pin=trig, echo_pin=echo, echo_timeout_us=10000)
dht_sensor = dht.DHT11(Pin(dht_pin))
led_pin = Pin(led, Pin.OUT)
rfid = MFRC522(sck, mosi, miso, rst, sda)


def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to network...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print("Network connected!")


def message_callback(topic, msg):
    print("Received message on topic {}: {}".format(topic.decode(), msg.decode()))


def setup_mqtt():
    client = mqtt.MQTTClient(
        "ESP8266", mqtt_broker, port=mqtt_port, user=mqtt_user, password=mqtt_password
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

                door_json = None

                if read_msg is None or read_msg == "":
                    door_json = json.dumps({"value": 0})
                else:
                    if read_msg == "Authorized":
                        print("Publishing authorized access")
                        door_json = json.dumps({"value": 1})
                    elif read_msg == "Unauthorized":
                        print("Publishing authorized access")
                        door_json = json.dumps({"value": 0})

                temp_json = json.dumps({"value": temp})
                humi_json = json.dumps({"value": humi})
                servo_json = json.dumps({"value": radar_sensor.distance_cm()})

                print("Publishing temperature, humidity, and servo data")
                client.publish(publish_temp_topic, temp_json)
                client.publish(publish_humi_topic, humi_json)
                client.publish(publish_servo_topic, servo_json)
                client.publish(publish_door_topic, door_json)

                last_publish_time = current_time
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user")


def main():
    connect_to_wifi()
    client = setup_mqtt()
    handle_mqtt(client)


if __name__ == "__main__":
    main()
