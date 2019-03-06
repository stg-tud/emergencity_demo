#!/usr/bin/python
import time

import RPi.GPIO as GPIO
import board
import busio

import Adafruit_DHT
import adafruit_tsl2561
import adafruit_ccs811

MOTION_SENSOR_PIN = 17

TEMP_HUMI_SENSOR = Adafruit_DHT.AM2302
TEMP_HUMI_PIN = 4

LIGHT_SENSOR = None

CO2_SENSOR = None


def test_motion(GPIO_PIN):
    print("MOTION!")


def init_sensors(motion_function):
    global LIGHT_SENSOR
    global CO2_SENSOR

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
    # sensor detects motion and falls back again
    GPIO.add_event_detect(
        MOTION_SENSOR_PIN, GPIO.BOTH, callback=motion_function)

    # i2c bus
    i2c = busio.I2C(board.SCL, board.SDA)

    ### CO2 Sensor ###
    CO2_SENSOR = adafruit_ccs811.CCS811(i2c)
    while not CO2_SENSOR.data_ready:
        pass

    ### Light Sensor ###
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


def co2():
    global CO2_SENSOR
    return CO2_SENSOR.eco2


if __name__ == '__main__':
    init_sensors(test_motion)

    while True:
        print("Temp: " + str(temperature()))
        print("Humi: " + str(humidity()))
        print("CO2: " + str(co2()))
        print("Broadband Light: " + str(broadband()))
        print("Infrared: " + str(ir()))
        print("Lux: " + str(lux()))
        time.sleep(1)
