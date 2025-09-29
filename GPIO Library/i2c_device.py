import lgpio

class I2C_Device:
    def __init__(self, addr, i2c_bus):
        self._addr = addr
        self._i2c_bus = i2c_bus
        self._device_handle = lgpio.i2c_open(addr, i2c_bus)
    
    def close(self):
        lgpio.i2c_close(self._handle)

    
