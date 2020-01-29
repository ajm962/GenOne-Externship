from tkinter import *
import RPi.GPIO as GPIO
import time
 
GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT)
pwm = GPIO.PWM(18, 100)
pwm.start(5)

GPIO.setup(16, GPIO.IN)
GPIO.setup(25, GPIO.IN)


class App:
	
    def __init__(self, master):
        frame = Frame(master)
        frame.pack()
        scale = Scale(frame, from_=0, to=90, 
              orient=HORIZONTAL, command=self.update)
        scale.grid(row=0)

## 16 = pin for limit switch on door
## NC so if switch is clicked then will read 0
if (GPIO.input(16) == 0):
    def update(self, angle):
        duty = float(angle) / 10.0 + 2.5
        pwm.ChangeDutyCycle(duty)

## 25 = pin for limit switch on deadbolt
## NO so if switch is clicked then will read 1
if (GPIO.input(25) == 1):
    def update(self, angle):
        duty = float(-(angle)) / 10.0 + 2.5
        pwm.ChangeDutyCycle(duty)


root = Tk()
root.wm_title('Servo Control')
app = App(root)
root.geometry("200x50+0+0")
root.mainloop()
if(KeyboardInterrupt):
    GPIO.cleanup()
