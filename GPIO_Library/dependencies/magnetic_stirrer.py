import lgpio
import time
from .gpio_device import GPIO_Device

class Magnetic_Stirrer(GPIO_Device):
	def __init__(self, chip, pin):
		
		#super().__init__(chip, pin)
		self.device_handle = lgpio.gpiochip_open(0)
		self.pin = pin
		lgpio.gpio_claim_output(self.device_handle, self.pin)
		self.is_on = False
		
	def on(self, pulse_width, period, event):
		
		while not event.is_set():
			lgpio.gpio_write(self.device_handle, self.pin, 1)
			time.sleep(1/pulse_width)
			lgpio.gpio_write(self.device_handle, self.pin, 0)
			time.sleep(1/period)
		lgpio.gpio_write(self.device_handle, self.pin, 0)
			
	def off(self):
		self.is_on = False

def stirr(chip, pin, event):
	try:
		stirrer = Magnetic_Stirrer(chip=0, pin=13)
		stirrer.on(50, 500, event)
	except Exception as e:
		pass
	finally:
		lgpio.gpio_write(stirrer.device_handle, stirrer.pin, 0)
		lgpio.gpiochip_close(stirrer.device_handle)

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

def call_stirrer_test(chip_handle, pin):
	start = time.time()
	h = chip_handle 
	lgpio.gpio_claim_output(h, pin)
	
	while time.time() - start < 10:
		lgpio.gpio_write(h, pin, 1)
		time.sleep(1/50)
		lgpio.gpio_write(h, pin, 0)
		time.sleep(1/500)
		
	lgpio.gpio_free(h, pin)	

def call_stirrer(chip_handle, pin, stop_event):
	
	h = chip_handle 
	lgpio.gpio_claim_output(h, pin)
	
	while not stop_event.is_set():
		lgpio.gpio_write(h, pin, 1)
		time.sleep(1/50)
		lgpio.gpio_write(h, pin, 0)
		time.sleep(1/500)
		
	lgpio.gpio_free(h, pin)
	
	
if __name__ == '__main__':
	h = lgpio.gpiochip_open(0)
	call_stirrer_test(h, 13)
	lgpio.gpiochip_close(h)