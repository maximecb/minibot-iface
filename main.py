#!/usr/bin/env python3

import threading
import signal
import sys
import time
import zmq
import numpy as np
import picamera
import picamera.array
from Adafruit_MotorHAT import Adafruit_MotorHAT
from scipy.misc import imresize

SERVER_PORT = 7777
CAMERA_RES = (1640, 1232)

# Create a default object, no changes to I2C address or frequency
motorhat = Adafruit_MotorHAT(addr=0x6f)
left_motor = motorhat.getMotor(1)
right_motor = motorhat.getMotor(2)

# Initialize the camera and set parameters
print("Initializing camera")
camera = picamera.PiCamera()
camera.resolution = CAMERA_RES
camera.framerate = 40
camera.iso = 200
time.sleep(2)
g = camera.awb_gains
camera.awb_mode = 'off'
camera.awb_gains = g
camera.shutter_speed = 30*1000

# Numpy array of shape (rows, columns, colors)
img_array = picamera.array.PiRGBArray(camera)

def set_motors(lSpeed, rSpeed):
    lSpeed = max(-255, min(255, int(lSpeed * 255)))
    rSpeed = max(-255, min(255, int(rSpeed * 255)))

    if lSpeed > 0:
        left_motor.run(Adafruit_MotorHAT.FORWARD)
        left_motor.setSpeed(lSpeed)
    elif lSpeed < 0:
        left_motor.run(Adafruit_MotorHAT.BACKWARD)
        left_motor.setSpeed(-lSpeed)
    else:
        left_motor.run(Adafruit_MotorHAT.RELEASE)

    if rSpeed > 0:
        right_motor.run(Adafruit_MotorHAT.FORWARD)
        right_motor.setSpeed(rSpeed)
    elif rSpeed < 0:
        right_motor.run(Adafruit_MotorHAT.BACKWARD)
        right_motor.setSpeed(-rSpeed)
    else:
        right_motor.run(Adafruit_MotorHAT.RELEASE)

def get_image():
    # Clear the image array between captures
    img_array.truncate(0)

    camera.capture(img_array, format='rgb')
    img = img_array.array

    print('Resizing image')

    # Drop some rows and columns to speed up resizing
    img = img[::3, ::3]

    # Resize to reduce the noise in the final image
    # We resize on the raspi to minimize bandwidth required
    img = imresize(img, (60, 80, 3), interp='cubic')

    # Drop some rows and columns to downsize the image
    #img = img[0:1232:20, 0:1640:20]
    #img = img[0:60, 0:80]
    #assert img.shape == (60, 80, 3), img.shape

    img = np.ascontiguousarray(img, dtype=np.uint8)

    return img

def signal_handler(signal, frame):
    print("Shutting down")

    # Stop the motors
    left_motor.run(Adafruit_MotorHAT.RELEASE)
    right_motor.run(Adafruit_MotorHAT.RELEASE)

    # Close the camera
    camera.close()

    time.sleep(0.25)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##############################################################################

serverAddr = "tcp://*:%s" % SERVER_PORT
print('Starting server at %s' % serverAddr)
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind(serverAddr)

def send_array(socket, array):
    """
    Send a numpy array with metadata over zmq
    """
    md = dict(
        dtype=str(array.dtype),
        shape=array.shape,
    )
    # SNDMORE flag specifies this is a multi-part message
    socket.send_json(md, flags=zmq.SNDMORE)
    return socket.send(array, copy=True, track=False, flags=0)

def poll_socket(socket, timetick = 10):
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    # wait up to 10msec
    try:
        print("Poller ready")
        while True:
            obj = dict(poller.poll(timetick))
            if socket in obj and obj[socket] == zmq.POLLIN:
                yield socket.recv_json()
    except KeyboardInterrupt:
        print ("stopping server")
        quit()

def handle_message(msg):
    if msg['command'] == 'reset':
        print('got reset command')
        set_motors(0, 0)

    elif msg['command'] == 'action':
        print('received action')

        action = msg['action']
        print(action)

        if action == 'move_forward':
            set_motors(0.4, 0.4)
            time.sleep(0.2)
            set_motors(0, 0)

        if action == 'move_back':
            set_motors(-0.4, -0.4)
            time.sleep(0.2)
            set_motors(0, 0)

        if action == 'turn_left':
            set_motors(-0.4, 0.4)
            time.sleep(0.2)
            set_motors(0, 0)

        if action == 'turn_right':
            set_motors(0.4, -0.4)
            time.sleep(0.2)
            set_motors(0, 0)

        if action == 'done':
            set_motors(0, 0)

    else:
        assert False, "unknown command"

    print('sending image')

    image = get_image()
    send_array(socket, image)
    print('sent image')

for message in poll_socket(socket):
    handle_message(message)
