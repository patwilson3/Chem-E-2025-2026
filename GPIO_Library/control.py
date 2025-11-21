import threading 
from magnetic_stirrer import call_stirrer
from run_ina226 import call_ina_226
from a4988 import call_motor_driver
from led_spi import call_leds
from ads1115 import call_ads1115

event = threading.Event()

if __name__ == '__main__':
	h = lgpio.gpiochip_open(0)
	args_a4988 = [h, 12, 27] #chip_handle, STEP_PIN, DIR_PIN GOOD
	args_led = []
	args_ads1115 = [0x48, 1, 1] #addr, bus, read_buffer_time GOOD
	args_stirrer = [h, ] #chip_handle, pin WOMP WOMP
	args_ina226 = [0x40, 0.40, 0.0945, 18, 0.05] #args: addr, max_expected_amps, shunt_oms, bus_voltage, shunt_volts_max WOMP WOMP
	#speed --> womp womp
	#test buttons
	#motor works! 
	
	
	
