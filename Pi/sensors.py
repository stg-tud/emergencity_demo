#!/usr/bin/python
import time

import RPi.GPIO as GPIO
import board
import busio

import Adafruit_DHT
import adafruit_tsl2561

from max30105 import MAX30105

MOTION_SENSOR_PIN = 17
MOTION_SENSOR_READ = 0
MOTION_SENSOR_STATE = 0

TEMP_HUMI_SENSOR = Adafruit_DHT.AM2302
TEMP_HUMI_PIN = 4

PARTICLE_SENSOR = None

LIGHT_SENSOR = None

def test_motion(GPIO_PIN):
    print("MOTION!")

def init_sensors(motion_function):
    global PARTICLE_SENSOR
    global LIGHT_SENSOR

    print("Setting GPIO mode.")
    # Use GPIO numbers instead of pin numbers
    GPIO.setmode(GPIO.BCM)

    ### Motion Sensor ###
    print("Initializing MOTION sensor.")
    # Init the motion sensor
    GPIO.setup(MOTION_SENSOR_PIN, GPIO.IN)

    # We need to wait until the sensor is ready.
    print("Waiting for the MOTION sensor.")
    while GPIO.input(MOTION_SENSOR_PIN) != 0:
        time.sleep(0.1)

    # Add a callback function to be triggered everytime the
    # sensor detects motion
    GPIO.add_event_detect(
        MOTION_SENSOR_PIN, GPIO.RISING, callback=motion_function)

    ### Particle Sensor ###
    print("Initializing PARTICLE sensor.")
    PARTICLE_SENSOR = MAX30105()
    PARTICLE_SENSOR.setup(leds_enable=3)

    PARTICLE_SENSOR.set_led_pulse_amplitude(1, 0.0)
    PARTICLE_SENSOR.set_led_pulse_amplitude(2, 0.0)
    PARTICLE_SENSOR.set_led_pulse_amplitude(3, 12.5)

    PARTICLE_SENSOR.set_slot_mode(1, 'red')
    PARTICLE_SENSOR.set_slot_mode(2, 'ir')
    PARTICLE_SENSOR.set_slot_mode(3, 'green')
    PARTICLE_SENSOR.set_slot_mode(4, 'off')

    ### Light Sensor ###
    i2c = busio.I2C(board.SCL, board.SDA)
    LIGHT_SENSOR = adafruit_tsl2561.TSL2561(i2c)
    LIGHT_SENSOR.enabled = True


def humidity():
    return Adafruit_DHT.read_retry(TEMP_HUMI_SENSOR, TEMP_HUMI_PIN)[0]


def temperature():
    return Adafruit_DHT.read_retry(TEMP_HUMI_SENSOR, TEMP_HUMI_PIN)[1]


def broadband():
    global LIGHT_SENSOR
    return LIGHT_SENSOR.broadband


def ir():
    global LIGHT_SENSOR
    return LIGHT_SENSOR.infrared


def lux():
    global LIGHT_SENSOR
    return LIGHT_SENSOR.lux


def particles():
    global PARTICLE_SENSOR
    samples = PARTICLE_SENSOR.get_samples()

    # The sensor sometimes returns None when coming to close.
    if samples:
        return 2000 * ((samples[2] & 0xff) / 255)
    else:
        return 2000


if __name__ == '__main__':
    init_sensors(test_motion)

    while True:
        print("Temp: " + str(temperature()))
        print("Humi: " + str(humidity()))
        print("Particles: " + str(particles()))
        print("Broadband Light: " + str(broadband()))
        print("Infrared: " + str(ir()))
        print("Lux: " + str(lux()))
        time.sleep(1)
