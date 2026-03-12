import threading 
from dependencies.magnetic_stirrer import stirr, call_stirrer
from dependencies.run_ina226 import call_ina_226
from dependencies.led_spi import call_leds
from dependencies.ads1115 import init_ads1115
from dependencies.online_alg import std_deviation_rate_of_change_alg_two_online
from dependencies.stepper import stepper_worker #done
from dependencies.board import Board
from dependencies.LS8366R_control import run_ls7366r
from dependencies.ina226_move import INA226
from dependencies.dashboard import Dashboard
from dependencies.hutton import speed_worker
import lgpio
import traceback
import time


alg_event = threading.Event()
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
		time.sleep(0.05)

def dummy_algo(event):
	print("dummy alg start")
	time.sleep(120)
	event.set()
	print("dummy alg finished")

def reset_listener(h, stop_event: threading.Event, reset_event: threading.Event):
	"""Wait for RESET press; when pressed, signal global stop."""
	lgpio.gpio_claim_input(h, RESET, lgpio.SET_PULL_UP)
	lgpio.gpio_claim_alert(h, RESET, lgpio.FALLING_EDGE, 0)

	while not reset_event.is_set():
		event = lgpio.gpio_read(h, RESET) 
		if event == 0:
			print("\nRESET pressed stopping everything.\n")
			dashboard = Dashboard()
			dashboard.update_reset("RESET")
			stop_event.set()
			reset_event.set()
			lgpio.gpio_free(h, RESET)
			break
		time.sleep(0.05)

def loop():
	board = Board()
	dashboard = Dashboard()
	chip = 0
	threads = []
	h = lgpio.gpiochip_open(0)
	lgpio.gpio_claim_input(h, START, lgpio.SET_PULL_UP)
	lgpio.gpio_claim_alert(h, START, lgpio.FALLING_EDGE, 0)

	ads1115 = init_ads1115()
	args_stirrer = [chip, 13, reset_event]
	args_ina226 = [0x40, 0.40, 0.0945, 18, 0.05, ina_event]
	args_alg = (15, 15, 1, 10, ads1115, alg_event, 0.1, 100, reset_event)

	def hw_loop():
		try:
			while True:
				ina_event.clear()
				alg_event.clear()
				reset_event.clear()

				dashboard.update_start("READY")      # waiting for button press
				dashboard.update_reset("IDLE")
				dashboard.update_alg('IDLE')

				ina = threading.Thread(target=call_ina_226, args=args_ina226)
				speed = threading.Thread(target=speed_worker, args=[reset_event])
				stepper_motor = threading.Thread(target=stepper_worker)#g
				t_stirrer    = threading.Thread(target=stirr, args=args_stirrer)#g
				reset_button_listener        = threading.Thread(target=reset_listener, args=(h, alg_event, reset_event))
				car_motor    = threading.Thread(target=turn_on_motor, args=(h, 23, alg_event))
				#algo         = threading.Thread(target=dummy_algo, args=(event,), daemon=True)
				algo = threading.Thread(target=std_deviation_rate_of_change_alg_two_online, args=args_alg, daemon=True)

				threads = [ina, t_stirrer, car_motor]

				ina.start() #start recording battery readings
				wait_for_start(h) #wait for button press
				dashboard.update_start("RUNNING")

				t_stirrer.start() #once button is pressed stirrer begins
				speed.start()
				time.sleep(5) #let solution stir for 5 seconds before starting injection
				stepper_motor.start() #start injections
				algo.start() #start algorithm
				stepper_motor.join() #wait for injection to finish
				car_motor.start() #once injection is done start car motor
				reset_button_listener.start() #listen for reset button if pressed
				dashboard.update_reset("LISTENING")
				algo.join() #wait for algorithm to finish, note algorithm will call even to stop the car
				dashboard.update_start("BLOCKED")
				ina_event.set() #call for ina to finish recording data
				for t in [ina, t_stirrer, car_motor, reset_button_listener]:
					t.join()
				time.sleep(2)
				
				dashboard.update_reset("IDLE")

		except Exception as e:
			traceback.print_exc()
		finally:
			print("closing")
			alg_event.set()
			ina_event.set()
			lgpio.gpiochip_close(h)

	# hardware loop in background thread
	threading.Thread(target=hw_loop, daemon=True).start()

	# tkinter must own the main thread
	dashboard.run()



def test_control():
	time_to_run = 15
	start = time.time()

	h = lgpio.gpiochip_open(0)
	
	args_stirrer = [h, 13, reset_event]
	#args_ina226 = [0x40, 0.40, 0.0945, 18, 0.05, ina_event]
	ads115 = init_ads1115()
	#ina = threading.Thread(target=call_ina_226, args=args_ina226)
	stepper_motor = threading.Thread(target=stepper_worker)
	t_stirrer    = threading.Thread(target=call_stirrer, args=args_stirrer)

	
	t_stirrer.start()
	stepper_motor.start()
	while time.time() - start < time_to_run:
		print(ads115.get_adjusted_mvs())
		time.sleep(0.2)

	reset_event.set()
	t_stirrer.join()
	reset_event.clear()

	lgpio.gpiochip_close(h)
	

def test_ina_motor():
	time_to_run = 15
	start = time.time()

	h = lgpio.gpiochip_open(0)
	args_ina226 = [0x40, 0.40, 0.0945, 18, 0.05, ina_event]
	ina = threading.Thread(target=call_ina_226, args=args_ina226)
	car_motor    = threading.Thread(target=turn_on_motor, args=(h, 23, alg_event))

	ina.start()
	car_motor.start()

	while time.time() - start < time_to_run:
		continue

	ina_event.set()
	alg_event.set()
	ina.join()
	car_motor.join()

	lgpio.gpiochip_close(h)

if __name__ == '__main__':
	loop()
	#test_control()
	#test_ina_motor()
