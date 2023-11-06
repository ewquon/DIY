#!/usr/bin/env python
import os
from time import sleep
import RPi.GPIO as GPIO
from gpiozero import PWMLED
from signal import pause

# GPIO pin IDs
led_pin = 6
button_pin = 21

transitiontime = 3.0
nstep = 50 # distinct brightness levels

controlfile = '/home/equon/DIY/led_state'

#
# setup
#

GPIO.setmode(GPIO.BCM)
GPIO.setup(
        button_pin,
        GPIO.IN,
        pull_up_down=GPIO.PUD_DOWN) # initial value is pulled low (off)

led = PWMLED(led_pin)
deltaT = transitiontime / nstep

bstate = False
fading = False
fadefrom = -1
fadeto = -1
deltaval = None
prevreq = None

while True:

    # check control file
    if not fading:
        try:
            with open(controlfile,'r') as f:
                reqstr = f.readline().strip()
                if reqstr != prevreq:
                    prevreq = reqstr
                    reqval = float(reqstr) if reqstr != '' else None
        except IOError:
            #print('Control file',controlfile,'does not exist')
            pass
        except ValueError as err:
            print('Control file:',err)
        else:
            if (reqval is not None) \
                    and (reqval != led.value) \
                    and (reqval >= 0) and (reqval <= 1):
                print('Requested LED setting:',reqval)
                fadefrom = led.value
                fadeto = reqval
                deltaval = (fadeto - fadefrom) / nstep
                fading = True
                bstate = True if reqval > 0 else False

    # check for button press
    if (not fading) and (GPIO.input(21) == GPIO.HIGH):
        fadefrom = led.value
        bstate = not bstate
        print('boop',bstate,': fade from',fadefrom,'to',fadeto)
        fadeto = int(bstate)
        deltaval = (fadeto - fadefrom) / nstep
        fading = True

        # reset control file
        prevreq = None
        with open(controlfile,'w') as f:
            f.write(str(fadeto))

    # update LED
    elif fading:
        sleep(deltaT)
        newval = led.value + deltaval
        if (deltaval > 0) and (newval >= fadeto):
            led.value = fadeto
            fading = False
            print('max brightness',newval)
        elif (deltaval < 0) and (newval <= fadeto):
            led.value = fadeto
            fading = False
            print('min brightness',newval)
        else:
            led.value = newval
            print('current brightness:',newval)
    else:
        sleep(0.1)

