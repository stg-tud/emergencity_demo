import configparser
import time
import threading
import signal
import sys

import RPi.GPIO as GPIO

import paho.mqtt.client as mqtt

import sensors


MQTT_CLIENT = None

CONFIG = configparser.ConfigParser()

TEMPERATURE_TOPIC = "city/temp"
HUMIDITY_TOPIC = "city/humi"
PARTICLES_TOPIC = "city/particles"
BROADBAND_TOPIC = "city/broadband"
IR_TOPIC = "city/ir"
LIGHT_TOPIC = "city/lux"
MOTION_TOPIC = "city/motion"

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


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    CONFIG.read('config/config.ini')

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_RING_PIN, GPIO.OUT)
    GPIO.output(LED_RING_PIN, GPIO.LOW)

    # Init sensors and MQTT
    sensors.init_sensors(on_motion)
    setup_mqtt()

    # Publish these sensors to the local MQTT.
    process_sensor_mqtt(sensors.humidity, HUMIDITY_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.temperature, TEMPERATURE_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.particles, PARTICLES_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.broadband, BROADBAND_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.ir, IR_TOPIC)
    time.sleep(THREAD_MEANTIME)
    process_sensor_mqtt(sensors.lux, LIGHT_TOPIC)
    time.sleep(THREAD_MEANTIME)

    update_config()

    switch_leds()

    # Since everything is threaded, we need to pause the main thread.
    signal.pause()
