import time
import wiringpi
 
# use 'GPIO naming'
wiringpi.wiringPiSetupGpio()
 
# set up pins
# wiringpi.pinMode(18, wiringpi.GPIO.PWM_OUTPUT)
# wiringpi.pinMode(16, wiringpi.GPIO.INPUT) 
# wiringpi.pinMode(25, wiringpi.GPIO.INPUT)
# 
# # set the PWM mode to milliseconds stype
# wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
#  
# # divide down clock
# wiringpi.pwmSetClock(190)
# wiringpi.pwmSetRange(150)
#  
# delay_period = 0.0004

def init_pins():
    # set up pins
    wiringpi.pinMode(18, wiringpi.GPIO.PWM_OUTPUT)
    wiringpi.pinMode(16, wiringpi.GPIO.INPUT) 
    wiringpi.pinMode(25, wiringpi.GPIO.INPUT)
    # set the PWM mode to milliseconds
    wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
    # divide down clock
    wiringpi.pwmSetClock(190)
    wiringpi.pwmSetRange(150)

def lock_state():
    if (wiringpi.digitalRead(16) == 0): # blue pressed
        return True
    elif (wiringpi.digitalRead(25) == 0): # green pressed
        return False

def unlock():
    for pulse in range(0, 300, 1):
            wiringpi.pwmWrite(18, pulse)
            time.sleep(.0004)

go = True
init_pins()
while go:
    if lock_state() == False:
        unlock()
        go = False
  
  




