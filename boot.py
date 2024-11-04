from network import WLAN, STA_IF
import time
from _global import SSID, PASS
from machine import Pin

def connect_to_wifi():
    wlan = WLAN(STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(SSID, PASS)
        for _ in range(10):  # Try for a limited time to connect
            if wlan.isconnected():
                print("Connected to Wi-Fi:", wlan.ifconfig())
                return True
            print("Waiting for Wi-Fi connection...")
            time.sleep(1)

connect_to_wifi()
