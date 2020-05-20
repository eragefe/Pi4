import RPi.GPIO as GPIO
import os

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

os.system('mpc clear')
os.system('mpc add alsa://hw:0,1')
os.system('mpc play')
GPIO.output(17, GPIO.LOW)
