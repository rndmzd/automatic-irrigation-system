import network
import urequests
import machine
import time
import config

led = machine.Pin("LED", machine.Pin.OUT)
led.off()

sensor1 = machine.ADC(26)
sensor2 = machine.ADC(27)

watering_threshold = config.WATERING_THRESHOLD
data_send_interval = config.DATA_SEND_INTERVAL
solenoid_controller_ip = config.SOLENOID_CONTROLLER_IP

wifi_ssid = config.WIFI_SSID
wifi_password = config.WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def connect_to_wifi():
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
            print(".")
        print("Connected to WiFi")

def read_sensors():
    value1 = sensor1.read_u16()
    value2 = sensor2.read_u16()
    return value1, value2

def scale_value(raw_value):
    return int((raw_value / 65535) * 100)

def send_data(value1, value2):
    led.on()
    
    scaled_value1 = scale_value(value1)
    print("scaled_value1:", scaled_value1)
    scaled_value2 = scale_value(value2)
    print("scaled_value2:", scaled_value2)
    
    url = 'http://' + solenoid_controller_ip + '/control'
    headers = {'Content-Type': 'application/json'}
    data = {
        'sensor1': scaled_value1,
        'sensor2': scaled_value2,
        #'solenoidState': scaled_value1 > watering_threshold,
        'solenoidState': False
    }
    try:
        response = urequests.post(url, json=data, headers=headers)
        print(response.text)
        response.close()
    except:
        print("Failed to send data.")
    
    led.off()

while True:
    connect_to_wifi()
    value1, value2 = read_sensors()
    send_data(value1, value2)
    time.sleep(data_send_interval)
