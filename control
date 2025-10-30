#import lgpio

#CHIP_RASPBERRY_PI = 0
#BUTTON_PIN_IN = 22
#DEVICE_PIN_OUT = 23

#h = lgpio.gpiochip_open(CHIP_RASPBERRY_PI)
#lgpio.gpio_claim_input(h, BUTTON_PIN_IN)
#lgpio.gpio_claim_output(h, BUTTON_PIN_OUT)
#initial_device_readings = False
#try:
    #while True:
        #if lgpio.gpio_read(h, BUTTON_PIN_IN) == 1:
            #initial_device_readings = not initial_device_readings
            #lgpio.gpio_write(h, int(initial_device_readings))
            #print("The device is on")
        #else:
            #initial_device_readings = False
            #lgpio.gpio_write(h, int(initial_device_readings))
            #print("The device is off")
#except KeyboardInterrupt:
    #lgpio.gpiochip_close(h)