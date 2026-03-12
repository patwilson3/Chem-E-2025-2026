"""
Simple A4988 stepper driver wrapper for Raspberry Pi using lgpio.

- Uses BCM GPIO numbering (GPIO18, GPIO23, etc.).
- Assumes /dev/gpiochip0 is the chip to open (standard on Raspberry Pi).
- Supports:
- Single-step moves (blocking) with software timing
- Moves by angle (degrees)
- Continuous stepping via lgpio.tx_pwm()

Install dependency:
sudo apt install python3-lgpio

"""

import time
import lgpio
import traceback
from gpio_device import GPIO_Device


class A4988Stepper(GPIO_Device):

	MIN_STEP_FREQ_HZ = 1       # safety / sanity
	MAX_STEP_FREQ_HZ = 5000    # conservative upper bound for many setups

	def __init__(
		self,
		step_pin: int,
		dir_pin: int,
		enable_pin: int | None = None,
		steps_per_rev: int = 200,
		chip: int = 0,
		invert_dir: bool = False,
		ms1=None,
		ms2=None,
		ms3=None
	):
		#super().__init__(chip, enable_pin)
		self.ms1 = ms1
		self.ms2 = ms2
		self.ms3 = ms3
		self.step_pin = step_pin
		self.dir_pin = dir_pin
		self.enable_pin = enable_pin
		self.steps_per_rev = steps_per_rev
		self.invert_dir = invert_dir

		# Open gpiochip and claim pins
		self._chip_handle = lgpio.gpiochip_open(0)

		# STEP and DIR as outputs
		lgpio.gpio_claim_output(self._chip_handle, self.step_pin)
		lgpio.gpio_claim_output(self._chip_handle, self.dir_pin)

		# Optional EN pin
		if self.enable_pin is not None:
			lgpio.gpio_claim_output(self._chip_handle, self.enable_pin)
			# Default: driver enabled (EN is active low)
			lgpio.gpio_write(self._chip_handle, self.enable_pin, 0)

		if (
			self.ms1 is not None
			and self.ms2 is not None
			and self.ms3 is not None
		):
			lgpio.gpio_claim_output(self._chip_handle, self.ms1)
			lgpio.gpio_write(self._chip_handle, self.ms1, 0)

			lgpio.gpio_claim_output(self._chip_handle, self.ms2)
			lgpio.gpio_write(self._chip_handle, self.ms2, 0)

			lgpio.gpio_claim_output(self._chip_handle, self.ms3)
			lgpio.gpio_write(self._chip_handle, self.ms3, 0)

		# make sure STEP starts low
		lgpio.gpio_write(self._chip_handle, self.step_pin, 0)

		self._continuous_running = False
		self._continuous_freq = 0.0

	# ------------------------------------------------------------------
	# Basic low-level helpers
	# ------------------------------------------------------------------

	def enable(self):
		"""Enable the A4988 (EN active low)."""
		if self.enable_pin is not None:
			lgpio.gpio_write(self._chip_handle, self.enable_pin, 0)

	def disable(self):
		"""Disable the A4988 (EN active low)."""
		if self.enable_pin is not None:
			lgpio.gpio_write(self._chip_handle, self.enable_pin, 1)

	def set_direction(self, clockwise: bool = True):
		"""
		Set direction.
		"""
		val = 1 if clockwise else 0
		if self.invert_dir:
			val = 0 if val == 1 else 1
		lgpio.gpio_write(self._chip_handle, self.dir_pin, val)

	def _single_step(self, delay_s: float):
		"""
		Generate one step pulse on STEP pin with given delay.
		delay_s is the total time for one step (on+off).
		"""
		# Rising edge
		lgpio.gpio_write(self._chip_handle, self.step_pin, 1)
		time.sleep(delay_s / 2.0)
		# Falling edge
		lgpio.gpio_write(self._chip_handle, self.step_pin, 0)
		time.sleep(delay_s / 2.0)

	# ------------------------------------------------------------------
	# Blocking moves (software-timed)
	# ------------------------------------------------------------------

	def move_steps(
		self,
		steps: int,
		rpm: float | None = None,
		step_delay_s: float | None = None,
		clockwise: bool = True,
	):
		"""
		Move a given number of microsteps, blocking.
		"""
		if steps == 0:
			return

		# Handle sign of steps
		if steps < 0:
			steps = abs(steps)
			clockwise = not clockwise

		if (rpm is None) == (step_delay_s is None):
			raise ValueError("Specify exactly one of rpm or step_delay_s.")

		# Compute delay per step if rpm given
		if rpm is not None:
			if rpm <= 0:
				raise ValueError("rpm must be > 0.")
			steps_per_sec = (rpm / 60.0) * self.steps_per_rev
			if steps_per_sec <= 0:
				raise ValueError("steps_per_sec computed <= 0.")
			step_delay_s = 1.0 / steps_per_sec

		if step_delay_s <= 0:
			raise ValueError("step_delay_s must be > 0.")

		self.enable()
		self.set_direction(clockwise)

		for _ in range(steps):
			self._single_step(step_delay_s)

	def move_degrees(
		self,
		degrees: float,
		rpm: float,
		clockwise: bool = True,
	):
		"""
		Move by a given angle (degrees) at a given RPM, blocking.
		"""
		print("stepping")
		if rpm <= 0:
			raise ValueError("rpm must be > 0.")

		# Convert degrees to steps
		steps_float = (degrees / 360.0) * self.steps_per_rev
		steps = int(round(abs(steps_float)))

		if degrees < 0:
			clockwise = not clockwise

		self.move_steps(steps=steps, rpm=rpm, clockwise=clockwise)

	# ------------------------------------------------------------------
	# Continuous stepping using tx_pwm
	# ------------------------------------------------------------------

	def start_continuous(
		self,
		freq_hz: float,
		clockwise: bool = True,
		duty_cycle_percent: float = 50.0,
	):
		"""
		Start continuous stepping using tx_pwm on STEP pin.
		"""
		if freq_hz <= 0:
			raise ValueError("freq_hz must be > 0.")
		if freq_hz < self.MIN_STEP_FREQ_HZ or freq_hz > self.MAX_STEP_FREQ_HZ:
			raise ValueError(
				f"freq_hz out of allowed range "
				f"({self.MIN_STEP_FREQ_HZ}-{self.MAX_STEP_FREQ_HZ})"
			)
		if not (0.0 <= duty_cycle_percent <= 100.0):
			raise ValueError("duty_cycle_percent must be between 0 and 100.")

		self.enable()
		self.set_direction(clockwise)

		lgpio.gpio_claim_output(self._chip_handle, self.step_pin)

		lgpio.tx_pwm(
			self._chip_handle,
			self.step_pin,
			int(freq_hz),
			float(duty_cycle_percent),
		)

		self._continuous_running = True
		self._continuous_freq = float(freq_hz)

	def stop_continuous(self):
		"""Stop continuous stepping."""
		if self._continuous_running:
			lgpio.tx_pwm(self._chip_handle, self.step_pin, 0, 0.0)
			self._continuous_running = False
			self._continuous_freq = 0.0

	# ------------------------------------------------------------------
	# Cleanup
	# ------------------------------------------------------------------

	def cleanup(self):
		"""Stop motion, disable driver, and close gpiochip."""
		self.stop_continuous()
		self.disable()
		lgpio.gpiochip_close(self._chip_handle)

	def __del__(self):
		try:
			self.cleanup()
		except Exception:
			pass


def stepper_worker():
	stepper = A4988Stepper(
		step_pin=6,
		dir_pin=27,
		enable_pin=26,
		steps_per_rev=200,
		ms1=21,
		ms2=20,
		ms3=19
	)
	try:
		print("MOVING")
		stepper.move_degrees(945.0, rpm=100.0, clockwise=False)
	finally:
		stepper.disable()
		stepper.cleanup()

def test():
    h = lgpio.gpiochip_open(0)
    try:
        # Claim once
        lgpio.gpio_claim_output(h, 26, 1)  # initial level optional
        lgpio.gpio_claim_output(h, 27, 1)
        lgpio.gpio_claim_output(h, 12, 0)

        # Set initial states
        lgpio.gpio_write(h, 26, 1)
        lgpio.gpio_write(h, 27, 1)

        # Toggle without re-opening/re-claiming
        for _ in range(5):
            lgpio.gpio_write(h, 12, 1)
            time.sleep(1)
            lgpio.gpio_write(h, 12, 0)
            time.sleep(1)

    finally:
        # Optional explicit frees (good hygiene if this code is embedded in a larger app)
        try:
            lgpio.gpio_free(h, 12)
            lgpio.gpio_free(h, 26)
            lgpio.gpio_free(h, 27)
        except Exception:
            pass
        lgpio.gpiochip_close(h)
def test_class():
	try:
		stepper = A4988Stepper(
			step_pin=12,
			dir_pin=27,
			enable_pin=26,
			steps_per_rev=200,
			ms1=21,
			ms2=20,
			ms3=19
	)
		stepper.move_degrees(950.0, rpm=50.0, clockwise=False)
		time.sleep(1.5)
		stepper.move_degrees(950.0, rpm=50.0, clockwise=True)
	except Exception:
		traceback.print_exc()
	finally:
		stepper.cleanup()


if __name__ == '__main__':
	stepper_worker()
	#test()
