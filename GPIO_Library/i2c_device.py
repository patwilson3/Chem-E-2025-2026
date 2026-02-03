import lgpio
from board import Board

class I2C_Device():
	def __init__(self, addr, i2c_bus):
		self.board = Board()
		self._addr = addr
		self._i2c_bus = i2c_bus
		self._device_handle = lgpio.i2c_open(i2c_bus, addr)#self.board.get_i2c_handle(i2c_bus, addr)
		print(self._device_handle)
		if self._device_handle < 0:
			raise RuntimeError(f"Failed to open I2C device at address 0x{addr:02x} on bus {i2c_bus}: {self._device_handle}")

	def close(self):
		"""Close the I2C device"""
		result = lgpio.i2c_close(self._device_handle)
		if result < 0:
			raise RuntimeError(f"Failed to close I2C device: {result}")
		return result

	def __enter__(self):
		"""Context manager entry"""
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""Context manager exit - ensures cleanup"""
		self.close()

	def get_handle(self):
		return self._device_handle

	def get_addr(self):
		return self._addr

	def get_bus(self):
		return self._i2c_bus


    
