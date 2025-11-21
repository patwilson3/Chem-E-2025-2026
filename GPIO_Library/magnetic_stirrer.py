import lgpio
import time



def main():
	try:
		pin = 13
		h = lgpio.gpiochip_open(0)
		lgpio.gpio_claim_output(h, pin)
	
	while True:
		print("turning")
		lgpio.gpio_write(h, pin, 1)
		time.sleep(1/50)
		lgpio.gpio_write(h, pin, 0)
		time.sleep(1/500)
		
			
	except KeyboardInterrupt as e:
		pass
		
	finally:
		lgpio.gpio_write(h, pin, 0)
		lgpio.gpio_free(h, pin)
		lgpio.gpiochip_close(h)
		
def main2():
	
    pin = 13  # PWM pin connected to motor driver INPUT
    h = lgpio.gpiochip_open(0)

    # Claim pin for PWM
    lgpio.gpio_claim_output(h, pin)

    try:
        print("Starting motor…")
        # Run PWM at 20 kHz, 50% duty cycle
        lgpio.tx_pwm(h, pin, 20000, 0.5)

        time.sleep(5)

        print("Slowing motor…")
        lgpio.tx_pwm(h, pin, 20000, 0.2)

        time.sleep(5)

        print("Stopping motor…")
        lgpio.tx_pwm(h, pin, 20000, 0)

    except KeyboardInterrupt:
        pass
    finally:
        lgpio.tx_pwm(h, pin, 0, 0)  # stop PWM
        lgpio.gpiochip_close(h)

	
def call_stirrer(chip_handle, pin, stop_event):
	
	h = chip_handle 
	lgpio.gpio_claim_output(h, pin)
	
	while not stop_event.is_set():
		lgpio.gpio_write(h, pin, 1)
		time.sleep(1/50)
		lgpio.gpio_write(h, pin, 0)
		time.sleep(1/500)
	lgpio.gpio_write(h, pin, 0)
		time.sleep(1/500)
		lgpio.gpio_write(h, pin, 0)
		time.sleep(1/50)
		
	lgpio.gpio_free(h, pin)
	
	
if __name__ == '__main__':
	main()
