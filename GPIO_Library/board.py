import lgpio

class Board:
	_instance = None
		
	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._initialized = False
		return cls._instance

	def __init__(self):
		if self._initialized:
			return
		self._initialized = True
		self._spi_handle = {}
		self._gpio_handle = {}
		self._i2c_handle = {}
		
		self._closed = False
		
	def get_gpio_handle(self, chip):
		if chip not in self._gpio_handle:
			self._gpio_handle[chip] = lgpio.gpiochip_open(chip)
		return self._gpio_handle[chip]
		
	def get_spi_handle(self, bus, cs, freq):
		if bus not in self._spi_handle:
			self._spi_handle[bus] = []
		self._spi_handle[bus].append(lgpio.spi_open(bus, cs, freq))
		return self._spi_handle[bus]
		
	def get_i2c_handle(self, chip, addr):
		if addr in self._i2c_handle:
			raise ValueError("Address already in use")
		else:
			self._i2c_handle[addr] = lgpio.i2c_open(chip, addr)
			return self._i2c_handle[addr]
				
	def close_gpio(self):
		for key, value in self._gpio_handle.items():
			lgpio.gpiochip_close(value)
		self._gpio_handle = {}

	def close_i2c(self):
		for key, value in self._i2c_handle.items():
			lgpio.i2c_close(value)
		self._i2c_handle = {}
		
	def close_spi(self):
		for key, values in self._spi_handle.items():
			for value in values:
				lgpio.spi_close(value)
		self._spi_handle = {}
		
	def close(self):
		print("im free")
		if self._closed:
			print("im not free")
			return             
		self._closed = True
		self.close_gpio()
		self.close_i2c()
		self.close_spi()

