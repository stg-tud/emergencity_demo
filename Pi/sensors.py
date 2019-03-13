#!/usr/bin/python
import time
import sys
import math
import urllib.request

import cv2
import numpy as np

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

CAMERA_URL = urllib.request.urlopen(
    'http://192.168.2.5/cgi-bin/mjpeg?resolution=1920x1080&quality=1&page=1551695809854&Language=9'
)


def camera():
    global CAMERA_URL

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

            if circles is None:
                print("No crisis detected.")
                return False

            print("Crisis detected!")
            return True

            # for circle in circles[0, :]:
            #     center = (circle[0], circle[1])
            #     radius = circle[2]
            #     print(radius)
            #     cv2.circle(img, center, radius, (0, 255, 0), 5)

            # cv2.imwrite('example.jpg', img)
            # cv2.imwrite('masked.jpg', masked)
            # cv2.imwrite('blurred.jpg', blurred)



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
        time.sleep(0.1)

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
        print("Camera: " + str(camera()))
        time.sleep(1)
