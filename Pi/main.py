#! /usr/bin/env python3

import configparser
import time
import threading
import _thread
import signal
import sys
import os
import random
import urllib.request

import cv2
import numpy as np

import RPi.GPIO as GPIO

import paho.mqtt.client as mqtt

import sensors


MQTT_CLIENT = None

CONFIG = configparser.ConfigParser()

TEMPERATURE_TOPIC = "city/temp"
HUMIDITY_TOPIC = "city/humi"
CO2_TOPIC = "city/co2"
BROADBAND_TOPIC = "city/broadband"
IR_TOPIC = "city/ir"
LIGHT_TOPIC = "city/lux"
MOTION_TOPIC = "city/motion"
CAMERA_TOPIC = "city/vid"

THREAD_MEANTIME = 1

LED_RING_PIN = 27


# Gracefully close the GPIO pins on ctrl-c
def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


# Open a MQTT connection to the docker container.
def setup_mqtt():
    global MQTT_CLIENT
    MQTT_CLIENT = mqtt.Client()
    MQTT_CLIENT.connect("localhost", 1883, 60)
    MQTT_CLIENT.loop_start()


# Send if motion is detected.
def on_motion(GPIO_PIN):
    global MQTT_CLIENT

    pin_state = GPIO.input(GPIO_PIN)
    print("## Publishing motion {} to topic {}".format(pin_state, MOTION_TOPIC))
    MQTT_CLIENT.publish(MOTION_TOPIC, pin_state)


# A generic function for reading a sensor (in func) and publishing the
# values to a topic in MQTT.
def process_sensor_mqtt(func, topic):
    global MQTT_CLIENT
    global CONFIG

    _thread = threading.Timer(
        int(CONFIG['DEFAULT'][func.__name__]), process_sensor_mqtt,
        [func, topic])
    _thread.daemon = True
    _thread.start()

    sensor_value = func()
    print("## Publishing {} to topic {} ({}) ".format(
        sensor_value, topic, CONFIG['DEFAULT'][func.__name__]))

    MQTT_CLIENT.publish(topic, sensor_value)


def update_config():
    global CONFIG

    _thread = threading.Timer(5, update_config)
    _thread.daemon = True
    _thread.start()

    print("### Updating config.")

    tmp_cfg = configparser.ConfigParser()
    tmp_cfg.read('config/config.ini')

    CONFIG = tmp_cfg


def block_devices():
    global CONFIG

    _thread = threading.Timer(5, block_devices)
    _thread.daemon = True
    _thread.start()

    if CONFIG['DEFAULT']['crisis'] == 'on':
        if not os.path.exists("./crisis"):
            print("Blocking devices")
            os.system("iptables -I INPUT -m mac --mac-source B4:9D:0B:63:79:31 -j REJECT")
            os.system("iptables -I INPUT -m mac --mac-source B4:9D:0B:63:74:39 -j REJECT")
            os.system("conntrack --flush")
            open("./crisis", "w").close()
    else:
        if os.path.exists("./crisis"):
            print("Unblocking Devices")
            os.system("iptables -D INPUT -m mac --mac-source B4:9D:0B:63:79:31 -j REJECT")
            os.system("iptables -D INPUT -m mac --mac-source B4:9D:0B:63:74:39 -j REJECT")
            os.remove("./crisis")

def switch_leds():
    global CONFIG

    _thread = threading.Timer(1, switch_leds)
    _thread.daemon = True
    _thread.start()

    if CONFIG['DEFAULT']['led_state'] == 'steady':
        if GPIO.input(LED_RING_PIN) == 0:
            return
        else:
            GPIO.output(LED_RING_PIN, not GPIO.input(LED_RING_PIN))

    GPIO.output(LED_RING_PIN, not GPIO.input(LED_RING_PIN))


def cam_detect_crisis():
    CAMERA_STATE = "restart"

    CAMERA_URL = urllib.request.urlopen('http://192.168.0.227/cgi-bin/mjpeg?resolution=1920x1080&quality=1&page=1551695809854&Language=9')

    byte_array = b''
    while True:
        byte_array += CAMERA_URL.read(1024)
        jpeg_sig_start = byte_array.find(b'\xff\xd8')
        jpeg_sig_end = byte_array.find(b'\xff\xd9')

        if jpeg_sig_start != -1 and jpeg_sig_end != -1:
            jpg = byte_array[jpeg_sig_start:jpeg_sig_end + 2]
            byte_array = byte_array[jpeg_sig_end + 2:]

            img = cv2.imdecode(
                np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

            img = cv2.medianBlur(img, 3)

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_red = cv2.inRange(hsv, np.array([5, 100, 100]),
                                    np.array([30, 255, 255]))
            upper_red = cv2.inRange(hsv, np.array([20, 100, 100]),
                                    np.array([60, 255, 255]))

            masked = cv2.addWeighted(lower_red, 1.0, upper_red, 1.0, 0.0)

            blurred = cv2.GaussianBlur(masked, (9, 9), 2)

            image_cols, image_rows = blurred.shape

            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                1,
                image_rows / 8,
                param1=100,
                param2=30,
                minRadius=100,
                maxRadius=300)

            if circles is not None:
                CAMERA_STATE = ("crisis" if CAMERA_STATE == "restart" else "restart")
                print("## Detected circles. Switching to {} mode.".format(CRISIS_STATE))
                MQTT_CLIENT.publish(CAMERA_TOPIC, CAMERA_STATE)

            time.sleep(2)

            # for circle in circles[0, :]:
            #     center = (circle[0], circle[1])
            #     radius = circle[2]
            #     print(radius)
            #     cv2.circle(img, center, radius, (0, 255, 0), 5)

            # cv2.imwrite('example.jpg', img)
            cv2.imwrite('masked.jpg', masked)
            # cv2.imwrite('blurred.jpg', blurred)


def testmode():
    global MQTT_CLIENT

    while True:
        MQTT_CLIENT.publish(
            random.choice(["city/temp", "city/humi", "city/co2", "city/broadband", "city/ir", "city/lux", "city/motion"]),
            random.randint(0, 1000)
        )
        time.sleep(5)


if __name__ == '__main__':
    setup_mqtt()

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        testmode()

    signal.signal(signal.SIGINT, signal_handler)
    CONFIG.read('config/config.ini')

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_RING_PIN, GPIO.OUT)
    GPIO.output(LED_RING_PIN, GPIO.LOW)

    # Init sensors and MQTT
    sensors.init_sensors(on_motion)

    # Publish these sensors to the local MQTT.
    process_sensor_mqtt(sensors.humidity, HUMIDITY_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.temperature, TEMPERATURE_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.co2, CO2_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.broadband, BROADBAND_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.ir, IR_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.lux, LIGHT_TOPIC)
    time.sleep(THREAD_MEANTIME)
    _thread.start_new_thread(cam_detect_crisis, ())
    block_devices()

    update_config()

    switch_leds()

    # Since everything is threaded, we need to pause the main thread.
    signal.pause()
