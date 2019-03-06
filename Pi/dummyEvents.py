import time
import threading
import signal
import sys
import random

import paho.mqtt.client as mqtt

MQTT_CLIENT = None

TEMPERATURE_TOPIC = "city/temp"
HUMIDITY_TOPIC = "city/humi"
CO2_TOPIC = "city/co2"
BROADBAND_TOPIC = "city/broadband"
IR_TOPIC = "city/ir"
LIGHT_TOPIC = "city/lux"
MOTION_TOPIC = "city/motion"

THREAD_MEANTIME = 1

# Gracefully close the GPIO pins on ctrl-c
def signal_handler(sig, frame):
    sys.exit(0)


# Open a MQTT connection to the docker container.
def setup_mqtt():
    global MQTT_CLIENT
    MQTT_CLIENT = mqtt.Client()
    MQTT_CLIENT.connect("localhost", 1883, 60)
    MQTT_CLIENT.loop_start()



def testmode():
    global MQTT_CLIENT

    while True:
        topic = random.choice(["city/temp", "city/humi", "city/co2", "city/broadband", "city/ir", "city/lux", "city/motion"])
        val = random.randint(0, 1000)
        print("Publishing %s %u" %(topic, val))
        MQTT_CLIENT.publish(
            topic,
            val
        )
        time.sleep(5)


if __name__ == '__main__':
    setup_mqtt()
    signal.signal(signal.SIGINT, signal_handler)
    testmode()