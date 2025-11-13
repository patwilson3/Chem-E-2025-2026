#import lgpio
#import threading
#import time

#Author: Allen Vilan (Add name if you ever modify this)

#CHIP_RASPBERRY_PI = 0
#BUTTON_PIN_IN = 22
#DEVICE_PIN_OUT = 23
#PIN_VOLTMETER = 24 #arbitrary pin for the voltmeter
#need arbitrary analog converter to translate readings from INA226

#h = lgpio.gpiochip_open(CHIP_RASPBERRY_PI)
#lgpio.gpio_claim_input(h, BUTTON_PIN_IN)
#lgpio.gpio_claim_input(h, PIN_VOLTMETER)
#lgpio.gpio_claim_output(h, BUTTON_PIN_OUT)
#initial_device_readings = False

#event_threadings = threading.Event()

#def analog_voltmeter_ampmeter(h, pin_voltmeter):
    #try:
        #while True:
            #if not event_threading.set():
                #volt_reads = lgpio.gpio_read(h, pin_voltmeter)
                #print(volt_reads)
                #time.sleep(1) #arbitrary time to sleep
    #except KeyboardInterrupt:
        #arbitrary exception
    #obviously needs more work since we need to translate the 1s, 0s in a readable voltage output

#t1 = threading.Thread(target=analog_voltmeter_ampmeter, args=(h, PIN_VOLTMETER))
#t1.start()

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
            #event_threadings.set()
    #time.sleep(0.5)
#except KeyboardInterrupt:
    #lgpio.gpiochip_close(h)