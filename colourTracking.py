#! /usr/bin/python3

import numpy as np
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import time
import sys
from avoidObstacle import turnLeft, turnRight, stopMotors

#Configure the picamera
camera = PiCamera()
camera.resolution = (320,240)
camera.rotation = 180
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(320,240))

#time for camera to stabilize
time.sleep(1)

selection = None
track_window = None
show_backproj = False
drag_start = None

#Mouse event for selecting the colour
def onmouse(event, x, y, flags, param):
    global selection, track_window, drag_start
    if event == cv2.EVENT_LBUTTONDOWN:
        drag_start = (x,y)
        track_window = None
    if drag_start:
        xmin = min(x, drag_start[0])
        ymin = min(y, drag_start[1])
        xmax = max(x, drag_start[0])
        ymax = max(y, drag_start[1])
        selection = (xmin, ymin, xmax, ymax)
    if event == cv2.EVENT_LBUTTONUP:
      drag_start = None
      track_window = (xmin, ymin, xmax - xmin, ymax - ymin)

#Create window to capture mouse events
cv2.namedWindow('camshift')
cv2.setMouseCallback('camshift', onmouse, 0)

#Processing the frames from the camera
for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):

  #grab each frame
  image = frame.array
  vis = image.copy()
  hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
  mask = cv2.inRange(hsv, np.array((0.,60.,32.)),np.array((180.,255.,255)))

  #use a mouse to select a region to track
  if selection:
    x0,y0,x1,y1 = selection
    hsv_roi = hsv[y0:y1, x0:x1]
    mask_roi = mask[y0:y1, x0:x1]
    hist = cv2.calcHist([hsv_roi], [0], mask_roi, [16], [0,180])
    cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
    hist = hist.reshape(-1)
    vis_roi = vis[y0:y1, x0:x1]
    cv2.bitwise_not(vis_roi,vis_roi)
    vis[mask==0] = 0

  if track_window and track_window[2] > 0 and track_window[3] > 0:
    selection = None
    prob = cv2.calcBackProject([hsv], [0], hist, [0,180], 1)
    prob &= mask
    term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    track_box, track_window = cv2.CamShift(prob, track_window, term_crit)

    if show_backproj:
      vis[:] = prob[...,np.newaxis]
    try:
      cv2.ellipse(vis, track_box, (0,0,255),2)
    except:
      print(track_box)
  
    pts = cv2.boxPoints(track_box)
    mp = np.mean(pts, axis=0)
    center = tuple(mp)

    ctrl_img = cv2.line(vis, center, (160, 120), (255, 0, 0), 2)

    if center[0] < 160:
      # turnLeft()
      print('turning left')
    elif center[0] > 160:
      # turnRight()
      print('turning right')
    else:
      # stopMotors()
      print('Stopping')

  #Drawing horizontal and verticle line passing through center of object
  cv2.imshow('camshift', vis)

  ctrl_img = cv2.line(vis, (0, 120), (320, 120), (255, 0, 0), 2)
  ctrl_img = cv2.line(vis, (160, 240), (160, 0), (255, 0, 0), 2)

  cv2.imshow('control', ctrl_img)


  ch = cv2.waitKey(5)

  #Refresh buffer
  rawCapture.truncate(0)

  if ch == 27:
    break
  if ch == ord('b'):
    show_backproj = not show_backproj

cv2.destroyAllWindows()