import threading 
from magnetic_stirrer import call_stirrer
from run_ina226 import call_ina_226
from a4988 import call_motor_driver
from led_spi import call_leds
from ads1115 import call_ads1115, init_ads1115
from online_alg import std_deviation_rate_of_change_alg_two_online
import lgpio
import traceback
import time

event = threading.Event()
ina_event = threading.Event()
CHIP   = 0
START  = 17 
RESET  = 27

def turn_on_motor(h, pin, stop_event):
	lgpio.gpio_write(h, pin, 1)
	while not stop_event.is_set():
		continue
	lgpio.gpio_write(h, pin, 0)
	lgpio.gpio_free(h, pin)

def wait_for_start(chip):
    """Block until START button is pressed."""

    lgpio.gpio_claim_alert(chip, START, lgpio.SET_PULL_DOWN, lgpio.RISING_EDGE)

    print("Waiting for START button...")
    while True:
        event = lgpio.gpio_read_event(chip, START) 
        if event:
            print("START pressed.")
            return


def reset_listener(chip, stop_event: threading.Event):
    """Wait for RESET press; when pressed, signal global stop."""
    lgpio.gpio_claim_alert(chip, RESET, lgpio.SET_PULL_DOWN, lgpio.RISING_EDGE)

    while not stop_event.is_set():
        event = lgpio.gpio_read_event(chip, RESET) 
        if event:
            print("RESET pressed → stopping everything.")
            stop_event.set()
            break


def loop():
	try:
		args_ina226 = [0x40, 0.40, 0.0945, 18, 0.05, ina_event]
		ina = threading.Thread(target=call_ina_226, args=args_ina226, daemon=True)
		ina.start()
		while True:
			event.clear()
			h = lgpio.gpiochip_open(CHIP)
			args_a4988 = [h, 12, 27] #chip_handle, STEP_PIN, DIR_PIN GOOD
			args_led = []
			args_stirrer = [h, 13, event] #chip_handle, pin GOOD, stopping_event
			motor_driver = threading.Thread(target=call_motor_driver, args=args_a4988, daemon=True)
			t_stirrer = threading.Thread(target=call_stirrer, args=args_stirrer, daemon=True)
			reset = threading.Thread(target=reset_listener, args=(h, event), daemon=True)
			algo = threading.Thread(target=std_deviation_rate_of_change_alg_two_online, args=[args_alg], daemon=True)


			try:
				t_stirrer.start()
				ads1115 = init_ads1115()
				args_alg = [10, 10, 2, 10, ads1115, event, 0.2, 120] #window=10,rot_window=10,threshold=5,hit_threshold=10,ads1115=None,stopping_event=None,period_s: float = 0.2,max_time_s = 150
				wait_for_start(h)
				algo.start()
				motor_driver.start()
				reset.start()

				algo.join() #alg will be recording data for like 120 seconds so reset button will not really work


			except Exception as e:
				traceback.print_exc()
			except KeyboardInterrupt as e:
				pass
			
			finally:
				event.set()
				lgpio.gpiochip_close(h)
	except Exception as e:
		pass
	finally:
		lgpio.gpiochip_close(h)
		ina_event.set()
			
         
          
	
	
	
