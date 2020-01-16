import time
import wiringpi
 
# use 'GPIO naming'
wiringpi.wiringPiSetupGpio()
 
# set up pins
wiringpi.pinMode(18, wiringpi.GPIO.PWM_OUTPUT)
wiringpi.pinMode(16, wiringpi.GPIO.INPUT) 
wiringpi.pinMode(25, wiringpi.GPIO.INPUT)

# set the PWM mode to milliseconds stype
wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
 
# divide down clock
wiringpi.pwmSetClock(192)
wiringpi.pwmSetRange(150)
 
delay_period = 0.01
 
def update():
   
    if (GPIO.input(16) == 0):
        for pulse in range(667, 1000, 1):
                wiringpi.pwmWrite(18, pulse)
                time.sleep(delay_period)

    if (GPIO.input(25) == 0):
         for pulse in range(1000, 667, -1):
                wiringpi.pwmWrite(18, pulse)
                time.sleep(delay_period)  

try:
    while True :
        update()

except(KeyboardInterrupt):
    

