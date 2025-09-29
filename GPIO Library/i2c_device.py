import lgpio

class I2C_Device:
    def __init__(self, addr, i2c_bus):
        self._addr = addr
        self._i2c_bus = i2c_bus
        self._device_handle = lgpio.i2c_open(i2c_bus, addr)
    
    def close(self):
        lgpio.i2c_close(self._handle)

    def get_handle(self):
        return self._device_handle

    def get_addr(self):
        return self._addr

    def get_bus(self)
        return self._i2c_bus
        

    
