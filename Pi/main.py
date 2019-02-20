import time
import threading
import signal
import sys

import RPi.GPIO as GPIO

import paho.mqtt.client as mqtt

import sensors


MQTT_CLIENT = None

TEMPERATURE_TOPIC = "city/temp"
HUMIDITY_TOPIC = "city/humi"
PARTICLES_TOPIC = "city/particles"
LIGHT_TOPIC = "city/lux"

# A timer on how often a sensor should be read.
# Maybe more fine grained in future.
TIMER = 5


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


# TODO
def on_motion(GPIO_PIN):
    pass


# A generic function for reading a sensor (in func) and publishing the
# values to a topic in MQTT.
def process_sensor_mqtt(func, topic):
    global MQTT_CLIENT
    _thread = threading.Timer(TIMER, process_sensor_mqtt, [func, topic])
    _thread.daemon = True
    _thread.start()

    sensor_value = func()
    print("## Publishing {} to topic {}".format(sensor_value, topic))

    MQTT_CLIENT.publish(topic, sensor_value)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    # Init sensors and MQTT
    sensors.init_sensors(on_motion)
    setup_mqtt()

    # Publish these sensors to the local MQTT.
    process_sensor_mqtt(sensors.humidity, HUMIDITY_TOPIC)
    process_sensor_mqtt(sensors.temperature, TEMPERATURE_TOPIC)
    process_sensor_mqtt(sensors.particles, PARTICLES_TOPIC)
    process_sensor_mqtt(sensors.lux, LIGHT_TOPIC)

    # Since everything is threaded, we need to pause the main thread.
    signal.pause()
