#! /usr/bin/python3

import numpy as np
import cv2
import time
import math
import io
import RPi.GPIO as GPIO
from picamera import PiCamera
from picamera.array import PiRGBArray

#Setting up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set variables for GPIO motor pins
pinMotorAForward = 10
pinMotorABackward = 9
pinMotorBForward = 8
pinMotorBBackward = 7

# PWN parameters
frequency = 30
DutyCycleA = 40
DutyCycleB = 40
Stop = 0

# set the GPIO pin mode
GPIO.setup(pinMotorAForward, GPIO.OUT)
GPIO.setup(pinMotorABackward, GPIO.OUT)
GPIO.setup(pinMotorBForward, GPIO.OUT)
GPIO.setup(pinMotorBBackward, GPIO.OUT)

# Set the GPIO to Software PWN at Frequency hertz
pwmMotorAForward = GPIO.PWM(pinMotorAForward, frequency)
pwmMotorABackward = GPIO.PWM(pinMotorABackward, frequency)
pwmMotorBForward = GPIO.PWM(pinMotorBForward, frequency)
pwmMotorBBackward = GPIO.PWM(pinMotorBBackward, frequency)

# set the duty cycle for the software PWM - initially to 0
pwmMotorAForward.start(Stop)
pwmMotorABackward.start(Stop)
pwmMotorBForward.start(Stop)
pwmMotorBBackward.start(Stop)

#Configure PiCamera
camera = PiCamera()
camera.resolution = (320,240)
camera.rotation = 180
camera.framerate = 16
rawCapture = PiRGBArray(camera, size=(320,240))

#Let the camera settle
time.sleep(1)

#Run in fullscreen
fullscreen = False

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

def stopMotors():
    pwmMotorAForward.ChangeDutyCycle(Stop)
    pwmMotorABackward.ChangeDutyCycle(Stop)
    pwmMotorBForward.ChangeDutyCycle(Stop)
    pwmMotorBBackward.ChangeDutyCycle(Stop)


def forward():
    pwmMotorAForward.ChangeDutyCycle(DutyCycleA)
    pwmMotorABackward.ChangeDutyCycle(Stop)
    pwmMotorBForward.ChangeDutyCycle(DutyCycleB)
    pwmMotorBBackward.ChangeDutyCycle(Stop)


def backward():
    pwmMotorAForward.ChangeDutyCycle(Stop)
    pwmMotorABackward.ChangeDutyCycle(DutyCycleA)
    pwmMotorBForward.ChangeDutyCycle(Stop)
    pwmMotorBBackward.ChangeDutyCycle(DutyCycleB)


def turnLeft():
    pwmMotorAForward.ChangeDutyCycle(Stop)
    pwmMotorABackward.ChangeDutyCycle(DutyCycleA)
    pwmMotorBForward.ChangeDutyCycle(DutyCycleB)
    pwmMotorBBackward.ChangeDutyCycle(Stop)


def turnRight():
    pwmMotorAForward.ChangeDutyCycle(DutyCycleA)
    pwmMotorABackward.ChangeDutyCycle(Stop)
    pwmMotorBForward.ChangeDutyCycle(Stop)
    pwmMotorBBackward.ChangeDutyCycle(DutyCycleB)

#setting up the kalman filter
kalman = cv2.KalmanFilter(4, 2, 0)
kalman.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
kalman.transitionMatrix = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], np.float32)
kalman.processNoiseCov = np.array([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], np.float32) * 0.03

#Setting up matrix for measure and prediction
measurement = np.array((2,1), np.float32)
prediction = np.array((2,1), np.float32)

#Creating windows by name
cv2.namedWindow("Kalman Object Tracking", cv2.WINDOW_NORMAL)
cv2.namedWindow("Hue histogram", cv2.WINDOW_NORMAL)

#Creating sliders for HSV selection thresholding
def nothing(x):
    pass

#Creating a mouse callback
cv2.setMouseCallback("Kalman Object Tracking", onMouse, 0)
cropped = False

#Setting up when the search should stop
cancelSearch = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 5)

#variabels for direction trends
frameCount = 0
directionLeft = 0
directionRight = 0

#Stopps any potentially running motors
stopMotors()

#Camera Capture
for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
    image = frame.array
    hsvImage = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    #Starting a timer to see how long processing and display takes
    timerStart = cv2.getTickCount()

    if(len(selectionBox) > 1) and (selectionBox[0][1] < selectionBox[1][1]) and (selectionBox[0][0] < selectionBox[1][0]):
      
      #Cropping the frame to the selected area
      crop = hsvImage[selectionBox[0][1]:selectionBox[1][1], selectionBox[0][0]:selectionBox[1][0]].copy()
      
      #size of the cropped area
      cropHeight, cropWidth, c = crop.shape
      if(cropHeight > 0) and (cropWidth > 0):
        cropped = True

        #Select all hue values and Saturation. Eleliminate values with very low saturation or value due to lack of useful information
        mask = cv2.inRange(crop, np.array((0., 60., 32.)), np.array((180., 255., 255.)))

        #histogram of hue and saturation values and normalize it
        cropHist = cv2.calcHist([crop], [0,1], mask, [180, 255], [0, 180, 0, 255])
        cropHist = cv2.normalize(cropHist, cropHist, 0, 255, cv2.NORM_MINMAX)

        #set inital position of object
        trackWindow = (selectionBox[0][0], selectionBox[0][1], selectionBox[1][0] - selectionBox[0][0], selectionBox[1][1] - selectionBox[0][1])
      
      #Reset the list of boxes
      selectionBox = []

    #Display of selection box
    if(userSelecting):
      topLeft = (selectionBox[0][0], selectionBox[0][1])
      bottomRight = (currentMousePosition[0], currentMousePosition[1])
      cv2.rectangle(image, topLeft, bottomRight, (0, 255, 0), 2)
      
    #If there is a selected region
    if(cropped):
        
      #back projection of histogram based on Hue and Saturation
      imgBackProject = cv2.calcBackProject([hsvImage], [0,1], cropHist, [0, 180, 0, 255], 1)
      cv2.imshow("Hue histogram", imgBackProject)

      #apply camshift to predict new location
      ret, trackWindow = cv2.CamShift(imgBackProject, trackWindow, cancelSearch)

      #draw observation in BLUE
      observX, observY, observW, observH = trackWindow
      cv2.rectangle(image, (observX, observY), (observX + observW, observY + observH), (255, 0, 0), 2)

      #get the centre of this observation and update kalmanFilter
      observPoints = cv2.boxPoints(ret)
      observPoints = np.int0(observPoints)
      observCenter = center(observPoints)
      #print(observCenter)
      kalman.correct(observCenter)

      #Get the new prediction
      prediction = kalman.predict()

      #Draw the prediction in GREEN
      cv2.rectangle(image,(int(prediction[0] - (0.5 * observW)), int(prediction[1] - (0.5 * observH))),(int(prediction[0] + (0.5 * observW)),int(prediction[1] + (0.5 * observH))),(0, 255, 0), 2)

      observCenter = tuple(observCenter)

      image = cv2.line(image, observCenter, (160, 120), (255,0,0), 2)
      
      if (frameCount is 3):
        if (directionRight > directionLeft):
          turnRight()
        elif (directionLeft > directionRight):
          turnLeft()
        else:
          print('ONWARD')
        frameCount = 0
        directionLeft = 0
        directionRight = 0
        stopMotors()
      else:
        if(observCenter[0] < 140):
          directionLeft += 1
        elif(observCenter[0] > 180):
          directionRight += 1
        frameCount += 1
      
      print(frameCount)


    image = cv2.line(image, (0,120), (320, 120), (255,0,0), 2)
    image = cv2.line(image, (160, 240), (160, 0), (255,0,0),2)

    #Display image
    cv2.imshow("Kalman Object Tracking", image)
    cv2.setWindowProperty("Kalman Object Tracking", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN & fullscreen)

    rawCapture.truncate(0)

    #Stop timer and convert to ms
    timerStop = ((cv2.getTickCount() - timerStart) / cv2.getTickFrequency()) * 1000

    key = cv2.waitKey(max(2, 40 - int(math.ceil(timerStop)))) & 0xFF
    
    if (key == ord('x')):
      break
  

cv2.destroyAllWindows()



