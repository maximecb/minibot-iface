#!/usr/bin/env python

import threading
import signal
import sys
import time
import zmq
import numpy as np
import picamera
import picamera.array
from Adafruit_MotorHAT import Adafruit_MotorHAT

SERVER_PORT = 7777
CAMERA_RES = (1640, 1232)

# Create a default object, no changes to I2C address or frequency
motorhat = Adafruit_MotorHAT(addr=0x60)
leftMotor = motorhat.getMotor(1)
rightMotor = motorhat.getMotor(2)

# Create camera object
camera = picamera.PiCamera()
camera.resolution = CAMERA_RES
camera.framerate = 30

# Numpy array of shape (rows, columns, colors)
imgArray = picamera.array.PiRGBArray(camera)

frameItr = camera.capture_continuous(imgArray, format='bgr', use_video_port=True)

def setMotors(lSpeed, rSpeed):
    lSpeed = max(-255, min(255, int(lSpeed * 255)))
    rSpeed = max(-255, min(255, int(rSpeed * 255)))

    if lSpeed > 0:
        leftMotor.run(Adafruit_MotorHAT.FORWARD)
        leftMotor.setSpeed(lSpeed)
    else:
        leftMotor.run(Adafruit_MotorHAT.BACKWARD)
        leftMotor.setSpeed(-lSpeed)

    if rSpeed > 0:
        rightMotor.run(Adafruit_MotorHAT.FORWARD)
        rightMotor.setSpeed(rSpeed)
    else:
        rightMotor.run(Adafruit_MotorHAT.BACKWARD)
        rightMotor.setSpeed(-rSpeed)

exiting = False
lastImg = None

def camWorker():
    global exiting
    global lastImg
    while not exiting:
        lastImg = getImage()
    print('camera thread exiting')

def getImage():
    # Clear the image array between captures
    imgArray.truncate(0)
    next(frameItr)

    img = imgArray.array

    # Drop some rows and columns to downsize the image
    img = img[0:1640:20, 0:1232:20]
    assert img.shape == (3, 80, 60), img.shape

    img = np.ascontiguousarray(img, dtype=np.uint8)

    return img

def signal_handler(signal, frame):
    global exiting

    print("exiting")

    exiting = True
    thread.join()

    # Stop the motors
    leftMotor.run(Adafruit_MotorHAT.RELEASE)
    rightMotor.run(Adafruit_MotorHAT.RELEASE)

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

# Start a new thread for the camera
thread = threading.Thread(target=camWorker)
thread.start()

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
    return socket.send(array, flags=0, copy=True, track=False)

def poll_socket(socket, timetick = 10):
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    # wait up to 10msec
    try:
        print("poller ready")
        while True:
            obj = dict(poller.poll(timetick))
            if socket in obj and obj[socket] == zmq.POLLIN:
                yield socket.recv_json()
    except KeyboardInterrupt:
        print ("stopping server")
        quit()

def handle_message(msg):
    if msg['command'] == 'action':
        print('received action')

        action = msg['action']
        print(action)


        #setMotors(left, right)


    elif msg['command'] == 'reset':
        print('got reset command')
    else:
        assert False, "unknown command"

    print('sending image')
    send_array(socket, lastImg)
    print('sent image')

for message in poll_socket(socket):
    handle_message(message)
