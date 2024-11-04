from machine import Pin, PWM
from read import do_read
from hcsr04 import HCSR04
from mfrc522 import MFRC522
from network import WLAN, STA_IF
import sys
import dht
import umqtt.robust as mqtt
import json
import time  # Import time for delays

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

def connect_to_wifi():
    wlan = WLAN(STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASS)
    print("Connecting to Wi-Fi...")

    while not wlan.isconnected():
        print("Waiting for Wi-Fi connection...")
        time.sleep(1)  # Add delay to avoid busy loop
    print("Connected to Wi-Fi:", wlan.ifconfig())

def message_callback(topic, msg):
    print((topic, msg))
    if topic == LED_SUBTOPIC:
        if msg == b"1":
            led.on()
        elif msg == b"0":
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
    print("MQTT setup done")

def check_messages():
    try:
        client.check_msg()
    except Exception as e:
        print("MQTT check message error:", e)
        client.disconnect()
        time.sleep(5)  # Retry delay
        client.connect()
        client.subscribe(LED_SUBTOPIC)
        client.subscribe(DOOR_PUBSUBTOPIC)

def publish_sensor_data():
    try:
        if button_pin.value():
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
    except Exception as e:
        print("MQTT publish error:", e)

def monitor_button():
    try:
        if not button_pin.value():
            print("Button pressed, hold the card close...")
            led_pin.off()
            read_msg = do_read()
            led_pin.on()

            if read_msg is None:
                door_json = json.dumps({"value": 0})
            else:
                if read_msg == "Authorized":
                    print("Publishing authorized access")
                    door_json = json.dumps({"value": 1})
                else:
                    print("Publishing unauthorized access")
                    door_json = json.dumps({"value": 0})
            client.publish(DOOR_PUBSUBTOPIC, door_json)

            while not button_pin.value():
                time.sleep(0.1)
    except Exception as e:
        print("Button monitor error:", e)

def main_loop():
    connect_to_wifi()
    setup_mqtt()

    while True:
        check_messages()       # Check for incoming MQTT messages
        publish_sensor_data()  # Publish sensor data
        monitor_button()       # Monitor the button for RFID reading
        time.sleep(1)          # Loop delay to reduce CPU load

try:
    main_loop()
except Exception as e:
    print("Exception occurred:", e)
    sys.print_exception(e)
    machine.reset()  # Reboot on unhandled exceptions
