from i2c_device import I2C_Device

class Bus:
    def __init__(self):
        pass

    def scan(self) -> list:
        pass

    def get_device(self, device_obj) -> I2C_Device:
        pass

    def close(self):
        pass

    