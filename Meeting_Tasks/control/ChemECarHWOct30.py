import lgpio
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
    previous_button_value=button_value