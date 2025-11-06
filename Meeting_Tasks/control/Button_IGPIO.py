#import lgpio
#import threading
import threading
import time

#Author: Allen Vilan (Add name if you ever modify this)

#CHIP_RASPBERRY_PI = 0
#BUTTON_PIN_IN = 22
#DEVICE_PIN_OUT = 23

#h = lgpio.gpiochip_open(CHIP_RASPBERRY_PI)
#lgpio.gpio_claim_input(h, BUTTON_PIN_IN)
#lgpio.gpio_claim_output(h, BUTTON_PIN_OUT)
#initial_device_readings = False
#stop_event = threading.Event()

#def print_msg(msg):
    #while not stop_event.set():
        #print(msg)
        #time.sleep(1)

#try:
    #while True:
        #if lgpio.gpio_read(h, BUTTON_PIN_IN) == 1:
            #t1 = threading.Thread(target=print_msg, args=('thread 1 ',))
            #t2 = threading.Thread(target=print_msg, args=('thread 2 ',))
            #initial_device_readings = not initial_device_readings
            #lgpio.gpio_write(h, int(initial_device_readings))
            #print("The device is on")
            #t1.start()
            #t2.start()
        #else:
            #stop_event.set()
            #initial_device_readings = False
            #lgpio.gpio_write(h, int(initial_device_readings))
            #print("The device is off")
    #time.sleep(0.01)
#except KeyboardInterrupt:
    #lgpio.gpiochip_close(h)