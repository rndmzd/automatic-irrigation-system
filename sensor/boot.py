import uos
import machine
import gc
import webrepl
import network
import socket
import time
import config

wifi_ssid = config.WIFI_SSID
wifi_password = config.WIFI_PASSWORD

led = machine.Pin("LED", machine.Pin.OUT)
led.on()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(wifi_ssid, wifi_password)

max_wait = 30

while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('Waiting for connection...')
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('Network connection failed')

print('Connected')
status = wlan.ifconfig()
print('ip = ' + status[0])

webrepl.start()
gc.collect()

time.sleep(15)

led.off()

import main