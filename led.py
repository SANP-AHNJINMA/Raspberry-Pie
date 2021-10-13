import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings (False)
GPIO.setup(17,GPIO.OUT)

while(True):
    GPIO.output(17,False)
    time.sleep(16)
    GPIO.output(17,True)
    time.sleep(10)
