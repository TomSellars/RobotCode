#! usr/bin/python3

import numpy as np
import cv2
import time
import math
import io
from motorControl import turnLeft, turnRight, stopMotors
from picamera import PiCamera
from picamera.array import PiRGBArray

#Configure PiCamera
camera = PiCamera()
camera.resolution = (320,240)
camera.rotation = 180
camera.framerate = 16
rawCapture = PiRGBArray(camera, size=(320,240))

#Let the camera settle
time.sleep(1)

#Area selection using the mouse
selectionBox = []
currentMousePosition = np.ones(2, dtype=np.int32)
userSelecting = False

def onMouse(event, x, y, flags, params):
    global selectionBox
    global userSelecting

    currentMousePosition[0] = x
    currentMousePosition[1] = y

    if event == cv2.EVENT_LBUTTONDOWN:
        selectionBox = []
        box = [x,y]
        userSelecting = True
        selectionBox.append(box)
    elif event == cv2.EVENT_LBUTTONUP:
        box = [x,y]
        userSelecting = False
        selectionBox.append(box)

#Function for returning the center points of a rectangle
def center(points):
    x = np.float32((points[0][0] + points[1][0] + points[2][0] + points[3][0]) / 4.0)
    y = np.float32((points[0][1] + points[1][1] + points[2][1] + points[3][1]) / 4.0)
    return np.array([np.float32(x), np.float32(y)], np.float32)

def findCircle(image):
  #Bluring the image and convert to Black and White
  image = cv2.medianBlur(image, 5)
  image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  #Finding all the circles in the image
  circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, 1, 20, param1=70, param2=40, minRadius=10, maxRadius=100)

  if circles is not None:
    # circles = np.uint16(np.around(circles))
    return circles[0,:]
  else:
    return ["No Circle Found"]

#Creating a mouse callback
cv2.setMouseCallback("Circle Detection", onMouse, 0)
cropped = False

#variable for consistant circles
frameCount = 0

for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
  image = frame.array
  hsvImage = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

  #Starting a timer to see how long processing and display takes
  timerStart = cv2.getTickCount()

  #Display of selection box
  if(userSelecting):
    topLeft = (selectionBox[0][0], selectionBox[0][1])
    bottomRight = (currentMousePosition[0], currentMousePosition[1])
    cv2.rectangle(image, topLeft, bottomRight, (0, 255, 0), 2)

  if(frameCount is 4):
    for circle in circles:
      x = circle[0]
      y = circle[1]
      radius = circle[2]
      cv2.circle(image,(x,y),radius,(0,0,255),2)
  else:
    print("do something else here")

  #draw circles in RED
  circles = findCircle(image)
  if (circles[0] != "No Circle Found"):
    for circle in circles:
      x = circle[0]
      y = circle[1]
      radius = circle[2]
      cv2.circle(image,(x,y),radius,(0,0,255),2)
      #cv2.rectangle(image, ((x - radius) - 5, (y - radius) - 5), ((x + radius) + 5, (y + radius) + 5),(0,0,255), 2)

  #Display image
  cv2.imshow("Kalman Object Tracking", image)

  rawCapture.truncate(0)

  #Stop timer and convert to ms
  timerStop = ((cv2.getTickCount() - timerStart) / cv2.getTickFrequency()) * 1000

  key = cv2.waitKey(max(2, 40 - int(math.ceil(timerStop)))) & 0xFF
    
  if (key == ord('x')):
    break
  
stopMotors()
cv2.destroyAllWindows()