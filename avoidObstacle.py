import RPi.GPIO as GPIO
import time

# set GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set variables for GPIO motor pins
pinMotorAForward = 10
pinMotorABackward = 9
pinMotorBForward = 8
pinMotorBBackward = 7
pinLineFollower = 25
pinSonarTrigger = 17
pinSonarEcho = 18
pinLEDBlue = 23
pinLEDRed = 24

# PWN parameters
frequency = 30
DutyCycleA = 40
DutyCycleB = 40
Stop = 0

# distance variables
howNear = 10.0
reverseTime = 0.5
turnTime = 0.75

# set the GPIO pin mode
GPIO.setup(pinMotorAForward, GPIO.OUT)
GPIO.setup(pinMotorABackward, GPIO.OUT)
GPIO.setup(pinMotorBForward, GPIO.OUT)
GPIO.setup(pinMotorBBackward, GPIO.OUT)
GPIO.setup(pinLineFollower, GPIO.IN)
GPIO.setup(pinSonarTrigger, GPIO.OUT)
GPIO.setup(pinSonarEcho, GPIO.IN)
GPIO.setup(pinLEDBlue, GPIO.OUT)
GPIO.setup(pinLEDRed, GPIO.OUT)

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


def measure():
    GPIO.output(pinSonarTrigger, True)
    time.sleep(0.00001)
    GPIO.output(pinSonarTrigger, False)

    startTime = time.time()
    stopTime = startTime

    while GPIO.input(pinSonarEcho) == 0:
        startTime = time.time()
        stopTime = startTime

    while GPIO.input(pinSonarEcho) == 1:
        stopTime = time.time()
        if stopTime - startTime >= 0.04:
            print('Object to close')
            stopTime = startTime
            break
    elapsedTime = stopTime - startTime
    distance = (elapsedTime * 34300) / 2
    return distance


def nearObstacle(loaclhownear):
    distance = measure()
    print('near obstacle: ' + str(distance))
    if distance < loaclhownear:
      GPIO.output(pinLEDRed, GPIO.HIGH)
      GPIO.output(pinLEDBlue, GPIO.LOW)
      return True
    else:
      GPIO.output(pinLEDBlue, GPIO.HIGH)
      GPIO.output(pinLEDRed, GPIO.LOW)
      return False


def avoidObstacle():
    backward()
    time.sleep(reverseTime)
    stopMotors()

    turnRight()
    time.sleep(turnTime)
    if(nearObstacle(howNear)):
      turnLeft()
      time.sleep(turnTime)
      time.sleep(turnTime)
      stopMotors()

try:
    GPIO.output(pinSonarTrigger, False)

    # Allow module to settle
    time.sleep(0.1)

    while True:
        forward()
        time.sleep(0.1)
        if nearObstacle(howNear):
            stopMotors()
            avoidObstacle()
except KeyboardInterrupt:
    GPIO.cleanup()
