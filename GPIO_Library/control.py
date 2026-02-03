import threading 
from magnetic_stirrer import stirr
from run_ina226 import call_ina_226
from a4988 import call_motor_driver, A4988
from led_spi import call_leds
from ads1115 import init_ads1115
from online_alg import std_deviation_rate_of_change_alg_two_online
from stepper import stepper_worker
from board import Board
import lgpio
import traceback
import time


event = threading.Event()
ina_event = threading.Event()
reset_event = threading.Event()
START  = 25
RESET  = 24


def turn_on_motor(h, pin, stop_event):
	lgpio.gpio_write(h, pin, 1)
	while not stop_event.is_set():
		continue
	lgpio.gpio_write(h, pin, 0)
	lgpio.gpio_free(h, pin)

def wait_for_start(h):
	"""Block until START button is pressed."""

	print("Waiting for START button...")
	while True:
		event = lgpio.gpio_read(h, START) 
		if event == 0:
			print("START pressed.")
			return

def dummy_algo(event):
	print("dummy alg start")
	time.sleep(120)
	event.set()
	print("dummy alg finished")

def reset_listener(h, stop_event: threading.Event, reset_event):
	"""Wait for RESET press; when pressed, signal global stop."""
	lgpio.gpio_claim_input(h, RESET, lgpio.SET_PULL_UP)
	lgpio.gpio_claim_alert(h, RESET, lgpio.FALLING_EDGE, 0)

	while not reset_event.is_set():
		event = lgpio.gpio_read(h, RESET) 
		if event == 0:
			print("\nRESET pressed stopping everything.\n")
			stop_event.set()
			reset_event.set()
			lgpio.gpio_free(h, RESET)
			break

def loop():
	board = Board()
	chip = 0
	threads = []
	h = lgpio.gpiochip_open(0)
	lgpio.gpio_claim_input(h, START, lgpio.SET_PULL_UP)
	lgpio.gpio_claim_alert(h, START, lgpio.FALLING_EDGE, 0)
	
	try:
		ads1115 = init_ads1115()
		args_stirrer = [chip, 13, reset_event]
		args_ina226 = [0x40, 0.40, 0.0945, 18, 0.05, ina_event]
		args_alg = (15, 15, 3, 10, ads1115, event, 0.2, 120, reset_event)

		while True:
			ina_event.clear()
			event.clear()
			reset_event.clear()

			ina = threading.Thread(target=call_ina_226, args=args_ina226)
			motor_driver = threading.Thread(target=stepper_worker)#g
			t_stirrer    = threading.Thread(target=stirr, args=args_stirrer)#g
			reset        = threading.Thread(target=reset_listener, args=(h, event, reset_event))
			car_motor    = threading.Thread(target=turn_on_motor, args=(h, 23, reset_event))
			#algo         = threading.Thread(target=dummy_algo, args=(event,), daemon=True)
			algo = threading.Thread(target=std_deviation_rate_of_change_alg_two_online, args=args_alg, daemon=True)

			threads = [ina, t_stirrer, car_motor]

			ina.start()
			wait_for_start(h)
			t_stirrer.start()
			time.sleep(2)
			motor_driver.start()
			algo.start()
			motor_driver.join()
			car_motor.start()
			reset.start()
			algo.join()
			ina_event.set()
			time.sleep(10)
			
	except Exception as e:
		traceback.print_exc()
	finally:
		event.set()
		ina_event.set()
		lgpio.gpiochip_close(h)

if __name__ == '__main__':
	loop()
