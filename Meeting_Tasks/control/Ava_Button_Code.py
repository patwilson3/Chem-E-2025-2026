import time
import lgpio
import threading
import button_on

h=lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h,22)
lgpio.gpio_claim_output(h,23)
output_device=0
previous_button_value=0

while True:
    button_value=lgpio.gpio_read(h,22)
    if button_value==1 and previous_button_value==0:
        output_device=1-output_device
        lgpio.gpio_write(h,23,output_device)
        thread_1=threading.Thread(target=button_on.button_on_one, args=('One', 1))
        thread_2=threading.Thread(target=button_on.button_on_two, args=('Two', 1))
        thread_1.start()
        thread_2.start()
    previous_button_value=button_value
    time.sleep(0.01)