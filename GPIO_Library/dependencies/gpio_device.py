import lgpio
from .board import Board

class GPIO_Device:
	
	def __init__(self, chip, pin):
		self.board = Board()
		self.device_handle = self.board.get_gpio_handle(chip)
		self._pin = pin

	def claim_output(self):
		self.lgpio_claim_output(self.device_handle, self._pin)

	def claim_input(self):
		self.lgpio_claim_input(self.device_handle, self._pin)
		
	def get_handle(self):
		return self.device_handle

	def close(self):
		lgpio.gpio_free(self.device_handle, self._pin)
