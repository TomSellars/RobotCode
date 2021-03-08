#! /usr/bin/python3

import numpy as np
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import time

#Configure the picamera
camera = PiCamera()
camera.resolution = (640,480)
camera.rotation = 180
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640,480))

#time for camera to stabilize
time.sleep(1)

selction = None
track_window = None
show_backproj = False
drag_start = None

def onmouse(event, x, y, flags, param):
    global selection, track_window, drag_start
    if event == cv2.EVENT_LBUTTONDOWN:
        drag_start = (x,y)
        track_window = None
    if drag_start:
        xmin = min(x, 
