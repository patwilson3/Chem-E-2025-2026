import lgpio
import time

BUTTON = 22
OUTPUT = 23

chip = lgpio.gpiochip_open(0)


lgpio.gpio_claim_intput(chip, BUTTON, lgpio.SET_PULL_DOWN)
lgpio.gpio_claim_output(chip, OUTPUT, 0, 0)


output_on = False

try:
    while True:
        curr = lgpio.gpio_read(chip, BUTTON)
        
        
        if curr == 1: #if button has been pressed
            output_on = not output_on #switch from on to off or off to on
        
            if output_on:
                lgpio.gpio_write(chip, OUTPUT, 1) #write output to on
            
            else:
                lgpio.gpio_write(chip, OUTPUT, 0) #write output to off 
        
        time.sleep(0.01)



except KeyboardInterrupt:
    lgpio.gpio_write(chip, OUTPUT, 0)
    lgpio.gpiochip_close(chip)

