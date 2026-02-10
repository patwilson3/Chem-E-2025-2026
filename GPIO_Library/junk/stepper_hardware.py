from pathlib import Path
import traceback
import lgpio
import time

class PWM:
	def __init__(self, channel):
		self.channel = channel
		contruct_path = None
		if self.channel is None:
			raise ValueError
		construct_path = f'/sys/class/pwm/pwmchip{self.channel}/pwm{self.channel}'
		self.path = str(Path(construct_path))
	
	def _write(self, path:Path, value:int):
		try:
			path.write_text((str(value)))
		except Exception as e:
			traceback.print_exc()
	
	def set_period(self, value_ns:int):
		path = Path(self.path + '/period')
		self._write(path, value_ns)
		
	def set_duty_cycle(self, value_ns:int):
		path = Path(self.path + '/duty_cycle')
		self._write(path, value_ns)
	
	def enable(self):
		path = Path(self.path + '/enable')
		self._write(path, 1)
	
	def disable(self):
		path = Path(self.path + '/enable')
		self._write(path, 0)
	
if __name__ == '__main__':
	pwm = PWM(0)
	print(pwm.path)
	pwm.disable()
	pwm.set_duty_cycle(0)
	pwm.set_period(100000)
	pwm.set_duty_cycle(50000)
	dir_pin = 27
	enable_pin = 26
	
	h=lgpio.gpiochip_open(0)
	lgpio.gpio_claim_output(h, dir_pin)
	lgpio.gpio_claim_output(h, enable_pin)
	lgpio.gpio_write(h, dir_pin, 0)
	lgpio.gpio_write(h, enable_pin, 0)
	
	pwm.enable()
	time.sleep(5)
	pwm.disable()
	lgpio.gpio_write(h, enable_pin, 1)
	lgpio.gpio_free(h, dir_pin)
	lgpio.gpio_free(h, enable_pin)
	lgpio.gpiochip_close(h)
	 
	
