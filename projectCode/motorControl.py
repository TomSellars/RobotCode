#! usr/bin/python3

import RPi.GPIO as GPIO

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
DutyCycleA = 30
DutyCycleB = 30
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


def turnRight():
    pwmMotorAForward.ChangeDutyCycle(Stop)
    pwmMotorABackward.ChangeDutyCycle(DutyCycleA)
    pwmMotorBForward.ChangeDutyCycle(DutyCycleB)
    pwmMotorBBackward.ChangeDutyCycle(Stop)


def turnLeft():
    pwmMotorAForward.ChangeDutyCycle(DutyCycleA)
    pwmMotorABackward.ChangeDutyCycle(Stop)
    pwmMotorBForward.ChangeDutyCycle(Stop)
    pwmMotorBBackward.ChangeDutyCycle(DutyCycleB)